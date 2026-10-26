"""Offline W6 checks for the Plan-Execute lesson and its executable fixture."""
from __future__ import annotations

import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/agent-paradigms/03-plan-and-execute.mdx"


def python_fences(text: str) -> list[str]:
    return re.findall(r"^```python\s*\n(.*?)^```\s*$", text, re.M | re.S)


class PlanExecuteLessonTests(unittest.TestCase):
    def test_lesson_distinguishes_static_dag_code_routing_and_model_replanning(self):
        text = LESSON.read_text()
        for phrase in (
            "依赖图可以无环，同时让路由函数按状态选择下一节点",
            "代码条件路由",
            "模型重规划",
            "完整性",
            "新观察",
            "原始逐次请求、响应、精确模型快照和完整评分记录没有归档",
            "不代表模型或框架行为",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)
        self.assertIn("https://reference.langchain.com/python/langgraph/graph/state/StateGraph/add_conditional_edges", text)

    def test_complete_offline_fixture_runs_and_matches_its_transcript(self):
        text = LESSON.read_text()
        blocks = python_fences(text)
        fixture = next((block for block in blocks if "def validate_plan" in block and "def main" in block), None)
        self.assertIsNotNone(fixture, "lesson must include a complete, runnable Plan-Execute fixture")
        completed = subprocess.run([sys.executable, "-c", fixture], check=True, text=True, capture_output=True)
        output_blocks = re.findall(r"^```text\s*\n(.*?)^```\s*$", text, re.M | re.S)
        self.assertIn(completed.stdout.rstrip(), [block.rstrip() for block in output_blocks])
        self.assertIn("providerCalls=0", completed.stdout)
        self.assertIn("externalNetworkCalls=0", completed.stdout)

    def test_plan_validator_rejects_whole_invalid_batch_before_any_dispatch(self):
        text = LESSON.read_text()
        blocks = python_fences(text)
        fixture = next((block for block in blocks if "def validate_plan" in block and "def main" in block), None)
        self.assertIsNotNone(fixture)
        self.assertIn("assert calls == before", fixture)
        self.assertIn("duplicate", fixture.lower())
        self.assertIn("cycle", fixture.lower())
        self.assertIn("unknown", fixture.lower())
        namespace = {"__name__": "lesson_fixture"}
        exec(compile(fixture, str(LESSON), "exec"), namespace)
        make_step = namespace["make_step"]
        invalid_plans = [
            [make_step("same", "北京", "明天"), make_step("same", "上海", "明天")],
            [{**make_step("bad-tool", "北京", "明天"), "tool": "delete_everything"}],
            [make_step("missing-parent", "北京", "明天", ["does-not-exist"])],
            [make_step("a", "北京", "明天", ["b"]), make_step("b", "上海", "明天", ["a"])],
        ]
        for invalid in invalid_plans:
            with self.subTest(plan=invalid):
                calls = []
                with self.assertRaises(ValueError):
                    namespace["execute_plan"](invalid, calls)
                self.assertEqual(calls, [], "invalid plan must be rejected before any dispatch")

    def test_unreproduced_historical_metrics_are_not_generalized(self):
        text = LESSON.read_text()
        self.assertIn("1,971", text)
        self.assertIn("3,087", text)
        self.assertIn("1,203", text)
        self.assertIn("506", text)
        self.assertIn("原始逐次请求、响应", text)
        self.assertNotIn("Plan-Execute 更省 token", text)
        self.assertNotIn("一定比 ReAct", text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
