"""Committed dispatch claim is the cancellation/revocation authorization boundary."""
import multiprocessing as mp
import signal

import pytest

from app.db import connect
from test_delivery_reconciliation import (sink, scheduled, approved_action, effect_count,
    event_kinds, expire_dispatch)
from test_worker_ownership import execution_service

pytestmark=pytest.mark.integration


def paused_dispatch(dsn,lease,action_id,url,phase,channel):
    from app.delivery import dispatch_once
    def checkpoint(name):
        if name==phase:
            channel.send(name)
            assert channel.poll(15)
            channel.recv()
    result=dispatch_once(dsn,lease,action_id,url,checkpoint=checkpoint)
    channel.send(result)


@pytest.mark.parametrize('operation',['cancel','revoke'])
@pytest.mark.parametrize('phase',[
    'before_claim','after_claim_before_send','after_sink_commit_before_receipt'])
def test_three_cancel_revoke_boundaries(execution_service,sink,operation,phase):
    from app.delivery import reconcile
    from app.worker import transition
    api=execution_service
    task_id,action_id,lease=scheduled(api)
    context=mp.get_context('spawn')
    parent,child=context.Pipe()
    process=context.Process(target=paused_dispatch,args=(api.dsn,lease,action_id,sink.url,phase,child))
    process.start()
    try:
        assert parent.poll(15) and parent.recv()==phase
        with connect(api.dsn) as conn:
            row=conn.execute('SELECT status FROM outbox WHERE action_id=%s',(action_id,)).fetchone()
            assert row['status']==('queued' if phase=='before_claim' else 'dispatching')
        assert effect_count(api.dsn,action_id)==(1 if phase=='after_sink_commit_before_receipt' else 0)
        if operation=='cancel':
            response=api.request('POST',f'/v1/tasks/{task_id}/cancel')
            assert response.status_code==200,response.text
            assert response.json()['status']==('cancelled' if phase=='before_claim' else 'reconciling')
        else:
            with connect(api.dsn) as conn:
                conn.execute("UPDATE resource_acl SET allowed=false WHERE tenant_id='tenant-a' AND caller_id='alice' AND resource_id='A-1001'")
        completion_attempted=operation=='cancel' or phase!='before_claim'
        if completion_attempted:
            with connect(api.dsn) as conn:
                assert transition(conn,lease,'completed')==0
        parent.send('continue')
        assert parent.poll(15)
        result=parent.recv()
        process.join(timeout=5)
        assert process.exitcode==0
        if phase=='before_claim':
            assert result=='unavailable'
            assert effect_count(api.dsn,action_id)==0
            with connect(api.dsn) as conn:
                assert conn.execute('SELECT status FROM actions WHERE id=%s',(action_id,)).fetchone()['status']==('cancelled' if operation=='cancel' else 'invalidated')
                assert conn.execute('SELECT status FROM tasks WHERE id=%s',(task_id,)).fetchone()['status']==('cancelled' if operation=='cancel' else 'failed')
            kinds=event_kinds(api.dsn,task_id)
            assert 'action.dispatching' not in kinds
        else:
            assert result=='succeeded'
            assert effect_count(api.dsn,action_id)==1
            with connect(api.dsn) as conn:
                assert conn.execute('SELECT status FROM tasks WHERE id=%s',(task_id,)).fetchone()['status']==('cancelled' if operation=='cancel' else 'queued')
                assert conn.execute('SELECT status FROM actions WHERE id=%s',(action_id,)).fetchone()['status']=='succeeded'
            kinds=event_kinds(api.dsn,task_id)
            assert kinds.index('action.dispatching')<kinds.index('outbox.receipt_saved')
            if operation=='cancel':
                assert kinds.index('action.dispatching')<kinds.index('task.cancel_requested')<kinds.index('task.cancelled')
        assert 'task.completed' not in kinds
        with connect(api.dsn) as conn:
            task_status=conn.execute('SELECT status FROM tasks WHERE id=%s',(task_id,)).fetchone()['status']
            action_status=conn.execute('SELECT status FROM actions WHERE id=%s',(action_id,)).fetchone()['status']
            outbox_status=conn.execute('SELECT status FROM outbox WHERE action_id=%s',(action_id,)).fetchone()['status']
            event_sequence=[r['kind'] for r in conn.execute('SELECT kind FROM events WHERE task_id=%s ORDER BY seq',(task_id,)).fetchall()]
        from conftest import record_drill_observation
        record_drill_observation('cancel-revoke-race', {
            'cancel_revoke_cases': [{
                'case_id': f"{phase.replace('_','-')}-{operation}", 'phase': phase,
                'operation': operation, 'task_status': task_status,
                'action_status': action_status, 'outbox_status': outbox_status,
                'sink_effect_count': effect_count(api.dsn, action_id),
                'event_kinds_in_order': event_sequence,
                'completion_attempted': completion_attempted,
                'completion_rejected': completion_attempted and 'task.completed' not in event_sequence,
            }]
        }, dsn=api.dsn, task_ids=[task_id])
    finally:
        if process.is_alive(): process.kill()
        process.join(timeout=5)
        with connect(api.dsn) as conn:
            conn.execute("UPDATE resource_acl SET allowed=true WHERE tenant_id='tenant-a' AND caller_id='alice' AND resource_id='A-1001'")


@pytest.mark.parametrize('mutation',['args','resource','acl','policy','approval_expiry','approver','identity'])
def test_claim_revalidates_frozen_authorization(execution_service,sink,mutation):
    from app.delivery import dispatch_once
    api=execution_service
    task_id,action_id,lease=scheduled(api)
    with connect(api.dsn) as conn:
        original_resource=conn.execute("SELECT version,acl_version FROM resources WHERE tenant_id='tenant-a' AND resource_id='A-1001'").fetchone()
        original_policy=conn.execute("SELECT version FROM tenant_policies WHERE tenant_id='tenant-a'").fetchone()['version']
    with connect(api.dsn) as conn:
        if mutation=='args':
            conn.execute("UPDATE actions SET args=jsonb_set(args,'{message}','\"tampered\"') WHERE id=%s",(action_id,))
        elif mutation in ('resource','acl'):
            field='version' if mutation=='resource' else 'acl_version'
            conn.execute(f"UPDATE resources SET {field}={field}+1 WHERE tenant_id='tenant-a' AND resource_id='A-1001'")
        elif mutation=='policy':
            conn.execute("UPDATE tenant_policies SET version=version+1 WHERE tenant_id='tenant-a'")
        elif mutation=='approval_expiry':
            conn.execute("UPDATE approvals SET expires_at=clock_timestamp()-interval '1 second' WHERE action_id=%s",(action_id,))
        elif mutation=='approver':
            conn.execute("UPDATE caller_identities SET roles=ARRAY['caller'] WHERE tenant_id='tenant-a' AND caller_id='approver'")
        else:
            conn.execute("UPDATE caller_identities SET active=false WHERE tenant_id='tenant-a' AND caller_id='alice'")
    try:
        assert dispatch_once(api.dsn,lease,action_id,sink.url)=='unavailable'
        assert effect_count(api.dsn,action_id)==0
        with connect(api.dsn) as conn:
            assert conn.execute('SELECT status FROM actions WHERE id=%s',(action_id,)).fetchone()['status']=='invalidated'
            assert conn.execute('SELECT status FROM tasks WHERE id=%s',(task_id,)).fetchone()['status']=='failed'
        assert 'action.dispatching' not in event_kinds(api.dsn,task_id)
    finally:
        with connect(api.dsn) as conn:
            conn.execute("UPDATE resources SET version=%s,acl_version=%s WHERE tenant_id='tenant-a' AND resource_id='A-1001'",
                         (original_resource['version'],original_resource['acl_version']))
            conn.execute("UPDATE tenant_policies SET version=%s WHERE tenant_id='tenant-a'",(original_policy,))
            conn.execute("UPDATE caller_identities SET active=true WHERE tenant_id='tenant-a' AND caller_id='alice'")
            conn.execute("UPDATE caller_identities SET roles=ARRAY['caller','approver'] WHERE tenant_id='tenant-a' AND caller_id='approver'")


def test_non_success_action_statuses_cannot_complete(execution_service):
    from app.worker import transition
    from app.outbox import schedule
    api=execution_service
    for status in ['waiting_approval','authorized_pending_delivery','authorized','denied','invalidated','cancelled','unknown']:
        task_id,action_id,lease=approved_action(api)
        with connect(api.dsn) as conn:
            conn.execute('UPDATE actions SET status=%s WHERE id=%s',(status,action_id))
            with pytest.raises(ValueError,match='all actions resolved'):
                transition(conn,lease,'completed')
            if status in ('denied','invalidated','cancelled','unknown'):
                assert schedule(conn,lease,action_id)==0
            assert conn.execute('SELECT status FROM tasks WHERE id=%s',(task_id,)).fetchone()['status']=='running'


def uncommitted_claim(dsn,lease,action_id,channel):
    from app.outbox import claim
    with connect(dsn) as conn:
        dispatch=claim(conn,lease,action_id)
        assert dispatch is not None
        channel.send('claim_locked')
        assert channel.poll(15)
        channel.recv()
    channel.send(dispatch)


@pytest.mark.parametrize('operation',['cancel','revoke'])
def test_claim_transaction_blocks_cancel_and_revoke_until_commit(execution_service,sink,operation):
    """Real row-lock contention, beyond the deterministic boundary injection."""
    from concurrent.futures import ThreadPoolExecutor,TimeoutError as FutureTimeout
    from app.delivery import send
    api=execution_service
    task_id,action_id,lease=scheduled(api)
    context=mp.get_context('spawn')
    parent,child=context.Pipe()
    process=context.Process(target=uncommitted_claim,args=(api.dsn,lease,action_id,child))
    process.start()
    try:
        assert parent.poll(15) and parent.recv()=='claim_locked'
        def mutation():
            if operation=='cancel':
                return api.request('POST',f'/v1/tasks/{task_id}/cancel')
            with connect(api.dsn) as conn:
                conn.execute("UPDATE resource_acl SET allowed=false WHERE tenant_id='tenant-a' AND caller_id='alice' AND resource_id='A-1001'")
            return None
        with ThreadPoolExecutor(1) as pool:
            future=pool.submit(mutation)
            with pytest.raises(FutureTimeout):
                future.result(timeout=.2)
            parent.send('commit')
            assert parent.poll(15)
            dispatch=parent.recv()
            result=future.result(timeout=10)
            if operation=='cancel':
                assert result.status_code==200 and result.json()['status']=='reconciling'
        process.join(timeout=5)
        assert process.exitcode==0
        assert send(api.dsn,dispatch,sink.url,lambda phase:None)=='succeeded'
        assert effect_count(api.dsn,action_id)==1
        with connect(api.dsn) as conn:
            assert conn.execute('SELECT status FROM tasks WHERE id=%s',(task_id,)).fetchone()['status']==('cancelled' if operation=='cancel' else 'queued')
    finally:
        if process.is_alive(): process.kill()
        process.join(timeout=5)
        with connect(api.dsn) as conn:
            conn.execute("UPDATE resource_acl SET allowed=true WHERE tenant_id='tenant-a' AND caller_id='alice' AND resource_id='A-1001'")
