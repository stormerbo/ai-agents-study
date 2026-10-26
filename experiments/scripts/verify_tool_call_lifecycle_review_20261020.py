from __future__ import annotations

import copy
import json
import os
import re
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
lesson_path = ROOT / "src/content/chapters/tool-calling/01-what-really-happens.mdx"
lesson = lesson_path.read_text(encoding="utf-8")
meta = (ROOT / "src/content/chapters/tool-calling/meta.ts").read_text(encoding="utf-8")
tick = chr(96) * 3
fences = re.findall(rf"^{tick}python\n([\s\S]*?)^{tick}\s*$", lesson, flags=re.MULTILINE)
main = next((f for f in fences if "def run(question:" in f), None)
checks: dict[str, bool] = {
    "lesson no longer claims all tools execute in the user's process":
        "平台托管的 server tool" in lesson and "本节只讲 Anthropic Messages API" in lesson,
    "stop reasons distinguish complete from truncated/refused/unsupported":
        "max_tokens" in lesson and "model_context_window_exceeded" in lesson and "只有 end_turn 才按完整答案返回" in lesson,
    "protocol pairing is not presented as execution/auth proof":
        "不证明宿主真的执行了工具" in lesson and "不是授权凭证或执行证明" in lesson,
    "tool outputs retain provenance and are treated as untrusted":
        "tool_result" in lesson and "prompt injection" in lesson and "不可信数据" in lesson,
    "historical missing-argument sample is not generalized":
        "不能估计“硬编参数”的频率" in lesson and "Opus 更可能追问" in lesson,
    "checkpoints cite current official references":
        all(x in meta for x in ("anthropic-stop-reasons", "anthropic-handle-tool-calls", "owasp-llm-prompt-injection")),
    "lesson Python fence compiles":
        len(fences) == 1 and main is not None,
}

class FakeMessages:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(copy.deepcopy(kwargs))
        return self.responses.pop(0)

def block(kind, **kwargs):
    return types.SimpleNamespace(type=kind, **kwargs)

def response(reason, content):
    return types.SimpleNamespace(stop_reason=reason, content=content)

def run_with(responses, prepare=None):
    api = FakeMessages(responses)
    sdk = types.ModuleType("anthropic")
    sdk.Anthropic = lambda **kwargs: types.SimpleNamespace(messages=api)
    previous = sys.modules.get("anthropic")
    sys.modules["anthropic"] = sdk
    previous_model = os.environ.get("VERIFY_MODEL")
    os.environ["VERIFY_MODEL"] = "offline-test-model"
    try:
        namespace = {"__name__": "lesson_offline_test"}
        exec(compile(main, str(lesson_path), "exec"), namespace)
        if prepare is not None:
            prepare(namespace)
        return namespace, api, namespace["run"]("test request")
    finally:
        if previous is None:
            sys.modules.pop("anthropic", None)
        else:
            sys.modules["anthropic"] = previous
        if previous_model is None:
            os.environ.pop("VERIFY_MODEL", None)
        else:
            os.environ["VERIFY_MODEL"] = previous_model

try:
    for index, fence in enumerate(fences, start=1):
        compile(fence, f"{lesson_path}:fence-{index}", "exec")

    _, api, result = run_with([response("end_turn", [block("text", text="done")])])
    checks["end_turn returns the final text"] = result == "done" and len(api.calls) == 1

    _, api, result = run_with([response("end_turn", [])])
    checks["empty end_turn is not exposed as a successful empty answer"] = result.startswith("已结束，但没有可展示的文本")
    checks["empty end_turn is not retried blindly"] = len(api.calls) == 1

    _, _, result = run_with([response("max_tokens", [block("text", text="partial")])])
    checks["max_tokens is never returned as a complete answer"] = result.startswith("未完成：")

    _, _, result = run_with([response("refusal", [block("text", text="no")])])
    checks["refusal does not execute a tool"] = result.startswith("模型拒绝")

    _, _, result = run_with([response("pause_turn", [])])
    checks["unsupported stop reasons fail closed"] = result.startswith("未完成：")

    call = block("tool_use", id="toolu-1", name="get_exchange_rate", input={"from": "USD", "to": "CNY"})
    _, api, result = run_with([
        response("tool_use", [call]),
        response("end_turn", [block("text", text="rate returned")]),
    ])
    sent = api.calls[1]["messages"][-1]["content"][0]
    checks["valid client tool gets called and its result is paired by the original id"] = (
        result == "rate returned" and sent["tool_use_id"] == "toolu-1"
        and json.loads(sent["content"])["rate"] == 7.23
    )

    bad = block("tool_use", id="toolu-bad", name="get_exchange_rate", input={"from": "USD", "to": 7, "secret": "do-not-echo"})
    _, api, _ = run_with([response("tool_use", [bad]), response("end_turn", [block("text", text="done")])])
    sent = api.calls[1]["messages"][-1]["content"][0]
    checks["invalid tool inputs are rejected before function dispatch"] = (
        sent["is_error"] is True and json.loads(sent["content"]) == {"error": "invalid_arguments"}
    )

    for label, calls in (
        ("missing", [block("tool_use", id="", name="get_exchange_rate", input={"from": "USD", "to": "CNY"})]),
        ("duplicate", [
            block("tool_use", id="same-id", name="get_exchange_rate", input={"from": "USD", "to": "CNY"}),
            block("tool_use", id="same-id", name="get_exchange_rate", input={"from": "USD", "to": "CNY"}),
        ]),
    ):
        executed = []
        def track_dispatch(namespace):
            namespace["IMPL"]["get_exchange_rate"] = lambda **kwargs: executed.append(kwargs) or {"rate": 7.23}
        _, api, result = run_with([response("tool_use", calls)], prepare=track_dispatch)
        checks[f"{label} tool-use ids fail closed before dispatch"] = (
            result.startswith("未完成：tool_use") and len(api.calls) == 1 and executed == []
        )

    unknown = block("tool_use", id="toolu-unknown", name="delete_everything", input={})
    _, api, _ = run_with([response("tool_use", [unknown]), response("end_turn", [block("text", text="done")])])
    sent = api.calls[1]["messages"][-1]["content"][0]
    checks["unknown tool names produce a sanitized error result"] = json.loads(sent["content"]) == {"error": "unknown_tool"}

    call = block("tool_use", id="toolu-fail", name="get_exchange_rate", input={"from": "USD", "to": "CNY"})
    namespace, api, _ = run_with([response("tool_use", [call]), response("end_turn", [block("text", text="done")])])
    namespace["IMPL"]["get_exchange_rate"] = lambda **kwargs: (_ for _ in ()).throw(RuntimeError("private-key-secret"))
    # Run again with a fresh module whose fake client supplies the same responses.
    api_responses = [response("tool_use", [call]), response("end_turn", [block("text", text="done")])]
    sdk = types.ModuleType("anthropic")
    fake_api = FakeMessages(api_responses)
    sdk.Anthropic = lambda **kwargs: types.SimpleNamespace(messages=fake_api)
    sys.modules["anthropic"] = sdk
    namespace["client"] = types.SimpleNamespace(messages=fake_api)
    namespace["run"]("test request")
    sent = fake_api.calls[1]["messages"][-1]["content"][0]
    checks["tool exceptions never expose exception text to the model"] = (
        json.loads(sent["content"]) == {"error": "tool_execution_failed"}
        and "private-key-secret" not in sent["content"]
    )
finally:
    sys.modules.pop("anthropic", None)

for name, passed in checks.items():
    print(("PASS" if passed else "FAIL") + ": " + name)

if not all(checks.values()):
    sys.exit(1)
