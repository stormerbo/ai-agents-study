"""SQLite teaching model for authorization before retrieval text enters context."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass


MAX_CANDIDATES = 500


@dataclass(frozen=True)
class Principal:
    """Identity and tenant copied from a validated server authentication context."""

    user_id: str
    tenant_id: str


class RetrievalStore:
    def __init__(self, path: str):
        self.db = sqlite3.connect(path)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA foreign_keys = ON")
        self.db.executescript(
            """
            CREATE TABLE documents (
                doc_id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                content TEXT NOT NULL
            );
            CREATE TABLE grants (
                user_id TEXT NOT NULL,
                doc_id TEXT NOT NULL REFERENCES documents(doc_id),
                PRIMARY KEY (user_id, doc_id)
            );
            """
        )

    def add_document(self, doc_id: str, tenant_id: str, content: str) -> None:
        self.db.execute(
            "INSERT INTO documents(doc_id, tenant_id, content) VALUES (?, ?, ?)",
            (doc_id, tenant_id, content),
        )
        self.db.commit()

    def grant(self, user_id: str, doc_id: str) -> None:
        self.db.execute("INSERT INTO grants(user_id, doc_id) VALUES (?, ?)", (user_id, doc_id))
        self.db.commit()

    def revoke(self, user_id: str, doc_id: str) -> None:
        self.db.execute("DELETE FROM grants WHERE user_id = ? AND doc_id = ?", (user_id, doc_id))
        self.db.commit()

    def retrieve_for_context(self, principal: Principal, candidate_ids: list[str], limit: int = 5) -> list[dict[str, str]]:
        """Hydrate only authorized candidates; unauthorized text never reaches the caller."""
        if limit < 1:
            raise ValueError("limit must be positive")
        ordered_ids = list(dict.fromkeys(candidate_ids))
        if len(ordered_ids) > MAX_CANDIDATES:
            raise ValueError(f"candidate_ids may contain at most {MAX_CANDIDATES} unique ids")
        if not ordered_ids:
            return []
        placeholders = ",".join("?" for _ in ordered_ids)
        rows = self.db.execute(
            f"""SELECT d.doc_id, d.content FROM documents AS d
                JOIN grants AS g ON g.doc_id = d.doc_id
                WHERE d.doc_id IN ({placeholders})
                  AND d.tenant_id = ?
                  AND g.user_id = ?""",
            (*ordered_ids, principal.tenant_id, principal.user_id),
        ).fetchall()
        authorized = {row["doc_id"]: row["content"] for row in rows}
        return [
            {"doc_id": doc_id, "content": authorized[doc_id]}
            for doc_id in ordered_ids
            if doc_id in authorized
        ][:limit]

    def close(self) -> None:
        self.db.close()
