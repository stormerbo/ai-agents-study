"""SQLite failure-boundary model for ERR-006/007.

This is an executable teaching model, not a production queue or proof of a
remote provider's guarantees. The receiver database represents a separate
service. Its unique external key is an explicit receiver-side idempotency
contract.
"""
from __future__ import annotations

import sqlite3
import uuid
from pathlib import Path


class FaultModel:
    def __init__(self, app_db: Path, receiver_db: Path):
        self.app_db = app_db
        self.receiver_db = receiver_db
        with self.connect(app_db) as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY, tenant TEXT NOT NULL, idem_key TEXT NOT NULL,
                    payload TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'queued',
                    owner TEXT, UNIQUE(tenant, idem_key)
                );
                CREATE TABLE IF NOT EXISTS outbox (
                    operation_id TEXT PRIMARY KEY, payload TEXT NOT NULL,
                    state TEXT NOT NULL DEFAULT 'queued', receipt TEXT
                );
            """)
        with self.connect(receiver_db) as db:
            db.execute("CREATE TABLE IF NOT EXISTS deliveries (external_key TEXT PRIMARY KEY, payload TEXT NOT NULL)")

    @staticmethod
    def connect(path: Path) -> sqlite3.Connection:
        db = sqlite3.connect(path, timeout=5, isolation_level=None)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA busy_timeout=5000")
        return db

    def submit(self, tenant: str, idem_key: str, payload: str) -> str:
        """Insert once per caller idempotency scope; retries return same task."""
        with self.connect(self.app_db) as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute(
                "INSERT OR IGNORE INTO tasks(id,tenant,idem_key,payload) VALUES(?,?,?,?)",
                (str(uuid.uuid4()), tenant, idem_key, payload),
            )
            existing = db.execute(
                "SELECT id, payload FROM tasks WHERE tenant=? AND idem_key=?", (tenant, idem_key)
            ).fetchone()
            if existing["payload"] != payload:
                raise ValueError("idempotency key was reused with a different payload")
            db.commit()
            return existing["id"]

    def claim(self, worker: str) -> str | None:
        """Atomic single-task claim in this SQLite model."""
        with self.connect(self.app_db) as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT id FROM tasks WHERE status='queued' ORDER BY id LIMIT 1").fetchone()
            if row is None:
                db.commit()
                return None
            changed = db.execute(
                "UPDATE tasks SET status='running', owner=? WHERE id=? AND status='queued'",
                (worker, row["id"]),
            ).rowcount
            db.commit()
            return row["id"] if changed == 1 else None

    def enqueue_external_action(self, operation_id: str, payload: str) -> None:
        with self.connect(self.app_db) as db:
            db.execute("INSERT OR IGNORE INTO outbox(operation_id,payload) VALUES(?,?)", (operation_id, payload))
            existing = db.execute(
                "SELECT payload FROM outbox WHERE operation_id=?", (operation_id,)
            ).fetchone()
            if existing["payload"] != payload:
                raise ValueError("operation_id was reused with a different payload")

    def dispatch(self, operation_id: str, crash_at: str | None = None) -> str:
        """Send with a stable key, exposing crash points around the remote call."""
        with self.connect(self.app_db) as db:
            db.execute("UPDATE outbox SET state='dispatching' WHERE operation_id=? AND state IN ('queued','unknown','dispatching')", (operation_id,))
            row = db.execute("SELECT payload FROM outbox WHERE operation_id=?", (operation_id,)).fetchone()
            if row is None:
                raise KeyError(operation_id)
        if crash_at == "before_external_call":
            raise RuntimeError("injected crash before external call")

        # The separate receiver commits the side effect and deduplicates by key.
        with self.connect(self.receiver_db) as receiver:
            receiver.execute("INSERT OR IGNORE INTO deliveries(external_key,payload) VALUES(?,?)", (operation_id, row["payload"]))
            delivery = receiver.execute(
                "SELECT external_key, payload FROM deliveries WHERE external_key=?", (operation_id,)
            ).fetchone()
            if delivery["payload"] != row["payload"]:
                raise ValueError("receiver idempotency key was reused with a different payload")
            receipt = delivery["external_key"]
        if crash_at == "after_external_call_before_receipt":
            raise RuntimeError("injected crash after external success, before local receipt")
        with self.connect(self.app_db) as db:
            db.execute("UPDATE outbox SET state='sent', receipt=? WHERE operation_id=?", (receipt, operation_id))
        return "sent"

    def reconcile(self, operation_id: str) -> str:
        with self.connect(self.app_db) as db:
            outbox_row = db.execute(
                "SELECT payload FROM outbox WHERE operation_id=?", (operation_id,)
            ).fetchone()
        if outbox_row is None:
            raise KeyError(operation_id)
        with self.connect(self.receiver_db) as receiver:
            row = receiver.execute(
                "SELECT external_key, payload FROM deliveries WHERE external_key=?", (operation_id,)
            ).fetchone()
        if row is None:
            return self.dispatch(operation_id)
        if row["payload"] != outbox_row["payload"]:
            raise ValueError("receiver idempotency key was reused with a different payload")
        with self.connect(self.app_db) as db:
            db.execute("UPDATE outbox SET state='sent', receipt=? WHERE operation_id=?", (row["external_key"], operation_id))
        return "reconciled_sent"

    def delivery_count(self, operation_id: str) -> int:
        with self.connect(self.receiver_db) as db:
            return db.execute("SELECT COUNT(*) FROM deliveries WHERE external_key=?", (operation_id,)).fetchone()[0]
