"""Real PostgreSQL and independent HTTP sink processes; all business data synthetic."""
from concurrent.futures import ThreadPoolExecutor
import importlib.util
import multiprocessing as mp
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import uuid

import httpx
import pytest

from app.db import connect
from conftest import unused_port, subprocess_environment
from test_worker_ownership import execution_service, new_task

P5 = Path(__file__).resolve().parents[2] / 'p5-agent-delivery'
if str(P5) not in sys.path:
    sys.path.insert(0, str(P5))

pytestmark = pytest.mark.integration


def test_delivery_modules_exist():
    assert importlib.util.find_spec('app.outbox') is not None
    assert importlib.util.find_spec('app.delivery') is not None
    assert importlib.util.find_spec('app.sink') is not None


def test_p5_coordinator_resumes_approved_write_dispatches_once_then_continues_model(service, execution_service, sink):
    import asyncio
    from app.actions import REGISTRY
    from app.retrieval import seed_corpus
    from app.worker import claim
    from host import drive_provider_round, resume_agent_turn

    api = execution_service
    task_id = new_task(service.dsn)
    endpoint = 'p5-orchestrator-' + uuid.uuid4().hex
    account = 'p5-orchestrator-budget-' + uuid.uuid4().hex
    mcp_tools = [
        {'name': 'lookup_order', 'inputSchema': REGISTRY['lookup_order'][0]},
        {'name': 'search_policy', 'inputSchema': REGISTRY['search_policy'][0]},
    ]
    with connect(service.dsn) as conn:
        seed_corpus(conn)
        release_id = conn.execute('SELECT release_id FROM tasks WHERE id=%s', (task_id,)).fetchone()['release_id']
        conn.execute('INSERT INTO provider_endpoints VALUES (%s,1,4)', (endpoint,))
        conn.execute('INSERT INTO budget_accounts(id,tenant_id,token_limit,tool_limit) VALUES (%s,%s,5000,40)',
                     (account, 'tenant-a'))
        lease = claim(conn, 'p5-orchestrator-first', task_id=task_id, lease_seconds=120)

    class Adapter:
        max_retries = 0
        calls = []

        def __call__(self, request):
            self.calls.append(request)
            if len(self.calls) == 1:
                return {'id': 'notice-proposal', 'stop_reason': 'tool_use',
                    'content': [{'type': 'tool_use', 'id': 'notice-1', 'name': 'send_notice',
                                 'input': {'resource_id': 'A-1001', 'message': 'synthetic approved notice'}}],
                    'usage': {'input_tokens': 10, 'output_tokens': 5,
                              'cache_creation_input_tokens': 0, 'cache_read_input_tokens': 0}}
            return {'id': 'notice-final', 'stop_reason': 'end_turn',
                'content': [{'type': 'text', 'text': '{"outcome":"answer","text":"已完成通知。","citations":[]}'}],
                'usage': {'input_tokens': 20, 'output_tokens': 6,
                          'cache_creation_input_tokens': 0, 'cache_read_input_tokens': 0}}

    class MCP:
        async def list_tools(self):
            return {'tools': mcp_tools}

        async def call_tool(self, name, args):
            raise AssertionError('The proposed turn contains no read actions')

    adapter = Adapter()
    common = {'endpoint': endpoint, 'budget_account': account, 'provider': adapter,
              'mcp_tools': mcp_tools, 'system_prompt': 'Return the required JSON shape.',
              'model': 'fixture-model', 'max_tokens': 128, 'max_rounds': 3,
              'reserved_tokens': 512, 'reserved_tools': 4}
    proposed = drive_provider_round(lambda: connect(service.dsn), lease, **common)
    assert proposed['status'] == 'waiting_approval'
    assert len(adapter.calls) == 1

    approval = api.request('GET', f'/v1/tasks/{task_id}/approvals').json()['approvals'][0]
    decision = api.request('POST', f"/v1/approvals/{approval['id']}/decision", token='dev-approver',
                           json={'decision': 'approved'})
    assert decision.status_code == 200, decision.text
    with connect(service.dsn) as conn:
        approved_lease = claim(conn, 'p5-orchestrator-approved', task_id=task_id, lease_seconds=120)
    assert approved_lease

    delivered = asyncio.run(resume_agent_turn(
        lambda: connect(service.dsn), approved_lease, mcp_session=MCP(), **common,
        delivery_dsn=service.dsn, sink_url=sink.url,
    ))
    assert delivered['status'] == 'delivery_succeeded'
    assert delivered['action_id'] == proposed['action_ids'][0]
    assert len(adapter.calls) == 1, 'Approval recovery must not call the model before dispatch resolves'

    with connect(service.dsn) as conn:
        assert conn.execute('SELECT status FROM tasks WHERE id=%s', (task_id,)).fetchone()['status'] == 'queued'
        assert conn.execute('SELECT count(*) AS n FROM sink_effects WHERE action_id=%s',
                            (uuid.UUID(delivered['action_id']),)).fetchone()['n'] == 1
        successor = claim(conn, 'p5-orchestrator-continue', task_id=task_id, lease_seconds=120)
    assert successor
    completed = asyncio.run(resume_agent_turn(
        lambda: connect(service.dsn), successor, mcp_session=MCP(), **common,
        delivery_dsn=service.dsn, sink_url=sink.url,
    ))
    assert completed['status'] == 'completed'
    assert len(adapter.calls) == 2
    assert adapter.calls[1]['messages'][-1]['content'][0]['tool_use_id'] == 'notice-1'
    from runner import _load_action_evidence
    with connect(service.dsn) as conn:
        assert conn.execute('SELECT status FROM tasks WHERE id=%s', (task_id,)).fetchone()['status'] == 'completed'
        assert conn.execute("SELECT count(*) AS n FROM outbox WHERE task_id=%s AND status='succeeded'",
                            (task_id,)).fetchone()['n'] == 1
        task_status = conn.execute('SELECT status FROM tasks WHERE id=%s', (task_id,)).fetchone()['status']
        action_status = conn.execute('SELECT status FROM actions WHERE id=%s',
                                     (uuid.UUID(delivered['action_id']),)).fetchone()['status']
        outbox_status = conn.execute('SELECT status FROM outbox WHERE action_id=%s',
                                     (uuid.UUID(delivered['action_id']),)).fetchone()['status']
        event_kinds = [row['kind'] for row in conn.execute(
            'SELECT kind FROM events WHERE task_id=%s ORDER BY seq', (task_id,)).fetchall()]
        effect_count = conn.execute('SELECT count(*) AS n FROM sink_effects WHERE action_id=%s',
                                     (uuid.UUID(delivered['action_id']),)).fetchone()['n']
        live_action = next(
            row for row in _load_action_evidence(conn, task_id)
            if row['tool'] == 'send_notice'
        )
        assert live_action['status'] == 'succeeded'
        assert live_action['approval_verified'] is True
        approval_record = conn.execute(
            'SELECT * FROM approvals WHERE action_id=%s', (uuid.UUID(delivered['action_id']),)
        ).fetchone()
        mismatch_values = {
            'status': 'pending',
            'decided_by': 'alice',
            'decided_at': None,
            'args_hash': 'f' * 64,
            'resource_version': approval_record['resource_version'] + 1,
            'acl_version': approval_record['acl_version'] + 1,
            'policy_version': approval_record['policy_version'] + 1,
        }
        for column, wrong_value in mismatch_values.items():
            conn.execute(f'UPDATE approvals SET {column}=%s WHERE action_id=%s',
                         (wrong_value, uuid.UUID(delivered['action_id'])))
            mismatched = next(
                row for row in _load_action_evidence(conn, task_id)
                if row['tool'] == 'send_notice'
            )
            assert mismatched['approval_verified'] is False, f'{column} mismatch must invalidate witness'
            conn.execute(f'UPDATE approvals SET {column}=%s WHERE action_id=%s',
                         (approval_record[column], uuid.UUID(delivered['action_id'])))
    from conftest import record_drill_observation
    record_drill_observation('approval-pause-resume', {
        'task_statuses': ['waiting_approval', 'queued', task_status],
        'action_statuses': ['waiting_approval', action_status],
        'outbox_statuses': [outbox_status], 'sink_effect_count': effect_count,
        'event_kinds_in_order': event_kinds, 'provider_calls': len(adapter.calls),
    }, dsn=service.dsn, task_ids=[task_id])


def test_p5_coordinator_stops_on_unknown_delivery_without_another_model_call(service, execution_service):
    import asyncio
    from app.actions import REGISTRY
    from app.retrieval import seed_corpus
    from app.worker import claim
    from host import drive_provider_round, resume_agent_turn

    task_id = new_task(service.dsn)
    endpoint = 'p5-unknown-' + uuid.uuid4().hex
    account = 'p5-unknown-budget-' + uuid.uuid4().hex
    mcp_tools = [
        {'name': 'lookup_order', 'inputSchema': REGISTRY['lookup_order'][0]},
        {'name': 'search_policy', 'inputSchema': REGISTRY['search_policy'][0]},
    ]
    with connect(service.dsn) as conn:
        seed_corpus(conn)
        conn.execute('INSERT INTO provider_endpoints VALUES (%s,1,4)', (endpoint,))
        conn.execute('INSERT INTO budget_accounts(id,tenant_id,token_limit,tool_limit) VALUES (%s,%s,5000,40)',
                     (account, 'tenant-a'))
        lease = claim(conn, 'p5-unknown-first', task_id=task_id, lease_seconds=120)

    class Adapter:
        max_retries = 0
        calls = 0

        def __call__(self, request):
            self.calls += 1
            return {'id': 'unknown-notice', 'stop_reason': 'tool_use',
                'content': [{'type': 'tool_use', 'id': 'unknown-notice-1', 'name': 'send_notice',
                             'input': {'resource_id': 'A-1001', 'message': 'synthetic only'}}],
                'usage': {'input_tokens': 10, 'output_tokens': 5,
                          'cache_creation_input_tokens': 0, 'cache_read_input_tokens': 0}}

    class MCP:
        async def list_tools(self):
            return {'tools': mcp_tools}

    adapter = Adapter()
    common = {'endpoint': endpoint, 'budget_account': account, 'provider': adapter,
              'mcp_tools': mcp_tools, 'system_prompt': 'Return the required JSON shape.',
              'model': 'fixture-model', 'max_tokens': 128, 'max_rounds': 3,
              'reserved_tokens': 512, 'reserved_tools': 4}
    proposed = drive_provider_round(lambda: connect(service.dsn), lease, **common)
    approval = execution_service.request('GET', f'/v1/tasks/{task_id}/approvals').json()['approvals'][0]
    decision = execution_service.request('POST', f"/v1/approvals/{approval['id']}/decision",
        token='dev-approver', json={'decision': 'approved'})
    assert decision.status_code == 200, decision.text
    with connect(service.dsn) as conn:
        approved_lease = claim(conn, 'p5-unknown-approved', task_id=task_id, lease_seconds=120)

    unavailable_sink = f'http://127.0.0.1:{unused_port()}'
    result = asyncio.run(resume_agent_turn(lambda: connect(service.dsn), approved_lease,
        mcp_session=MCP(), **common, delivery_dsn=service.dsn, sink_url=unavailable_sink))
    assert result['status'] == 'reconciling'
    assert adapter.calls == 1
    with connect(service.dsn) as conn:
        assert conn.execute('SELECT status FROM tasks WHERE id=%s', (task_id,)).fetchone()['status'] == 'reconciling'
        assert conn.execute("SELECT status FROM outbox WHERE action_id=%s",
                            (uuid.UUID(proposed['action_ids'][0]),)).fetchone()['status'] == 'unknown'


@pytest.fixture
def sink(service):
    class Sink:
        def start(self):
            port=unused_port()
            self.url=f'http://127.0.0.1:{port}'
            env={**subprocess_environment(),'DATABASE_URL':service.dsn,
                 'PYTHONPATH':str(Path(__file__).resolve().parents[2])}
            self.process=subprocess.Popen([sys.executable,'-m','uvicorn','app.sink:app','--host','127.0.0.1',
                '--port',str(port),'--no-access-log','--log-level','critical'],
                cwd=Path(__file__).resolve().parents[1],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            for _ in range(200):
                if self.process.poll() is not None:
                    raise RuntimeError('Synthetic sink process exited')
                try:
                    if httpx.get(self.url+'/health/ready',timeout=.2).status_code==200:
                        return
                except httpx.HTTPError:
                    pass
                time.sleep(.025)
            raise RuntimeError('Synthetic sink readiness timeout')

        def stop(self):
            self.process.terminate()
            self.process.wait(timeout=5)

        def restart(self):
            self.stop()
            self.start()
    instance=Sink()
    instance.start()
    try:
        yield instance
    finally:
        instance.stop()


def approved_action(api):
    from app.actions import propose_turn
    from app.retrieval import seed_corpus
    from app.worker import claim
    task_id=new_task(api.dsn)
    with connect(api.dsn) as conn:
        seed_corpus(conn)
        first=claim(conn,'approval-setup',task_id=task_id)
        action_id=propose_turn(conn,first,[{'id':'notice','name':'send_notice',
            'input':{'resource_id':'A-1001','message':'synthetic only'}}])[0]
    approval=api.request('GET',f'/v1/tasks/{task_id}/approvals').json()['approvals'][0]
    response=api.request('POST',f"/v1/approvals/{approval['id']}/decision",token='dev-approver',json={'decision':'approved'})
    assert response.status_code==200,response.text
    with connect(api.dsn) as conn:
        lease=claim(conn,'delivery-owner',task_id=task_id,lease_seconds=120)
    return task_id,action_id,lease


def scheduled(api):
    from app.outbox import schedule
    task_id,action_id,lease=approved_action(api)
    with connect(api.dsn) as conn:
        assert schedule(conn,lease,action_id)==1
    return task_id,action_id,lease


def effect_count(dsn, action_id):
    with connect(dsn) as conn:
        return conn.execute('SELECT count(*) AS n FROM sink_effects WHERE action_id=%s',(action_id,)).fetchone()['n']


def event_kinds(dsn, task_id):
    with connect(dsn) as conn:
        rows=conn.execute('SELECT seq,kind FROM events WHERE task_id=%s ORDER BY seq',(task_id,)).fetchall()
        assert [r['seq'] for r in rows]==list(range(1,len(rows)+1))
        return [r['kind'] for r in rows]


def expire_dispatch(dsn, action_id):
    with connect(dsn) as conn:
        conn.execute("UPDATE outbox SET claim_until=clock_timestamp()-interval '1 second' WHERE action_id=%s",(action_id,))


def test_schedule_is_atomic_and_stale_epoch_cannot_create_outbox(execution_service):
    from app.outbox import schedule
    api=execution_service
    task_id,action_id,stale=approved_action(api)
    with connect(api.dsn) as conn:
        assert schedule(conn,stale,action_id)==1
        conn.rollback()
    with connect(api.dsn) as conn:
        assert conn.execute('SELECT count(*) AS n FROM outbox WHERE task_id=%s',(task_id,)).fetchone()['n']==0
        assert conn.execute('SELECT status FROM actions WHERE id=%s',(action_id,)).fetchone()['status']=='waiting_approval'
        conn.execute("UPDATE tasks SET lease_until=clock_timestamp()-interval '1 second' WHERE id=%s",(task_id,))
    result=subprocess.run([sys.executable,'-m','app.worker','--once','--task',str(task_id),'--owner','successor'],
        env={**subprocess_environment(),'DATABASE_URL':api.dsn},capture_output=True,text=True,timeout=10)
    assert result.returncode==0,result.stderr
    with connect(api.dsn) as conn:
        before=conn.execute('SELECT last_event_seq FROM tasks WHERE id=%s',(task_id,)).fetchone()['last_event_seq']
        assert schedule(conn,stale,action_id)==0
        assert conn.execute('SELECT last_event_seq FROM tasks WHERE id=%s',(task_id,)).fetchone()['last_event_seq']==before
        assert conn.execute('SELECT count(*) AS n FROM outbox WHERE task_id=%s',(task_id,)).fetchone()['n']==0
        from app.worker import Lease
        successor=Lease(task_id,'successor',stale.epoch+1)
        assert schedule(conn,successor,action_id)==1
        assert schedule(conn,successor,action_id)==0
        from app.outbox import claim as claim_dispatch
        before=conn.execute('SELECT last_event_seq FROM tasks WHERE id=%s',(task_id,)).fetchone()['last_event_seq']
        assert claim_dispatch(conn,stale,action_id) is None
        assert conn.execute('SELECT last_event_seq FROM tasks WHERE id=%s',(task_id,)).fetchone()['last_event_seq']==before
        row=conn.execute('SELECT external_key,status FROM outbox WHERE action_id=%s',(action_id,)).fetchone()
        assert row=={'external_key':f'p4-notice:{action_id}','status':'queued'}
    assert event_kinds(api.dsn,task_id).count('action.authorized')==1


def test_sink_dedup_and_receipt_survive_restart_and_reject_changed_payload(execution_service,sink):
    from app.delivery import dispatch_once
    api=execution_service
    task_id,action_id,lease=scheduled(api)
    assert dispatch_once(api.dsn,lease,action_id,sink.url)=='succeeded'
    assert effect_count(api.dsn,action_id)==1
    sink.restart()
    headers={'Authorization':'Bearer local-only-sink'}
    with connect(api.dsn) as conn:
        payload=conn.execute('SELECT payload FROM outbox WHERE action_id=%s',(action_id,)).fetchone()['payload']
        receipt=conn.execute('SELECT receipt FROM outbox WHERE action_id=%s',(action_id,)).fetchone()['receipt']
    def send(_):
        return httpx.post(sink.url+'/v1/notices',json=payload,headers=headers,timeout=10)
    with ThreadPoolExecutor(2) as pool:
        duplicates=list(pool.map(send,range(2)))
    assert all(r.status_code==200 and r.json()['receipt']==receipt for r in duplicates)
    altered={**payload,'args':{**payload['args'],'message':'changed'}}
    assert httpx.post(sink.url+'/v1/notices',json=altered,headers=headers).status_code==409
    assert effect_count(api.dsn,action_id)==1
    with connect(api.dsn) as conn:
        assert conn.execute('SELECT status FROM tasks WHERE id=%s',(task_id,)).fetchone()['status']=='queued'
    assert event_kinds(api.dsn,task_id)[-3:]==['action.succeeded','outbox.receipt_saved','task.delivery_resolved']


def crash_dispatch(dsn,lease,action_id,url,phase,channel):
    from app.delivery import dispatch_once
    def checkpoint(name):
        if name==phase:
            channel.send(name)
            signal.pause()
    dispatch_once(dsn,lease,action_id,url,checkpoint=checkpoint)


@pytest.mark.parametrize('phase,initial_effects',[
    ('after_claim_before_send',0),('after_sink_commit_before_receipt',1)])
def test_process_death_reconciles_query_before_retry(execution_service,sink,phase,initial_effects):
    from app.delivery import reconcile
    from app.worker import transition
    api=execution_service
    task_id,action_id,lease=scheduled(api)
    ctx=mp.get_context('spawn')
    parent,child=ctx.Pipe()
    worker=ctx.Process(target=crash_dispatch,args=(api.dsn,lease,action_id,sink.url,phase,child))
    worker.start()
    try:
        assert parent.poll(15) and parent.recv()==phase
        assert effect_count(api.dsn,action_id)==initial_effects
        os.kill(worker.pid,signal.SIGKILL)
        worker.join(timeout=5)
        with connect(api.dsn) as conn:
            assert conn.execute('SELECT status FROM tasks WHERE id=%s',(task_id,)).fetchone()['status']=='reconciling'
            assert transition(conn,lease,'completed')==0
        expire_dispatch(api.dsn,action_id)
        assert reconcile(api.dsn,action_id,sink.url)=='succeeded'
        assert effect_count(api.dsn,action_id)==1
        with connect(api.dsn) as conn:
            methods=[r['method'] for r in conn.execute('SELECT method FROM sink_requests WHERE external_key=%s ORDER BY seq',(f'p4-notice:{action_id}',)).fetchall()]
            assert methods==(['GET','POST'] if initial_effects==0 else ['POST','GET'])
            assert conn.execute('SELECT status FROM tasks WHERE id=%s',(task_id,)).fetchone()['status']=='queued'
        kinds=event_kinds(api.dsn,task_id)
        assert kinds.index('action.unknown')<kinds.index('outbox.reconciliation_query')<kinds.index('action.succeeded')
        assert reconcile(api.dsn,action_id,sink.url)=='unavailable'
    finally:
        if worker.is_alive(): worker.kill()
        worker.join(timeout=5)


def test_connection_failure_unknown_blocks_completion_and_unavailable_query_does_not_retry(execution_service,sink):
    from app.delivery import dispatch_once,reconcile
    from app.worker import transition
    api=execution_service
    task_id,action_id,lease=scheduled(api)
    unavailable=f'http://127.0.0.1:{unused_port()}'
    assert dispatch_once(api.dsn,lease,action_id,unavailable)=='unknown'
    assert reconcile(api.dsn,action_id,unavailable)=='unknown'
    with connect(api.dsn) as conn:
        assert transition(conn,lease,'completed')==0
        assert conn.execute('SELECT status FROM tasks WHERE id=%s',(task_id,)).fetchone()['status']=='reconciling'
        assert conn.execute('SELECT status FROM actions WHERE id=%s',(action_id,)).fetchone()['status']=='unknown'
    assert effect_count(api.dsn,action_id)==0
    assert reconcile(api.dsn,action_id,sink.url)=='succeeded'
    assert effect_count(api.dsn,action_id)==1
    with connect(api.dsn) as conn:
        task_status=conn.execute('SELECT status FROM tasks WHERE id=%s',(task_id,)).fetchone()['status']
        action_status=conn.execute('SELECT status FROM actions WHERE id=%s',(action_id,)).fetchone()['status']
        outbox_status=conn.execute('SELECT status FROM outbox WHERE action_id=%s',(action_id,)).fetchone()['status']
        event_kinds=[r['kind'] for r in conn.execute('SELECT kind FROM events WHERE task_id=%s ORDER BY seq',(task_id,)).fetchall()]
    from conftest import record_drill_observation
    record_drill_observation('unknown-reconcile', {
        'task_statuses':['reconciling',task_status], 'action_statuses':['unknown',action_status],
        'outbox_statuses':['unknown',outbox_status], 'sink_effect_count':effect_count(api.dsn,action_id),
        'event_kinds_in_order':event_kinds, 'request_methods':['connection-error','receipt-query'],
        'completion_attempts':['rejected-before-reconcile'],
    }, dsn=api.dsn, task_ids=[task_id])


def response_loss_proxy(port,sink_address,ready):
    """Actual TCP response loss after the receiver commits, not a mocked DB."""
    from http.server import BaseHTTPRequestHandler,HTTPServer
    import socket
    class Proxy(BaseHTTPRequestHandler):
        def do_POST(self):
            body=self.rfile.read(int(self.headers['Content-Length']))
            response=httpx.post(sink_address+self.path,content=body,headers={
                'Authorization':self.headers.get('Authorization',''),'Content-Type':'application/json'},timeout=5)
            assert response.status_code==200
            self.connection.shutdown(socket.SHUT_RDWR)
            self.connection.close()
        def do_GET(self):
            response=httpx.get(sink_address+self.path,headers={'Authorization':self.headers.get('Authorization','')},timeout=5)
            self.send_response(response.status_code)
            self.send_header('Content-Type','application/json')
            self.end_headers()
            self.wfile.write(response.content)
        def log_message(self,*args):
            pass
    server=HTTPServer(('127.0.0.1',port),Proxy)
    ready.set()
    server.serve_forever()


def test_lost_http_response_after_sink_commit_is_unknown_then_queries_receipt(execution_service,sink):
    from app.delivery import dispatch_once,reconcile
    api=execution_service
    task_id,action_id,lease=scheduled(api)
    context=mp.get_context('spawn')
    ready=context.Event()
    port=unused_port()
    proxy=context.Process(target=response_loss_proxy,args=(port,sink.url,ready))
    proxy.start()
    try:
        assert ready.wait(timeout=10)
        url=f'http://127.0.0.1:{port}'
        assert dispatch_once(api.dsn,lease,action_id,url)=='unknown'
        assert effect_count(api.dsn,action_id)==1
        with connect(api.dsn) as conn:
            assert conn.execute('SELECT status FROM actions WHERE id=%s',(action_id,)).fetchone()['status']=='unknown'
            assert conn.execute('SELECT status FROM tasks WHERE id=%s',(task_id,)).fetchone()['status']=='reconciling'
        assert reconcile(api.dsn,action_id,url)=='succeeded'
        assert effect_count(api.dsn,action_id)==1
        with connect(api.dsn) as conn:
            methods=[r['method'] for r in conn.execute('SELECT method FROM sink_requests WHERE external_key=%s ORDER BY seq',(f'p4-notice:{action_id}',)).fetchall()]
            assert methods==['POST','GET']
            task_status=conn.execute('SELECT status FROM tasks WHERE id=%s',(task_id,)).fetchone()['status']
            action_status=conn.execute('SELECT status FROM actions WHERE id=%s',(action_id,)).fetchone()['status']
            outbox_status=conn.execute('SELECT status FROM outbox WHERE action_id=%s',(action_id,)).fetchone()['status']
            event_kinds=[r['kind'] for r in conn.execute('SELECT kind FROM events WHERE task_id=%s ORDER BY seq',(task_id,)).fetchall()]
        from conftest import record_drill_observation
        record_drill_observation('unknown-reconcile', {
            'task_statuses':['reconciling',task_status], 'action_statuses':['unknown',action_status],
            'outbox_statuses':['unknown',outbox_status], 'sink_effect_count':effect_count(api.dsn,action_id),
            'event_kinds_in_order':event_kinds, 'request_methods':methods,
            'completion_attempts':['blocked-while-unknown'],
        }, dsn=api.dsn, task_ids=[task_id])
    finally:
        proxy.terminate()
        proxy.join(timeout=5)


def claim_with_barrier(dsn,lease,action_id,barrier,channel):
    from app.outbox import claim
    barrier.wait(timeout=10)
    with connect(dsn) as conn:
        result=claim(conn,lease,action_id)
    channel.send(result)


def test_two_dispatcher_processes_claim_once_and_stale_dispatch_token_is_fenced(execution_service,sink):
    from app.outbox import recover,save_receipt,mark_unknown
    from app.delivery import reconcile
    api=execution_service
    task_id,action_id,lease=scheduled(api)
    context=mp.get_context('spawn')
    barrier=context.Barrier(3)
    channels=[context.Pipe() for _ in range(2)]
    processes=[context.Process(target=claim_with_barrier,args=(api.dsn,lease,action_id,barrier,c[1])) for c in channels]
    try:
        for process in processes: process.start()
        barrier.wait(timeout=10)
        claims=[]
        for parent,_ in channels:
            assert parent.poll(15)
            claims.append(parent.recv())
        for process in processes:
            process.join(timeout=5)
            assert process.exitcode==0
        assert sum(c is not None for c in claims)==1
        old=next(c for c in claims if c is not None)
        expire_dispatch(api.dsn,action_id)
        with connect(api.dsn) as conn:
            new=recover(conn,action_id)
            assert new and new.token!=old.token
            before=conn.execute('SELECT last_event_seq FROM tasks WHERE id=%s',(task_id,)).fetchone()['last_event_seq']
            assert save_receipt(conn,old,{'forged':'must not save'})==0
            assert mark_unknown(conn,old)==0
            assert conn.execute('SELECT last_event_seq FROM tasks WHERE id=%s',(task_id,)).fetchone()['last_event_seq']==before
        expire_dispatch(api.dsn,action_id)
        assert reconcile(api.dsn,action_id,sink.url)=='succeeded'
        assert effect_count(api.dsn,action_id)==1
        assert event_kinds(api.dsn,task_id).count('action.dispatching')==1
    finally:
        for process in processes:
            if process.is_alive(): process.kill()
            process.join(timeout=5)


def test_claim_rejects_tampered_outbox_payload(execution_service,sink):
    from app.delivery import dispatch_once
    api=execution_service
    task_id,action_id,lease=scheduled(api)
    with connect(api.dsn) as conn:
        conn.execute("UPDATE outbox SET payload=jsonb_set(payload,'{args,message}','\"tampered\"') WHERE action_id=%s",(action_id,))
    assert dispatch_once(api.dsn,lease,action_id,sink.url)=='unavailable'
    assert effect_count(api.dsn,action_id)==0
    with connect(api.dsn) as conn:
        assert conn.execute('SELECT status FROM tasks WHERE id=%s',(task_id,)).fetchone()['status']=='failed'


def unproven_receiver(port,body,status,ready,posts):
    from http.server import BaseHTTPRequestHandler,HTTPServer
    import json
    class Receiver(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(status)
            self.send_header('Content-Type','application/json')
            self.end_headers()
            self.wfile.write(json.dumps(body).encode())
        def do_POST(self):
            with posts.get_lock(): posts.value+=1
            self.send_response(500)
            self.end_headers()
        def log_message(self,*args): pass
    server=HTTPServer(('127.0.0.1',port),Receiver)
    ready.set()
    server.serve_forever()


@pytest.mark.parametrize('variant',['unproven','malformed','mismatched_receipt','invalid_receipt_id'])
def test_unproven_or_malformed_query_cannot_authorize_retry_or_completion(execution_service,variant):
    from app.delivery import dispatch_once,reconcile
    from app.services import SINK_CONTRACT
    api=execution_service
    task_id,action_id,lease=scheduled(api)
    assert dispatch_once(api.dsn,lease,action_id,f'http://127.0.0.1:{unused_port()}')=='unknown'
    if variant=='unproven':
        body,status={'external_key':f'p4-notice:{action_id}','safe_retry':True},404
    elif variant=='malformed':
        body,status=[],404
    elif variant=='mismatched_receipt':
        body,status={'contract':SINK_CONTRACT,'receipt':{'external_key':'wrong-key'}},200
    else:
        from app.actions import args_hash
        with connect(api.dsn) as conn:
            payload=conn.execute('SELECT payload FROM outbox WHERE action_id=%s',(action_id,)).fetchone()['payload']
        body,status={'contract':SINK_CONTRACT,'receipt':{'external_key':f'p4-notice:{action_id}',
            'action_id':str(action_id),'tenant_id':'tenant-a','payload_hash':args_hash(payload),
            'outcome':'applied','receipt_id':123}},200
    context=mp.get_context('spawn')
    ready=context.Event()
    posts=context.Value('i',0)
    port=unused_port()
    receiver=context.Process(target=unproven_receiver,args=(port,body,status,ready,posts))
    receiver.start()
    try:
        assert ready.wait(timeout=10)
        assert reconcile(api.dsn,action_id,f'http://127.0.0.1:{port}')=='unknown'
        assert posts.value==0
        with connect(api.dsn) as conn:
            assert conn.execute('SELECT status FROM tasks WHERE id=%s',(task_id,)).fetchone()['status']=='reconciling'
            row=conn.execute('SELECT attempts,receipt FROM outbox WHERE action_id=%s',(action_id,)).fetchone()
            assert row=={'attempts':1,'receipt':None}
    finally:
        receiver.terminate()
        receiver.join(timeout=5)


def test_multiple_notices_remain_pending_until_real_receipts_and_validated_output(execution_service,sink):
    from app.actions import propose_turn
    from app.outbox import schedule
    from app.delivery import dispatch_once
    from app.retrieval import seed_corpus
    from app.worker import claim,transition
    api=execution_service
    task_id=new_task(api.dsn)
    with connect(api.dsn) as conn:
        seed_corpus(conn)
        lease=claim(conn,'multi-notice-proposal',task_id=task_id)
        actions=propose_turn(conn,lease,[{'id':f'notice-{i}','name':'send_notice',
            'input':{'resource_id':'A-1001','message':f'synthetic notice {i}'}} for i in range(2)])
    approvals=api.request('GET',f'/v1/tasks/{task_id}/approvals').json()['approvals']
    for approval in approvals:
        assert api.request('POST',f"/v1/approvals/{approval['id']}/decision",token='dev-approver',json={'decision':'approved'}).status_code==200
    with connect(api.dsn) as conn:
        lease=claim(conn,'multi-notice-scheduler',task_id=task_id)
        for action_id in actions:
            assert schedule(conn,lease,action_id)==1
    assert dispatch_once(api.dsn,lease,actions[0],sink.url)=='succeeded'
    with connect(api.dsn) as conn:
        task=conn.execute('SELECT status,checkpoint FROM tasks WHERE id=%s',(task_id,)).fetchone()
        assert task['status']=='queued'
        assert task['checkpoint']['pending_action_ids']==[str(actions[1])]
        assert len(task['checkpoint']['tool_results'])==1
        lease=claim(conn,'second-notice',task_id=task_id)
        with pytest.raises(ValueError,match='all actions resolved'):
            transition(conn,lease,'completed')
    assert dispatch_once(api.dsn,lease,actions[1],sink.url)=='succeeded'
    with connect(api.dsn) as conn:
        task=conn.execute('SELECT status,checkpoint FROM tasks WHERE id=%s',(task_id,)).fetchone()
        assert task['status']=='queued'
        assert task['checkpoint']['pending_action_ids']==[]
        assert [r['tool_call_id'] for r in task['checkpoint']['tool_results']]==['notice-0','notice-1']
        lease=claim(conn,'validated-final-output',task_id=task_id)
        with pytest.raises(ValueError,match='validated output'):
            transition(conn,lease,'completed')
        from app.runtime import finalize_output
        assert finalize_output(conn,lease,{'outcome':'answer','text':'Synthetic notices delivered.','citations':[]})==1
    assert [effect_count(api.dsn,i) for i in actions]==[1,1]


@pytest.mark.parametrize('operation',['schedule','claim'])
def test_lease_expiring_while_authorization_rows_are_locked_cannot_schedule_or_claim(execution_service,operation):
    from app.outbox import schedule,claim
    from concurrent.futures import TimeoutError as FutureTimeout
    api=execution_service
    task_id,action_id,lease=scheduled(api) if operation=='claim' else approved_action(api)
    with connect(api.dsn) as conn:
        conn.execute("UPDATE tasks SET lease_until=clock_timestamp()+interval '1 second' WHERE id=%s",(task_id,))
    with connect(api.dsn) as blocker:
        blocker.execute("SELECT * FROM resources WHERE tenant_id='tenant-a' AND resource_id='A-1001' FOR UPDATE")
        def attempt():
            with connect(api.dsn) as conn:
                return schedule(conn,lease,action_id) if operation=='schedule' else claim(conn,lease,action_id)
        with ThreadPoolExecutor(1) as pool:
            future=pool.submit(attempt)
            with pytest.raises(FutureTimeout):
                future.result(timeout=.2)
            time.sleep(1)
            blocker.commit()
            result=future.result(timeout=10)
    assert result==(0 if operation=='schedule' else None)
    with connect(api.dsn) as conn:
        assert conn.execute('SELECT status FROM actions WHERE id=%s',(action_id,)).fetchone()['status']==('waiting_approval' if operation=='schedule' else 'authorized')
        row=conn.execute('SELECT status FROM outbox WHERE action_id=%s',(action_id,)).fetchone()
        assert row==(None if operation=='schedule' else {'status':'queued'})
    assert 'action.dispatching' not in event_kinds(api.dsn,task_id)
