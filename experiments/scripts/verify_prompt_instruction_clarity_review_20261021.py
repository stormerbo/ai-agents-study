"""Offline verifier for the instruction-clarity lesson; never calls a provider."""
from __future__ import annotations

import contextlib
import io
import json
import os
import re
import sys
import tempfile
import types
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/prompt-engineering/01-instruction-clarity.mdx"
FENCES = [
    match.group(1)
    for match in re.finditer(r"^```[^\n]*\n([\s\S]*?)^```\s*$", LESSON.read_text(), re.M)
]
CODE = FENCES[0]


class FakeMessages:
    calls = 0

    def create(self, **_kwargs):
        type(self).calls += 1
        return SimpleNamespace(
            stop_reason="end_turn",
            model="fixture-model-snapshot",
            content=[SimpleNamespace(type="text", text=f"结果 {type(self).calls}")],
            usage=SimpleNamespace(
                input_tokens=2,
                output_tokens=3,
                cache_creation_input_tokens=0,
                cache_read_input_tokens=0,
            ),
        )


class InstructionClarityReview(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = {"__name__": "lesson_fixture"}
        fake_sdk = types.SimpleNamespace(
            Anthropic=lambda: SimpleNamespace(messages=FakeMessages())
        )
        with patch.dict(
            sys.modules,
            {"anthropic": fake_sdk},
        ), patch.dict(os.environ, {"ANTHROPIC_MODEL": "fixture-model"}):
            exec(compile(CODE, str(LESSON), "exec"), cls.ns)

    def test_anthropic_system_message_support_is_model_scoped(self):
        lesson = LESSON.read_text(encoding="utf-8")
        meta = (ROOT / "src/content/chapters/prompt-engineering/meta.ts").read_text(
            encoding="utf-8"
        )
        resources = (ROOT / "src/content/curriculum/resources.ts").read_text(
            encoding="utf-8"
        )
        self.assertIn("Claude Fable 5 与 Opus 4.8", lesson)
        self.assertIn("其他模型不一定支持", lesson)
        self.assertIn("anthropic-working-with-messages", meta)
        self.assertIn("https://platform.claude.com/docs/en/build-with-claude/working-with-messages", resources)

    def test_python_fence_compiles(self):
        compile(CODE, str(LESSON), "exec")
        self.assertLessEqual(max(map(len, CODE.splitlines())), 88)

    def test_chinese_count_and_lexical_proxies_are_explicit(self):
        self.assertEqual(self.ns["chinese_chars"]("AI 你好 123"), 2)
        self.assertEqual(self.ns["FORBIDDEN_TERMS"].findall("成本不在范围内"), ["成本"])
        self.assertTrue(self.ns["DIGITS"].search("含数字 12"))
        self.assertFalse(self.ns["DIGITS"].search("没有数字"))

    def test_extract_text_requires_complete_nonempty_response(self):
        good = SimpleNamespace(
            stop_reason="end_turn",
            content=[SimpleNamespace(type="text", text="答案")],
        )
        self.assertEqual(self.ns["extract_text"](good), "答案")
        for response in (
            SimpleNamespace(stop_reason="max_tokens", content=good.content),
            SimpleNamespace(stop_reason="end_turn", content=[]),
        ):
            with self.assertRaises(RuntimeError):
                self.ns["extract_text"](response)

    def test_usage_requires_core_counts_and_keeps_cache_fields_separate(self):
        valid = SimpleNamespace(
            usage=SimpleNamespace(
                input_tokens=2,
                output_tokens=3,
                cache_creation_input_tokens=5,
                cache_read_input_tokens=7,
            )
        )
        self.assertEqual(
            self.ns["read_usage"](valid),
            {
                "input_tokens": 2,
                "output_tokens": 3,
                "cache_creation_input_tokens": 5,
                "cache_read_input_tokens": 7,
            },
        )
        invalid = SimpleNamespace(
            usage=SimpleNamespace(input_tokens=None, output_tokens=3)
        )
        with self.assertRaises(RuntimeError):
            self.ns["read_usage"](invalid)
        nullable = SimpleNamespace(
            usage=SimpleNamespace(
                input_tokens=2,
                output_tokens=3,
                cache_creation_input_tokens=None,
                cache_read_input_tokens=None,
            )
        )
        self.assertEqual(
            self.ns["read_usage"](nullable)["cache_creation_input_tokens"], 0
        )
        self.assertEqual(
            self.ns["read_usage"](nullable)["cache_read_input_tokens"], 0
        )

    def test_usage_rejects_boolean_and_malformed_cache_counts(self):
        for value in (False, True, 1.5, "0", -1):
            response = SimpleNamespace(
                usage=SimpleNamespace(
                    input_tokens=2,
                    output_tokens=3,
                    cache_creation_input_tokens=value,
                    cache_read_input_tokens=0,
                )
            )
            with self.subTest(value=value), self.assertRaises(RuntimeError):
                self.ns["read_usage"](response)

    def test_main_archives_refusal_truncation_and_missing_text(self):
        original = FakeMessages.create

        def varied(client, **kwargs):
            response = original(client, **kwargs)
            if FakeMessages.calls == 1:
                response.stop_reason = "max_tokens"
            elif FakeMessages.calls == 2:
                response.stop_reason = "refusal"
            elif FakeMessages.calls == 3:
                response.content = []
            elif FakeMessages.calls == 4:
                response.content = [
                    SimpleNamespace(type="text", text="费用不在范围内，产线数字2026")
                ]
            elif FakeMessages.calls == 5:
                response.usage.cache_creation_input_tokens = False
            return response

        FakeMessages.calls = 0
        with tempfile.TemporaryDirectory() as tmp, patch.object(
            FakeMessages, "create", new=varied
        ):
            previous = os.getcwd()
            os.chdir(tmp)
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    self.ns["main"]()
                rows = [
                    json.loads(line)
                    for line in Path("instruction-clarity-results.jsonl")
                    .read_text()
                    .splitlines()
                ]
            finally:
                os.chdir(previous)
        self.assertEqual(len(rows), 24)
        for status in (
            "incomplete", "refusal", "missing_text", "invalid_usage"
        ):
            self.assertEqual(sum(row["status"] == status for row in rows), 1)
        flagged = next(row for row in rows if row["text"].startswith("费用"))
        self.assertEqual(flagged["keyword_hits"], ["费用"])
        self.assertTrue(flagged["contains_digits"])

    def test_main_archives_request_errors_without_dropping_attempts(self):
        original = FakeMessages.create

        def timeout_once(client, **kwargs):
            if FakeMessages.calls == 0:
                FakeMessages.calls += 1
                raise TimeoutError("fixture timeout")
            return original(client, **kwargs)

        FakeMessages.calls = 0
        with tempfile.TemporaryDirectory() as tmp, patch.object(
            FakeMessages, "create", new=timeout_once
        ):
            previous = os.getcwd()
            os.chdir(tmp)
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    self.ns["main"]()
                rows = [
                    json.loads(line)
                    for line in Path("instruction-clarity-results.jsonl")
                    .read_text()
                    .splitlines()
                ]
            finally:
                os.chdir(previous)
        self.assertEqual(len(rows), 24)
        failed = [row for row in rows if row["status"] == "request_error"]
        self.assertEqual(len(failed), 1)
        self.assertEqual(failed[0]["error_type"], "TimeoutError")
        self.assertEqual(failed[0]["text"], "")

    def test_main_refuses_archive_overwrite_and_console_omits_content(self):
        FakeMessages.calls = 0
        with tempfile.TemporaryDirectory() as tmp:
            previous = os.getcwd()
            os.chdir(tmp)
            try:
                Path("instruction-clarity-results.jsonl").write_text("keep")
                with self.assertRaises(FileExistsError):
                    self.ns["main"]()
                self.assertEqual(FakeMessages.calls, 0)
                self.assertEqual(
                    Path("instruction-clarity-results.jsonl").read_text(), "keep"
                )
            finally:
                os.chdir(previous)

        with tempfile.TemporaryDirectory() as tmp:
            previous = os.getcwd()
            os.chdir(tmp)
            output = io.StringIO()
            try:
                with contextlib.redirect_stdout(output):
                    self.ns["main"]()
            finally:
                os.chdir(previous)
        self.assertNotIn(self.ns["TASK"], output.getvalue())
        self.assertNotIn('"text"', output.getvalue())
        self.assertIn("keyword_flags=", output.getvalue())
        self.assertIn("digit_flags=", output.getvalue())

    def test_main_runs_interleaved_fixture_calls_and_archives_every_output(self):
        FakeMessages.calls = 0
        with tempfile.TemporaryDirectory() as tmp, patch("os.getcwd", return_value=tmp):
            # Path writes use the process cwd; change it only inside this isolated fixture.
            previous = os.getcwd()
            os.chdir(tmp)
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    self.ns["main"]()
                archive = Path("instruction-clarity-results.jsonl")
                rows = [json.loads(line) for line in archive.read_text().splitlines()]
            finally:
                os.chdir(previous)
        self.assertEqual(FakeMessages.calls, 24)
        self.assertEqual(len(rows), 24)
        self.assertEqual({row["variant"] for row in rows}, set(self.ns["VARIANTS"]))
        for run in range(1, self.ns["RUNS"] + 1):
            run_rows = [row for row in rows if row["run"] == run]
            self.assertEqual(
                {row["variant"] for row in run_rows}, set(self.ns["VARIANTS"])
            )
        orders = [
            tuple(row["variant"] for row in rows if row["run"] == run)
            for run in range(1, self.ns["RUNS"] + 1)
        ]
        self.assertGreater(len(set(orders)), 1)
        self.assertTrue(all(row["requested_model"] == "fixture-model" for row in rows))
        self.assertTrue(all(row["response_model"] == "fixture-model-snapshot" for row in rows))


if __name__ == "__main__":
    unittest.main(verbosity=2)
