from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import threading
import uuid

import pytest

from app.db import connect
from test_worker_ownership import execution_service, new_task

pytestmark = pytest.mark.integration


def test_queue_full_idempotent_replay_deadline_and_slot_release(execution_service):
    from app.worker import claim, expire_deadlines
    api = execution_service
    key = uuid.uuid4().hex
    with connect(api.dsn) as conn:
        conn.execute("UPDATE service_limits SET queue_limit=10000, task_limit=1 WHERE singleton")
    response = api.request('POST','/v1/tasks',json={'prompt':'bounded'},headers={'Idempotency-Key':key})
    assert response.status_code == 201
    task_id = response.json()['id']
    with connect(api.dsn) as conn:
        conn.execute('UPDATE service_limits SET queue_limit=0 WHERE singleton')
    try:
        assert api.request('POST','/v1/tasks',json={'prompt':'bounded'},headers={'Idempotency-Key':key}).status_code == 200
        full = api.request('POST','/v1/tasks',json={'prompt':'full'},headers={'Idempotency-Key':uuid.uuid4().hex})
        assert full.status_code == 429 and full.json()['error']['code'] == 'queue_full'
        with connect(api.dsn) as conn:
            # Other integration tests may leave leases; expire them first.
            conn.execute("UPDATE tasks SET lease_until=clock_timestamp()-interval '1 second' WHERE lease_owner IS NOT NULL")
            lease = claim(conn, 'slots', task_id=task_id)
            assert lease
            other = new_task(api.dsn)
            assert claim(conn, 'blocked', task_id=other) is None
            conn.execute("UPDATE tasks SET deadline=clock_timestamp()-interval '1 second' WHERE id=%s",(task_id,))
            expire_deadlines(conn)
            assert conn.execute('SELECT status FROM tasks WHERE id=%s',(task_id,)).fetchone()['status']=='failed'
            assert conn.execute('SELECT count(*) AS n FROM task_slots WHERE task_id=%s',(task_id,)).fetchone()['n']==0
            assert claim(conn, 'unblocked', task_id=other)
    finally:
        with connect(api.dsn) as conn:
            conn.execute('UPDATE service_limits SET queue_limit=10000, task_limit=100 WHERE singleton')


def test_endpoint_slots_retry_jitter_and_deadline(service):
    from app.worker import claim
    from app.limits import acquire_provider, schedule_429
    task_id = new_task(service.dsn)
    endpoint = 'fixture-'+uuid.uuid4().hex
    with connect(service.dsn) as conn:
        lease = claim(conn,'endpoint',task_id=task_id)
        conn.execute('INSERT INTO provider_endpoints (id,concurrency_limit,max_attempts) VALUES (%s,1,2)',(endpoint,))
        slot = acquire_provider(conn,lease,endpoint)
        assert slot
        assert acquire_provider(conn,lease,endpoint) is None
        before = datetime.now(timezone.utc)
        retry = schedule_429(conn,lease,endpoint,slot,retry_after=2,jitter=.25)
        assert 2 <= (retry-before).total_seconds() <= 2.5
        assert acquire_provider(conn,lease,endpoint) is None
        assert conn.execute('SELECT next_retry_at FROM tasks WHERE id=%s',(task_id,)).fetchone()['next_retry_at']==retry
        conn.execute("UPDATE tasks SET next_retry_at=clock_timestamp()-interval '1 second',deadline=clock_timestamp()+interval '1 second' WHERE id=%s",(task_id,))
        slot = acquire_provider(conn,lease,endpoint)
        assert slot
        assert schedule_429(conn,lease,endpoint,slot,retry_after=2,jitter=0) is None
        assert conn.execute('SELECT status FROM tasks WHERE id=%s',(task_id,)).fetchone()['status']=='failed'
        assert conn.execute('SELECT count(*) AS n FROM provider_slots WHERE task_id=%s',(task_id,)).fetchone()['n']==0


def test_shared_budget_barrier_unknown_usage_and_unsent_release(service):
    from app.worker import claim
    from app.limits import reserve, mark_sent, reconcile, release_unsent, budget_report
    task_ids = [new_task(service.dsn), new_task(service.dsn)]
    account = 'budget-'+uuid.uuid4().hex
    with connect(service.dsn) as conn:
        conn.execute('INSERT INTO budget_accounts (id,tenant_id,token_limit,tool_limit) VALUES (%s,%s,100,10)',(account,'tenant-a'))
        leases = [claim(conn,'budget-'+str(i),task_id=tid) for i,tid in enumerate(task_ids)]
    barrier = threading.Barrier(2)
    def contender(lease):
        with connect(service.dsn) as conn:
            barrier.wait(timeout=5)
            return reserve(conn,lease,account,tokens=70,tools=7)
    with ThreadPoolExecutor(2) as pool:
        reservations = list(pool.map(contender,leases))
    assert sum(r is not None for r in reservations)==1
    reservation = next(r for r in reservations if r)
    with connect(service.dsn) as conn:
        assert mark_sent(conn,reservation)
        assert not release_unsent(conn,reservation)
        reconcile(conn,reservation,tokens=None,tools=None)
        report_before = budget_report(conn,account)
        assert report_before['reserved_tokens']==70 and report_before['consumed_tokens']==0
        reconcile(conn,reservation,tokens=50,tools=5)
        report_after = budget_report(conn,account)
        assert report_after['reserved_tokens']==0 and report_after['consumed_tokens']==50
        assert report_after['available_tokens']==50
        assert not reconcile(conn,reservation,tokens=1,tools=1)
        unsent = reserve(conn,leases[0],account,tokens=30,tools=3)
        assert unsent and release_unsent(conn,unsent)
        assert budget_report(conn,account)['available_tokens']==50
    from conftest import record_drill_observation
    record_drill_observation('budget-unknown', {
        'budget_before':{'reserved_tokens':report_before['reserved_tokens'],'consumed_tokens':report_before['consumed_tokens'],
                         'reserved_tools':report_before['reserved_tools'],'consumed_tools':report_before['consumed_tools']},
        'budget_after':{'reserved_tokens':report_after['reserved_tokens'],'consumed_tokens':report_after['consumed_tokens'],
                        'reserved_tools':report_after['reserved_tools'],'consumed_tools':report_after['consumed_tools']},
        'provider_call_states':['no-provider-call:tool-budget-only'],
        'reservation_states':['unknown','settled','released'],
    }, dsn=service.dsn, task_ids=task_ids)


def test_provider_endpoint_capacity_is_shared_and_max_attempts_stop(service):
    from app.worker import claim
    from app.limits import acquire_provider, schedule_429
    endpoint='parallel-'+uuid.uuid4().hex
    task_ids=[new_task(service.dsn),new_task(service.dsn)]
    with connect(service.dsn) as conn:
        conn.execute('INSERT INTO provider_endpoints VALUES (%s,1,1)',(endpoint,))
        leases=[claim(conn,'provider-'+str(i),task_id=tid) for i,tid in enumerate(task_ids)]
    barrier=threading.Barrier(2)
    def attempt(lease):
        with connect(service.dsn) as conn:
            barrier.wait(timeout=5)
            return acquire_provider(conn,lease,endpoint)
    with ThreadPoolExecutor(2) as pool:
        slots=list(pool.map(attempt,leases))
    assert sum(s is not None for s in slots)==1
    winner=next(i for i,s in enumerate(slots) if s)
    with connect(service.dsn) as conn:
        assert schedule_429(conn,leases[winner],endpoint,slots[winner],retry_after=1,jitter=0) is None
        assert conn.execute('SELECT status FROM tasks WHERE id=%s',(task_ids[winner],)).fetchone()['status']=='failed'
        assert acquire_provider(conn,leases[winner],endpoint) is None


def test_exhausted_tool_budget_prevents_mcp_invocation(service):
    import asyncio
    from app.worker import claim
    from app.actions import propose_turn
    from app.runtime import execute_reads
    from app.retrieval import seed_corpus
    task_id=new_task(service.dsn)
    account='no-tools-'+uuid.uuid4().hex
    class NeverCalled:
        async def list_tools(self):
            return {'tools':[{'name':'search_policy','inputSchema':{'type':'object','properties':{'query':{'type':'string'}},'required':['query'],'additionalProperties':False}}]}
        async def call_tool(self,*args):
            raise AssertionError('No budget: no MCP invocation permitted')
    with connect(service.dsn) as conn:
        seed_corpus(conn)
        conn.execute('INSERT INTO budget_accounts(id,tenant_id,token_limit,tool_limit) VALUES (%s,%s,0,0)',(account,'tenant-a'))
        lease=claim(conn,'no-tools',task_id=task_id)
        propose_turn(conn,lease,[{'id':'p','name':'search_policy','input':{'query':'return'}}])
        assert asyncio.run(execute_reads(conn,lease,NeverCalled(),budget_account=account))==[]
        assert conn.execute('SELECT status FROM tasks WHERE id=%s',(task_id,)).fetchone()['status']=='failed'
        assert conn.execute('SELECT count(*) AS n FROM budget_reservations WHERE task_id=%s',(task_id,)).fetchone()['n']==0


def test_provider_slot_releases_after_response_and_stale_release_is_fenced(service):
    from app.worker import claim, Lease
    from app.limits import acquire_provider, release_provider
    task_id=new_task(service.dsn)
    endpoint='release-'+uuid.uuid4().hex
    with connect(service.dsn) as conn:
        lease=claim(conn,'release-provider',task_id=task_id)
        conn.execute('INSERT INTO provider_endpoints VALUES (%s,1,3)',(endpoint,))
        first=acquire_provider(conn,lease,endpoint)
        assert first and acquire_provider(conn,lease,endpoint) is None
        assert not release_provider(conn,Lease(lease.task_id,'stale-owner',lease.epoch),first)
        assert release_provider(conn,lease,first)
        assert acquire_provider(conn,lease,endpoint)
