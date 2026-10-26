"""Verify W6 unique lesson coverage and synchronized status at 126/144."""

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
    def test_master_label_matches_126_unique_lesson_ids(self):
        line = next(line for line in PLAN.read_text(encoding="utf-8").splitlines() if line.startswith(MASTER_PREFIX))
        match = re.search(r"Recorded W6 full-lesson scope passes \(2026-10-22\): (\d+)/144 unique lessons \(([\d.]+)%\)", line)
        self.assertIsNotNone(match)
        lesson_ids = re.findall(r"`([a-z0-9-]+/[a-z0-9-]+)`", line)
        self.assertEqual(len(lesson_ids), 126)
        self.assertEqual(len(set(lesson_ids)), 126)
        self.assertEqual(int(match.group(1)), len(lesson_ids))
        self.assertEqual(match.group(2), "87.50")
        self.assertEqual(lesson_ids.count("multimodal/resolution-and-cost"), 1)

    def test_master_ids_resolve_in_tracker(self):
        line = next(line for line in PLAN.read_text(encoding="utf-8").splitlines() if line.startswith(MASTER_PREFIX))
        lesson_ids = set(re.findall(r"`([a-z0-9-]+/[a-z0-9-]+)`", line))
        tracker = TRACKER.read_text(encoding="utf-8")
        self.assertEqual(sorted(x for x in lesson_ids if f"`{x}`" not in tracker), [])

    def test_current_status_documents_agree(self):
        for path in (PLAN, SPEC, TRACKER, AUDIT):
            text = path.read_text(encoding="utf-8")
            self.assertIn("126/144", text, str(path))
            expected = "remaining 18 lessons" if path == PLAN else "18 节待审"
            self.assertIn(expected, text, str(path))

    def test_latest_progress_records_125_to_126(self):
        latest = next(line for line in reversed(PROGRESS.read_text(encoding="utf-8").splitlines()) if "ERR-309" in line)
        self.assertIn("125/144", latest)
        self.assertIn("126/144", latest)
        self.assertIn("还剩 18 节", latest)


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(UniqueW6Count)
    )
    print(f"providerCalls=0; externalNetworkCalls=0; tests={result.testsRun}; failures={len(result.failures) + len(result.errors)}")
    raise SystemExit(not result.wasSuccessful())
