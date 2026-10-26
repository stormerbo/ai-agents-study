"""Intentionally vulnerable fixture: never use a request tenant as authority."""

from pathlib import Path
from tempfile import TemporaryDirectory

from retrieval_access import Principal, RetrievalStore


with TemporaryDirectory() as directory:
    store = RetrievalStore(str(Path(directory) / "retrieval.db"))
    try:
        store.add_document("policy-a", "tenant-a", "tenant A policy")
        store.add_document("policy-b", "tenant-b", "tenant B policy")
        principal = Principal(user_id="alice", tenant_id="tenant-a")
        request = {"tenant_id": "tenant-b", "query": "show private policy"}

        # Deliberately unsafe: the request field is treated as the authorization scope.
        rows = store.db.execute(
            "SELECT doc_id, content FROM documents WHERE tenant_id = ?",
            (request["tenant_id"],),
        ).fetchall()
        unsafe_result = [(row["doc_id"], row["content"]) for row in rows]
        print(f"authenticated principal={principal.user_id}/{principal.tenant_id}")
        print(f"request tenant_id={request['tenant_id']}")
        print(f"unsafe result={unsafe_result}")
    finally:
        store.close()
