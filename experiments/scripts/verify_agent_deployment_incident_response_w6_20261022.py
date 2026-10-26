"""Offline whole-lesson checks for agent-deployment/incident-response."""
from __future__ import annotations

import contextlib
import io
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/agent-deployment/03-incident-response.mdx"


class IncidentResponseReview(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = LESSON.read_text(encoding="utf-8")
        cls.fences = re.findall(r"^```([^\n]*)\n([\s\S]*?)^```\s*$", cls.text, re.M)
        cls.python_blocks = [body for language, body in cls.fences if language == "python"]

    def test_provider_specific_response_and_usage_contracts_are_explicit(self):
        for phrase in (
            "Anthropic Messages",
            "OpenAI Responses API",
            "DeepSeek",
            "cache_read_input_tokens",
            "cache_creation_input_tokens",
            "input_tokens_details.cached_tokens",
            "finish_reason",
        ):
            self.assertIn(phrase, self.text)
        self.assertNotIn("全部来自**响应体的 `usage` 对象**", self.text)
        self.assertIn("https://platform.claude.com/docs/en/api/messages", self.text)
        self.assertIn("https://developers.openai.com/api/reference/resources/responses/methods/create", self.text)
        self.assertIn("https://developers.openai.com/api/docs/guides/prompt-caching", self.text)

    def test_operational_thresholds_are_fixture_parameters_not_defaults(self):
        self.assertIn("合成演示阈值", self.text)
        self.assertIn("不是生产默认值", self.text)
        self.assertIn("时间窗", self.text)
        self.assertIn("分母", self.text)
        self.assertNotIn("一个实用的分级是：**P0", self.text)
        self.assertNotIn("一次花不到半小时", self.text)

    def test_degradation_drill_injects_a_failure_before_expectations(self):
        self.assertIn("故障注入", self.text)
        self.assertIn("恢复后再运行成功请求", self.text)
        self.assertNotIn("跑一个正常任务，确认熔断真的打开", self.text)

    def test_triage_rejects_missing_invalid_and_zero_denominator_metrics(self):
        self.assertEqual(len(self.python_blocks), 1)
        namespace = {"__name__": "review_fixture"}
        exec(compile(self.python_blocks[0], "incident-response-demo", "exec"), namespace)
        triage = namespace["triage"]
        with self.assertRaises(ValueError):
            triage({})
        bad = {"max_tokens_ratio": float("nan"), "token_p50": 0, "token_p99": 1,
               "fail_streak": -1, "deny_rate": 0, "cache_read_share": 0, "err_rate": 0}
        with self.assertRaises(ValueError):
            triage(bad)

    def test_python_demo_output_matches_its_published_block(self):
        self.assertEqual(len(self.python_blocks), 1)
        for index, (language, source) in enumerate(self.fences):
            if language != "python":
                continue
            next_language, expected = self.fences[index + 1]
            self.assertEqual(next_language, "text")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                exec(compile(source, f"incident-response-demo-{index}", "exec"), {"__name__": "__main__"})
            self.assertEqual(output.getvalue(), expected)


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(IncidentResponseReview)
    )
    print(f"providerCalls=0; tests={result.testsRun}; failures={len(result.failures) + len(result.errors)}")
    raise SystemExit(not result.wasSuccessful())
