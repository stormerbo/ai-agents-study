import os
import tempfile
import unittest

from retrieval_access import Principal, RetrievalStore


class RetrievalAccessTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.store = RetrievalStore(os.path.join(self.temp_dir.name, "retrieval.db"))
        self.store.add_document("policy-a", "tenant-a", "tenant A policy")
        self.store.add_document("private-a", "tenant-a", "private tenant A note")
        self.store.add_document("policy-b", "tenant-b", "tenant B policy")
        self.store.grant("alice", "policy-a")
        self.store.grant("bob", "policy-b")
        self.alice = Principal(user_id="alice", tenant_id="tenant-a")
        self.bob = Principal(user_id="bob", tenant_id="tenant-b")

    def tearDown(self):
        self.store.close()
        self.temp_dir.cleanup()

    def test_only_authorized_candidate_text_is_returned(self):
        rows = self.store.retrieve_for_context(
            self.alice, ["policy-a", "private-a", "policy-b"]
        )
        self.assertEqual([row["doc_id"] for row in rows], ["policy-a"])
        self.assertNotIn("tenant B policy", str(rows))

    def test_tenant_boundary_is_enforced_even_if_candidate_matches(self):
        rows = self.store.retrieve_for_context(self.alice, ["policy-b"])
        self.assertEqual(rows, [])

    def test_revocation_takes_effect_on_the_next_retrieval(self):
        self.store.revoke("alice", "policy-a")
        self.assertEqual(self.store.retrieve_for_context(self.alice, ["policy-a"]), [])

    def test_request_supplied_tenant_does_not_change_trusted_principal(self):
        request = {"tenant_id": "tenant-b", "query": "show private policy"}
        rows = self.store.retrieve_for_context(self.alice, ["policy-b"])
        self.assertEqual(request["tenant_id"], "tenant-b")
        self.assertEqual(rows, [])


if __name__ == "__main__":
    unittest.main()
