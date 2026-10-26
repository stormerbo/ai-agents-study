import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from fault_models import FaultModel


class FaultBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.model = FaultModel(root / "app.sqlite", root / "receiver.sqlite")

    def tearDown(self):
        self.temp.cleanup()

    def test_crash_before_external_call_can_reconcile_then_deliver_once(self):
        self.model.enqueue_external_action("action-1", "notice")
        with self.assertRaisesRegex(RuntimeError, "before external call"):
            self.model.dispatch("action-1", "before_external_call")
        self.assertEqual(self.model.delivery_count("action-1"), 0)
        self.assertEqual(self.model.reconcile("action-1"), "sent")
        self.assertEqual(self.model.delivery_count("action-1"), 1)

    def test_crash_after_external_success_reconciles_without_duplicate(self):
        self.model.enqueue_external_action("action-2", "notice")
        with self.assertRaisesRegex(RuntimeError, "before local receipt"):
            self.model.dispatch("action-2", "after_external_call_before_receipt")
        self.assertEqual(self.model.delivery_count("action-2"), 1)
        with self.model.connect(self.model.app_db) as db:
            state = db.execute(
                "SELECT state FROM outbox WHERE operation_id=?", ("action-2",)
            ).fetchone()["state"]
        self.assertEqual(state, "dispatching")
        self.assertEqual(self.model.reconcile("action-2"), "reconciled_sent")
        self.assertEqual(self.model.delivery_count("action-2"), 1)

    def test_concurrent_submit_retries_return_one_durable_task(self):
        barrier = threading.Barrier(8)

        def submit(_):
            barrier.wait()
            return self.model.submit("tenant-a", "request-123", "same request")

        with ThreadPoolExecutor(max_workers=8) as pool:
            ids = list(pool.map(submit, range(8)))
        self.assertEqual(len(set(ids)), 1)
        self.assertEqual(self.model.claim("worker-a"), ids[0])
        self.assertIsNone(self.model.claim("worker-b"))
        # A later HTTP retry observes the original task, including after the wait timed out.
        self.assertEqual(self.model.submit("tenant-a", "request-123", "same request"), ids[0])
        # Idempotency is tenant-scoped; the same caller key in another tenant is distinct.
        other_tenant_task = self.model.submit("tenant-b", "request-123", "same request")
        self.assertNotEqual(other_tenant_task, ids[0])

    def test_same_tenant_idempotency_key_with_different_payload_is_rejected(self):
        original = self.model.submit("tenant-a", "request-456", "original")
        self.assertEqual(self.model.submit("tenant-a", "request-456", "original"), original)
        with self.assertRaisesRegex(ValueError, "different payload"):
            self.model.submit("tenant-a", "request-456", "changed")

    def test_external_operation_key_cannot_be_reused_with_different_payload(self):
        self.model.enqueue_external_action("action-3", "original")
        self.model.dispatch("action-3")
        with self.assertRaisesRegex(ValueError, "different payload"):
            self.model.enqueue_external_action("action-3", "changed")

    def test_receiver_rejects_existing_operation_key_with_different_payload(self):
        self.model.enqueue_external_action("action-4", "expected")
        with self.model.connect(self.model.receiver_db) as receiver:
            receiver.execute(
                "INSERT INTO deliveries(external_key,payload) VALUES(?,?)",
                ("action-4", "conflicting"),
            )
        with self.assertRaisesRegex(ValueError, "receiver idempotency key"):
            self.model.dispatch("action-4")
        self.assertEqual(self.model.delivery_count("action-4"), 1)

    def test_reconcile_does_not_confirm_receiver_key_with_different_payload(self):
        self.model.enqueue_external_action("action-5", "expected")
        with self.model.connect(self.model.receiver_db) as receiver:
            receiver.execute(
                "INSERT INTO deliveries(external_key,payload) VALUES(?,?)",
                ("action-5", "conflicting"),
            )
        with self.assertRaisesRegex(ValueError, "receiver idempotency key"):
            self.model.reconcile("action-5")
        with self.model.connect(self.model.app_db) as db:
            state = db.execute(
                "SELECT state FROM outbox WHERE operation_id=?", ("action-5",)
            ).fetchone()["state"]
        self.assertEqual(state, "queued")


if __name__ == "__main__":
    unittest.main(verbosity=2)
