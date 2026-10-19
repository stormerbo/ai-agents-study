from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
import uuid

import psycopg
import pytest

pytestmark = pytest.mark.integration


def test_create_read_restart_and_cursor(service, task):
    task_id = task["id"]
    assert task["status"] == "queued"
    assert task["tenant_id"] == "tenant-a"
    assert task["owner_id"] == "alice"
    assert service.request("GET", f"/v1/tasks/{task_id}", index=1).json() == task
    service.restart_api(0)
    service.restart_api(1)
    assert service.request("GET", f"/v1/tasks/{task_id}").json() == task
    events = service.request("GET", f"/v1/tasks/{task_id}/events").json()
    assert [e["seq"] for e in events["events"]] == [1]
    assert events["events"][0]["kind"] == "task.created"
    assert events["next_after"] == 1
    assert service.request("GET", f"/v1/tasks/{task_id}/events?after=1").json() == {"events": [], "next_after": 1}
    assert service.request("GET", f"/v1/tasks/{task_id}/events?after=-1").status_code == 422
    assert service.request("GET", f"/v1/tasks/{task_id}/events?limit=101").status_code == 422


def test_tenant_owner_boundary_and_forged_body(service, task):
    assert service.request("GET", f"/v1/tasks/{task['id']}/approvals").status_code == 501
    for token in ("dev-bob", "dev-mallory"):
        for suffix in ("", "/events", "/approvals"):
            assert service.request("GET", f"/v1/tasks/{task['id']}{suffix}", token=token).status_code == 404
    for field in ("tenant_id", "owner_id", "caller_id", "roles"):
        forged = service.request("POST", "/v1/tasks", json={"prompt": "synthetic", field: "tenant-b"},
                                 headers={"Idempotency-Key": uuid.uuid4().hex})
        assert forged.status_code == 422
    assert service.request("POST", "/v1/tasks", token="unknown", json={"prompt": "x"}).status_code == 401
    assert service.request("GET", "/v1/tasks/not-a-uuid").status_code == 422


def test_revocation_is_rechecked_for_task_events_approvals_and_submit(service, task):
    with psycopg.connect(service.dsn) as conn:
        conn.execute("UPDATE caller_identities SET active=false WHERE tenant_id='tenant-a' AND caller_id='alice'")
    try:
        for index in (0, 1):
            for suffix in ("", "/events", "/approvals"):
                assert service.request("GET", f"/v1/tasks/{task['id']}{suffix}", index=index).status_code == 403
            assert service.request("POST", "/v1/tasks", index=index, json={"prompt": "x"},
                                   headers={"Idempotency-Key": uuid.uuid4().hex}).status_code == 403
    finally:
        with psycopg.connect(service.dsn) as conn:
            conn.execute("UPDATE caller_identities SET active=true WHERE tenant_id='tenant-a' AND caller_id='alice'")


def test_roles_are_current_not_copied_from_token(service, task):
    with psycopg.connect(service.dsn) as conn:
        conn.execute("UPDATE caller_identities SET roles='{}' WHERE tenant_id='tenant-a' AND caller_id='alice'")
    try:
        assert service.request("GET", f"/v1/tasks/{task['id']}").status_code == 403
    finally:
        with psycopg.connect(service.dsn) as conn:
            conn.execute("UPDATE caller_identities SET roles=ARRAY['caller'] WHERE tenant_id='tenant-a' AND caller_id='alice'")


def test_ordered_append_only_events_under_concurrency(service, task):
    from app.db import append_event
    barrier = Barrier(8)

    def append(n):
        barrier.wait(timeout=10)
        with psycopg.connect(service.dsn) as conn:
            return append_event(conn, task["id"], "test.observed", {"index": n})

    with ThreadPoolExecutor(max_workers=8) as pool:
        seqs = list(pool.map(append, range(8)))
    assert sorted(seqs) == list(range(2, 10))
    events = service.request("GET", f"/v1/tasks/{task['id']}/events?after=1&limit=3").json()
    assert [e["seq"] for e in events["events"]] == [2, 3, 4]
    assert events["next_after"] == 4
    assert [e["seq"] for e in service.request("GET", f"/v1/tasks/{task['id']}/events?after=4").json()["events"]] == list(range(5, 10))
    for statement in ("UPDATE events SET kind='tampered' WHERE task_id=%s", "DELETE FROM events WHERE task_id=%s"):
        with pytest.raises(psycopg.errors.RaiseException):
            with psycopg.connect(service.dsn) as conn:
                conn.execute(statement, (task["id"],))


def test_task_event_and_idempotency_rollback_together(service):
    from app.db import create_task, connect
    from app.auth import Principal
    from app.models import TaskCreate
    key = uuid.uuid4().hex
    with pytest.raises(RuntimeError):
        with connect(service.dsn) as conn:
            created, _ = create_task(conn, Principal("tenant-a", "alice", ("caller",)), key, TaskCreate(prompt="rollback"))
            task_id = created["id"]
            raise RuntimeError("synthetic rollback")
    with psycopg.connect(service.dsn) as conn:
        assert conn.execute("SELECT count(*) FROM tasks WHERE id=%s", (task_id,)).fetchone()[0] == 0
        assert conn.execute("SELECT count(*) FROM events WHERE task_id=%s", (task_id,)).fetchone()[0] == 0
        assert conn.execute("SELECT count(*) FROM idempotency_records WHERE idempotency_key=%s", (key,)).fetchone()[0] == 0


def test_health_distinguishes_live_from_unavailable_postgres(service):
    service.compose("stop", "postgres")
    try:
        assert service.request("GET", "/health/live").status_code == 200
        response = service.request("GET", "/health/ready")
        assert response.status_code == 503
        assert response.json() == {"error": {"code": "database_unavailable", "message": "Database unavailable"}}
    finally:
        service.compose("up", "-d", "--wait", "--wait-timeout", "90", "postgres")
    assert service.request("GET", "/health/ready").status_code == 200


def test_migration_rerun_and_foreign_keys(service):
    from app.db import migrate
    migrate(service.dsn)
    with psycopg.connect(service.dsn) as conn:
        assert conn.execute("SELECT count(*) FROM schema_migrations").fetchone()[0] == 1
    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        with psycopg.connect(service.dsn) as conn:
            conn.execute("INSERT INTO tasks (id,tenant_id,owner_id,input,input_hash,release_id) VALUES (%s,'tenant-b','alice','{}','x','test')", (uuid.uuid4(),))


def test_commit_failure_never_returns_a_successful_task(service):
    # A deferred trigger fails at COMMIT, after the endpoint body has returned.
    key = uuid.uuid4().hex
    with psycopg.connect(service.dsn) as conn:
        conn.execute("""CREATE FUNCTION fail_task_commit() RETURNS trigger LANGUAGE plpgsql AS $$
          BEGIN RAISE EXCEPTION 'synthetic commit failure'; END; $$""")
        conn.execute("""CREATE CONSTRAINT TRIGGER test_deferred_commit
          AFTER INSERT ON tasks DEFERRABLE INITIALLY DEFERRED
          FOR EACH ROW EXECUTE FUNCTION fail_task_commit()""")
    try:
        response = service.request("POST", "/v1/tasks", json={"prompt": "commit failure"}, headers={"Idempotency-Key": key})
        assert response.status_code == 503
        with psycopg.connect(service.dsn) as conn:
            assert conn.execute("SELECT count(*) FROM idempotency_records WHERE idempotency_key=%s", (key,)).fetchone()[0] == 0
    finally:
        with psycopg.connect(service.dsn) as conn:
            conn.execute("DROP TRIGGER test_deferred_commit ON tasks")
            conn.execute("DROP FUNCTION fail_task_commit()")
