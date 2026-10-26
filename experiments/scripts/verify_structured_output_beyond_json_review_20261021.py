"""Offline full-scope checks for structured-output/beyond-json."""
from __future__ import annotations

import contextlib
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
LESSON = ROOT / "src/content/chapters/structured-output/04-beyond-json.mdx"
SOURCE = LESSON.read_text(encoding="utf-8")
FENCES = re.findall(r"^```([^\n]*)\n([\s\S]*?)^```\s*$", SOURCE, re.M)
PYTHON = [body for language, body in FENCES if language == "python"]


def load_example(source: str, *, main: bool = False):
    namespace = {"__name__": "__main__" if main else "review_fixture"}
    exec(compile(source, "beyond-json-example", "exec"), namespace)
    return namespace


class ResponseClient:
    def __init__(self, response):
        self.response = response
        self.requests = []
        self.messages = self

    def create(self, **request):
        self.requests.append(request)
        return self.response


def response(input_value=None, *, name="extract_order_id", tool_id="tool-1", stop="tool_use", count=1):
    content = [
        NS(type="tool_use", id=tool_id, name=name, input=input_value)
        for _ in range(count)
    ]
    return NS(stop_reason=stop, content=content)


class BeyondJsonReview(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if len(PYTHON) != 2:
            raise AssertionError(f"expected two Python fences, got {len(PYTHON)}")
        cls.extract = load_example(PYTHON[0])
        cls.approval = load_example(PYTHON[1])

    def test_historical_model_results_are_not_claimed_as_reproduced(self):
        self.assertIn("历史摘要", SOURCE)
        self.assertIn("逐次请求/响应、完整 prompt、精确模型版本与 scorer 未归档", SOURCE)
        self.assertIn("原始轨迹缺失，未独立复核", SOURCE)
        self.assertIn("不能证明模型普遍会编造", SOURCE)
        self.assertIn("不能单独证明 prompt 造成了输出差异", SOURCE)
        self.assertIn("不能独立复核", SOURCE)
        self.assertNotIn("实测数据，`deepseek-flash`", SOURCE)

    def test_schema_boundary_is_distinguished_from_truth_and_business_rules(self):
        self.assertIn("结构合法不等于事实可信，也不等于业务规则通过", SOURCE)
        self.assertIn("没有通用关键字比较两个任意字段的值", SOURCE)
        self.assertIn("`format: date` 是否运行断言还取决于校验器配置", SOURCE)
        self.assertIn("授权的数据源", SOURCE)
        self.assertIn("所有写入路径都必须经过它", SOURCE)

    def test_unknown_enum_is_not_presented_as_a_correctness_guarantee(self):
        self.assertIn("只增加 `other` 并不能证明生成内容正确", SOURCE)
        self.assertIn("unknown`、缺失值、拒绝和人工处理的语义也应区分", SOURCE)
        self.assertIn("历史 6/6 结果无法复核", SOURCE)

    def test_current_tool_choice_scope_and_local_validation_are_explicit(self):
        self.assertIn("/agents-and-tools/tool-use/define-tools", SOURCE)
        self.assertIn("并非所有模型和设置都支持强制工具调用", SOURCE)
        self.assertIn("普通 `input_schema` 也不等于生成端的 strict 约束", SOURCE)
        self.assertIn("始终在应用端校验", SOURCE)
        self.assertNotIn('thinking={"type": "disabled"}', PYTHON[0])

    def test_fake_client_schema_excludes_status_and_example_stdout_matches(self):
        source = PYTHON[0]
        self.assertIn('assert set(properties) == {"order_id"}', source)
        self.assertNotIn('"status": str', source)
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            load_example(source, main=True)
        python_index = next(i for i, (language, body) in enumerate(FENCES)
                            if language == "python" and body == source)
        expected = next(body for language, body in FENCES[python_index + 1:]
                        if language == "text")
        self.assertEqual(output.getvalue(), expected)

    def test_fake_tool_call_returns_only_extracted_id_and_app_owned_provenance(self):
        client = ResponseClient(response({"order_id": "A-1001"}))
        ticket = self.extract["build_ticket"](
            client, "fixture-model", "订单 A-1001 怎么样了", {
                "A-1001": {"status": "已取消", "record_id": "orders/A-1001", "revision": "r18"}
            }
        )
        self.assertEqual(ticket, {
            "order_id": "A-1001", "status": "已取消",
            "status_source": {"system": "orders", "record_id": "orders/A-1001", "revision": "r18"},
        })
        props = client.requests[0]["tools"][0]["input_schema"]["properties"]
        self.assertEqual(set(props), {"order_id"})
        self.assertEqual(client.requests[0]["tool_choice"], {"type": "tool", "name": "extract_order_id"})

    def test_missing_order_is_explicit_and_not_guessed(self):
        client = ResponseClient(response({"order_id": "A-9999"}))
        ticket = self.extract["build_ticket"](client, "fixture-model", "订单 A-9999", {})
        self.assertIsNone(ticket["status"])
        self.assertEqual(ticket["status_source"], {"system": "orders", "lookup": "not_found"})

    def test_non_tool_stop_fails_closed_without_reading_output_as_a_fact(self):
        client = ResponseClient(response({"order_id": "A-1001"}, stop="max_tokens"))
        with self.assertRaisesRegex(RuntimeError, "max_tokens"):
            self.extract["call_tool"](client, "fixture-model", "ask", self.extract["Extracted"], "extract_order_id")
        self.assertEqual(len(client.requests), 1)

    def test_wrong_missing_or_multiple_tool_uses_fail_closed(self):
        for candidate in (
            response({"order_id": "A-1"}, name="wrong_tool"),
            response({"order_id": "A-1"}, tool_id=""),
            response({"order_id": "A-1"}, count=2),
            NS(stop_reason="tool_use", content=[]),
        ):
            with self.subTest(candidate=candidate):
                client = ResponseClient(candidate)
                with self.assertRaisesRegex(RuntimeError, "工具响应不符合预期"):
                    self.extract["call_tool"](client, "fixture-model", "ask", self.extract["Extracted"], "extract_order_id")

    def test_pydantic_validation_rejects_missing_and_wrongly_typed_ids(self):
        for invalid in ({}, {"order_id": 1001}):
            client = ResponseClient(response(invalid))
            with self.subTest(invalid=invalid), self.assertRaises(ValidationError):
                self.extract["call_tool"](client, "fixture-model", "ask", self.extract["Extracted"], "extract_order_id")

    def test_source_marker_is_not_described_as_proof_of_truth_or_authorization(self):
        self.assertIn("不构成真实性或授权证明", SOURCE)
        self.assertIn("租户/查询范围、读取时间和权限判定证据", SOURCE)
        self.assertIn("标签只提供追踪线索", SOURCE)

    def test_constructed_final_records_are_valid_json_and_show_policy_version(self):
        json_fences = [body for language, body in FENCES if language == "json"]
        self.assertEqual(len(json_fences), 4)
        # The first fence contains three independent constructed JSON objects.
        for line in json_fences[0].splitlines():
            if line.strip():
                json.loads(line)
        first_record, missing_record = map(json.loads, json_fences[1:3])
        json.loads(json_fences[3])  # date-order counterexample
        self.assertEqual(first_record["policy_version"], "demo_policy_v1")
        self.assertEqual(missing_record["approval"], "hold")
        self.assertIsNone(missing_record["amount_minor_units"])
        self.assertTrue(all("//" not in body for body in json_fences))

    def test_approval_policy_is_explicit_about_currency_units_and_invalid_inputs(self):
        approve = self.approval["approve"]
        self.assertEqual(approve(500_000, "CNY")["approval"], "auto")
        self.assertEqual(approve(500_001, "CNY")["approval"], "human")
        for amount, currency in ((None, "CNY"), (-1, "CNY"), (True, "CNY"), (1.5, "CNY"), (10, "USD")):
            with self.subTest(amount=amount, currency=currency):
                result = approve(amount, currency)
                self.assertEqual(result["approval"], "hold")
                self.assertEqual(result["policy_version"], "demo_policy_v1")

    def test_approval_example_stdout_matches_and_policy_version_is_in_every_result(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            load_example(PYTHON[1], main=True)
        index = next(i for i, (language, body) in enumerate(FENCES)
                     if language == "python" and body == PYTHON[1])
        expected = next(body for language, body in FENCES[index + 1:] if language == "text")
        self.assertEqual(output.getvalue(), expected)
        for amount, currency in ((482_000, "CNY"), (1_200_000, "CNY"), (None, "CNY")):
            result = self.approval["approve"](amount, currency)
            self.assertEqual(result["policy_version"], "demo_policy_v1")

    def test_historical_arithmetic_summary_is_scoped_and_does_not_claim_zero_risk(self):
        self.assertIn("23 次运行全部正确", SOURCE)
        self.assertIn("不可独立复核的历史摘要", SOURCE)
        self.assertIn("逐次输出、模型快照与 scorer 未保存在当前工作树", SOURCE)
        self.assertIn("让代码计算并用独立测试验证", SOURCE)

    def test_python_fences_compile_and_the_lesson_has_only_fake_local_clients(self):
        self.assertEqual(len(PYTHON), 2)
        for index, source in enumerate(PYTHON):
            compile(source, f"beyond-json-{index}", "exec")
        self.assertIn("FakeClient", PYTHON[0])
        self.assertIn("不包含真实 provider 调用", SOURCE)
        self.assertIn("未调用 provider", SOURCE)

    def test_lesson_hash_matches_the_reviewed_source(self):
        self.assertEqual(
            hashlib.sha256(SOURCE.encode()).hexdigest(),
            "f43236b65e9d6175d8b5c0860a716600a6f8d426475ebd175de5acb4405e066b",
        )


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(BeyondJsonReview)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print(
        f"providerCalls=0; externalNetworkCalls=0; pydanticVersion={pydantic.__version__}; "
        f"tests={result.testsRun}; failures={len(result.failures) + len(result.errors)}"
    )
    raise SystemExit(not result.wasSuccessful())
