"""Offline regression checks for the prompt-boundary lesson review."""
from __future__ import annotations

import re
import contextlib
import io
import json
import os
import sys
import tempfile
import types
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/prompt-engineering/02-structure-and-separation.mdx"


class PromptBoundaryReview(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = LESSON.read_text()

    def test_historical_rates_are_not_presented_as_verified_effects(self):
        self.assertRegex(self.text, r"(?is)逐次请求、原始响应.{0,80}(?:没有归档|缺失).{0,100}不能作为标签有效性")
        self.assertNotRegex(self.text, r"(?s)标签确实有效|XML 标签只挡住了一半|得逞率从 \*\*6/6 降到 2/6\*\*")

    def test_boundary_labels_are_mitigation_not_access_control(self):
        self.assertRegex(self.text, r"(?is)标签.{0,100}(?:不执行权限控制|不能形成访问控制)")
        self.assertRegex(self.text, r"(?is)(?:最小权限|服务端授权|人工确认)")

    def test_fact_check_requires_separate_trusted_evidence(self):
        self.assertIn("独立可信来源", self.text)
        self.assertIn("逐字引用", self.text)
        self.assertNotRegex(self.text, r"unsupported_tokens\(summary,\s*doc\)")

    def test_python_fences_compile(self):
        fences = re.findall(r"^```python\s*\n([\s\S]*?)^```\s*$", self.text, re.M)
        self.assertTrue(fences)
        for index, code in enumerate(fences, 1):
            compile(code, f"{LESSON}:python-fence-{index}", "exec")

    def test_anthropic_harness_fails_closed_and_archives_every_mock_response(self):
        fences = re.findall(r"^```python\s*\n([\s\S]*?)^```\s*$", self.text, re.M)
        code = next(fence for fence in fences if "prompt-injection-results.jsonl" in fence)

        class FakeMessages:
            calls = 0
            stop_reason = "end_turn"
            text = "摘要含 12%"

            def create(self, **_kwargs):
                type(self).calls += 1
                return SimpleNamespace(
                    stop_reason=type(self).stop_reason,
                    model="fixture-model-snapshot",
                    content=[SimpleNamespace(type="text", text=type(self).text)],
                    usage=SimpleNamespace(
                        input_tokens=2,
                        output_tokens=3,
                        cache_creation_input_tokens=0,
                        cache_read_input_tokens=0,
                    ),
                )

        fake_sdk = types.SimpleNamespace(
            Anthropic=lambda **_kwargs: SimpleNamespace(messages=FakeMessages())
        )
        FakeMessages.calls = 0
        namespace: dict = {"__name__": "lesson_fixture"}
        with patch.dict(sys.modules, {"anthropic": fake_sdk}), patch.dict(
            os.environ, {"VERIFY_MODEL": "fixture-model"}
        ):
            exec(compile(code, str(LESSON), "exec"), namespace)
            namespace["client"] = SimpleNamespace(messages=FakeMessages())
            namespace["MODEL"] = "fixture-model"
            self.assertEqual(
                namespace["run"]("脚本式（要求输出标记）", "doc", False, 1)["response_model"],
                "fixture-model-snapshot",
            )
            FakeMessages.stop_reason = "max_tokens"
            self.assertEqual(
                namespace["run"]("脚本式（要求输出标记）", "doc", True, 2)["status"], "truncated"
            )
            FakeMessages.stop_reason = "end_turn"
            FakeMessages.text = "  "
            self.assertEqual(
                namespace["run"]("脚本式（要求输出标记）", "doc", True, 3)["status"], "empty_text"
            )
            FakeMessages.text = "摘要含 12%"
            FakeMessages.calls = 0
            with tempfile.TemporaryDirectory() as tmp:
                previous = os.getcwd()
                os.chdir(tmp)
                try:
                    with contextlib.redirect_stdout(io.StringIO()), patch.object(
                        sys, "argv", ["injection_experiment.py", "--run-live"]
                    ):
                        namespace["__name__"] = "__main__"
                        with self.assertRaises(SystemExit) as error:
                            exec(compile(code, str(LESSON), "exec"), namespace)
                        self.assertEqual(error.exception.code, 0)
                    rows = [json.loads(line) for line in Path("prompt-injection-results.jsonl").read_text().splitlines()]
                finally:
                    os.chdir(previous)
            self.assertEqual(FakeMessages.calls, 36)
            results = [row for row in rows if row.get("phase") == "result"]
            starts = [row for row in rows if row.get("phase") == "started"]
            self.assertEqual(len(rows), 72)
            self.assertEqual(len(starts), 36)
            self.assertEqual(len(results), 36)
            self.assertTrue(
                all(row["response_model"] == "fixture-model-snapshot" for row in results)
            )

    def test_independent_source_quote_checker_rejects_unknown_sources(self):
        fences = re.findall(r"^```python\s*\n([\s\S]*?)^```\s*$", self.text, re.M)
        code = next(fence for fence in fences if "exact_quote_from_allowed_record" in fence)
        namespace: dict = {}
        exec(compile(code, "cite-check.py", "exec"), namespace)
        check = namespace["exact_quote_from_allowed_record"]
        evidence = {"annual-report": "Revenue increased by 12%."}
        allowed = {"annual-report"}
        self.assertTrue(check("annual-report", "Revenue increased by 12%.", evidence, allowed))
        self.assertFalse(check("annual-report", "Profit doubled.", evidence, allowed))
        self.assertFalse(check("user-upload", "Revenue increased by 12%.", evidence, allowed))


    def test_live_harness_archives_failures_and_stops_at_existing_evidence(self):
        fence_mark = chr(96) * 3
        pattern = rf"^{re.escape(fence_mark)}python\s*\n([\s\S]*?)^{re.escape(fence_mark)}\s*$"
        fences = re.findall(pattern, self.text, re.M)
        code = next(fence for fence in fences if "prompt-injection-results.jsonl" in fence)

        class QueueMessages:
            def __init__(self, responses):
                self.responses = list(responses)

            def create(self, **_kwargs):
                outcome = self.responses.pop(0)
                if isinstance(outcome, Exception):
                    raise outcome
                return outcome

        def response(reason, text, input_tokens=2, output_tokens=3, cache=None):
            return SimpleNamespace(
                stop_reason=reason,
                model="fixture-model",
                _request_id="req-fixture",
                content=[SimpleNamespace(type="text", text=text)],
                usage=SimpleNamespace(
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    cache_creation_input_tokens=cache,
                    cache_read_input_tokens=None,
                ),
            )

        outcomes = [
            ConnectionError("fixture network failure"),
            response("refusal", "无法安全给出判断"),
            response("max_tokens", "部分摘要"),
            response("end_turn", "摘要", input_tokens=True),
            response("end_turn", "摘要", cache=None),
        ]
        sdk = types.SimpleNamespace(
            Anthropic=lambda **_kwargs: SimpleNamespace(
                messages=QueueMessages(outcomes)
            )
        )
        namespace = {"__name__": "lesson_fixture"}
        with patch.dict(sys.modules, {"anthropic": sdk}), patch.dict(
            os.environ, {"VERIFY_MODEL": "fixture-model"}
        ):
            exec(compile(code, str(LESSON), "exec"), namespace)
            namespace["client"] = SimpleNamespace(
                messages=QueueMessages(outcomes)
            )
            namespace["MODEL"] = "fixture-model"
            with tempfile.TemporaryDirectory() as tmp:
                output = Path(tmp) / "attempts.jsonl"
                jobs = [
                    ("脚本式（要求输出标记）", "synthetic document", False, index)
                    for index in range(1, 6)
                ]
                summary = namespace["execute_jobs"](jobs, output)
                rows = [
                    json.loads(line) for line in output.read_text().splitlines()
                ]
                starts = [row for row in rows if row["phase"] == "started"]
                results = [row for row in rows if row["phase"] == "result"]
                self.assertEqual(len(starts), 5)
                self.assertEqual(
                    [row["status"] for row in results],
                    [
                        "request_error",
                        "refusal",
                        "truncated",
                        "invalid_usage",
                        "complete",
                    ],
                )
                self.assertEqual(summary["attempted"], 5)
                self.assertEqual(summary["complete"], 1)
                self.assertEqual(summary["failed"], 4)
                self.assertEqual(results[1]["usage"]["input_tokens"], 2)
                self.assertEqual(
                    results[1]["usage"]["cache_creation_input_tokens"], 0
                )
                self.assertEqual(results[4]["usage"]["cache_read_input_tokens"], 0)
                self.assertEqual(results[0]["error_type"], "ConnectionError")
                self.assertEqual(starts[0]["input_sha256"], results[0]["input_sha256"])
                before = output.read_bytes()
                with self.assertRaises(FileExistsError):
                    namespace["execute_jobs"]([], output)
                self.assertEqual(output.read_bytes(), before)

    def test_command_requires_explicit_live_cost_opt_in(self):
        fence_mark = chr(96) * 3
        pattern = rf"^{re.escape(fence_mark)}python\s*\n([\s\S]*?)^{re.escape(fence_mark)}\s*$"
        fences = re.findall(pattern, self.text, re.M)
        code = next(fence for fence in fences if "prompt-injection-results.jsonl" in fence)
        sdk = types.SimpleNamespace(
            Anthropic=lambda **_kwargs: (_ for _ in ()).throw(
                AssertionError("provider client must not be created")
            )
        )
        namespace = {"__name__": "__main__"}
        output = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp, patch.dict(
            sys.modules, {"anthropic": sdk}
        ), patch.dict(os.environ, {"VERIFY_MODEL": "fixture-model"}), patch.object(
            sys, "argv", ["injection_experiment.py"]
        ), contextlib.redirect_stdout(output):
            previous = os.getcwd()
            os.chdir(tmp)
            try:
                with self.assertRaises(SystemExit) as error:
                    exec(compile(code, str(LESSON), "exec"), namespace)
                self.assertEqual(error.exception.code, 0)
            finally:
                os.chdir(previous)
        self.assertIn("--run-live", output.getvalue())
        self.assertFalse((Path(tmp) / "prompt-injection-results.jsonl").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
