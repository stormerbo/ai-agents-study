"""Offline full-scope checks for structured-output/validation-retry."""
from __future__ import annotations

import contextlib
import copy
import hashlib
import io
import json
import re
import unittest
from pathlib import Path
from types import SimpleNamespace as NS

import pydantic
from pydantic import ValidationError

ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/structured-output/03-validation-retry.mdx"
SOURCE = LESSON.read_text(encoding="utf-8")
FENCES = re.findall(r"^```([^\n]*)\n([\s\S]*?)^```\s*$", SOURCE, re.M)
PYTHON = [body for language, body in FENCES if language == "python"]


def load_example(index: int, *, main: bool = False):
    namespace = {"__name__": "__main__" if main else "review_fixture"}
    exec(compile(PYTHON[index], f"validation-retry-example-{index}", "exec"), namespace)
    return namespace


class FakeMessages:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def create(self, **request):
        self.calls.append(copy.deepcopy(request))
        return self.responses.pop(0)


def tool_response(value, *, tool_id="tool-1", stop_reason="tool_use"):
    block = NS(type="tool_use", id=tool_id, name="save_refund", input=value)
    return NS(stop_reason=stop_reason, content=[block])


class ValidationRetryReview(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.retry = load_example(0)
        cls.degrade = load_example(1)

    def test_historical_results_are_explicitly_unverifiable(self):
        self.assertIn("逐次请求/响应", SOURCE)
        self.assertIn("不能证明各组首轮都按设计失败", SOURCE)
        self.assertIn("不能当作可复现的模型成功率", SOURCE)
        self.assertIn("不能独立复核", SOURCE)
        self.assertIn("不能据此估计模型编造率", SOURCE)
        self.assertIn("并不相同，而且都缺少原始轨迹", SOURCE)

    def test_failure_taxonomy_has_four_distinct_layers(self):
        for label in (
            "结构/本地约束失败", "provider 终止状态", "API/传输失败", "信息缺失"
        ):
            self.assertIn(label, SOURCE)
        self.assertIn("分四类", SOURCE)
        self.assertIn("本例的 `extract_refund` 只捕获 Pydantic `ValidationError`", SOURCE)
        self.assertIn("第四类（信息缺失）", SOURCE)

    def test_pydantic_classification_does_not_invent_business_rule(self):
        classify = self.retry["classify"]
        self.assertEqual(classify([{"type": "multiple_of"}]), "constraint")
        self.assertEqual(classify([{"type": "missing"}]), "shape")
        self.assertEqual(classify([{"type": "string_too_short"}]), "constraint")
        self.assertEqual(classify([{"type": "url_parsing"}]), "validation_other")
        self.assertIn("真正的 `business_rule` 应来自应用自己的领域校验器", SOURCE)
        self.assertIn("当前代码不把它伪装成 Pydantic 输出", SOURCE)

    def test_validation_feedback_is_redacted_and_paired_with_tool_result(self):
        fake = FakeMessages([
            tool_response({"amount": 1234, "reason": "PRIVATE_NOTE"}, tool_id="bad-1"),
            tool_response({"amount": 1200, "reason": "已脱敏示例"}, tool_id="good-2"),
        ])
        result = self.retry["extract_refund"](
            NS(messages=NS(create=fake.create)), "fake-model", "PRIVATE_SOURCE", {}
        )
        self.assertEqual(result["attempts"], 2)
        self.assertFalse(result["first_round_ok"])
        self.assertEqual(result["result"].amount, 1200)
        self.assertEqual(len(fake.calls), 2)
        retry_messages = fake.calls[1]["messages"]
        self.assertEqual(retry_messages[-2]["role"], "assistant")
        self.assertEqual(retry_messages[-1]["role"], "user")
        tool_result = retry_messages[-1]["content"][0]
        self.assertEqual(tool_result["type"], "tool_result")
        self.assertEqual(tool_result["tool_use_id"], "bad-1")
        self.assertTrue(tool_result["is_error"])
        self.assertNotIn("PRIVATE_NOTE", tool_result["content"])
        self.assertNotIn("PRIVATE_SOURCE", json.dumps(tool_result, ensure_ascii=False))

    def test_retry_exhaustion_returns_actual_attempt_count_and_redacted_report(self):
        fake = FakeMessages([
            tool_response({"amount": 1234, "reason": "PRIVATE_NOTE"}, tool_id=f"bad-{i}")
            for i in range(1, 4)
        ])
        result = self.retry["extract_refund"](
            NS(messages=NS(create=fake.create)), "fake-model", "PRIVATE_SOURCE", {}
        )
        self.assertIsNone(result["result"])
        self.assertEqual(result["attempts"], 3)
        self.assertEqual(len(fake.calls), 3)
        self.assertEqual(result["error_type"], "constraint")
        report = json.dumps(result["last_report"], ensure_ascii=False)
        self.assertNotIn("PRIVATE_NOTE", report)
        self.assertNotIn("PRIVATE_SOURCE", report)

    def test_missing_information_is_not_inferred_from_validation_error(self):
        with self.assertRaises(ValidationError) as caught:
            self.retry["Refund"].model_validate({"amount": 1200})
        report = self.retry["safe_report"](caught.exception)
        self.assertEqual(self.retry["classify"](report), "shape")
        self.assertNotIn("business_rule", {item["type"] for item in report})
        self.assertIn("询问、补充来源或表达未知", SOURCE)

    def test_refusal_truncation_and_unexpected_stop_are_not_blindly_retried(self):
        for stop_reason, expected in (
            ("refusal", "refusal"),
            ("max_tokens", "truncated"),
            ("model_context_window_exceeded", "context_limit"),
            ("end_turn", "unexpected_stop_reason"),
        ):
            fake = FakeMessages([NS(stop_reason=stop_reason, content=[])])
            result = self.retry["extract_refund"](
                NS(messages=NS(create=fake.create)), "fake-model", "ask", {}
            )
            self.assertEqual(result["error_type"], expected)
            self.assertEqual(result["attempts"], 1)
            self.assertEqual(len(fake.calls), 1)

    def test_unexpected_tool_output_fails_closed(self):
        response = NS(stop_reason="tool_use", content=[
            NS(type="tool_use", id="other", name="other_tool", input={})
        ])
        fake = FakeMessages([response])
        result = self.retry["extract_refund"](
            NS(messages=NS(create=fake.create)), "fake-model", "ask", {}
        )
        self.assertEqual(result["error_type"], "unexpected_tool_output")
        self.assertEqual(result["attempts"], 1)

    def test_retry_budget_is_positive_and_stop_states_are_separate_from_transport(self):
        self.assertGreaterEqual(self.retry["MAX_ATTEMPTS"], 1)
        self.assertIn("使用单独的退避、重试与总预算策略", SOURCE)
        self.assertIn("传输失败则在 API 响应层另行处理", SOURCE)

    def test_transport_exceptions_propagate_to_the_outer_runtime(self):
        attempts = []

        def fail_request(**request):
            attempts.append(request)
            raise TimeoutError("offline transport fixture")

        with self.assertRaisesRegex(TimeoutError, "offline transport fixture"):
            self.retry["extract_refund"](
                NS(messages=NS(create=fail_request)), "fake-model", "ask", {}
            )
        self.assertEqual(len(attempts), 1)
        self.assertIn("由调用方的 API/runtime 层", SOURCE)

    def test_degradation_policies_require_explicit_inputs_and_do_not_log_raw_data(self):
        run = self.degrade["run"]
        fixed = {"result": self.degrade["Refund"](amount=1200, reason="safe"),
                 "attempts": 2, "first_round_ok": False, "error_type": None,
                 "last_report": []}
        failed = {"result": None, "attempts": 3, "first_round_ok": False,
                  "error_type": "business_rule", "last_report": [
                      {"type": "business_rule", "field": "amount", "message": "safe"}]}
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream):
            ok = run("PRIVATE_ASK", lambda _: fixed, request_id="r1",
                     fallback_policy="human_queue", case_ref="case-safe")
            human = run("PRIVATE_ASK", lambda _: failed, request_id="r2",
                        fallback_policy="human_queue", case_ref="case-safe")
            conservative = run("PRIVATE_ASK", lambda _: failed, request_id="r3",
                               fallback_policy="conservative_default", default_value=None)
            split = run("PRIVATE_ASK", lambda _: failed, request_id="r4",
                        fallback_policy="split_retry", case_ref="case-safe",
                        split_fields=("amount",), remaining_attempts=1)
        self.assertEqual([ok["action"], human["action"], conservative["action"], split["action"]],
                         ["validated", "human_queue", "conservative_default", "split_retry"])
        self.assertEqual(ok["attempts"], 2)
        self.assertEqual(human["attempts"], 3)
        self.assertNotIn("PRIVATE_ASK", stream.getvalue())
        self.assertNotIn("case-safe", stream.getvalue())

    def test_fallback_configuration_errors_are_explicit(self):
        run = self.degrade["run"]
        failed = {"result": None, "attempts": 3, "first_round_ok": False,
                  "error_type": "constraint", "last_report": []}
        with self.assertRaisesRegex(ValueError, "case_ref"):
            run("ask", lambda _: failed, request_id="r", fallback_policy="human_queue")
        with self.assertRaisesRegex(ValueError, "default_value"):
            run("ask", lambda _: failed, request_id="r", fallback_policy="conservative_default")
        with self.assertRaisesRegex(ValueError, "remaining budget"):
            run("ask", lambda _: failed, request_id="r", fallback_policy="split_retry",
                case_ref="case", split_fields=("amount",), remaining_attempts=0)

    def test_every_python_example_runs_and_stdout_matches_its_published_text_fence(self):
        self.assertEqual(len(PYTHON), 2)
        cursor = 0
        for index, (language, source) in enumerate(FENCES):
            if language != "python":
                continue
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                load_example(index=0 if source == PYTHON[0] else 1, main=True)
            following_text = next(
                body for next_language, body in FENCES[index + 1:]
                if next_language == "text"
            )
            self.assertEqual(output.getvalue(), following_text)
            cursor += 1
        self.assertEqual(cursor, 2)

    def test_published_output_is_non_sensitive_and_attempt_counts_are_real(self):
        self.assertIn('"attempts": attempts', PYTHON[0])
        self.assertNotIn('"attempts": 3,\n        "first_round_ok": False', PYTHON[0])
        self.assertIn("实际 requests 是从 outcome 中计数", SOURCE)
        self.assertIn("只记录最少字段", SOURCE)
        self.assertNotIn('"raw_input"', PYTHON[1])
        self.assertIn("case_ref", PYTHON[1])
        self.assertIn("字段级 worker", PYTHON[1])

    def test_cost_model_and_budget_are_conditional_not_universal_thresholds(self):
        self.assertIn("按等差数列增长", SOURCE)
        self.assertIn("不适用于有状态 API", SOURCE)
        self.assertIn("不是跨 provider 的经验门槛", SOURCE)
        self.assertIn("幂等与对账", SOURCE)

    def test_current_messages_api_contract_and_capability_boundary_are_stated(self):
        self.assertIn("/agents-and-tools/tool-use/handle-tool-calls", SOURCE)
        self.assertIn("tool_use_id", PYTHON[0])
        self.assertIn('"is_error": True', PYTHON[0])
        self.assertIn("本例没有连 provider 实测", SOURCE)
        self.assertIn("按各自协议验证", SOURCE)

    def test_lesson_hash_is_stable_for_registry_pin(self):
        self.assertEqual(
            hashlib.sha256(SOURCE.encode()).hexdigest(),
            "45be29bac1206ff34c11772d206ae7f82d6099b8c8f8b65e0954304d79abbd98",
        )


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(ValidationRetryReview)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print(
        f"providerCalls=0; externalNetworkCalls=0; pydanticVersion="
        f"{pydantic.__version__}; tests={result.testsRun}; "
        f"failures={len(result.failures) + len(result.errors)}"
    )
    raise SystemExit(not result.wasSuccessful())
