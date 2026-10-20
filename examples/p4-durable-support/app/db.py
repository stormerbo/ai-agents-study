"""PostgreSQL transactions; no in-memory or SQLite durability substitute."""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException
import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from .models import TaskCreate, canonical_payload

MIGRATIONS = Path(__file__).resolve().parents[1] / "migrations"
TASK_COLUMNS = "id, tenant_id, owner_id, status, state_version, release_id, created_at"


def connect(dsn):
    return psycopg.connect(dsn, row_factory=dict_row, connect_timeout=2,
                           options="-c statement_timeout=5000 -c lock_timeout=4000")


def migrate(dsn):
    with connect(dsn) as conn:
        conn.execute("SELECT pg_advisory_xact_lock(4001001)")
        conn.execute("CREATE TABLE IF NOT EXISTS schema_migrations (version text PRIMARY KEY, checksum text NOT NULL, applied_at timestamptz NOT NULL DEFAULT now())")
        for path in sorted(MIGRATIONS.glob("*.sql")):
            source = path.read_text(encoding="utf-8")
            checksum = sha256(source.encode()).hexdigest()
            row = conn.execute("SELECT checksum FROM schema_migrations WHERE version=%s", (path.name,)).fetchone()
            if row:
                if row["checksum"] != checksum:
                    raise RuntimeError("Applied migration checksum changed")
                continue
            conn.execute(source)
            conn.execute("INSERT INTO schema_migrations (version,checksum) VALUES (%s,%s)", (path.name, checksum))


def seed(dsn):
    """Idempotent synthetic setup; reruns never undo a revocation."""
    with connect(dsn) as conn:
        for tenant in ("tenant-a", "tenant-b"):
            conn.execute("INSERT INTO tenants VALUES (%s,%s) ON CONFLICT DO NOTHING", (tenant, "Synthetic " + tenant))
        for tenant, caller, roles in [("tenant-a", "alice", ["caller"]), ("tenant-a", "bob", ["caller"]),
                                      ("tenant-a", "approver", ["caller", "approver"]),
                                      ("tenant-a", "operator", ["caller", "operator"]), ("tenant-b", "mallory", ["caller"])]:
            conn.execute("INSERT INTO caller_identities (tenant_id,caller_id,roles) VALUES (%s,%s,%s) ON CONFLICT DO NOTHING",
                         (tenant, caller, roles))


def append_event(conn, task_id, kind, payload):
    """The task-row lock assigns sequence and append in the caller's transaction."""
    row = conn.execute("UPDATE tasks SET last_event_seq=last_event_seq+1 WHERE id=%s RETURNING last_event_seq", (task_id,)).fetchone()
    if row is None:
        raise ValueError("Task does not exist")
    seq = row["last_event_seq"] if isinstance(row, dict) else row[0]
    conn.execute("INSERT INTO events (task_id,seq,kind,payload) VALUES (%s,%s,%s,%s)", (task_id, seq, kind, Jsonb(payload)))
    return seq


def owned_task(conn, principal, task_id):
    row = conn.execute(f"SELECT {TASK_COLUMNS} FROM tasks WHERE id=%s AND tenant_id=%s AND owner_id=%s",
                       (task_id, principal.tenant_id, principal.caller_id)).fetchone()
    if row is None:
        raise HTTPException(404, detail={"code": "not_found", "message": "Task not found"})
    return row


def create_task(conn, principal, key: str, payload: TaskCreate):
    canonical = canonical_payload(payload)
    digest = sha256(canonical.encode()).hexdigest()
    # Hash collision merely serializes unrelated submissions; SQL uniqueness is final.
    lock_material = json.dumps([principal.tenant_id, principal.caller_id, key], separators=(",", ":"))
    lock_id = int.from_bytes(sha256(lock_material.encode()).digest()[:8], "big", signed=True)
    conn.execute("SELECT pg_advisory_xact_lock(%s)", (lock_id,))
    old = conn.execute("SELECT payload_hash,task_id FROM idempotency_records WHERE tenant_id=%s AND caller_id=%s AND idempotency_key=%s",
                       (principal.tenant_id, principal.caller_id, key)).fetchone()
    if old:
        if old["payload_hash"] != digest:
            raise HTTPException(409, detail={"code": "idempotency_conflict", "message": "Key already used with different payload"})
        return owned_task(conn, principal, old["task_id"]), False
    task_id = uuid4()
    row = conn.execute(f"INSERT INTO tasks (id,tenant_id,owner_id,input,input_hash,release_id) VALUES (%s,%s,%s,%s,%s,%s) RETURNING {TASK_COLUMNS}",
                       (task_id, principal.tenant_id, principal.caller_id, Jsonb(payload.model_dump()), digest, payload.release_id)).fetchone()
    # Never copy user prompts into events/logs. Detailed synthetic input stays in tasks.
    append_event(conn, task_id, "task.created", {"status": "queued", "release_id": payload.release_id})
    conn.execute("INSERT INTO idempotency_records (tenant_id,caller_id,idempotency_key,payload_hash,task_id) VALUES (%s,%s,%s,%s,%s)",
                 (principal.tenant_id, principal.caller_id, key, digest, task_id))
    return row, True


def main():
    from .config import Settings
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["migrate", "seed"])
    args = parser.parse_args()
    dsn = Settings.from_env().database_url
    {"migrate": migrate, "seed": seed}[args.command](dsn)
    print(args.command + " completed (synthetic local service)")


if __name__ == "__main__":
    main()
