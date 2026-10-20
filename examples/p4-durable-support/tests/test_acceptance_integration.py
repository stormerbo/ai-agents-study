"""Stage 4 acceptance checks over the required real PostgreSQL harness."""
import psycopg
import uuid

import pytest

pytestmark = pytest.mark.integration


def test_stage4_acceptance_uses_latest_schema_and_cross_process_task_reads(service):
    expected_migrations = {
        "0001_base.sql",
        "0002_execution.sql",
        "0003_delivery.sql",
        "0004_manual_resolution.sql",
    }
    with psycopg.connect(service.dsn) as conn:
        applied = {row[0] for row in conn.execute("SELECT version FROM schema_migrations")}
        latest_row = conn.execute(
            "SELECT version, checksum, applied_at FROM schema_migrations WHERE version='0004_manual_resolution.sql'"
        ).fetchone()
    assert applied == expected_migrations

    # Both API processes must refuse readiness unless the entire Stage 4 schema exists.
    assert service.request("GET", "/health/ready", index=0).status_code == 200
    assert service.request("GET", "/health/ready", index=1).status_code == 200

    # Readiness is tied to the latest schema, not merely a connected database.
    with psycopg.connect(service.dsn) as conn:
        conn.execute("DELETE FROM schema_migrations WHERE version='0004_manual_resolution.sql'")
    try:
        assert service.request("GET", "/health/ready", index=0).status_code == 503
        assert service.request("GET", "/health/ready", index=1).status_code == 503
    finally:
        with psycopg.connect(service.dsn) as conn:
            conn.execute(
                "INSERT INTO schema_migrations (version,checksum,applied_at) VALUES (%s,%s,%s)", latest_row
            )
    assert service.request("GET", "/health/ready", index=0).status_code == 200

    key = "acceptance-" + uuid.uuid4().hex
    created = service.request(
        "POST", "/v1/tasks", index=0, json={"prompt": "查询合成订单 A-1001"},
        headers={"Idempotency-Key": key},
    )
    assert created.status_code == 201, created.text
    task_id = created.json()["id"]

    # A separate API OS process sees the durable tenant/owner-scoped task and event.
    read = service.request("GET", f"/v1/tasks/{task_id}", index=1)
    assert read.status_code == 200
    assert read.json()["id"] == task_id
    events = service.request("GET", f"/v1/tasks/{task_id}/events", index=1)
    assert events.status_code == 200
    assert [event["kind"] for event in events.json()["events"]] == ["task.created"]

    # Stage 4 proves durable control-plane behavior with synthetic data; it does not
    # execute a model turn or establish provider quality.
    assert read.json()["status"] == "queued"
