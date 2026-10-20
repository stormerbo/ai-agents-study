import os
import tempfile
import unittest

from task_ownership import StaleOwnership, TaskStore


class TaskOwnershipTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.store = TaskStore(os.path.join(self.temp_dir.name, "tasks.db"))

    def tearDown(self):
        self.store.close()
        self.temp_dir.cleanup()

    def test_new_task_is_claimed_with_first_epoch(self):
        self.store.enqueue("task-1")
        claim = self.store.claim_next("worker-a", now=100, lease_seconds=10)
        self.assertEqual((claim.task_id, claim.epoch, claim.lease_until), ("task-1", 1, 110))

    def test_reclaimed_task_increments_epoch_and_rejects_stale_checkpoint(self):
        self.store.enqueue("task-1")
        first = self.store.claim_next("worker-a", now=100, lease_seconds=10)
        second = self.store.claim_next("worker-b", now=110, lease_seconds=10)
        self.assertEqual(second.epoch, 2)
        with self.assertRaises(StaleOwnership):
            self.store.write_checkpoint(first, now=111, value="stale")
        self.store.write_checkpoint(second, now=111, value="current")
        self.assertEqual(self.store.read_checkpoint("task-1"), (1, "current"))

    def test_expired_owner_cannot_renew_its_lease(self):
        self.store.enqueue("task-1")
        claim = self.store.claim_next("worker-a", now=100, lease_seconds=10)
        with self.assertRaises(StaleOwnership):
            self.store.renew(claim, now=110, lease_seconds=10)

    def test_no_eligible_task_returns_none(self):
        self.assertIsNone(self.store.claim_next("worker-a", now=100, lease_seconds=10))


if __name__ == "__main__":
    unittest.main()
