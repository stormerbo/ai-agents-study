"""Offline checks for the JSON Schema / constrained-output lesson review."""

from __future__ import annotations

import contextlib
import io
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

from pydantic import TypeAdapter


ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/structured-output/02-json-schema-strict.mdx"
RETRY_LESSON = ROOT / "src/content/chapters/structured-output/03-validation-retry.mdx"
BUSINESS_LESSON = ROOT / "src/content/chapters/structured-output/04-beyond-json.mdx"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def python_fences(text: str) -> list[str]:
    return re.findall(r"^```python\s*\n(.*?)^```\s*$", text, re.MULTILINE | re.DOTALL)


def main() -> None:
    text = LESSON.read_text(encoding="utf-8")
    checks = 0

    fences = re.findall(r"^```", text, re.MULTILINE)
    require(len(fences) % 2 == 0, "Markdown fences are not paired")
    checks += 1

    require("\\n\\nAnthropic" not in text, "Literal escaped newlines remain in prose")
    checks += 1

    require("逐次请求/响应、精确模型快照、完整 schema 与可重算 scorer" in text, "Historical evidence boundary is missing")
    require("不能据此认定关键字失效或推广到其他 endpoint" in text, "Historical results are generalized")
    checks += 1

    require("https://api-docs.deepseek.com/guides/tool_calls/" in text, "DeepSeek source is missing")
    require("https://platform.claude.com/docs/en/agents-and-tools/tool-use/strict-tool-use" in text, "Anthropic strict-tool source is missing")
    require("https://platform.claude.com/docs/en/build-with-claude/structured-outputs" in text, "Anthropic structured-output source is missing")
    require("https://docs.pydantic.dev/2.9/concepts/strict_mode/" in text, "Pydantic strict-mode source is missing")
    checks += 1

    require("errors(include_url=False, include_context=False, include_input=False)" in text, "Pydantic error redaction is missing")
    require("exc.json(" not in text, "Exception serialization outside its scope remains")
    require("datetime.date" in text, "Date comparison rationale is missing")
    require("ConfigDict(strict=True)" in text, "Pydantic strict-type policy is not explicit")
    require(TypeAdapter(int).validate_json('"1200"') == 1200, "Pydantic 2.9.2 default lax integer coercion changed")
    require('stop_reason="refusal"' in text and "max_tokens" in text, "Structured-output refusal/truncation exceptions are missing")
    require("大小写边界" in text and "语法编译复杂度限制" in text, "Current provider caveats are missing")
    checks += 1

    blocks = python_fences(text)
    require(len(blocks) == 2, f"Expected two Python fences, found {len(blocks)}")
    for index, block in enumerate(blocks, 1):
        compile(block, f"lesson-python-fence-{index}", "exec")
    checks += 1

    require(blocks[0].count("model_validate_json") == 3, "Pydantic demo cases changed unexpectedly")
    env = {"PATH": os.environ.get("PATH", ""), "PYTHONDONTWRITEBYTECODE": "1"}
    run = subprocess.run(
        [sys.executable, "-c", blocks[0]],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
        check=True,
    )
    expected = "\n".join(
        [
            "校验结果： 不通过",
            '问题清单： [{"type": "multiple_of", "field": "amount", "msg": "Input should be a multiple of 100"}, {"type": "literal_error", "field": "issue_type", "msg": "Input should be \'refund\' or \'repair\'"}]',
            '通过时的下游对象： {"amount":1200,"issue_type":"refund","start_date":"2026-10-01","end_date":"2026-10-15"}',
            '跨字段业务规则问题： [{"type": "business_rule", "field": "end_date", "msg": "end_date 早于 start_date：区间不可满足"}]',
        ]
    )
    require(run.stdout.strip() == expected, f"Pydantic demo output differs:\n{run.stdout}")

    namespace: dict[str, object] = {}
    exec(blocks[0], namespace)
    exec(blocks[1], namespace)
    refund_model = namespace["Refund"]
    try:
        refund_model.model_validate_json(
            '{"amount":"1200","issue_type":"refund","start_date":"2026-10-01","end_date":"2026-10-15"}'
        )
    except namespace["ValidationError"]:
        pass
    else:
        raise AssertionError("Strict Pydantic model accepted a string for the integer amount")
    decision = namespace["decide"]
    require(decision(None, [{"type": "multiple_of"}])["action"] == "needs_review", "Decision helper accepted invalid output")
    valid = refund_model.model_validate_json(
        '{"amount":1200,"issue_type":"refund","start_date":"2026-10-01","end_date":"2026-10-15"}'
    )
    require(
        decision(valid, [])
        == {
            "action": "validated",
            "payload": {
                "amount": 1200,
                "issue_type": "refund",
                "start_date": "2026-10-01",
                "end_date": "2026-10-15",
            },
        },
        "Decision helper output changed",
    )
    checks += 1

    require("不应假设" in text and "本地 schema 与业务校验" in text, "Application-side validation boundary is missing")
    checks += 1

    retry_text = RETRY_LESSON.read_text(encoding="utf-8")
    business_text = BUSINESS_LESSON.read_text(encoding="utf-8")
    require("只是未复核的历史摘要，不能据此估计模型编造率" in retry_text, "Retry lesson still generalizes the unarchived required-field result")
    require("format` 是否执行验证取决于所用校验器及配置" in business_text, "Business-rules lesson still presents provider history as a current format rule")
    require("JSON Schema 表达不了 `end >= start`" not in business_text, "Cross-field rule wording is still absolute")
    checks += 1

    retry_text = RETRY_LESSON.read_text(encoding="utf-8")
    retry_blocks = python_fences(retry_text)
    require(len(retry_blocks) == 2, f"Expected two retry-example Python fences, found {len(retry_blocks)}")
    api_example, degrade_example = retry_blocks
    require('"type": "tool_result"' in api_example and '"tool_use_id"' in api_example, "Validation feedback does not close the Messages API tool-use turn")
    require('"is_error": True' in api_example, "Validation rejection is not represented as a tool error result")
    require("attempts = 1 if first_ok else 3" not in degrade_example, "Degradation metrics infer rather than count actual attempts")
    require('"raw_input": ask' not in degrade_example, "Human-queue payload embeds raw input without a secure reference")
    require('"split_retry"' in degrade_example, "The split-retry fallback described in prose is not implemented")
    require("2026-10-08" in retry_text and "不能证明各组首轮都按设计失败" in retry_text, "Historical retry rates are not bounded to their missing evidence")
    checks += 1

    api_ns: dict[str, object] = {"__name__": "lesson"}
    exec(api_example, api_ns)
    class FakeMessages:
        def __init__(self, responses):
            self.responses = list(responses)
            self.calls = []

        def create(self, **kwargs):
            self.calls.append(kwargs)
            return self.responses.pop(0)

    invalid = SimpleNamespace(
        type="tool_use", id="call-1", name="save_refund",
        input={"amount": 1234, "reason": "private-marker"},
    )
    valid = SimpleNamespace(
        type="tool_use", id="call-2", name="save_refund",
        input={"amount": 1200, "reason": "报销"},
    )
    fake_messages = FakeMessages([
        SimpleNamespace(stop_reason="tool_use", content=[invalid]),
        SimpleNamespace(stop_reason="tool_use", content=[valid]),
    ])
    outcome = api_ns["extract_refund"](
        SimpleNamespace(messages=fake_messages), "fake-model", "输入", {}
    )
    require(outcome["attempts"] == 2 and not outcome["first_round_ok"], "Retry example does not return the actual attempt count")
    require(outcome["result"].amount == 1200 and outcome["error_type"] is None, "Retry example failed to accept a corrected local result")
    feedback_turn = fake_messages.calls[1]["messages"][-1]["content"][0]
    feedback = json.loads(feedback_turn["content"])
    require(feedback_turn["type"] == "tool_result" and feedback_turn["tool_use_id"] == "call-1" and feedback_turn["is_error"] is True, "Retry transcript does not pair validation error with the matching tool_use")
    require("private-marker" not in feedback_turn["content"] and "input" not in feedback["issues"][0], "Retry feedback leaks the rejected raw value")
    checks += 1

    refused_messages = FakeMessages([SimpleNamespace(stop_reason="refusal", content=[])])
    refused = api_ns["extract_refund"](
        SimpleNamespace(messages=refused_messages), "fake-model", "输入", {}
    )
    require(refused["error_type"] == "refusal" and refused["attempts"] == 1 and len(refused_messages.calls) == 1, "Refusal was blindly retried as a schema error")
    truncated_messages = FakeMessages([SimpleNamespace(stop_reason="max_tokens", content=[])])
    truncated = api_ns["extract_refund"](
        SimpleNamespace(messages=truncated_messages), "fake-model", "输入", {}
    )
    require(truncated["error_type"] == "truncated", "Token truncation was not separated from validation failure")
    checks += 1

    degrade_ns: dict[str, object] = {"__name__": "lesson"}
    exec(degrade_example, degrade_ns)
    degrade_run = subprocess.run(
        [sys.executable, "-c", degrade_example],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
        check=True,
    )
    expected_degrade = "\n".join([
        '[metric] {"request_id": "req_demo", "attempts": 2, "first_round_ok": false, "error_type": null, "action": "validated"}',
        '两轮内修正 {"attempts": 2, "first_round_ok": false, "error_type": null, "action": "validated", "payload_fields": ["amount", "reason"]}',
        '[metric] {"request_id": "req_demo", "attempts": 3, "first_round_ok": false, "error_type": "business_rule", "action": "human_queue"}',
        '重试耗尽转人工 {"attempts": 3, "first_round_ok": false, "error_type": "business_rule", "action": "human_queue", "payload_fields": ["case_ref", "last_report"]}',
        '[metric] {"request_id": "req_demo", "attempts": 3, "first_round_ok": false, "error_type": "business_rule", "action": "conservative_default"}',
        '不确定默认值 {"attempts": 3, "first_round_ok": false, "error_type": "business_rule", "action": "conservative_default", "payload_fields": ["is_uncertain", "value"]}',
        '[metric] {"request_id": "req_demo", "attempts": 3, "first_round_ok": false, "error_type": "business_rule", "action": "split_retry"}',
        '字段拆分计划 {"attempts": 3, "first_round_ok": false, "error_type": "business_rule", "action": "split_retry", "payload_fields": ["case_ref", "fields", "remaining_attempts"]}',
    ])
    require(degrade_run.stdout.strip() == expected_degrade, "Degradation example output differs from the reviewed result")
    require(expected_degrade in retry_text, "Published degradation output differs from the local Fake-client stdout")
    require("仅供测试的输入" not in degrade_run.stdout, "Metrics output includes raw input")
    run_degrade = degrade_ns["run"]
    failed = lambda _ask: {
        "result": None, "attempts": 3, "first_round_ok": False,
        "error_type": "business_rule",
        "last_report": [{"type": "business_rule", "field": "amount", "message": "金额无效"}],
    }
    with contextlib.redirect_stdout(io.StringIO()):
        human = run_degrade("private-marker", failed, request_id="r1", fallback_policy="human_queue", case_ref="case-1")
        conservative = run_degrade("private-marker", failed, request_id="r2", fallback_policy="conservative_default", default_value=None)
        split = run_degrade("private-marker", failed, request_id="r3", fallback_policy="split_retry", case_ref="case-2", split_fields=("amount",), remaining_attempts=1)
    require(human["payload"]["case_ref"] == "case-1" and "private-marker" not in str(human["payload"]), "Human queue does not use the protected case reference")
    require(conservative["payload"] == {"value": None, "is_uncertain": True}, "Conservative fallback is not explicit and marked uncertain")
    require(split["payload"]["fields"] == ["amount"] and split["payload"]["remaining_attempts"] == 1, "Split retry plan does not preserve the remaining budget")
    checks += 2

    print(f"PASS: {checks} checks; Python fences=2; pydanticVersion=2.9.2; providerRequests=0; externalNetworkCalls=0")


if __name__ == "__main__":
    main()
