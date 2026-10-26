"""Offline W6 checks for Reflection review boundaries and the runnable fixture."""
from __future__ import annotations

import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/agent-paradigms/04-reflection.mdx"


def fences(text: str, language: str) -> list[str]:
    return re.findall(rf"^```{re.escape(language)}\s*\n(.*?)^```\s*$", text, re.M | re.S)


class ReflectionLessonTests(unittest.TestCase):
    def test_lesson_distinguishes_review_from_independent_verification(self):
        text = LESSON.read_text()
        for phrase in (
            "Reflection（自我复核）",
            "Reflexion",
            "更多证据不等于独立验证",
            "独立程序校验",
            "逐次原始请求/响应",
            "合成的天气观测",
            "不证明真实模型会找到错误",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)
        self.assertIn("https://arxiv.org/abs/2303.11366", text)
        self.assertIn("https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents", text)

    def test_online_provider_example_is_replaced_by_complete_offline_fixture(self):
        text = LESSON.read_text()
        self.assertNotIn("ANTHROPIC_AUTH_TOKEN", text)
        self.assertNotIn("ANTHROPIC_BASE_URL", text)
        self.assertNotIn("urllib.request", text)
        blocks = fences(text, "python")
        fixture = next((block for block in blocks if "def parse_review" in block and "def main" in block), None)
        self.assertIsNotNone(fixture, "lesson needs a complete standalone offline review fixture")
        run = subprocess.run([sys.executable, "-c", fixture], check=True, text=True, capture_output=True)
        transcripts = fences(text, "text")
        self.assertIn(run.stdout.rstrip(), [item.rstrip() for item in transcripts])
        self.assertIn("providerCalls=0", run.stdout)
        self.assertIn("externalNetworkCalls=0", run.stdout)

    def test_nonterminal_or_malformed_review_never_becomes_deliverable(self):
        text = LESSON.read_text()
        fixture = next((block for block in fences(text, "python") if "def parse_review" in block and "def main" in block), None)
        self.assertIsNotNone(fixture)
        for reason in ('"truncated"', '"refused"', '"complete"'):
            self.assertIn(reason, fixture)
        self.assertIn("independent_validate", fixture)
        self.assertIn("assert candidate is None and not can_deliver", fixture)

    def test_old_accuracy_and_cost_summaries_stay_historical(self):
        text = LESSON.read_text()
        for item in ("1,203", "2,568", "2 次改坏", "3/3"):
            self.assertIn(item, text)
        self.assertIn("不能换算成错误率、证明修订等价", text)
        self.assertNotIn("113% 的附加成本就直接省掉", text)
        self.assertNotIn("线性任务上它是 2 倍", text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
