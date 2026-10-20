"""Frozen multi-action turns survive process restarts; fixtures prove control flow only."""
from concurrent.futures import ThreadPoolExecutor
import multiprocessing as mp
import uuid

import pytest

from app.db import connect
from test_worker_ownership import execution_service, new_task

pytestmark = pytest.mark.integration

CALLS = [
    {'id':'read-1','name':'lookup_order','input':{'order_id':'A-1001'}},
    {'id':'write-1','name':'send_notice','input':{'resource_id':'A-1001','message':'synthetic notice'}},
    {'id':'read-2','name':'search_policy','input':{'query':'return'}},
]


def make_waiting(dsn, task_id):
    from app.worker import claim
    from app.actions import propose_turn
    from app.retrieval import seed_corpus
    with connect(dsn) as conn:
        seed_corpus(conn)
        lease = claim(conn, 'approval-worker', task_id=task_id)
        actions = propose_turn(conn, lease, CALLS)
        return lease, actions


def test_restart_frozen_turn_and_concurrent_decision(execution_service):
    from app.worker import claim
    from app.runtime import resume_turn
    api = execution_service
    task_id = new_task(api.dsn)
    ctx = mp.get_context('spawn')
    # The worker is a real OS process that exits while waiting.
    worker = ctx.Process(target=make_waiting, args=(api.dsn, task_id))
    worker.start(); worker.join(timeout=10)
    assert worker.exitcode == 0
    api.restart()
    listing = api.request('GET', f'/v1/tasks/{task_id}/approvals')
    assert listing.status_code == 200, listing.text
    approval = listing.json()['approvals'][0]
    with connect(api.dsn) as conn:
        row = conn.execute('SELECT * FROM tasks WHERE id=%s', (task_id,)).fetchone()
        assert row['status'] == 'waiting_approval'
        assert len(row['checkpoint']['pending_action_ids']) == 3
        assert 'tool_results' not in row['checkpoint']
        assert conn.execute('SELECT count(*) AS n FROM actions WHERE task_id=%s', (task_id,)).fetchone()['n'] == 3
    assert api.request('POST', f"/v1/approvals/{approval['id']}/decision", json={'decision':'approved'}).status_code == 403
    assert api.request('POST', f"/v1/approvals/{approval['id']}/decision", token='dev-mallory', json={'decision':'approved'}).status_code == 404
    def decide(_):
        return api.request('POST', f"/v1/approvals/{approval['id']}/decision", token='dev-approver', json={'decision':'approved'}).status_code
    with ThreadPoolExecutor(2) as pool:
        assert sorted(pool.map(decide, range(2))) == [200, 409]
    with connect(api.dsn) as conn:
        lease = claim(conn, 'resumed-worker', task_id=task_id)
        actions = resume_turn(conn, lease)
        assert len(actions) == 3
        assert [a['tool_call_id'] for a in actions] == ['read-1','write-1','read-2']
        assert [a['status'] for a in actions] == ['proposed','authorized_pending_delivery','proposed']
        assert conn.execute('SELECT count(*) AS n FROM outbox WHERE task_id=%s',(task_id,)).fetchone()['n'] == 0
        assert conn.execute('SELECT count(*) AS n FROM events WHERE task_id=%s AND kind=%s', (task_id,'action.authorized_pending_delivery')).fetchone()['n'] == 1


@pytest.mark.parametrize('mutation', ['args', 'acl', 'policy', 'resource', 'expired', 'permission', 'identity'])
def test_frozen_approval_rejects_changes(execution_service, mutation):
    from app.worker import claim
    from app.runtime import resume_turn
    api = execution_service
    task_id = new_task(api.dsn)
    _, actions = make_waiting(api.dsn, task_id)
    action = actions[1]
    approval = api.request('GET', f'/v1/tasks/{task_id}/approvals').json()['approvals'][0]
    with connect(api.dsn) as conn:
        if mutation == 'expired':
            conn.execute("UPDATE approvals SET expires_at=clock_timestamp()-interval '1 second' WHERE id=%s", (approval['id'],))
    decision = api.request('POST', f"/v1/approvals/{approval['id']}/decision", token='dev-approver', json={'decision':'approved'})
    if mutation == 'expired':
        assert decision.status_code == 409
        return
    assert decision.status_code == 200
    with connect(api.dsn) as conn:
        if mutation == 'args':
            conn.execute("UPDATE actions SET args=jsonb_set(args,'{message}','\"changed\"') WHERE id=%s", (action,))
        elif mutation == 'acl':
            conn.execute("UPDATE resources SET acl_version=acl_version+1 WHERE tenant_id='tenant-a' AND resource_id='A-1001'")
        elif mutation == 'policy':
            conn.execute("UPDATE tenant_policies SET version=version+1 WHERE tenant_id='tenant-a'")
        elif mutation == 'resource':
            conn.execute("UPDATE resources SET version=version+1 WHERE tenant_id='tenant-a' AND resource_id='A-1001'")
        elif mutation == 'permission':
            conn.execute("UPDATE resource_acl SET allowed=false WHERE tenant_id='tenant-a' AND resource_id='A-1001' AND caller_id='alice'")
        elif mutation == 'identity':
            conn.execute("UPDATE caller_identities SET active=false WHERE tenant_id='tenant-a' AND caller_id='alice'")
        lease = claim(conn, 'changed-worker', task_id=task_id)
        resume_turn(conn, lease)
        status = conn.execute('SELECT status FROM actions WHERE id=%s', (action,)).fetchone()['status']
        assert status != 'authorized_pending_delivery'
        # Restore shared corpus/identity without resurrecting the invalidated approval.
        conn.execute("UPDATE caller_identities SET active=true WHERE tenant_id='tenant-a' AND caller_id='alice'")
        conn.execute("UPDATE resource_acl SET allowed=true WHERE tenant_id='tenant-a' AND resource_id='A-1001' AND caller_id='alice'")


def test_cancel_revoked_access_and_denial(execution_service):
    api = execution_service
    task_id = new_task(api.dsn)
    make_waiting(api.dsn, task_id)
    approval = api.request('GET', f'/v1/tasks/{task_id}/approvals').json()['approvals'][0]
    assert api.request('GET', f'/v1/tasks/{task_id}/approvals', token='dev-bob').status_code == 404
    with connect(api.dsn) as conn:
        conn.execute("UPDATE caller_identities SET roles=ARRAY['caller'] WHERE caller_id='approver' AND tenant_id='tenant-a'")
    assert api.request('POST', f"/v1/approvals/{approval['id']}/decision", token='dev-approver', json={'decision':'approved'}).status_code == 403
    with connect(api.dsn) as conn:
        conn.execute("UPDATE caller_identities SET roles=ARRAY['caller','approver'] WHERE caller_id='approver' AND tenant_id='tenant-a'")
    assert api.request('POST', f"/v1/approvals/{approval['id']}/decision", token='dev-approver', json={'decision':'denied'}).status_code == 200
    with connect(api.dsn) as conn:
        assert conn.execute('SELECT status FROM tasks WHERE id=%s',(task_id,)).fetchone()['status'] == 'failed'
    assert api.request('POST', f'/v1/tasks/{task_id}/cancel').status_code == 409
    task_id = new_task(api.dsn)
    assert api.request('POST', f'/v1/tasks/{task_id}/cancel').status_code == 200
    with connect(api.dsn) as conn:
        assert conn.execute('SELECT status FROM tasks WHERE id=%s',(task_id,)).fetchone()['status'] == 'cancelled'


def test_expiry_after_approval_and_request_identity_injection(execution_service):
    from app.worker import claim
    from app.runtime import resume_turn
    api=execution_service
    task_id=new_task(api.dsn)
    _,actions=make_waiting(api.dsn,task_id)
    approval=api.request('GET',f'/v1/tasks/{task_id}/approvals').json()['approvals'][0]
    path=f"/v1/approvals/{approval['id']}/decision"
    assert api.request('POST',path,token='dev-approver',json={'decision':'approved','decided_by':'alice'}).status_code==422
    assert api.request('POST',path,token='dev-approver',json={'decision':'approved'}).status_code==200
    with connect(api.dsn) as conn:
        conn.execute("UPDATE approvals SET expires_at=clock_timestamp()-interval '1 second' WHERE id=%s",(approval['id'],))
        lease=claim(conn,'expired-resume',task_id=task_id)
        resume_turn(conn,lease)
        assert conn.execute('SELECT status FROM actions WHERE id=%s',(actions[1],)).fetchone()['status']=='invalidated'


def test_persist_invalid_call_independently_and_reject_approval_after_deadline(execution_service):
    from app.worker import claim
    from app.actions import propose_turn
    from app.retrieval import seed_corpus
    api=execution_service
    task_id=new_task(api.dsn)
    with connect(api.dsn) as conn:
        seed_corpus(conn)
        lease=claim(conn,'invalid-calls',task_id=task_id)
        ids=propose_turn(conn,lease,[{'id':'bad','name':'send_notice','input':[]},CALLS[0]])
        assert len(ids)==2
        assert conn.execute('SELECT status FROM actions WHERE id=%s',(ids[0],)).fetchone()['status']=='denied'
    task_id=new_task(api.dsn)
    make_waiting(api.dsn,task_id)
    approval=api.request('GET',f'/v1/tasks/{task_id}/approvals').json()['approvals'][0]
    with connect(api.dsn) as conn:
        conn.execute("UPDATE tasks SET deadline=clock_timestamp()-interval '1 second' WHERE id=%s",(task_id,))
    assert api.request('POST',f"/v1/approvals/{approval['id']}/decision",token='dev-approver',json={'decision':'approved'}).status_code==409


def test_read_actions_preserve_stage3_mcp_argument_contract(service):
    from app.worker import claim
    from app.actions import propose_turn
    from app.retrieval import seed_corpus
    task_id=new_task(service.dsn)
    with connect(service.dsn) as conn:
        seed_corpus(conn)
        lease=claim(conn,'mcp-contract',task_id=task_id)
        ids=propose_turn(conn,lease,[{'id':'read-order','name':'lookup_order','input':{'order_id':'A-1001'}},
                                   {'id':'read-policy','name':'search_policy','input':{'query':'returns'}}])
        rows=conn.execute('SELECT * FROM actions WHERE task_id=%s ORDER BY position',(task_id,)).fetchall()
        assert len(ids)==2 and all(r['status']=='proposed' for r in rows)
        assert [r['resource_id'] for r in rows]==['A-1001','policy-public']


def test_read_resume_calls_only_frozen_mcp_args_after_whole_turn_approval(execution_service):
    import asyncio
    from app.worker import claim
    from app.runtime import execute_reads
    api=execution_service
    task_id=new_task(api.dsn)
    old,ids=make_waiting(api.dsn,task_id)
    class ReadPeer:
        def __init__(self): self.calls=[]
        async def list_tools(self):
            return {'tools':[
                {'name':'lookup_order','inputSchema':{'type':'object','properties':{'order_id':{'type':'string','enum':['A-1001','A-1002']}},'required':['order_id'],'additionalProperties':False}},
                {'name':'search_policy','inputSchema':{'type':'object','properties':{'query':{'type':'string'}},'required':['query'],'additionalProperties':False}}]}
        async def call_tool(self,name,args):
            self.calls.append((name,args))
            with connect(api.dsn) as observer:
                assert observer.execute('SELECT count(*) AS n FROM budget_reservations WHERE task_id=%s AND sent',(task_id,)).fetchone()['n']>=1
            return {'content':[{'type':'text','text':'synthetic read result'}]}
    peer=ReadPeer()
    budget='read-budget-'+uuid.uuid4().hex
    with connect(api.dsn) as conn:
        conn.execute('INSERT INTO budget_accounts(id,tenant_id,token_limit,tool_limit) VALUES (%s,%s,0,10)',(budget,'tenant-a'))
    with connect(api.dsn) as conn:
        assert asyncio.run(execute_reads(conn,old,peer,budget_account=budget))==[]
        assert peer.calls==[]
    approval=api.request('GET',f'/v1/tasks/{task_id}/approvals').json()['approvals'][0]
    assert api.request('POST',f"/v1/approvals/{approval['id']}/decision",token='dev-approver',json={'decision':'approved'}).status_code==200
    with connect(api.dsn) as conn:
        lease=claim(conn,'read-resume',task_id=task_id)
        results=asyncio.run(execute_reads(conn,lease,peer,budget_account=budget))
        assert len(results)==2
        assert peer.calls==[('lookup_order',CALLS[0]['input']),('search_policy',CALLS[2]['input'])]
        assert conn.execute('SELECT status FROM actions WHERE id=%s',(ids[1],)).fetchone()['status']=='authorized_pending_delivery'
        # Replaying the checkpoint cannot repeat completed reads.
        assert asyncio.run(execute_reads(conn,lease,peer,budget_account=budget))==[]
        assert len(peer.calls)==2
        saved=conn.execute('SELECT checkpoint FROM tasks WHERE id=%s',(task_id,)).fetchone()['checkpoint']
        assert len(saved['tool_results'])==2


def test_read_response_takeover_retries_until_result_is_durable(service, monkeypatch):
    """A finished remote read is retryable until its result is committed locally."""
    import asyncio
    import app.runtime as runtime
    from app.actions import propose_turn
    from app.retrieval import seed_corpus
    from app.worker import claim, checkpoint, emit

    task_id=new_task(service.dsn)
    budget='takeover-read-'+uuid.uuid4().hex
    original_args={'query':'return'}
    with connect(service.dsn) as conn:
        seed_corpus(conn)
        stale=claim(conn,'reader-before-takeover',task_id=task_id)
        action_id=propose_turn(conn,stale,[{'id':'frozen-read','name':'search_policy','input':original_args}])[0]
        conn.execute('INSERT INTO budget_accounts(id,tenant_id,token_limit,tool_limit) VALUES (%s,%s,0,10)',(budget,'tenant-a'))
        saved_checkpoint=conn.execute('SELECT checkpoint FROM tasks WHERE id=%s',(task_id,)).fetchone()['checkpoint']

    class ReadPeer:
        def __init__(self):
            self.calls=[]

        async def list_tools(self):
            return {'tools':[{'name':'search_policy','inputSchema':{
                'type':'object','properties':{'query':{'type':'string'}},
                'required':['query'],'additionalProperties':False}}]}

        async def call_tool(self,name,args):
            self.calls.append((name,dict(args)))
            return {'content':[{'type':'text','text':f'synthetic read attempt {len(self.calls)}'}]}

    peer=ReadPeer()
    successor=[]
    original_plain=runtime._plain

    def take_over_after_response(response):
        # execute_reads calls _plain only after awaiting the MCP response. Inject
        # takeover at that boundary, before usage settlement/fence/result writes.
        if not successor:
            assert response['content'][0]['text']=='synthetic read attempt 1'
            with connect(service.dsn) as takeover:
                pending=takeover.execute('SELECT status,result FROM actions WHERE id=%s',(action_id,)).fetchone()
                assert pending=={'status':'proposed','result':None}
                takeover.execute("UPDATE tasks SET lease_until=clock_timestamp()-interval '1 second' WHERE id=%s",(task_id,))
                replacement=claim(takeover,'reader-after-takeover',task_id=task_id)
                assert replacement and replacement.epoch==stale.epoch+1
                successor.append(replacement)
        return original_plain(response)

    monkeypatch.setattr(runtime,'_plain',take_over_after_response)
    with connect(service.dsn) as conn:
        assert asyncio.run(runtime.execute_reads(conn,stale,peer,budget_account=budget))==[]
    assert peer.calls==[('search_policy',original_args)]

    with connect(service.dsn) as conn:
        action=conn.execute('SELECT status,result FROM actions WHERE id=%s',(action_id,)).fetchone()
        task=conn.execute('SELECT lease_owner,execution_epoch,checkpoint FROM tasks WHERE id=%s',(task_id,)).fetchone()
        assert action=={'status':'proposed','result':None}
        assert task['lease_owner']==successor[0].owner and task['execution_epoch']==successor[0].epoch
        assert task['checkpoint']==saved_checkpoint
        assert checkpoint(conn,stale,{'stale_result':'must not persist'})==0
        assert emit(conn,stale,'stale.read_result',{})==0
        assert conn.execute("SELECT count(*) AS n FROM events WHERE task_id=%s AND kind IN ('action.succeeded','stale.read_result')",(task_id,)).fetchone()['n']==0

    with connect(service.dsn) as conn:
        results=asyncio.run(runtime.execute_reads(conn,successor[0],peer,budget_account=budget))
        assert len(results)==1 and results[0]['action_id']==str(action_id)
        assert results[0]['tool_call_id']=='frozen-read'
        assert results[0]['result']['content'][0]['text']=='synthetic read attempt 2'
    assert peer.calls==[('search_policy',original_args),('search_policy',original_args)]

    # A new connection observes the committed result and reuses the checkpoint;
    # no full model-history replay or third read is needed to recover this turn.
    with connect(service.dsn) as conn:
        action=conn.execute('SELECT status,result FROM actions WHERE id=%s',(action_id,)).fetchone()
        saved=conn.execute('SELECT checkpoint FROM tasks WHERE id=%s',(task_id,)).fetchone()['checkpoint']
        assert action['status']=='succeeded' and action['result']==results[0]['result']
        assert saved['pending_action_ids']==[] and saved['tool_results']==results
        assert asyncio.run(runtime.execute_reads(conn,successor[0],peer,budget_account=budget))==[]
        assert conn.execute('SELECT checkpoint FROM tasks WHERE id=%s',(task_id,)).fetchone()['checkpoint']==saved
        # A safe retry is still a separate charged attempt, not a free replay.
        usage=conn.execute('SELECT consumed_tools,reserved_tools FROM budget_accounts WHERE id=%s',(budget,)).fetchone()
        assert usage=={'consumed_tools':2,'reserved_tools':0}
    assert len(peer.calls)==2
