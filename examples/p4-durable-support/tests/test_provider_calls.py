"""Durable provider-call state and late-response fencing on real PostgreSQL."""
import hashlib
import json
import uuid

import pytest

from app.db import connect
from test_worker_ownership import new_task

pytestmark = pytest.mark.integration


def _prepared(service):
    from app.worker import claim
    from app.limits import acquire_provider, reserve
    from app.provider_calls import prepare

    task_id = new_task(service.dsn)
    endpoint = 'call-' + uuid.uuid4().hex
    account = 'call-budget-' + uuid.uuid4().hex
    request = {'model': 'fixture-model', 'messages': [{'role': 'user', 'content': 'synthetic'}]}
    digest = hashlib.sha256(json.dumps(request, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    request_id = uuid.uuid4()
    with connect(service.dsn) as conn:
        release_id = conn.execute('SELECT release_id FROM tasks WHERE id=%s', (task_id,)).fetchone()['release_id']
        conn.execute('INSERT INTO provider_endpoints VALUES (%s,1,3)', (endpoint,))
        conn.execute('INSERT INTO budget_accounts(id,tenant_id,token_limit,tool_limit) VALUES (%s,%s,1000,10)', (account, 'tenant-a'))
        lease = claim(conn, 'provider-call', task_id=task_id)
        slot = acquire_provider(conn, lease, endpoint)
        reservation = reserve(conn, lease, account, tokens=100, tools=2)
        assert slot and reservation
        assert prepare(conn, lease, request_id=request_id, endpoint=endpoint, slot_id=slot,
                       reservation_id=reservation, release_id=release_id, model='fixture-model',
                       request=request, request_hash=digest)
    return task_id, lease, endpoint, account, slot, reservation, request_id, request, digest, release_id


def test_prepare_send_response_and_usage_settlement_are_idempotent(service):
    from app.limits import budget_report
    from app.provider_calls import mark_sending, record_response, get_call

    task_id, lease, endpoint, account, slot, reservation, request_id, request, digest, release_id = _prepared(service)
    with connect(service.dsn) as conn:
        row = get_call(conn, request_id)
        assert row['state'] == 'prepared'
        assert row['request_hash'] == digest
        assert row['request_body'] == request
        assert mark_sending(conn, lease, request_id)
        response = {'id': 'resp-1', 'content': [{'type': 'text', 'text': 'ok'}]}
        response_hash = hashlib.sha256(json.dumps(response, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        assert record_response(conn, request_id, response=response, response_hash=response_hash,
                               stop_reason='end_turn', usage_tokens=37, usage_tools=0)
        assert record_response(conn, request_id, response=response, response_hash=response_hash,
                               stop_reason='end_turn', usage_tokens=37, usage_tools=0)
        report = budget_report(conn, account)
        assert report['reserved_tokens'] == 0
        assert report['consumed_tokens'] == 37
        assert get_call(conn, request_id)['state'] == 'response_saved'
        conflict = {'id': 'different'}
        conflict_hash = hashlib.sha256(json.dumps(conflict, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        assert not record_response(conn, request_id, response=conflict, response_hash=conflict_hash,
                                   stop_reason='end_turn', usage_tokens=1, usage_tools=0)


def test_late_response_settles_usage_but_stale_epoch_cannot_process_it(service):
    from app.worker import claim
    from app.limits import budget_report
    from app.provider_calls import mark_sending, record_response, mark_processed, get_call

    task_id, old_lease, endpoint, account, slot, reservation, request_id, request, digest, release_id = _prepared(service)
    with connect(service.dsn) as conn:
        assert mark_sending(conn, old_lease, request_id)
        conn.execute("UPDATE tasks SET lease_until=clock_timestamp()-interval '1 second' WHERE id=%s", (task_id,))
        new_lease = claim(conn, 'successor', task_id=task_id)
        assert new_lease and new_lease.epoch == old_lease.epoch + 1
        response = {'id': 'late-response', 'content': []}
        response_hash = hashlib.sha256(json.dumps(response, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        assert record_response(conn, request_id, response=response, response_hash=response_hash,
                               stop_reason='end_turn', usage_tokens=24, usage_tools=0)
        assert not mark_processed(conn, old_lease, request_id)
        assert get_call(conn, request_id)['state'] == 'response_saved'
        assert mark_processed(conn, new_lease, request_id)
        assert get_call(conn, request_id)['state'] == 'processed'
        assert budget_report(conn, account)['consumed_tokens'] == 24
        assert not mark_processed(conn, new_lease, request_id)
        current=conn.execute('SELECT checkpoint FROM tasks WHERE id=%s',(task_id,)).fetchone()['checkpoint']
        checkpoint_hash=hashlib.sha256(json.dumps(current,sort_keys=True,default=str).encode()).hexdigest()
        budget=budget_report(conn,account)
        call_state=get_call(conn,request_id)['state']
    from conftest import record_drill_observation
    record_drill_observation('lease-takeover', {
        'owner_epochs':[old_lease.epoch,new_lease.epoch],
        'stale_mutation_counts':{'provider_consume_rejected':1},
        'checkpoint_sha256':checkpoint_hash,'provider_call_status':call_state,
        'budget':{'reserved_tokens':budget['reserved_tokens'],'consumed_tokens':budget['consumed_tokens'],
                  'reserved_tools':budget['reserved_tools'],'consumed_tools':budget['consumed_tools']},
    }, dsn=service.dsn, task_ids=[task_id])


def test_sending_call_can_be_marked_unknown_but_never_retried(service):
    from app.provider_calls import mark_sending, mark_unknown, prepare, record_response, get_call
    from app.limits import budget_report, reserve, acquire_provider

    task_id, lease, endpoint, account, slot, reservation, request_id, request, digest, release_id = _prepared(service)
    with connect(service.dsn) as conn:
        assert mark_sending(conn, lease, request_id)
        assert mark_unknown(conn, request_id)
        assert not mark_sending(conn, lease, request_id)
        assert not prepare(conn, lease, request_id=request_id, endpoint=endpoint, slot_id=slot,
                           reservation_id=reservation, release_id=release_id, model='fixture-model',
                           request=request, request_hash=digest)
        row = conn.execute('SELECT state FROM budget_reservations WHERE id=%s', (reservation,)).fetchone()
        assert row['state'] == 'unknown'
        assert budget_report(conn, account)['reserved_tokens'] == 100
        conn.execute('UPDATE provider_endpoints SET concurrency_limit=2 WHERE id=%s', (endpoint,))
        retry_slot = acquire_provider(conn, lease, endpoint)
        retry_reservation = reserve(conn, lease, account, tokens=100, tools=2)
        assert retry_slot and retry_reservation
        retry_request_id = uuid.uuid4()
        assert not prepare(conn, lease, request_id=retry_request_id, endpoint=endpoint, slot_id=retry_slot,
                           reservation_id=retry_reservation, release_id=release_id, model='fixture-model',
                           request=request, request_hash=digest, round_index=1)
        response = {'id': 'late-after-unknown', 'content': []}
        response_hash = hashlib.sha256(json.dumps(response, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        assert record_response(conn, request_id, response=response, response_hash=response_hash,
                               stop_reason='end_turn', usage_tokens=19, usage_tools=0)
        assert get_call(conn, request_id)['state'] == 'response_saved'
        report=budget_report(conn, account)
        assert report['consumed_tokens'] == 19
    from conftest import record_drill_observation
    record_drill_observation('budget-unknown', {
        'provider_call_states':['unknown','response_saved'],
        'reservation_states':['unknown','settled','reserved'],
        'budget_after':{'reserved_tokens':report['reserved_tokens'],'consumed_tokens':report['consumed_tokens'],
                        'reserved_tools':report['reserved_tools'],'consumed_tools':report['consumed_tools']},
    }, dsn=service.dsn, task_ids=[task_id])


def test_saved_response_with_missing_usage_can_be_reconciled_later(service):
    from app.limits import budget_report
    from app.provider_calls import mark_sending, record_response

    task_id, lease, endpoint, account, slot, reservation, request_id, request, digest, release_id = _prepared(service)
    response = {'id': 'usage-late', 'content': []}
    response_hash = hashlib.sha256(json.dumps(response, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    with connect(service.dsn) as conn:
        assert mark_sending(conn, lease, request_id)
        assert record_response(conn, request_id, response=response, response_hash=response_hash,
                               stop_reason='end_turn', usage_tokens=None, usage_tools=None)
        assert budget_report(conn, account)['reserved_tokens'] == 100
        assert record_response(conn, request_id, response=response, response_hash=response_hash,
                               stop_reason='end_turn', usage_tokens=42, usage_tools=1)
        assert budget_report(conn, account)['reserved_tokens'] == 0
        assert budget_report(conn, account)['consumed_tokens'] == 42
        report=budget_report(conn,account)
    from conftest import record_drill_observation
    record_drill_observation('budget-unknown', {
        'provider_call_states':['response_saved-with-missing-usage','response_saved-settled'],
        'reservation_states':['unknown','settled'],
        'budget_after':{'reserved_tokens':report['reserved_tokens'],'consumed_tokens':report['consumed_tokens'],
                        'reserved_tools':report['reserved_tools'],'consumed_tools':report['consumed_tools']},
    }, dsn=service.dsn, task_ids=[task_id])


def test_successor_can_abandon_only_unsent_prepared_call_and_release_resources(service):
    from app.limits import budget_report, acquire_provider, reserve
    from app.provider_calls import abandon_prepared, get_call, prepare
    from app.worker import claim

    task_id, old_lease, endpoint, account, slot, reservation, request_id, request, digest, release_id = _prepared(service)
    with connect(service.dsn) as conn:
        conn.execute("UPDATE tasks SET lease_until=clock_timestamp()-interval '1 second' WHERE id=%s", (task_id,))
        successor = claim(conn, 'prepared-recovery', task_id=task_id)
        assert successor and successor.epoch == old_lease.epoch + 1
        assert abandon_prepared(conn, successor, request_id)
        assert get_call(conn, request_id)['state'] == 'failed'
        assert conn.execute('SELECT state FROM budget_reservations WHERE id=%s', (reservation,)).fetchone()['state'] == 'released'
        report = budget_report(conn, account)
        assert report['reserved_tokens'] == 0
        assert conn.execute('SELECT 1 FROM provider_slots WHERE id=%s', (slot,)).fetchone() is None
        new_slot = acquire_provider(conn, successor, endpoint)
        new_reservation = reserve(conn, successor, account, tokens=100, tools=2)
        new_request_id = uuid.uuid4()
        assert prepare(conn, successor, request_id=new_request_id, endpoint=endpoint, slot_id=new_slot,
                       reservation_id=new_reservation, release_id=release_id, model='fixture-model',
                       request=request, request_hash=digest, round_index=1)


def test_successor_cannot_abandon_a_sending_call(service):
    from app.provider_calls import abandon_prepared, mark_sending
    from app.worker import claim

    task_id, old_lease, endpoint, account, slot, reservation, request_id, request, digest, release_id = _prepared(service)
    with connect(service.dsn) as conn:
        assert mark_sending(conn, old_lease, request_id)
        conn.execute("UPDATE tasks SET lease_until=clock_timestamp()-interval '1 second' WHERE id=%s", (task_id,))
        successor = claim(conn, 'sending-recovery', task_id=task_id)
        assert successor and successor.epoch == old_lease.epoch + 1
        assert not abandon_prepared(conn, successor, request_id)
        assert conn.execute('SELECT state FROM provider_calls WHERE request_id=%s', (request_id,)).fetchone()['state'] == 'sending'
        assert conn.execute('SELECT state FROM budget_reservations WHERE id=%s', (reservation,)).fetchone()['state'] == 'reserved'
