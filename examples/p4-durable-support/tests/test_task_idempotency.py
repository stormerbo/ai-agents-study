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


def test_same_key_is_scoped_to_tenant_and_caller(service):
    key = uuid.uuid4().hex
    ids = set()
    for token in ("dev-alice", "dev-bob", "dev-mallory"):
        response = service.request("POST", "/v1/tasks", token=token, json={"prompt": "synthetic"}, headers={"Idempotency-Key": key})
        assert response.status_code == 201
        ids.add(response.json()["id"])
    assert len(ids) == 3


def test_key_is_required_and_bounded(service):
    for headers in ({}, {"Idempotency-Key": ""}, {"Idempotency-Key": "x" * 201}):
        assert service.request("POST", "/v1/tasks", json={"prompt": "synthetic"}, headers=headers).status_code == 422
