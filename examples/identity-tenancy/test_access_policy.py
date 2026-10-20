import unittest

from access_policy import AccessStore


class IdentityTenancyTests(unittest.TestCase):
    def setUp(self):
        self.store = AccessStore()
        self.store.add_member("alice", "tenant-a")
        self.store.add_member("bob", "tenant-b")
        self.store.add_member("bob", "tenant-a")
        self.store.add_member("carol", "tenant-a")
        self.store.add_member("disabled", "tenant-a", active=False)
        self.store.add_document("doc-a", "tenant-a", "alice", "tenant A secret")

    def tearDown(self):
        self.store.close()

    def test_authenticated_member_reads_same_tenant_document(self):
        decision = self.store.access(
            authenticated_subject="carol", trusted_tenant_id="tenant-a",
            document_id="doc-a", action="read"
        )
        self.assertEqual((decision.allowed, decision.body), (True, "tenant A secret"))

    def test_cross_tenant_identifier_does_not_reveal_document(self):
        decision = self.store.access(
            authenticated_subject="bob", trusted_tenant_id="tenant-b",
            document_id="doc-a", action="read"
        )
        self.assertEqual((decision.allowed, decision.body), (False, None))

    def test_request_tenant_cannot_override_authenticated_membership(self):
        decision = self.store.access(
            authenticated_subject="bob",
            trusted_tenant_id="tenant-b",
            document_id="doc-a",
            action="read",
            request_tenant_id="tenant-a",
        )
        self.assertEqual(decision.reason, "resource_outside_tenant")

    def test_update_requires_resource_owner(self):
        decision = self.store.access(
            authenticated_subject="carol", trusted_tenant_id="tenant-a",
            document_id="doc-a", action="update"
        )
        self.assertEqual(decision.reason, "not_resource_owner")

    def test_inactive_membership_is_denied(self):
        decision = self.store.access(
            authenticated_subject="disabled", trusted_tenant_id="tenant-a",
            document_id="doc-a", action="read"
        )
        self.assertEqual(decision.reason, "inactive_or_unknown_membership")

    def test_unknown_action_fails_closed(self):
        decision = self.store.access(
            authenticated_subject="alice", trusted_tenant_id="tenant-a",
            document_id="doc-a", action="delete"
        )
        self.assertEqual(decision.reason, "unknown_action")


if __name__ == "__main__":
    unittest.main()
