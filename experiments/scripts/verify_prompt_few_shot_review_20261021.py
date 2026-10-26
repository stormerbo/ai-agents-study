"""Offline checks for few-shot lesson examples; never calls a provider."""
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
LESSON = ROOT / "src/content/chapters/prompt-engineering/03-few-shot.mdx"
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
            content=[SimpleNamespace(type="text", text="中性")],
            usage=SimpleNamespace(
                input_tokens=3,
                output_tokens=1,
                cache_creation_input_tokens=0,
                cache_read_input_tokens=0,
            ),
        )


class FewShotReview(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = {"__name__": "lesson_fixture"}
        fake_sdk = types.SimpleNamespace(
            Anthropic=lambda: SimpleNamespace(messages=FakeMessages())
        )
        with patch.dict(sys.modules, {"anthropic": fake_sdk}), patch.dict(
            os.environ, {"ANTHROPIC_MODEL": "fixture-model"}
        ):
            exec(compile(CODE, str(LESSON), "exec"), cls.ns)

    def test_python_fence_fits_88_columns(self):
        self.assertLessEqual(max(map(len, CODE.splitlines())), 88)

    def test_python_fence_compiles(self):
        compile(CODE, str(LESSON), "exec")

    def test_new_fixture_variants_have_no_exact_train_test_overlap(self):
        for examples in self.ns["VARIANTS"].values():
            self.ns["assert_no_exact_overlap"](examples, self.ns["TEST"])

    def test_leakage_check_rejects_exact_duplicate(self):
        with self.assertRaisesRegex(ValueError, "leakage"):
            self.ns["assert_no_exact_overlap"](
                [("复用案例", "中性")], [("t1", "复用案例", "中性")]
            )

    def test_legacy_table_has_one_exact_overlap(self):
        legacy_test = {
            "这个产品很好用", "完全是个灾难", "东西收到了",
            "总算没搞砸，但也就那样", "还行吧，没什么特别的",
            "客服态度不错，问题解决了", "用了三天就坏了",
            "请问什么时候发货", "比我想象的好太多了", "下次不会再买了",
        }
        legacy_boundary = {
            "东西是好东西，就是太贵",
            "总算没搞砸，但也就那样",
            "不是不好用，只是不适合我",
        }
        self.assertEqual(
            legacy_test & legacy_boundary,
            {"总算没搞砸，但也就那样"},
        )

    def test_unrun_legacy_ablation_script_has_three_overlaps(self):
        boundary_tests = {
            "东西是好东西，就是太贵",
            "不是不好用，只是不适合我",
            "总算没搞砸，但也就那样",
        }
        examples = set(boundary_tests)
        self.assertEqual(boundary_tests & examples, boundary_tests)

    def test_label_parser_requires_one_exact_label(self):
        parse = self.ns["parse_label"]
        self.assertEqual(parse("正面"), "正面")
        for value in ("答案：正面", "正面 / 负面", "", "neutral"):
            self.assertIsNone(parse(value))

    def test_response_requires_end_turn_and_text(self):
        extract = self.ns["extract_text"]
        good = SimpleNamespace(
            stop_reason="end_turn",
            content=[SimpleNamespace(type="text", text="中性")],
        )
        self.assertEqual(extract(good), "中性")
        for response in (
            SimpleNamespace(stop_reason="max_tokens", content=good.content),
            SimpleNamespace(stop_reason="end_turn", content=[]),
        ):
            with self.assertRaises(RuntimeError):
                extract(response)

    def test_usage_requires_core_counts_and_keeps_cache_separate(self):
        usage = self.ns["usage_fields"]
        valid = SimpleNamespace(
            usage=SimpleNamespace(
                input_tokens=3,
                output_tokens=1,
                cache_creation_input_tokens=5,
                cache_read_input_tokens=7,
            )
        )
        self.assertEqual(usage(valid), {
            "input_tokens": 3,
            "output_tokens": 1,
            "cache_creation_input_tokens": 5,
            "cache_read_input_tokens": 7,
        })
        with self.assertRaises(RuntimeError):
            usage(SimpleNamespace(usage=SimpleNamespace(input_tokens=None, output_tokens=1)))
        nullable = SimpleNamespace(
            usage=SimpleNamespace(
                input_tokens=3,
                output_tokens=1,
                cache_creation_input_tokens=None,
                cache_read_input_tokens=None,
            )
        )
        self.assertEqual(usage(nullable)["cache_creation_input_tokens"], 0)
        self.assertEqual(usage(nullable)["cache_read_input_tokens"], 0)

    def test_usage_rejects_boolean_and_non_integer_cache_counts(self):
        usage = self.ns["usage_fields"]
        for value in (False, True, 1.5, "0", -1):
            response = SimpleNamespace(
                usage=SimpleNamespace(
                    input_tokens=3,
                    output_tokens=1,
                    cache_creation_input_tokens=value,
                    cache_read_input_tokens=0,
                )
            )
            with self.subTest(value=value), self.assertRaises(RuntimeError):
                usage(response)

    def test_main_archives_incomplete_responses_instead_of_dropping_them(self):
        original = FakeMessages.create

        def truncated(client, **kwargs):
            response = original(client, **kwargs)
            if FakeMessages.calls == 1:
                response.stop_reason = "max_tokens"
            elif FakeMessages.calls == 2:
                response.stop_reason = "refusal"
            elif FakeMessages.calls == 3:
                response.content = [SimpleNamespace(type="text", text="正面 / 负面")]
            elif FakeMessages.calls == 4:
                response.content = []
            return response

        FakeMessages.calls = 0
        with tempfile.TemporaryDirectory() as tmp, patch.object(
            FakeMessages, "create", new=truncated
        ):
            previous = os.getcwd()
            os.chdir(tmp)
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    self.ns["main"]()
                rows = [
                    json.loads(line)
                    for line in Path("few-shot-results.jsonl").read_text().splitlines()
                ]
            finally:
                os.chdir(previous)
        self.assertEqual(len(rows), 240)
        failed = [row for row in rows if row["status"] == "incomplete"]
        self.assertEqual(len(failed), 1)
        self.assertEqual(failed[0]["stop_reason"], "max_tokens")
        self.assertFalse(failed[0]["correct"])
        for status in ("refusal", "invalid_label", "missing_text"):
            self.assertEqual(sum(row["status"] == status for row in rows), 1)

    def test_main_archives_request_exceptions_instead_of_dropping_them(self):
        original = FakeMessages.create

        def flaky(client, **kwargs):
            if FakeMessages.calls == 1:
                FakeMessages.calls += 1
                raise TimeoutError("fixture timeout")
            return original(client, **kwargs)

        FakeMessages.calls = 0
        with tempfile.TemporaryDirectory() as tmp, patch.object(
            FakeMessages, "create", new=flaky
        ):
            previous = os.getcwd()
            os.chdir(tmp)
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    self.ns["main"]()
                rows = [
                    json.loads(line)
                    for line in Path("few-shot-results.jsonl").read_text().splitlines()
                ]
            finally:
                os.chdir(previous)
        self.assertEqual(len(rows), 240)
        failed = [row for row in rows if row["status"] == "request_error"]
        self.assertEqual(len(failed), 1)
        self.assertEqual(failed[0]["error_type"], "TimeoutError")
        self.assertFalse(failed[0]["correct"])

    def test_main_console_progress_omits_inputs_and_raw_responses(self):
        with tempfile.TemporaryDirectory() as tmp:
            previous = os.getcwd()
            os.chdir(tmp)
            output = io.StringIO()
            try:
                with contextlib.redirect_stdout(output):
                    self.ns["main"]()
            finally:
                os.chdir(previous)
        self.assertNotIn("说明书看着复杂", output.getvalue())
        self.assertNotIn('"raw_output"', output.getvalue())
        self.assertIn("archived", output.getvalue())

    def test_main_refuses_to_overwrite_an_existing_archive(self):
        FakeMessages.calls = 0
        with tempfile.TemporaryDirectory() as tmp:
            previous = os.getcwd()
            os.chdir(tmp)
            try:
                Path("few-shot-results.jsonl").write_text("keep this archive")
                with self.assertRaises(FileExistsError):
                    self.ns["main"]()
                self.assertEqual(FakeMessages.calls, 0)
                self.assertEqual(
                    Path("few-shot-results.jsonl").read_text(), "keep this archive"
                )
            finally:
                os.chdir(previous)

    def test_main_archives_every_fixture_response_and_model(self):
        FakeMessages.calls = 0
        with tempfile.TemporaryDirectory() as tmp:
            previous = os.getcwd()
            os.chdir(tmp)
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    self.ns["main"]()
                rows = [
                    json.loads(line)
                    for line in Path("few-shot-results.jsonl").read_text().splitlines()
                ]
            finally:
                os.chdir(previous)
        expected_calls = 4 * len(self.ns["TEST"]) * self.ns["RUNS"]
        self.assertEqual(FakeMessages.calls, expected_calls)
        self.assertEqual(len(rows), expected_calls)
        self.assertTrue(all(row["response_model"] == "fixture-model-snapshot" for row in rows))
        self.assertEqual({row["condition"] for row in rows}, set(self.ns["VARIANTS"]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
