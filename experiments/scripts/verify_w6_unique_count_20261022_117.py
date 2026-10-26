"""Verify W6 unique lesson coverage and synchronized status at 117/144."""

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
    def test_master_label_matches_117_unique_lesson_ids(self):
        line = next(line for line in PLAN.read_text(encoding="utf-8").splitlines() if line.startswith(MASTER_PREFIX))
        match = re.search(
            r"Recorded W6 full-lesson scope passes \(2026-10-22\): "
            r"(\d+)/144 unique lessons \(([\d.]+)%\)",
            line,
        )
        self.assertIsNotNone(match)
        lesson_ids = re.findall(r"`([a-z0-9-]+/[a-z0-9-]+)`", line)
        self.assertEqual(len(lesson_ids), 117)
        self.assertEqual(len(set(lesson_ids)), 117)
        self.assertEqual(int(match.group(1)), len(lesson_ids))
        self.assertEqual(match.group(2), "81.25")
        self.assertEqual(lesson_ids.count("memory/when-to-recall"), 1)
        self.assertEqual(lesson_ids.count("memory/what-to-write"), 1)
        self.assertEqual(lesson_ids.count("memory/memory-cost-and-eval"), 1)
        self.assertEqual(lesson_ids.count("memory/forgetting-and-conflict"), 1)
        self.assertEqual(lesson_ids.count("mcp/why-protocol"), 1)

    def test_master_ids_resolve_in_tracker(self):
        line = next(line for line in PLAN.read_text(encoding="utf-8").splitlines() if line.startswith(MASTER_PREFIX))
        lesson_ids = set(re.findall(r"`([a-z0-9-]+/[a-z0-9-]+)`", line))
        tracker = TRACKER.read_text(encoding="utf-8")
        missing = sorted(lesson_id for lesson_id in lesson_ids if f"`{lesson_id}`" not in tracker)
        self.assertEqual(missing, [])

    def test_current_status_documents_agree(self):
        for path in (PLAN, SPEC, TRACKER, AUDIT):
            text = path.read_text(encoding="utf-8")
            self.assertIn("117/144", text, str(path))
            self.assertIn("27 节待审" if path != PLAN else "remaining 27 lessons", text, str(path))

    def test_latest_progress_records_113_to_117(self):
        lines = PROGRESS.read_text(encoding="utf-8").splitlines()
        latest = next(line for line in reversed(lines) if "`memory/when-to-recall` 新增 ERR-291" in line)
        self.assertIn("116/144", latest)
        self.assertIn("117/144", latest)
        self.assertIn("27 节待审", latest)


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(UniqueW6Count)
    )
    print(
        f"providerCalls=0; externalNetworkCalls=0; tests={result.testsRun}; "
        f"failures={len(result.failures) + len(result.errors)}"
    )
    raise SystemExit(not result.wasSuccessful())
