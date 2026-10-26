#!/usr/bin/env python3
"""Offline whole-lesson checks for the agent-framework abstraction lesson."""

from __future__ import annotations

import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/agent-frameworks/02-abstraction-models.mdx"
SOURCE = LESSON.read_text(encoding="utf-8")


def complete_comparison() -> str:
    match = re.search(r"```python\n(.*?)\n```", SOURCE, flags=re.S)
    for candidate in re.findall(r"```python\n(.*?)\n```", SOURCE, flags=re.S):
        if "三个执行形状的离线 fixture" in candidate:
            return candidate
    raise AssertionError("complete three-abstraction Python example is missing")


def published_output() -> str:
    marker = "实跑输出：\n\n```text\n"
    start = SOURCE.index(marker) + len(marker)
    end = SOURCE.index("\n```", start)
    return SOURCE[start:end] + "\n"


class LessonBoundaryTests(unittest.TestCase):
    def test_linear_chain_claim_is_scoped(self):
        self.assertIn("RunnableSequence", SOURCE)
        self.assertNotIn("优点非常明确：**可预测、可测试、可在编译期检查。**", SOURCE)
        self.assertNotIn("缺点是它表达不了循环和分支", SOURCE)

    def test_graph_persistence_is_conditional(self):
        self.assertIn("checkpointer", SOURCE)
        self.assertNotIn("图的节点边界是可序列化的", SOURCE)
        self.assertNotIn("位置可序列化（断点恢复）", SOURCE)

    def test_scripted_fixture_does_not_claim_model_control(self):
        self.assertIn("脚本化策略替身", SOURCE)
        self.assertNotIn("走几步由「模型」决定", SOURCE)
        self.assertIn("不验证模型自主决策", SOURCE)

    def test_historical_token_comparisons_are_bounded(self):
        self.assertIn("506", SOURCE)
        self.assertIn("1,203", SOURCE)
        self.assertIn("5,000", SOURCE)
        self.assertIn("27,000", SOURCE)
        self.assertIn("无法独立复核", SOURCE)
        self.assertNotIn("链是最优选", SOURCE)

    def test_cost_claims_distinguish_call_count_from_spend(self):
        self.assertIn("max_turns", SOURCE)
        self.assertIn("token、时间和费用上限", SOURCE)
        self.assertNotIn("能给出一个准确的单次成本上界", SOURCE)
        self.assertNotIn("成本可控，前提是你主动加那个上限", SOURCE)

    def test_obsolete_appendix_is_removed(self):
        self.assertNotIn("## 附：schema 生成实验", SOURCE)
        self.assertNotIn("from langchain_anthropic import ChatAnthropic", SOURCE)

    def test_all_fences_are_balanced(self):
        self.assertEqual(len(re.findall(r"^```", SOURCE, re.M)) % 2, 0)

    @unittest.skipUnless("--execute" in sys.argv, "run the pinned LangGraph fixture with --execute")
    def test_comparison_stdout_matches(self):
        code = complete_comparison()
        with tempfile.TemporaryDirectory(prefix="abstraction-models-w6-") as directory:
            from importlib.metadata import version

            self.assertEqual(sys.version_info[:2], (3, 10))
            self.assertEqual(version("langgraph"), "1.2.14")
            self.assertEqual(version("langchain-core"), "1.6.12")
            script = Path(directory) / "comparison.py"
            script.write_text(code, encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(script)],
                check=True,
                capture_output=True,
                text=True,
                cwd=directory,
            )
        self.assertEqual(result.stdout, published_output())
        self.assertEqual(result.stderr, "")


if __name__ == "__main__":
    unittest.main(argv=[sys.argv[0]], verbosity=2)
