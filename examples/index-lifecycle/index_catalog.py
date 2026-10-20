"""SQLite teaching model for versioned retrieval-index lifecycle metadata."""

from __future__ import annotations

import hashlib
import sqlite3
from contextlib import contextmanager
from typing import Iterator


class StaleGeneration(RuntimeError):
    """The source catalog changed after this generation was built."""


class RevisionConflict(RuntimeError):
    """One source revision was reused with different content or operation."""


class IndexCatalog:
    def __init__(self, path: str):
        self.db = sqlite3.connect(path, isolation_level=None)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA foreign_keys = ON")
        self.db.executescript(
            """
            CREATE TABLE IF NOT EXISTS documents (
                doc_id TEXT PRIMARY KEY,
                source_revision INTEGER NOT NULL,
                doc_version INTEGER NOT NULL,
                content_hash TEXT NOT NULL,
                deleted INTEGER NOT NULL CHECK (deleted IN (0, 1))
            );
            CREATE TABLE IF NOT EXISTS generations (
                generation_id INTEGER PRIMARY KEY AUTOINCREMENT,
                status TEXT NOT NULL CHECK (status IN ('ready', 'active', 'retired', 'failed'))
            );
            CREATE TABLE IF NOT EXISTS generation_entries (
                generation_id INTEGER NOT NULL REFERENCES generations(generation_id),
                doc_id TEXT NOT NULL,
                doc_version INTEGER NOT NULL,
                content_hash TEXT NOT NULL,
                PRIMARY KEY (generation_id, doc_id)
            );
            CREATE TABLE IF NOT EXISTS active_index (
                singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
                generation_id INTEGER NOT NULL REFERENCES generations(generation_id)
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

    @staticmethod
    def _hash(content: str) -> str:
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def _apply_revision(self, doc_id: str, source_revision: int, content_hash: str, deleted: bool) -> int:
        if source_revision < 0:
            raise ValueError("source_revision must be non-negative")
        current = self.db.execute(
            "SELECT source_revision, doc_version, content_hash, deleted FROM documents WHERE doc_id = ?",
            (doc_id,),
        ).fetchone()
        if current is not None:
            if source_revision < current["source_revision"]:
                return current["doc_version"]
            if source_revision == current["source_revision"]:
                same_operation = current["deleted"] == int(deleted)
                same_content = current["content_hash"] == content_hash
                if same_operation and same_content:
                    return current["doc_version"]
                raise RevisionConflict(f"source revision reused for {doc_id}")
            if not deleted and not current["deleted"] and current["content_hash"] == content_hash:
                self.db.execute(
                    "UPDATE documents SET source_revision = ? WHERE doc_id = ?",
                    (source_revision, doc_id),
                )
                return current["doc_version"]
            version = current["doc_version"] + 1
        else:
            version = 1

        self.db.execute(
            """INSERT INTO documents(doc_id, source_revision, doc_version, content_hash, deleted)
               VALUES (?, ?, ?, ?, ?)
               ON CONFLICT(doc_id) DO UPDATE SET
                 source_revision = excluded.source_revision,
                 doc_version = excluded.doc_version,
                 content_hash = excluded.content_hash,
                 deleted = excluded.deleted""",
            (doc_id, source_revision, version, content_hash, int(deleted)),
        )
        return version

    def upsert_document(self, doc_id: str, source_revision: int, content: str) -> int:
        with self._write():
            return self._apply_revision(doc_id, source_revision, self._hash(content), deleted=False)

    def delete_document(self, doc_id: str, source_revision: int) -> int:
        with self._write():
            return self._apply_revision(doc_id, source_revision, "", deleted=True)

    def build_generation(self) -> int:
        with self._write():
            cursor = self.db.execute("INSERT INTO generations(status) VALUES ('ready')")
            generation_id = int(cursor.lastrowid)
            self.db.execute(
                """INSERT INTO generation_entries(generation_id, doc_id, doc_version, content_hash)
                   SELECT ?, doc_id, doc_version, content_hash
                   FROM documents WHERE deleted = 0 ORDER BY doc_id""",
                (generation_id,),
            )
            return generation_id

    def activate_generation(self, generation_id: int) -> None:
        with self._write():
            row = self.db.execute(
                "SELECT status FROM generations WHERE generation_id = ?", (generation_id,)
            ).fetchone()
            if row is None or row["status"] != "ready":
                raise ValueError("generation must exist and be ready")
            expected = [
                (r["doc_id"], r["doc_version"], r["content_hash"])
                for r in self.db.execute(
                    "SELECT doc_id, doc_version, content_hash FROM documents WHERE deleted = 0 ORDER BY doc_id"
                )
            ]
            built = [
                (r["doc_id"], r["doc_version"], r["content_hash"])
                for r in self.db.execute(
                    """SELECT doc_id, doc_version, content_hash FROM generation_entries
                       WHERE generation_id = ? ORDER BY doc_id""",
                    (generation_id,),
                )
            ]
            if built != expected:
                raise StaleGeneration(f"generation {generation_id} no longer matches source state")
            active = self.db.execute("SELECT generation_id FROM active_index WHERE singleton = 1").fetchone()
            if active is not None:
                self.db.execute(
                    "UPDATE generations SET status = 'retired' WHERE generation_id = ?",
                    (active["generation_id"],),
                )
            self.db.execute("UPDATE generations SET status = 'active' WHERE generation_id = ?", (generation_id,))
            self.db.execute(
                """INSERT INTO active_index(singleton, generation_id) VALUES (1, ?)
                   ON CONFLICT(singleton) DO UPDATE SET generation_id = excluded.generation_id""",
                (generation_id,),
            )

    def fail_generation(self, generation_id: int) -> None:
        with self._write():
            cursor = self.db.execute(
                "UPDATE generations SET status = 'failed' WHERE generation_id = ? AND status = 'ready'",
                (generation_id,),
            )
            if cursor.rowcount != 1:
                raise ValueError("only a ready generation can fail")

    def active_generation(self) -> int | None:
        row = self.db.execute("SELECT generation_id FROM active_index WHERE singleton = 1").fetchone()
        return int(row["generation_id"]) if row else None

    def generation_document_ids(self, generation_id: int) -> list[str]:
        rows = self.db.execute(
            "SELECT doc_id FROM generation_entries WHERE generation_id = ? ORDER BY doc_id",
            (generation_id,),
        )
        return [row["doc_id"] for row in rows]

    def active_document_ids(self) -> list[str]:
        """Exclude tombstoned and superseded entries even before a rebuild publishes."""
        rows = self.db.execute(
            """SELECT e.doc_id FROM active_index a
               JOIN generation_entries e ON e.generation_id = a.generation_id
               JOIN documents d ON d.doc_id = e.doc_id
               WHERE a.singleton = 1 AND d.deleted = 0
                 AND d.doc_version = e.doc_version
                 AND d.content_hash = e.content_hash
               ORDER BY e.doc_id"""
        )
        return [row["doc_id"] for row in rows]

    def close(self) -> None:
        self.db.close()
