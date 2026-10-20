"""Composed Task 2 API and durable normalized-response control flow.

The worker CLI only claims; trusted host code calls consume_response/resume_turn.
There is no automatic provider call or outbound delivery in this milestone.
"""
from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header, HTTPException, Response

from support_agent.providers import normalize_response, _value, _plain
from .actions import propose_turn, authorize_action, validate_frozen, move_action
from .api import authorized_connection, read_task, read_events
from .db import create_task, connect
from .models import TaskCreate, TaskView, EventPage
from .worker import fence, transition


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
            row=conn.execute("SELECT 1 FROM schema_migrations WHERE version='0002_execution.sql'").fetchone()
            if not row:
                raise HTTPException(503,detail={'code':'schema_unavailable','message':'Execution migration missing'})
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
        if not fence(conn,lease):
            conn.commit()
            return results
        if _value(result,'isError',_value(result,'is_error',False)):
            move_action(conn,action,'invalidated')
            transition(conn,lease,'failed')
            return results
        conn.execute('UPDATE actions SET result=%s WHERE id=%s',(Jsonb(result),action['id']))
        move_action(conn,action,'succeeded')
        results.append({'action_id':str(action['id']),'tool_call_id':action['tool_call_id'],'result':result})
    # Keep every pending id until its real result exists, including the local write.
    from .worker import checkpoint
    pending=conn.execute("SELECT id FROM actions WHERE task_id=%s AND id=ANY(%s::uuid[]) AND status!='succeeded' ORDER BY position",
                         (lease.task_id,[a['id'] for a in actions])).fetchall()
    result_ids=[UUID(r['action_id']) for r in task['checkpoint'].get('tool_results',[])]
    completed=conn.execute('SELECT id,tool_call_id,result FROM actions WHERE task_id=%s AND id=ANY(%s::uuid[]) AND result IS NOT NULL ORDER BY position',
                           (lease.task_id,[a['id'] for a in actions]+result_ids)).fetchall()
    checkpoint(conn,lease,{'turn_id':task['checkpoint'].get('turn_id'),'pending_action_ids':[str(a['id']) for a in pending],
                          'tool_results':[{'action_id':str(a['id']),'tool_call_id':a['tool_call_id'],'result':a['result']} for a in completed]})
    return results
