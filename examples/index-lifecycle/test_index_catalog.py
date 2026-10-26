import os
import sqlite3
import tempfile
import unittest

from index_catalog import IndexCatalog, StaleGeneration


class IndexCatalogTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.catalog = IndexCatalog(os.path.join(self.temp_dir.name, "catalog.db"))

    def tearDown(self):
        self.catalog.close()
        self.temp_dir.cleanup()

    def test_same_content_is_idempotent_and_changed_content_advances_version(self):
        self.assertEqual(self.catalog.upsert_document("policy", 1, "return window: 30 days"), 1)
        self.assertEqual(self.catalog.upsert_document("policy", 1, "return window: 30 days"), 1)
        self.assertEqual(self.catalog.upsert_document("policy", 2, "return window: 30 days"), 1)
        self.assertEqual(self.catalog.upsert_document("policy", 3, "return window: 14 days"), 2)

    def test_late_source_revision_cannot_restore_deleted_document(self):
        self.catalog.upsert_document("policy", 1, "return window: 30 days")
        self.catalog.delete_document("policy", 2)
        self.catalog.upsert_document("policy", 1, "return window: 30 days")
        generation = self.catalog.build_generation()
        self.assertEqual(self.catalog.generation_document_ids(generation), [])

    def test_deleted_document_is_absent_from_next_generation(self):
        self.catalog.upsert_document("policy", 1, "return window: 30 days")
        first = self.catalog.build_generation()
        self.catalog.activate_generation(first)
        self.catalog.delete_document("policy", 2)
        self.assertEqual(self.catalog.active_document_ids(), [])
        second = self.catalog.build_generation()
        self.assertEqual(self.catalog.generation_document_ids(second), [])

    def test_stale_generation_cannot_replace_current_index(self):
        self.catalog.upsert_document("policy", 1, "return window: 30 days")
        first = self.catalog.build_generation()
        self.catalog.activate_generation(first)
        stale = self.catalog.build_generation()
        self.catalog.upsert_document("policy", 2, "return window: 14 days")
        with self.assertRaises(StaleGeneration):
            self.catalog.activate_generation(stale)
        self.assertEqual(self.catalog.active_generation(), first)

    def test_failed_ready_candidate_leaves_previous_generation_active(self):
        self.catalog.upsert_document("policy", 1, "return window: 30 days")
        first = self.catalog.build_generation()
        self.catalog.activate_generation(first)
        failed = self.catalog.build_generation()
        self.catalog.fail_generation(failed)
        with self.assertRaisesRegex(ValueError, "generation must exist and be ready"):
            self.catalog.activate_generation(failed)
        self.assertEqual(self.catalog.active_generation(), first)


    def test_mid_build_write_failure_rolls_back_candidate_and_keeps_active_generation(self):
        self.catalog.upsert_document("policy-a", 1, "return window: 30 days")
        self.catalog.upsert_document("policy-b", 1, "return window: 14 days")
        active = self.catalog.build_generation()
        self.catalog.activate_generation(active)
        self.catalog.db.execute(
            """CREATE TRIGGER fail_second_candidate_entry
               BEFORE INSERT ON generation_entries
               WHEN NEW.doc_id = 'policy-b'
               BEGIN SELECT RAISE(ABORT, 'simulated build write failure'); END"""
        )

        with self.assertRaisesRegex(sqlite3.IntegrityError, "simulated build write failure"):
            self.catalog.build_generation()

        self.assertEqual(self.catalog.active_generation(), active)
        generations = self.catalog.db.execute(
            "SELECT generation_id, status FROM generations ORDER BY generation_id"
        ).fetchall()
        self.assertEqual([(row["generation_id"], row["status"]) for row in generations], [(active, "active")])
        entries = self.catalog.db.execute(
            "SELECT generation_id, doc_id FROM generation_entries ORDER BY generation_id, doc_id"
        ).fetchall()
        self.assertEqual(
            [(row["generation_id"], row["doc_id"]) for row in entries],
            [(active, "policy-a"), (active, "policy-b")],
        )


if __name__ == "__main__":
    unittest.main()
