import tempfile
import threading
import unittest
from pathlib import Path

from registry_sequence_floor import SequenceFloorConflict, SqliteSequenceFloorStore


class SequenceFloorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "sequence-floor.sqlite3"
        self.store = SqliteSequenceFloorStore(self.path)
        self.scope = {
            "environment_id": "production-eval",
            "log_id": "holdout-log-1",
            "trust_bundle_sha256": "a" * 64,
        }

    def tearDown(self):
        self.temp.cleanup()

    def test_empty_scope_starts_at_zero_and_can_advance_monotonically(self):
        self.assertEqual(self.store.read(self.scope), 0)
        self.assertEqual(self.store.advance(self.scope, expected=0, new_sequence=1), 1)
        self.assertEqual(self.store.advance(self.scope, expected=1, new_sequence=4), 4)
        self.assertEqual(self.store.read(self.scope), 4)

    def test_rejects_stale_expected_floor_and_non_increasing_sequence(self):
        self.store.advance(self.scope, expected=0, new_sequence=3)
        with self.assertRaises(SequenceFloorConflict):
            self.store.advance(self.scope, expected=0, new_sequence=5)
        with self.assertRaises(ValueError):
            self.store.advance(self.scope, expected=3, new_sequence=3)
        with self.assertRaises(ValueError):
            self.store.advance(self.scope, expected=3, new_sequence=2)

    def test_floors_are_isolated_by_log_and_bundle_scope(self):
        self.store.advance(self.scope, expected=0, new_sequence=7)
        other_log = {**self.scope, "log_id": "other-log"}
        other_bundle = {**self.scope, "trust_bundle_sha256": "b" * 64}
        self.assertEqual(self.store.read(other_log), 0)
        self.assertEqual(self.store.read(other_bundle), 0)

    def test_floor_survives_reopening_the_store(self):
        self.store.advance(self.scope, expected=0, new_sequence=9)
        reopened = SqliteSequenceFloorStore(self.path)
        self.assertEqual(reopened.read(self.scope), 9)

    def test_two_concurrent_advances_cannot_both_consume_the_same_floor(self):
        barrier = threading.Barrier(3)
        results = []
        lock = threading.Lock()

        def advance(sequence):
            barrier.wait()
            try:
                result = self.store.advance(self.scope, expected=0, new_sequence=sequence)
            except SequenceFloorConflict:
                result = "conflict"
            with lock:
                results.append(result)

        threads = [threading.Thread(target=advance, args=(sequence,)) for sequence in (1, 2)]
        for thread in threads:
            thread.start()
        barrier.wait()
        for thread in threads:
            thread.join()
        self.assertCountEqual(results, [1, "conflict"] if 1 in results else [2, "conflict"])
        self.assertIn(self.store.read(self.scope), {1, 2})

    def test_rejects_malformed_scope_and_boolean_sequence(self):
        with self.assertRaises(ValueError):
            self.store.read({**self.scope, "log_id": ""})
        with self.assertRaises(ValueError):
            self.store.advance(self.scope, expected=True, new_sequence=2)
        with self.assertRaises(ValueError):
            self.store.advance({**self.scope, "trust_bundle_sha256": "not-a-digest"},
                               expected=0, new_sequence=1)


if __name__ == "__main__":
    unittest.main()
