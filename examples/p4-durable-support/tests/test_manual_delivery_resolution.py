"""Operator decisions close irrecoverable unknowns without inventing tool success."""
from concurrent.futures import ThreadPoolExecutor
import uuid

import httpx
import psycopg
import pytest

from app.db import connect
from conftest import unused_port
from test_delivery_reconciliation import scheduled, approved_action, event_kinds
from test_worker_ownership import execution_service

pytestmark=pytest.mark.integration


def unknown_action(api):
    from app.delivery import dispatch_once
    task_id,action_id,lease=scheduled(api)
    assert dispatch_once(api.dsn,lease,action_id,f'http://127.0.0.1:{unused_port()}')=='unknown'
    with connect(api.dsn) as conn:
        row=conn.execute('SELECT dispatch_token FROM outbox WHERE action_id=%s',(action_id,)).fetchone()
        checkpoint=conn.execute('SELECT checkpoint FROM tasks WHERE id=%s',(task_id,)).fetchone()['checkpoint']
    return task_id,action_id,lease,row['dispatch_token'],checkpoint


def decision(token,**changes):
    return {'dispatch_token':str(token),'outcome':'effect_not_applied',
        'evidence_reference':'local-investigation:case-42','reason':'Operator chose to close this synthetic incident.',**changes}


def resolve(api,action_id,body,token='dev-operator'):
    return api.request('POST',f'/v1/actions/{action_id}/manual-resolution',token=token,json=body)


def test_manual_resolution_requires_authenticated_current_operator(execution_service):
    api=execution_service
    task_id,action_id,lease,token,checkpoint=unknown_action(api)
    path=f'/v1/actions/{action_id}/manual-resolution'
    assert httpx.post(api.url+path,json=decision(token)).status_code==401
    for caller in ('dev-alice','dev-approver','dev-bob','dev-mallory'):
        assert resolve(api,action_id,decision(token),caller).status_code==403
    with connect(api.dsn) as conn:
        conn.execute("UPDATE caller_identities SET roles=ARRAY['caller'] WHERE tenant_id='tenant-a' AND caller_id='operator'")
    try:
        assert resolve(api,action_id,decision(token)).status_code==403
    finally:
        with connect(api.dsn) as conn:
            conn.execute("UPDATE caller_identities SET roles=ARRAY['caller','operator'] WHERE tenant_id='tenant-a' AND caller_id='operator'")
    assert resolve(api,uuid.uuid4(),decision(token)).status_code==404
    assert api.request('GET',f'/v1/actions/{action_id}/delivery').status_code==403
    inspection=api.request('GET',f'/v1/actions/{action_id}/delivery',token='dev-operator')
    assert inspection.status_code==200,inspection.text
    assert inspection.json()['dispatch_token']==str(token) and inspection.json()['status']=='unknown'
    with connect(api.dsn) as conn:
        assert conn.execute('SELECT status FROM tasks WHERE id=%s',(task_id,)).fetchone()['status']=='reconciling'
        assert conn.execute('SELECT count(*) AS n FROM manual_delivery_resolutions WHERE action_id=%s',(action_id,)).fetchone()['n']==0


@pytest.mark.parametrize('field,value',[
    ('evidence_reference',None),('evidence_reference',''),('evidence_reference','   '),
    ('reason',None),('reason',''),('reason','   '),('outcome','success')])
def test_manual_resolution_requires_explicit_outcome_evidence_and_reason(execution_service,field,value):
    api=execution_service
    task_id,action_id,lease,token,checkpoint=unknown_action(api)
    body=decision(token)
    if value is None:
        del body[field]
    else:
        body[field]=value
    assert resolve(api,action_id,body).status_code==422
    assert resolve(api,action_id,{**decision(token),'operator_id':'alice'}).status_code==422
    with connect(api.dsn) as conn:
        assert conn.execute('SELECT status FROM actions WHERE id=%s',(action_id,)).fetchone()['status']=='unknown'
        assert conn.execute('SELECT count(*) AS n FROM manual_delivery_resolutions WHERE action_id=%s',(action_id,)).fetchone()['n']==0


@pytest.mark.parametrize('outcome',['effect_applied','effect_not_applied','abandon'])
@pytest.mark.parametrize('cancelled',[False,True])
def test_all_manual_outcomes_close_without_receipt_or_result_and_cannot_complete(execution_service,outcome,cancelled):
    from app.delivery import reconcile
    from app.worker import transition,claim
    from app.outbox import Dispatch,save_receipt
    api=execution_service
    task_id,action_id,lease,token,checkpoint=unknown_action(api)
    if cancelled:
        assert api.request('POST',f'/v1/tasks/{task_id}/cancel').json()['status']=='reconciling'
    response=resolve(api,action_id,decision(token,outcome=outcome))
    assert response.status_code==200,response.text
    assert response.json()['status']==('cancelled' if cancelled else 'failed')
    assert resolve(api,action_id,decision(token,outcome=outcome)).status_code==409
    with connect(api.dsn) as conn:
        task=conn.execute('SELECT status,checkpoint FROM tasks WHERE id=%s',(task_id,)).fetchone()
        action=conn.execute('SELECT status,result FROM actions WHERE id=%s',(action_id,)).fetchone()
        row=conn.execute('SELECT status,receipt,payload,dispatch_token FROM outbox WHERE action_id=%s',(action_id,)).fetchone()
        audit=conn.execute('SELECT * FROM manual_delivery_resolutions WHERE action_id=%s',(action_id,)).fetchone()
        assert task['checkpoint']==checkpoint
        assert action=={'status':'cancelled' if outcome=='abandon' else 'failed','result':None}
        assert row['receipt'] is None and row['dispatch_token'] is None
        assert audit['outcome']==outcome and audit['operator_id']=='operator'
        assert audit['evidence_reference']=='local-investigation:case-42'
        assert audit['reason']=='Operator chose to close this synthetic incident.'
        assert audit['dispatch_token']==token
        assert claim(conn,'must-not-resume',task_id=task_id) is None
        assert transition(conn,lease,'completed',output_valid=True)==0
        stale=Dispatch(action_id,task_id,token,f'p4-notice:{action_id}',row['payload'])
        assert save_receipt(conn,stale,{'forged':'late response'})==0
    assert reconcile(api.dsn,action_id,f'http://127.0.0.1:{unused_port()}')=='unavailable'
    kinds=event_kinds(api.dsn,task_id)
    assert kinds.count('action.manual_resolved')==1
    assert 'action.succeeded' not in kinds and 'task.completed' not in kinds
    with connect(api.dsn) as conn:
        # Even an accidental host-side requeue cannot bypass the existing
        # all-actions-succeeded completion guard after a manual decision.
        conn.execute("UPDATE tasks SET status='queued',cancel_requested=false WHERE id=%s",(task_id,))
        renewed=claim(conn,'invalid-host-requeue',task_id=task_id)
        with pytest.raises(ValueError,match='all actions resolved'):
            transition(conn,renewed,'completed',output_valid=True)
        conn.rollback()


def test_manual_resolution_rejects_stale_token_and_active_reconciliation_claim(execution_service):
    from app.outbox import recover
    api=execution_service
    task_id,action_id,lease,old,checkpoint=unknown_action(api)
    with connect(api.dsn) as conn:
        fresh=recover(conn,action_id)
        assert fresh and fresh.token!=old
    assert resolve(api,action_id,decision(old)).status_code==409
    assert resolve(api,action_id,decision(fresh.token)).status_code==409
    with connect(api.dsn) as conn:
        conn.execute("UPDATE outbox SET claim_until=clock_timestamp()-interval '1 second' WHERE action_id=%s",(action_id,))
    assert resolve(api,action_id,decision(old)).status_code==409
    assert resolve(api,action_id,decision(fresh.token)).status_code==200


def test_manual_resolution_rejects_queued_and_dispatching_actions(execution_service):
    from app.outbox import claim
    api=execution_service
    task_id,action_id,lease=scheduled(api)
    assert resolve(api,action_id,decision(uuid.uuid4())).status_code==409
    with connect(api.dsn) as conn:
        dispatch=claim(conn,lease,action_id)
        assert dispatch
        conn.execute("UPDATE outbox SET claim_until=clock_timestamp()-interval '1 second' WHERE action_id=%s",(action_id,))
    assert resolve(api,action_id,decision(dispatch.token)).status_code==409


def test_manual_resolution_is_single_decision_and_audit_is_append_only(execution_service):
    api=execution_service
    task_id,action_id,lease,token,checkpoint=unknown_action(api)
    def submit(outcome):
        return resolve(api,action_id,decision(token,outcome=outcome)).status_code
    with ThreadPoolExecutor(2) as pool:
        assert sorted(pool.map(submit,['effect_applied','abandon']))==[200,409]
    for sql in [
        'UPDATE manual_delivery_resolutions SET reason=reason WHERE action_id=%s',
        'DELETE FROM manual_delivery_resolutions WHERE action_id=%s',
        'TRUNCATE manual_delivery_resolutions',
    ]:
        with connect(api.dsn) as conn:
            with pytest.raises(psycopg.Error):
                conn.execute(sql,() if sql.startswith('TRUNCATE') else (action_id,))
            conn.rollback()
    with connect(api.dsn) as conn:
        assert conn.execute('SELECT count(*) AS n FROM manual_delivery_resolutions WHERE action_id=%s',(action_id,)).fetchone()['n']==1
    assert event_kinds(api.dsn,task_id).count('action.manual_resolved')==1


@pytest.mark.parametrize('winner',['manual','reconcile'])
def test_manual_decision_and_reconcile_takeover_serialize_on_task_lock(execution_service,winner):
    from concurrent.futures import TimeoutError as FutureTimeout
    from app.outbox import manual_resolve,recover
    api=execution_service
    task_id,action_id,lease,token,checkpoint=unknown_action(api)
    with connect(api.dsn) as first:
        first.execute('SELECT id FROM tasks WHERE id=%s FOR UPDATE',(task_id,))
        if winner=='reconcile':
            newer=recover(first,action_id)
            assert newer and newer.token!=token
        def competing():
            if winner=='reconcile':
                return resolve(api,action_id,decision(token)).status_code
            with connect(api.dsn) as second:
                return recover(second,action_id)
        with ThreadPoolExecutor(1) as pool:
            future=pool.submit(competing)
            with pytest.raises(FutureTimeout):
                future.result(timeout=.2)
            if winner=='manual':
                result=manual_resolve(first,action_id,'tenant-a','operator',token,
                    'effect_not_applied','local-investigation:locked','Explicit non-success closure.')
                assert result and result['status']=='failed'
            first.commit()
            result=future.result(timeout=10)
    assert result==(409 if winner=='reconcile' else None)
    with connect(api.dsn) as conn:
        audits=conn.execute('SELECT count(*) AS n FROM manual_delivery_resolutions WHERE action_id=%s',(action_id,)).fetchone()['n']
        assert audits==(0 if winner=='reconcile' else 1)
        assert conn.execute('SELECT checkpoint FROM tasks WHERE id=%s',(task_id,)).fetchone()['checkpoint']==checkpoint


def test_operator_cannot_inspect_or_close_another_tenants_action(execution_service):
    from app.auth import Principal
    from app.db import create_task
    from app.models import TaskCreate
    from psycopg.types.json import Jsonb
    api=execution_service
    action_id=uuid.uuid4()
    token=uuid.uuid4()
    # A synthetic foreign-tenant unknown ledger row isolates the API's tenant
    # boundary; it asserts no receiver behavior or successful authorization.
    with connect(api.dsn) as conn:
        task_id=create_task(conn,Principal('tenant-b','mallory',('caller',)),uuid.uuid4().hex,
                            TaskCreate(prompt='Synthetic foreign incident'))[0]['id']
        conn.execute("UPDATE tasks SET status='reconciling' WHERE id=%s",(task_id,))
        conn.execute('''INSERT INTO actions(id,task_id,tenant_id,turn_epoch,turn_id,position,tool_call_id,
            tool,args,canonical_args_hash,requires_approval,status)
            VALUES (%s,%s,'tenant-b',1,%s,0,'foreign','send_notice','{}','synthetic',true,'unknown')''',
            (action_id,task_id,uuid.uuid4()))
        conn.execute('''INSERT INTO outbox(action_id,task_id,tenant_id,external_key,payload,scheduled_epoch,
            status,dispatch_token,claim_until) VALUES (%s,%s,'tenant-b',%s,%s,1,'unknown',%s,clock_timestamp()-interval '1 second')''',
            (action_id,task_id,f'p4-notice:{action_id}',Jsonb({}),token))
    assert api.request('GET',f'/v1/actions/{action_id}/delivery',token='dev-operator').status_code==404
    assert resolve(api,action_id,decision(token)).status_code==404
    with connect(api.dsn) as conn:
        assert conn.execute('SELECT status FROM outbox WHERE action_id=%s',(action_id,)).fetchone()['status']=='unknown'
        assert conn.execute('SELECT count(*) AS n FROM manual_delivery_resolutions WHERE action_id=%s',(action_id,)).fetchone()['n']==0
