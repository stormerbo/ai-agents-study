"""Offline checks for the CoT/prefill lesson examples; never calls a provider."""
from __future__ import annotations

import os
import re
import sys
import types
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/prompt-engineering/04-chain-of-thought.mdx"
FENCES = [
    match.group(1)
    for match in re.finditer(r"^```[^\n]*\n([\s\S]*?)^```\s*$", LESSON.read_text(), re.M)
]
PREFILL_CODE = FENCES[4]
COT_CODE = FENCES[5]
TEXT_FENCES = [
    match.group(1)
    for match in re.finditer(
        r"^```text\\n([\\s\\S]*?)^```\\s*$", LESSON.read_text(), re.M
    )
]


class FakeMessages:
    response = None
    calls = 0

    def create(self, **_kwargs):
        type(self).calls += 1
        return type(self).response


class PromptCotReview(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prefill = {}
        exec(compile(PREFILL_CODE, str(LESSON), "exec"), cls.prefill)

        fake_sdk = types.SimpleNamespace(
            Anthropic=lambda **_kwargs: SimpleNamespace(messages=FakeMessages())
        )
        cls.cot = {"__name__": "lesson_fixture"}
        with patch.dict(sys.modules, {"anthropic": fake_sdk}), patch.dict(
            os.environ,
            {"ANTHROPIC_API_KEY": "fixture-only", "VERIFY_MODEL": "fixture-model"},
        ):
            exec(compile(COT_CODE, str(LESSON), "exec"), cls.cot)

    def setUp(self):
        FakeMessages.calls = 0
        FakeMessages.response = SimpleNamespace(
            stop_reason="end_turn",
            content=[SimpleNamespace(type="text", text="答案：6")],
            usage=SimpleNamespace(
                input_tokens=2,
                output_tokens=3,
                cache_creation_input_tokens=4,
                cache_read_input_tokens=5,
            ),
        )

    def test_python_fence_lines_fit_88_columns(self):
        for fence in (PREFILL_CODE, COT_CODE):
            self.assertLessEqual(max(map(len, fence.splitlines())), 88)

    def test_text_fence_lines_fit_88_columns(self):
        for fence in TEXT_FENCES:
            self.assertLessEqual(max(map(len, fence.splitlines())), 88)

    def test_both_python_fences_compile(self):
        compile(PREFILL_CODE, str(LESSON), "exec")
        compile(COT_CODE, str(LESSON), "exec")

    def test_prefill_parser_accepts_explicit_full_and_suffix_fixtures(self):
        full = self.prefill["parse_response"]('{"city":"北京","temp_c":20}', mode="full")
        suffix = self.prefill["parse_response"]("20}", mode="suffix")
        self.assertEqual(full, suffix)
        self.assertEqual(full, {"city": "北京", "temp_c": 20})

    def test_prefill_parser_fails_closed_on_wrong_schema_or_mode(self):
        with self.assertRaises(ValueError):
            self.prefill["parse_response"]('{"city":"北京","temp_c":null}', mode="full")
        with self.assertRaises(ValueError):
            self.prefill["parse_response"]('{"city":"北京","temp_c":NaN}', mode="full")
        with self.assertRaises(ValueError):
            self.prefill["parse_response"]("20}", mode="guess")

    def test_prefill_parser_rejects_duplicate_json_keys(self):
        with self.assertRaises(ValueError):
            self.prefill["parse_response"](
                '{"city":"北京","temp_c":20,"temp_c":999}', mode="full"
            )

    def test_answer_parser_is_numeric_not_substring_based(self):
        self.assertEqual(self.cot["extract_answer"]("答案：6"), 6)
        self.assertEqual(self.cot["extract_answer"]("答案：16"), 16)
        with self.assertRaises(ValueError):
            self.cot["extract_answer"]("答案：七天")

    def test_usage_is_returned_by_separate_fields(self):
        text, usage = self.cot["ask"]("fixture", "question")
        self.assertEqual(text, "答案：6")
        self.assertEqual(usage, {
            "input_tokens": 2,
            "output_tokens": 3,
            "cache_creation_input_tokens": 4,
            "cache_read_input_tokens": 5,
        })
        self.assertEqual(FakeMessages.calls, 1)

    def test_missing_required_usage_fails_closed(self):
        FakeMessages.response.usage = SimpleNamespace(output_tokens=3)
        with self.assertRaisesRegex(RuntimeError, "usage.input_tokens"):
            self.cot["ask"]("fixture", "question")

    def test_invalid_cache_usage_fails_closed(self):
        FakeMessages.response.usage.cache_read_input_tokens = -1
        with self.assertRaisesRegex(RuntimeError, "usage.cache_read_input_tokens"):
            self.cot["ask"]("fixture", "question")

    def test_non_end_turn_fails_closed(self):
        FakeMessages.response.stop_reason = "max_tokens"
        with self.assertRaisesRegex(RuntimeError, "未完整结束"):
            self.cot["ask"]("fixture", "question")

    def test_empty_text_fails_closed(self):
        FakeMessages.response.content = []
        with self.assertRaisesRegex(RuntimeError, "没有可评分"):
            self.cot["ask"]("fixture", "question")


if __name__ == "__main__":
    unittest.main(verbosity=2)
