"""Verify W6 unique lesson coverage and synchronized progress documents."""
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
    def test_master_label_matches_97_unique_lesson_ids(self):
        line = next(line for line in PLAN.read_text(encoding="utf-8").splitlines() if line.startswith(MASTER_PREFIX))
        match = re.search(r"\*\*Recorded W6 full-lesson scope passes \(2026-10-22\): (\d+)/144 unique lessons \(([\d.]+)%\)\*\*", line)
        self.assertIsNotNone(match, "master W6 line must publish count and percentage")
        lesson_ids = re.findall(r"`([a-z0-9-]+/[a-z0-9-]+)`", line)
        self.assertEqual(len(lesson_ids), 97)
        self.assertEqual(len(set(lesson_ids)), 97)
        self.assertEqual(int(match.group(1)), len(lesson_ids))
        self.assertEqual(match.group(2), "67.36")
        self.assertIn("cost-and-latency/concurrency-and-backpressure", lesson_ids)
        self.assertIn("cost-and-latency/budget-guardrails", lesson_ids)
        self.assertIn("cost-and-latency/caching", lesson_ids)

    def test_master_ids_resolve_in_tracker(self):
        line = next(line for line in PLAN.read_text(encoding="utf-8").splitlines() if line.startswith(MASTER_PREFIX))
        lesson_ids = set(re.findall(r"`([a-z0-9-]+/[a-z0-9-]+)`", line))
        tracker = TRACKER.read_text(encoding="utf-8")
        missing = sorted(lesson_id for lesson_id in lesson_ids if f"`{lesson_id}`" not in tracker)
        self.assertEqual(missing, [])

    def test_current_count_summaries_agree(self):
        current_lines = {
            PLAN: "**W6 audit status (2026-10-22, current workspace):**",
            SPEC: "状态：设计持续实施中。",
            TRACKER: "> 全书 144 个 lesson ID 已恢复到本表；",
            AUDIT: "> 本表覆盖 144 个 lesson ID。",
        }
        for path, prefix in current_lines.items():
            line = next(line for line in path.read_text(encoding="utf-8").splitlines() if line.startswith(prefix))
            self.assertIn("97/144", line, str(path))
            self.assertIn("47 节待审" if path != PLAN else "remaining 47 lessons", line, str(path))

    def test_latest_progress_records_96_to_97(self):
        lines = PROGRESS.read_text(encoding="utf-8").splitlines()
        latest = next(line for line in reversed(lines) if "W6 全节复核继续" in line)
        self.assertIn("96/144", latest)
        self.assertIn("97/144", latest)
        self.assertIn("47 节待审", latest)


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(UniqueW6Count)
    )
    print(f"providerCalls=0; externalNetworkCalls=0; tests={result.testsRun}; failures={len(result.failures) + len(result.errors)}")
    raise SystemExit(not result.wasSuccessful())
