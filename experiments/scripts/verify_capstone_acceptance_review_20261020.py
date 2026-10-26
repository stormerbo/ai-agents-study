from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "examples/capstone-acceptance"))
from acceptance import REQUIRED_GATES, REQUIRED_KINDS  # noqa: E402

LESSON = ROOT / "src/content/chapters/capstone/06-acceptance.mdx"
TEXT = LESSON.read_text(encoding="utf-8")


class CapstoneAcceptanceReview(unittest.TestCase):
    def test_markdown_lists_each_required_gate_exactly_once(self) -> None:
        table = TEXT.split("| ID | 场景 | 通过条件 |", 1)[1].split("\n\n", 1)[0]
        ids = re.findall(r"\| `([^`]+)` \|", table)
        self.assertEqual(len(ids), 19)
        self.assertEqual(len(set(ids)), len(ids))
        self.assertEqual(set(ids), REQUIRED_GATES)
        self.assertEqual(set(REQUIRED_KINDS), REQUIRED_GATES)

    def test_decisions_and_matrix_states_match_implementation(self) -> None:
        for decision in (
            "ready-for-human-acceptance", "blocked", "incomplete",
            "insufficient-evidence", "invalid-report",
        ):
            self.assertIn(f"`{decision}`", TEXT)
        for state in ("missing", "failed", "unverified", "passed", "invalid-report", "not-evaluated"):
            self.assertIn(f"`{state}`", TEXT)
        self.assertIn("19 项矩阵", TEXT)
        self.assertNotIn("18 项矩阵", TEXT)

    def test_human_and_authentication_boundaries_are_explicit(self) -> None:
        for phrase in (
            "authenticated: false", "外部 registry 真实",
            "不会替团队批准上线", "fixture 不能满足正式 holdout",
        ):
            self.assertIn(phrase, TEXT)

    def test_live_smoke_report_is_described_as_incomplete_and_not_success(self) -> None:
        self.assertIn("实跑状态（2026-10-20）：未通过", TEXT)
        self.assertIn("registry 仍为 `incomplete`", TEXT)
        self.assertIn("最终输出没有生成", TEXT)
        self.assertIn("不证明 `live_model_normal` 成功", TEXT)


if __name__ == "__main__":
    unittest.main()
