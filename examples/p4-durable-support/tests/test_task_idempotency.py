from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
import uuid

import psycopg
import pytest

pytestmark = pytest.mark.integration


def test_simultaneous_same_key_across_two_api_processes(service):
    barrier = Barrier(2)
    key = uuid.uuid4().hex

    def submit(index):
        barrier.wait(timeout=10)
        payload = {"prompt": "查询合成订单"} if index == 0 else {"release_id": "stage4-local-v1", "prompt": "查询合成订单"}
        return service.request("POST", "/v1/tasks", index=index, json=payload, headers={"Idempotency-Key": key})

    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(submit, range(2)))
    assert sorted(r.status_code for r in responses) == [200, 201]
    assert responses[0].json() == responses[1].json()
    task_id = responses[0].json()["id"]
    with psycopg.connect(service.dsn) as conn:
        assert conn.execute("SELECT count(*) FROM idempotency_records WHERE idempotency_key=%s", (key,)).fetchone()[0] == 1
        assert conn.execute("SELECT count(*) FROM events WHERE task_id=%s", (task_id,)).fetchone()[0] == 1
    conflict = service.request("POST", "/v1/tasks", json={"prompt": "different"}, headers={"Idempotency-Key": key})
    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == "idempotency_conflict"
    service.restart_api(1)
    assert service.request("POST", "/v1/tasks", index=1, json={"prompt": "查询合成订单"}, headers={"Idempotency-Key": key}).json()["id"] == task_id
    from conftest import record_drill_observation
    record_drill_observation('idempotency', {
        'response_statuses': [r.status_code for r in responses] + [conflict.status_code, 200],
        'unique_task_ids': 1, 'task_count': 1, 'event_count': 1,
        'idempotency_record_count': 1,
    }, dsn=service.dsn, task_ids=[task_id])


def test_same_key_is_scoped_to_tenant_and_caller(service):
    key = uuid.uuid4().hex
    ids = set()
    for token in ("dev-alice", "dev-bob", "dev-mallory"):
        response = service.request("POST", "/v1/tasks", token=token, json={"prompt": "synthetic"}, headers={"Idempotency-Key": key})
        assert response.status_code == 201
        ids.add(response.json()["id"])
    assert len(ids) == 3
    with psycopg.connect(service.dsn) as conn:
        record_count = conn.execute("SELECT count(*) FROM idempotency_records WHERE idempotency_key=%s", (key,)).fetchone()[0]
        event_count = conn.execute("SELECT count(*) FROM events e JOIN idempotency_records i ON i.task_id=e.task_id WHERE i.idempotency_key=%s", (key,)).fetchone()[0]
    from conftest import record_drill_observation
    record_drill_observation('idempotency', {
        'response_statuses': [201, 201, 201], 'unique_task_ids': len(ids),
        'task_count': len(ids), 'event_count': event_count,
        'idempotency_record_count': record_count,
    }, dsn=service.dsn, task_ids=list(ids))


def test_key_is_required_and_bounded(service):
    for headers in ({}, {"Idempotency-Key": ""}, {"Idempotency-Key": "x" * 201}):
        assert service.request("POST", "/v1/tasks", json={"prompt": "synthetic"}, headers=headers).status_code == 422
