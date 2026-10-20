"""SQLite teaching model for per-request identity and tenant authorization."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass


@dataclass(frozen=True)
class Decision:
    allowed: bool
    reason: str
    body: str | None = None


class AccessStore:
    def __init__(self):
        self.db = sqlite3.connect(":memory:")
        self.db.executescript(
            """
            CREATE TABLE memberships (
                subject TEXT NOT NULL,
                tenant_id TEXT NOT NULL,
                active INTEGER NOT NULL,
                PRIMARY KEY(subject, tenant_id)
            );
            CREATE TABLE documents (
                document_id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                owner_subject TEXT NOT NULL,
                body TEXT NOT NULL
            );
            """
        )

    def add_member(self, subject: str, tenant_id: str, active: bool = True) -> None:
        self.db.execute(
            "INSERT INTO memberships VALUES (?, ?, ?)",
            (subject, tenant_id, int(active)),
        )

    def add_document(self, document_id: str, tenant_id: str, owner: str, body: str) -> None:
        self.db.execute(
            "INSERT INTO documents VALUES (?, ?, ?, ?)",
            (document_id, tenant_id, owner, body),
        )

    def access(
        self,
        *,
        authenticated_subject: str | None,
        trusted_tenant_id: str | None,
        document_id: str,
        action: str,
        request_tenant_id: str | None = None,
    ) -> Decision:
        """Use authenticated identity and stored membership; ignore client tenant."""
        if not authenticated_subject:
            return Decision(False, "unauthenticated")
        if action not in {"read", "update"}:
            return Decision(False, "unknown_action")
        if not trusted_tenant_id:
            return Decision(False, "missing_trusted_tenant")
        member = self.db.execute(
            "SELECT 1 FROM memberships WHERE subject = ? AND tenant_id = ? AND active = 1",
            (authenticated_subject, trusted_tenant_id),
        ).fetchone()
        if member is None:
            return Decision(False, "inactive_or_unknown_membership")
        row = self.db.execute(
            """SELECT body, owner_subject FROM documents
               WHERE document_id = ? AND tenant_id = ?""",
            (document_id, trusted_tenant_id),
        ).fetchone()
        if row is None:
            return Decision(False, "resource_outside_tenant")
        if action == "update" and row[1] != authenticated_subject:
            return Decision(False, "not_resource_owner")
        return Decision(True, "allowed", row[0])

    def close(self) -> None:
        self.db.close()
