"""SQLite teaching model for leased task ownership and fencing epochs."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Iterator


class StaleOwnership(RuntimeError):
    """The worker no longer owns the current task epoch or lease."""


@dataclass(frozen=True)
class Claim:
    task_id: str
    owner: str
    epoch: int
    lease_until: int


class TaskStore:
    def __init__(self, path: str):
        self.db = sqlite3.connect(path, isolation_level=None)
        self.db.row_factory = sqlite3.Row
        self.db.executescript(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                task_id TEXT PRIMARY KEY,
                status TEXT NOT NULL CHECK (status IN ('queued', 'running')),
                created_at INTEGER NOT NULL,
                owner TEXT,
                epoch INTEGER NOT NULL DEFAULT 0,
                lease_until INTEGER,
                checkpoint_seq INTEGER NOT NULL DEFAULT 0,
                checkpoint TEXT NOT NULL DEFAULT ''
            );
            """
        )

    @contextmanager
    def _write(self) -> Iterator[None]:
        self.db.execute("BEGIN IMMEDIATE")
        try:
            yield
        except BaseException:
            self.db.rollback()
            raise
        else:
            self.db.commit()

    def enqueue(self, task_id: str, created_at: int = 0) -> None:
        self.db.execute(
            "INSERT INTO tasks(task_id, status, created_at) VALUES (?, 'queued', ?)",
            (task_id, created_at),
        )

    def claim_next(self, owner: str, now: int, lease_seconds: int) -> Claim | None:
        if not owner or lease_seconds <= 0:
            raise ValueError("owner must be non-empty and lease_seconds must be positive")
        with self._write():
            row = self.db.execute(
                """SELECT task_id, epoch FROM tasks
                   WHERE status = 'queued' OR (status = 'running' AND lease_until <= ?)
                   ORDER BY created_at, task_id LIMIT 1""",
                (now,),
            ).fetchone()
            if row is None:
                return None
            epoch = int(row["epoch"]) + 1
            lease_until = now + lease_seconds
            self.db.execute(
                """UPDATE tasks SET status = 'running', owner = ?, epoch = ?, lease_until = ?
                   WHERE task_id = ?""",
                (owner, epoch, lease_until, row["task_id"]),
            )
            return Claim(str(row["task_id"]), owner, epoch, lease_until)

    def renew(self, claim: Claim, now: int, lease_seconds: int) -> Claim:
        if lease_seconds <= 0:
            raise ValueError("lease_seconds must be positive")
        with self._write():
            cursor = self.db.execute(
                """UPDATE tasks SET lease_until = ?
                   WHERE task_id = ? AND status = 'running' AND owner = ?
                     AND epoch = ? AND lease_until > ?""",
                (now + lease_seconds, claim.task_id, claim.owner, claim.epoch, now),
            )
            if cursor.rowcount != 1:
                raise StaleOwnership(f"worker {claim.owner} no longer owns {claim.task_id}")
            return Claim(claim.task_id, claim.owner, claim.epoch, now + lease_seconds)

    def write_checkpoint(self, claim: Claim, now: int, value: str) -> int:
        with self._write():
            cursor = self.db.execute(
                """UPDATE tasks SET checkpoint = ?, checkpoint_seq = checkpoint_seq + 1
                   WHERE task_id = ? AND status = 'running' AND owner = ?
                     AND epoch = ? AND lease_until > ?""",
                (value, claim.task_id, claim.owner, claim.epoch, now),
            )
            if cursor.rowcount != 1:
                raise StaleOwnership(f"worker {claim.owner} no longer owns {claim.task_id}")
            row = self.db.execute(
                "SELECT checkpoint_seq FROM tasks WHERE task_id = ?", (claim.task_id,)
            ).fetchone()
            return int(row["checkpoint_seq"])

    def read_checkpoint(self, task_id: str) -> tuple[int, str]:
        row = self.db.execute(
            "SELECT checkpoint_seq, checkpoint FROM tasks WHERE task_id = ?", (task_id,)
        ).fetchone()
        if row is None:
            raise KeyError(task_id)
        return int(row["checkpoint_seq"]), str(row["checkpoint"])

    def close(self) -> None:
        self.db.close()
