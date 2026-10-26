"""Offline checks for identity/tenant authorization claims and teaching fixture."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/agent-security/06-identity-and-tenancy.mdx"
CODE_DIR = ROOT / "examples/identity-tenancy"


def main() -> None:
    text = LESSON.read_text(encoding="utf-8")
    checks = 0

    def require(condition: bool, message: str) -> None:
        nonlocal checks
        if not condition:
            raise AssertionError(message)
        checks += 1

    for phrase in (
        "FOR SELECT TO app_runtime",
        "FOR INSERT TO app_runtime",
        "FOR UPDATE TO app_runtime",
        "USING (tenant_id = current_setting('app.tenant_id', true))",
        "WITH CHECK (tenant_id = current_setting('app.tenant_id', true))",
        "set_config('app.tenant_id', $1, true)",
        "不能证明这些部署层属性",
        "不能把可由会话设置的 tenant 值当成独立身份边界",
    ):
        require(phrase in text, f"lesson missing boundary: {phrase}")

    sys.path.insert(0, str(CODE_DIR))
    from access_policy import AccessStore

    store = AccessStore()
    try:
        store.add_member("alice", "tenant-a")
        store.add_member("bob", "tenant-b")
        store.add_member("carol", "tenant-a")
        store.add_document("doc-a", "tenant-a", "alice", "secret-a")
        read = store.access(
            authenticated_subject="carol", trusted_tenant_id="tenant-a",
            document_id="doc-a", action="read"
        )
        require(read.allowed and read.body == "secret-a", "authorized read failed")
        cross_tenant = store.access(
            authenticated_subject="bob", trusted_tenant_id="tenant-b",
            document_id="doc-a", action="read"
        )
        require(not cross_tenant.allowed and cross_tenant.body is None, "cross-tenant read leaked")
        denied_update = store.access(
            authenticated_subject="carol", trusted_tenant_id="tenant-a",
            document_id="doc-a", action="update"
        )
        require(not denied_update.allowed and denied_update.body is None, "denied update leaked body")
        allowed_update = store.access(
            authenticated_subject="alice", trusted_tenant_id="tenant-a",
            document_id="doc-a", action="update"
        )
        require(allowed_update.allowed and allowed_update.body is None, "update decision returned body")
    finally:
        store.close()

    print(json.dumps({"assertions": checks, "providerCalls": 0, "externalNetworkCalls": 0}))


if __name__ == "__main__":
    main()
