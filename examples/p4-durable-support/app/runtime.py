"""Composed Task 2 API and durable normalized-response control flow.

The worker CLI only claims; trusted host code calls consume_response/resume_turn.
There is no automatic provider call or outbound delivery in this milestone.
"""
from hashlib import sha256
import json
from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header, HTTPException, Response

from support_agent.providers import normalize_response, _value, _plain
from .actions import propose_turn, authorize_action, validate_frozen, move_action
from .api import authorized_connection, read_task, read_events
from .db import create_task, connect
from .models import TaskCreate, TaskView, EventPage
from .worker import fence, transition, release_slots
from .db import append_event
from psycopg.types.json import Jsonb


def _validate_final_output(conn, task, output):
    """Validate a bounded structured answer and every citation against live ACL state.

    This proves citation provenance/current visibility, not semantic entailment.
    """
    if not isinstance(output, dict) or set(output) != {'outcome', 'text', 'citations'}:
        raise ValueError('Final output must contain exactly outcome, text, and citations')
    if not isinstance(output['outcome'], str) or output['outcome'] not in {'answer', 'clarify', 'refuse'}:
        raise ValueError('Invalid final outcome')
    text = output['text']
    citations = output['citations']
    if not isinstance(text, str) or not text.strip() or len(text) > 20000:
        raise ValueError('Final text must be non-empty and bounded')
    if not isinstance(citations, list) or len(citations) > 50:
        raise ValueError('Citations must be a bounded list')
    seen = set()
    normalized = []
    # Serialize with retrieval ACL/index lifecycle mutations and retain row locks
    # until output+completion commit, so citations cannot go stale mid-finalize.
    from .retrieval import _tenant_lock
    _tenant_lock(conn, task['tenant_id'])
    for citation in citations:
        if not isinstance(citation, dict) or set(citation) != {'resource_id', 'version', 'chunk_id'}:
            raise ValueError('Invalid citation shape')
        resource_id, version, chunk_id = citation['resource_id'], citation['version'], citation['chunk_id']
        if (not isinstance(resource_id, str) or not resource_id or len(resource_id) > 200
                or isinstance(version, bool) or not isinstance(version, int) or version <= 0
                or not isinstance(chunk_id, str)):
            raise ValueError('Invalid citation values')
        try:
            chunk_uuid = UUID(chunk_id)
        except (ValueError, TypeError, AttributeError) as exc:
            raise ValueError('Invalid citation chunk id') from exc
        if chunk_uuid in seen:
            raise ValueError('Duplicate citation')
        seen.add(chunk_uuid)
        source = conn.execute('''SELECT 1 FROM chunks c JOIN documents d ON d.id=c.document_id
            JOIN resources r ON r.tenant_id=d.tenant_id AND r.resource_id=d.resource_id
            JOIN resource_acl a ON a.tenant_id=r.tenant_id AND a.resource_id=r.resource_id
            JOIN caller_identities u ON u.tenant_id=a.tenant_id AND u.caller_id=a.caller_id
            JOIN index_versions i ON i.id=d.index_version AND i.tenant_id=d.tenant_id
            WHERE c.id=%s AND c.tenant_id=%s AND c.resource_id=%s
              AND d.doc_version=%s AND d.doc_version=r.version AND d.acl_version=r.acl_version
              AND r.deleted_at IS NULL AND d.deleted_at IS NULL AND a.caller_id=%s AND a.allowed
              AND u.active AND 'caller'=ANY(u.roles) AND i.state='active'
            FOR SHARE OF c,d,r,a,u,i ''',
            (chunk_uuid, task['tenant_id'], resource_id, version, task['owner_id'])).fetchone()
        if not source:
            raise ValueError('Citation is missing, stale, deleted, or not currently authorized')
        normalized.append({'resource_id': resource_id, 'version': version, 'chunk_id': str(chunk_uuid)})
    return {'outcome': output['outcome'], 'text': text.strip(), 'citations': normalized}


def finalize_output(conn, lease, output):
    """Validate, persist output, complete task and append event in caller transaction."""
    task = fence(conn, lease)
    if not task:
        return 0
    if task['status'] != 'running':
        raise ValueError('Only a running task can be completed')
    validated = _validate_final_output(conn, task, output)
    unresolved = conn.execute("SELECT 1 FROM actions WHERE task_id=%s AND (status!='succeeded' OR result IS NULL) LIMIT 1",
                              (lease.task_id,)).fetchone()
    missing_write_receipt = conn.execute('''SELECT 1 FROM actions a LEFT JOIN outbox o ON o.action_id=a.id
        WHERE a.task_id=%s AND a.tool='send_notice'
          AND (a.status!='succeeded' OR a.result IS NULL OR o.status!='succeeded' OR o.receipt IS NULL)
        LIMIT 1''', (lease.task_id,)).fetchone()
    if unresolved or missing_write_receipt:
        raise ValueError('Completion requires all actions and delivery receipts resolved')
    canonical = json.dumps(validated, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False)
    digest = sha256(canonical.encode('utf-8')).hexdigest()
    conn.execute('INSERT INTO final_outputs(task_id,output,output_hash,execution_epoch) VALUES (%s,%s,%s,%s)',
                 (lease.task_id, Jsonb(validated), digest, lease.epoch))
    changed = conn.execute("""UPDATE tasks SET status='completed',state_version=state_version+1,
        lease_owner=NULL,lease_until=NULL WHERE id=%s AND status='running'""", (lease.task_id,)).rowcount
    if changed != 1:
        raise ValueError('Task completion lost its state transition')
    release_slots(conn, lease.task_id)
    append_event(conn, lease.task_id, 'task.completed', {'output_hash': digest})
    return 1


def resume_turn(conn, lease):
    task=fence(conn,lease)
    if not task:
        return []
    ids=task['checkpoint'].get('pending_action_ids',[])
    actions=[]
    for action_id in ids:
        action=conn.execute('SELECT * FROM actions WHERE id=%s AND task_id=%s FOR UPDATE',(UUID(action_id),lease.task_id)).fetchone()
        if action is None:
            raise ValueError('Checkpoint action missing')
        if action['status']=='waiting_approval':
            authorize_action(conn,lease,action['id'])
        elif action['status'] in ('proposed','authorized_pending_delivery') and not validate_frozen(conn,task,action):
            move_action(conn,action,'invalidated')
        action=conn.execute('SELECT * FROM actions WHERE id=%s',(action['id'],)).fetchone()
        actions.append(action)
    if any(a['status'] in ('invalidated','denied','cancelled') for a in actions):
        transition(conn,lease,'failed')
    return actions


def consume_response(conn, lease, response):
    """Reuse Stage 3 normalization; final output still requires host validation."""
    if not fence(conn,lease):
        return []
    outcome=normalize_response(response)
    if outcome.kind=='tool_calls':
        calls=[{'id':_value(c,'id'),'name':_value(c,'name'),'input':_plain(_value(c,'input'))}
               for c in outcome.content if _value(c,'type')=='tool_use']
        return propose_turn(conn,lease,calls)
    if outcome.kind!='final':
        transition(conn,lease,'failed')
    return []


def consume_saved_response(conn, lease, request_id):
    """Fenced, idempotent consumption of one durably saved provider response."""
    from .provider_calls import get_call, mark_processed
    from .actions import propose_turn
    from .worker import fence
    from support_agent.tool_gateway import MAX_TOOL_CALLS

    task = fence(conn, lease)
    if not task:
        return {"status": "stale"}
    call = get_call(conn, request_id)
    if not call or call["task_id"] != lease.task_id or call["release_id"] != task["release_id"]:
        return {"status": "missing"}
    if call["state"] != "response_saved":
        return {"status": "already_consumed" if call["state"] == "processed" else call["state"]}
    try:
        outcome = normalize_response(call["response_body"])
    except (TypeError, ValueError):
        if mark_processed(conn, lease, request_id):
            transition(conn, lease, "failed")
        return {"status": "failed"}
    if not mark_processed(conn, lease, request_id):
        return {"status": "stale"}
    if outcome.kind == "tool_calls":
        calls = []
        seen = set()
        for block in outcome.content:
            if _value(block, "type") != "tool_use":
                continue
            call_id = _value(block, "id")
            name = _value(block, "name")
            args = _plain(_value(block, "input"))
            if not isinstance(call_id, str) or not call_id or call_id in seen or len(call_id) > 200:
                transition(conn, lease, "failed")
                return {"status": "failed"}
            seen.add(call_id)
            calls.append({"id": call_id, "name": name, "input": args})
        if not calls or len(calls) > MAX_TOOL_CALLS:
            transition(conn, lease, "failed")
            return {"status": "failed"}
        ids = propose_turn(conn, lease, calls, request_id=request_id)
        current = conn.execute("SELECT status FROM tasks WHERE id=%s", (lease.task_id,)).fetchone()
        return {"status": "actions_proposed" if current["status"] == "running" else current["status"],
                "action_ids": [str(item) for item in ids]}
    if outcome.kind == "refusal":
        refusal = " ".join(str(_value(block, "refusal", "")).strip() for block in outcome.content
                            if _value(block, "type") == "refusal").strip()
        if refusal and finalize_output(conn, lease, {"outcome": "refuse", "text": refusal, "citations": []}):
            return {"status": "completed"}
    if outcome.kind == "final":
        text = "".join(str(_value(block, "text", "")) for block in outcome.content if _value(block, "type") == "text")
        try:
            output = json.loads(text)
            if finalize_output(conn, lease, output):
                return {"status": "completed"}
        except (json.JSONDecodeError, TypeError, ValueError):
            pass
    transition(conn, lease, "failed")
    return {"status": "failed"}


def create_app(settings=None):
    from .main import create_app as base_app
    from .approvals import router
    from .delivery import router as delivery_router
    app=base_app(settings)
    # FastAPI 0.146 keeps included routers deferred. Compose from the public
    # compatibility read handlers, keeping only the base health/docs routes.
    base_paths={'/openapi.json','/docs','/docs/oauth2-redirect','/redoc','/health/live'}
    app.router.routes[:]=[r for r in app.router.routes if getattr(r,'path',None) in base_paths]
    app.add_api_route('/v1/tasks/{task_id}',read_task,methods=['GET'],response_model=TaskView)
    app.add_api_route('/v1/tasks/{task_id}/events',read_events,methods=['GET'],response_model=EventPage)
    app.include_router(router)
    app.include_router(delivery_router)

    @app.post('/v1/tasks',response_model=TaskView,status_code=201)
    def submit(payload:TaskCreate,response:Response,
               idempotency_key:Annotated[str,Header(min_length=1,max_length=200)],
               context=Depends(authorized_connection,scope='function')):
        conn,principal=context
        conn.execute('SELECT pg_advisory_xact_lock(4002003)')
        old=conn.execute('SELECT 1 FROM idempotency_records WHERE tenant_id=%s AND caller_id=%s AND idempotency_key=%s',
                         (principal.tenant_id,principal.caller_id,idempotency_key)).fetchone()
        cap=conn.execute('SELECT queue_limit FROM service_limits WHERE singleton').fetchone()['queue_limit']
        queued=conn.execute("SELECT count(*) AS n FROM tasks WHERE status='queued' AND deadline>clock_timestamp()").fetchone()['n']
        if not old and queued>=cap:
            raise HTTPException(429,detail={'code':'queue_full','message':'Durable queue capacity reached'},headers={'Retry-After':'1'})
        row,created=create_task(conn,principal,idempotency_key,payload)
        response.status_code=201 if created else 200
        response.headers['Location']=f"/v1/tasks/{row['id']}"
        return row

    @app.get('/health/ready')
    def ready():
        with connect(app.state.settings.database_url) as conn:
            required={'0001_base.sql','0002_execution.sql','0003_delivery.sql','0004_manual_resolution.sql','0005_provider_calls.sql','0006_final_outputs.sql'}
            applied={row['version'] for row in conn.execute('SELECT version FROM schema_migrations').fetchall()}
            if not required.issubset(applied):
                raise HTTPException(503,detail={'code':'schema_unavailable','message':'Required migration missing'})
        return {'status':'ready'}
    return app


async def execute_reads(conn, lease, session, *, budget_account):
    """Resume only stored read calls through Stage 3's read-only MCP contract.

    No calls occur while the entire turn is waiting for approval. Delivery remains
    blocked for Task 3; actual read results are persisted independently and never
    regenerated as successful placeholders on restart. This coordinator commits
    each reservation + sent marker before the MCP request; do not wrap it in a
    larger atomic transaction. Process death cannot refund an already sent call.
    """
    from psycopg.types.json import Jsonb
    from support_agent.tool_gateway import provider_tools, validate_tool_arguments, ALLOWED_TOOLS
    task=fence(conn,lease)
    if not task:
        return []
    actions=resume_turn(conn,lease)
    if not fence(conn,lease):
        return []
    listed=await session.list_tools()
    schemas={t['name']:t['input_schema'] for t in provider_tools(list(_value(listed,'tools',[])))}
    results=[]
    for action in actions:
        if action['status']!='proposed' or action['tool'] not in ALLOWED_TOOLS:
            continue
        if action['tool'] not in schemas or not validate_tool_arguments(schemas[action['tool']],action['args'])[0]:
            move_action(conn,action,'invalidated')
            transition(conn,lease,'failed')
            return results
        if not validate_frozen(conn,task,action):
            move_action(conn,action,'invalidated')
            transition(conn,lease,'failed')
            return results
        from .limits import reserve, mark_sent, reconcile, release_unsent
        reservation=reserve(conn,lease,budget_account,tokens=0,tools=1)
        if reservation is None:
            transition(conn,lease,'failed')
            return results
        if not mark_sent(conn,reservation):
            release_unsent(conn,reservation)
            return results
        # Persist conservative send intent before crossing the process boundary.
        # A crash after commit leaves reserved usage; it is never auto-refunded.
        conn.commit()
        try:
            result=_plain(await session.call_tool(action['tool'],action['args']))
        except (ConnectionError,TimeoutError,OSError):
            reconcile(conn,reservation,tokens=None,tools=None)
            transition(conn,lease,'failed')
            conn.commit()
            return results
        reconcile(conn,reservation,tokens=0,tools=1)
        task = fence(conn,lease)
        if not task:
            conn.commit()
            return results
        current_action=conn.execute('SELECT * FROM actions WHERE id=%s AND task_id=%s FOR UPDATE',
                                    (action['id'],lease.task_id)).fetchone()
        if not current_action or current_action['status']!='proposed' or not validate_frozen(conn,task,current_action):
            if current_action and current_action['status']=='proposed':
                move_action(conn,current_action,'invalidated')
            transition(conn,lease,'failed')
            return results
        from .retrieval import current_citations
        citations=current_citations(conn,task['tenant_id'],task['owner_id'],current_action['resource_id'])
        if not citations or not isinstance(result,dict):
            move_action(conn,current_action,'invalidated')
            transition(conn,lease,'failed')
            return results
        result={**result,'citations':citations}
        if _value(result,'isError',_value(result,'is_error',False)):
            move_action(conn,current_action,'invalidated')
            transition(conn,lease,'failed')
            return results
        conn.execute('UPDATE actions SET result=%s WHERE id=%s',(Jsonb(result),current_action['id']))
        move_action(conn,current_action,'succeeded')
        results.append({'action_id':str(current_action['id']),'tool_call_id':current_action['tool_call_id'],'result':result})
    # Keep every pending id until its real result exists, including the local write.
    from .worker import checkpoint
    pending=conn.execute("SELECT id FROM actions WHERE task_id=%s AND id=ANY(%s::uuid[]) AND status!='succeeded' ORDER BY position",
                         (lease.task_id,[a['id'] for a in actions])).fetchall()
    result_ids=[UUID(r['action_id']) for r in task['checkpoint'].get('tool_results',[])]
    completed=conn.execute('SELECT id,tool_call_id,result FROM actions WHERE task_id=%s AND id=ANY(%s::uuid[]) AND result IS NOT NULL ORDER BY position',
                           (lease.task_id,[a['id'] for a in actions]+result_ids)).fetchall()
    checkpoint(conn,lease,{**task['checkpoint'],'turn_id':task['checkpoint'].get('turn_id'),'pending_action_ids':[str(a['id']) for a in pending],
                          'tool_results':[{'action_id':str(a['id']),'tool_call_id':a['tool_call_id'],'result':a['result']} for a in completed]})
    return results
