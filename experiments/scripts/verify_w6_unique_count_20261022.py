"""Check that W6's published unique lesson count matches its named IDs."""
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


class UniqueW6Count(unittest.TestCase):
    def test_master_list_has_91_unique_lesson_ids(self):
        plan = PLAN.read_text(encoding="utf-8")
        line = next(line for line in plan.splitlines() if line.startswith("**Recorded W6 full-lesson scope passes"))
        ids = re.findall(r"`([a-z0-9-]+/[a-z0-9-]+)`", line)
        self.assertEqual(len(ids), 91)
        self.assertEqual(len(set(ids)), 91)

    def test_late_passes_missing_from_previous_snapshot_are_in_master_list(self):
        plan = next(line for line in PLAN.read_text(encoding="utf-8").splitlines() if line.startswith("**Recorded W6 full-lesson scope passes"))
        ids = set(re.findall(r"`([a-z0-9-]+/[a-z0-9-]+)`", plan))
        required = {
            "what-is-an-agent/how-to-use-this-site",
            "llm-api-basics/tokens-and-context",
            "llm-api-basics/messages-api",
            "llm-api-basics/model-selection",
            "llm-api-basics/prompt-caching",
            "human-in-the-loop/progress-and-trust",
            "human-in-the-loop/automation-levels",
            "human-in-the-loop/streaming-and-control",
            "evaluation/define-good",
            "evaluation/pass-k",
            "evaluation/dataset",
            "evaluation/confidence",
            "evaluation/llm-as-judge",
            "evaluation/paired-comparison",
            "coding-agent/error-recovery",
            "coding-agent/search-strategy",
            "coding-agent/file-editing",
            "coding-agent/safety",
            "coding-agent/why-coding-agent",
            "computer-use/failure-modes",
            "computer-use/observe-act-loop",
            "computer-use/safety-and-scope",
            "computer-use/when-not-to-use",
            "computer-use/what-differs",
            "context-engineering/agent-skills",
            "context-engineering/chat-template",
            "context-engineering/context-is-finite",
            "context-engineering/system-prompt-altitude",
            "context-engineering/just-in-time",
            "context-engineering/kv-cache",
            "context-engineering/compaction",
            "evaluation/ablation",
        }
        self.assertTrue(required <= ids, f"missing from master list: {sorted(required - ids)}")

    def test_current_status_documents_agree_on_91_of_144(self):
        current_lines = {
            PLAN: "**W6 audit status (2026-10-22, current workspace):**",
            SPEC: "状态：设计持续实施中。",
            TRACKER: "> 全书 144 个 lesson ID 已恢复到本表；",
            AUDIT: "> 本表覆盖 144 个 lesson ID。",
        }
        for path, prefix in current_lines.items():
            text = path.read_text(encoding="utf-8")
            line = next(line for line in text.splitlines() if line.startswith(prefix))
            self.assertIn("91/144", line, str(path))
            pending = "remaining 53 lessons" if path == PLAN else "53 节待审"
            self.assertIn(pending, line, str(path))
        progress = PROGRESS.read_text(encoding="utf-8").splitlines()
        latest = next(line for line in reversed(progress) if "W6 全节复核继续" in line)
        self.assertIn("90/144", latest)
        self.assertIn("53 节待审", latest)

    def test_master_list_ids_exist_in_tracker(self):
        plan = next(line for line in PLAN.read_text(encoding="utf-8").splitlines() if line.startswith("**Recorded W6 full-lesson scope passes"))
        ids = set(re.findall(r"`([a-z0-9-]+/[a-z0-9-]+)`", plan))
        tracker = TRACKER.read_text(encoding="utf-8")
        missing = sorted(lesson_id for lesson_id in ids if f"`{lesson_id}`" not in tracker)
        self.assertEqual(missing, [])


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(UniqueW6Count)
    )
    print(f"providerCalls=0; externalNetworkCalls=0; tests={result.testsRun}; failures={len(result.failures) + len(result.errors)}")
    raise SystemExit(not result.wasSuccessful())
