"""Local reference store for monotonic key-status sequence floors.

This store is suitable for tests and a single verifier deployment only. It
cannot detect restoration of an old database snapshot or an administrator
rewriting the file; production deployments need rollback-resistant external
state shared by all verifier instances.
"""

from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path
from typing import Any


MAX_SEQUENCE = (1 << 63) - 1


class SequenceFloorConflict(RuntimeError):
    """The persisted sequence floor changed or cannot advance as requested."""


class SqliteSequenceFloorStore:
    """Persist one monotonic status sequence per environment/log/bundle scope."""

    def __init__(self, path: str | Path):
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS key_status_sequence_floor (
                    scope_sha256 TEXT PRIMARY KEY,
                    environment_id TEXT NOT NULL,
                    log_id TEXT NOT NULL,
                    trust_bundle_sha256 TEXT NOT NULL,
                    sequence INTEGER NOT NULL CHECK (sequence >= 0)
                )
                """
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._path, timeout=10, isolation_level=None)
        connection.execute("PRAGMA busy_timeout = 10000")
        return connection

    @staticmethod
    def _scope(scope: Any) -> tuple[str, str, str, str]:
        if not isinstance(scope, dict) or set(scope) != {
            "environment_id", "log_id", "trust_bundle_sha256"
        }:
            raise ValueError("sequence floor scope must contain exact environment/log/bundle fields")
        environment_id = scope["environment_id"]
        log_id = scope["log_id"]
        bundle_digest = scope["trust_bundle_sha256"]
        if not isinstance(environment_id, str) or not environment_id.strip() or "\x00" in environment_id:
            raise ValueError("environment_id must be a non-empty string")
        if not isinstance(log_id, str) or not log_id.strip() or "\x00" in log_id:
            raise ValueError("log_id must be a non-empty string")
        if (not isinstance(bundle_digest, str) or len(bundle_digest) != 64
                or any(character not in "0123456789abcdef" for character in bundle_digest)):
            raise ValueError("trust_bundle_sha256 must be lowercase SHA-256 hex")
        scope_bytes = "\x00".join((environment_id, log_id, bundle_digest)).encode("utf-8")
        scope_digest = hashlib.sha256(scope_bytes).hexdigest()
        return scope_digest, environment_id, log_id, bundle_digest

    @staticmethod
    def _sequence(value: Any, label: str) -> int:
        if type(value) is not int or not 0 <= value <= MAX_SEQUENCE:
            raise ValueError(f"{label} must be a SQLite-safe non-negative integer")
        return value

    def read(self, scope: Any) -> int:
        scope_digest, _, _, _ = self._scope(scope)
        with self._connect() as connection:
            row = connection.execute(
                "SELECT sequence FROM key_status_sequence_floor WHERE scope_sha256 = ?",
                (scope_digest,),
            ).fetchone()
        return 0 if row is None else row[0]

    def advance(self, scope: Any, *, expected: Any, new_sequence: Any) -> int:
        scope_digest, environment_id, log_id, bundle_digest = self._scope(scope)
        expected = self._sequence(expected, "expected")
        new_sequence = self._sequence(new_sequence, "new_sequence")
        if new_sequence <= expected:
            raise ValueError("new_sequence must be greater than expected")

        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT sequence FROM key_status_sequence_floor WHERE scope_sha256 = ?",
                (scope_digest,),
            ).fetchone()
            current = 0 if row is None else row[0]
            if current != expected:
                connection.rollback()
                raise SequenceFloorConflict("persisted sequence floor no longer matches expected")
            if row is None:
                connection.execute(
                    """INSERT INTO key_status_sequence_floor
                       (scope_sha256, environment_id, log_id, trust_bundle_sha256, sequence)
                       VALUES (?, ?, ?, ?, ?)""",
                    (scope_digest, environment_id, log_id, bundle_digest, new_sequence),
                )
            else:
                connection.execute(
                    "UPDATE key_status_sequence_floor SET sequence = ? WHERE scope_sha256 = ?",
                    (new_sequence, scope_digest),
                )
            connection.commit()
        return new_sequence
