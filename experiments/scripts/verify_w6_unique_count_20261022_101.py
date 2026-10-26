"""Verify the W6 unique-lesson counter after evaluation/eval-env (101/144)."""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PLAN = ROOT / "docs/superpowers/plans/2026-10-19-curriculum-reliability.md"
SPEC = ROOT / "docs/superpowers/specs/2026-10-19-curriculum-reliability-design.md"
TRACKER = ROOT / "docs/CURRICULUM-REVIEW-TRACKER.md"
AUDIT = ROOT / "docs/CURRICULUM-ACCURACY-AUDIT-2026-10-20.md"
PROGRESS = ROOT / "docs/PROGRESS.md"
MASTER_PREFIX = "**Recorded W6 full-lesson scope passes"


class UniqueW6Count(unittest.TestCase):
    def test_master_label_matches_101_unique_lesson_ids(self):
        line = next(
            line for line in PLAN.read_text(encoding="utf-8").splitlines()
            if line.startswith(MASTER_PREFIX)
        )
        match = re.search(
            r"Recorded W6 full-lesson scope passes \(2026-10-22\): "
            r"(\d+)/144 unique lessons \(([\d.]+)%\)",
            line,
        )
        self.assertIsNotNone(match, "master W6 line must publish count and percentage")
        lesson_ids = re.findall(r"`([a-z0-9-]+/[a-z0-9-]+)`", line)
        self.assertEqual(len(lesson_ids), 101)
        self.assertEqual(len(set(lesson_ids)), 101)
        self.assertEqual(int(match.group(1)), len(lesson_ids))
        self.assertEqual(match.group(2), "70.14")
        self.assertEqual(lesson_ids.count("evaluation/eval-env"), 1)

    def test_master_ids_resolve_in_tracker(self):
        line = next(
            line for line in PLAN.read_text(encoding="utf-8").splitlines()
            if line.startswith(MASTER_PREFIX)
        )
        lesson_ids = set(re.findall(r"`([a-z0-9-]+/[a-z0-9-]+)`", line))
        tracker = TRACKER.read_text(encoding="utf-8")
        missing = sorted(lesson_id for lesson_id in lesson_ids if f"`{lesson_id}`" not in tracker)
        self.assertEqual(missing, [])

    def test_current_status_documents_agree(self):
        checks = [
            (PLAN, "101/144", "remaining 43 lessons"),
            (SPEC, "101/144", "43 节待审"),
            (TRACKER, "101/144", "43 节待审"),
            (AUDIT, "101/144", "43 节待审"),
        ]
        for path, count, remaining in checks:
            text = path.read_text(encoding="utf-8")
            self.assertIn(count, text, str(path))
            self.assertIn(remaining, text, str(path))

    def test_latest_progress_records_100_to_101(self):
        lines = PROGRESS.read_text(encoding="utf-8").splitlines()
        latest = next(
            line for line in reversed(lines)
            if "`evaluation/eval-env` 新增 ERR-257" in line
        )
        self.assertIn("100/144", latest)
        self.assertIn("101/144", latest)
        self.assertIn("43 节待审", latest)


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(UniqueW6Count)
    )
    print(
        f"providerCalls=0; externalNetworkCalls=0; tests={result.testsRun}; "
        f"failures={len(result.failures) + len(result.errors)}"
    )
    raise SystemExit(not result.wasSuccessful())
