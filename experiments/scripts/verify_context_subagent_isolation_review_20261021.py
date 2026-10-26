"""Offline contract checks for the subagent isolation lesson. No provider calls."""
from __future__ import annotations

import ast
import os
import sys
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/context-engineering/05-subagent-isolation.mdx"
source = LESSON.read_text()
fences = [body for lang, body in __import__("re").findall(r"^```([^\n]*)\n([\s\S]*?)^```\s*$", source, __import__("re").M)]
python_fences = [body for body in fences if body.startswith("# subagent_cost.py")]
if len(python_fences) != 1:
    raise SystemExit(f"expected one complete sample fence, got {len(python_fences)}")
code = python_fences[0]
compile(code, str(LESSON), "exec")

class FakeBlock:
    def __init__(self, kind, **kwargs):
        self.type = kind
        self.__dict__.update(kwargs)

class FakeResponse:
    def __init__(self, stop_reason, content=(), usage=None):
        self.stop_reason = stop_reason
        self.content = list(content)
        self.usage = types.SimpleNamespace(
            input_tokens=10, cache_read_input_tokens=2,
            cache_creation_input_tokens=3, output_tokens=5,
        ) if usage is None else usage

class FakeMessages:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = 0
    def create(self, **_kwargs):
        self.calls += 1
        if not self.responses:
            raise AssertionError("unexpected provider call")
        return self.responses.pop(0)

class FakeClient:
    def __init__(self, responses):
        self.messages = FakeMessages(responses)

checks = 0
def check(condition, label):
    global checks
    checks += 1
    if not condition:
        raise AssertionError(label)

def tool_call(item_id="ITEM-01", name="check_item", args=None):
    return FakeBlock("tool_use", id="tool-1", name=name,
                     input={"item_id": item_id} if args is None else args)

def text_block(text):
    return FakeBlock("text", text=text)

def runtime(responses, auth_token_mode=False):
    fake_anthropic = types.ModuleType("anthropic")
    client_options = {}
    def make_client(**kwargs):
        client_options.update(kwargs)
        return FakeClient([])
    fake_anthropic.Anthropic = make_client
    old = sys.modules.get("anthropic")
    sys.modules["anthropic"] = fake_anthropic
    env_keys = ("VERIFY_MODEL", "MAX_OUTPUT_TOKENS", "ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN")
    old_env = {key: os.environ.get(key) for key in env_keys}
    os.environ["VERIFY_MODEL"] = "fixture"
    os.environ["MAX_OUTPUT_TOKENS"] = "64"
    if auth_token_mode:
        os.environ.pop("ANTHROPIC_API_KEY", None)
        os.environ["ANTHROPIC_AUTH_TOKEN"] = "synthetic-fixture-token"
    else:
        os.environ["ANTHROPIC_API_KEY"] = "synthetic-fixture-key"
        os.environ.pop("ANTHROPIC_AUTH_TOKEN", None)
    namespace = {"__name__": "offline_audit"}
    exec(compile(code, str(LESSON), "exec"), namespace)
    namespace["client"] = FakeClient(responses)
    namespace["_test_client_options"] = client_options
    for key, value in old_env.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value
    if old is None:
        sys.modules.pop("anthropic", None)
    else:
        sys.modules["anthropic"] = old
    return namespace

class SubagentContractTests(unittest.TestCase):
    def test_lesson_scopes_historical_evidence_and_security_boundary(self):
        check("不能据此判断两条路线质量相同或普遍更便宜" in source, "historical comparison is not generalized")
        check("无法确认是不是 thinking 消耗了预算" in source, "max_tokens causality is qualified")
        check("生产工具必须在每次读取时按可信调用身份、租户和对象权限检查" in source, "authorization stays host-enforced")
        check("不代表账单或质量" in source, "sample is scoped to token volume")

    def test_usage_and_success_path(self):
        ns = runtime([
            FakeResponse("tool_use", [tool_call()]),
            FakeResponse("end_turn", [text_block("ready")]),
            FakeResponse("end_turn", [text_block('{"did":[{"item_id":"ITEM-01","finding":"missing timeout"}]}')]),
        ])
        check(ns["total_tokens"](FakeResponse("end_turn")) == 20, "Anthropic usage sum")
        result, used = ns["run_subagent"]("check", "rules", {"ITEM-01"})
        check(result["status"] == "complete", "successful task status")
        check(result["did"][0]["item_id"] == "ITEM-01", "finding bound to checked item")
        check(result["pending"] == [], "successful task has no pending id")
        check(used == 60, "all three Anthropic responses counted")
        check(ns["_test_client_options"]["api_key"] == "synthetic-fixture-key", "API key uses api_key")
        ns = runtime([], auth_token_mode=True)
        check(ns["_test_client_options"]["auth_token"] == "synthetic-fixture-token", "bearer token uses auth_token")
        check(ns["_test_client_options"]["api_key"] is None, "bearer token is not sent as API key")

    def test_invalid_tool_is_host_failure(self):
        ns = runtime([
            FakeResponse("tool_use", [tool_call(name="delete_everything")]),
            FakeResponse("end_turn", [text_block("ready")]),
            FakeResponse("end_turn", [text_block('{"did":[]}')]),
        ])
        result, _ = ns["run_subagent"]("check", "rules", {"ITEM-01"})
        check(result["status"] == "partial", "invalid tool cannot complete task")
        check(any(item.startswith("invalid_tool_request:") for item in result["failed"]), "host records invalid tool")
        check(result["pending"] == ["ITEM-01"], "invalid tool leaves expected id pending")

    def test_incomplete_and_exhausted_loops_fail_closed(self):
        ns = runtime([FakeResponse("max_tokens", [text_block("")])])
        result, _ = ns["run_subagent"]("check", "rules", {"ITEM-01"})
        check(result["status"] == "incomplete", "max_tokens is incomplete")
        check(result["pending"] == ["ITEM-01"], "truncated run leaves task pending")
        ns = runtime([FakeResponse("tool_use", [tool_call()]) for _ in range(4)])
        result, _ = ns["run_subagent"]("check", "rules", {"ITEM-01"})
        check(result["status"] == "incomplete", "round limit is incomplete")
        check(ns["client"].messages.calls == 4, "round limit is enforced")

    def test_schema_and_stop_reason_fail_closed(self):
        ns = runtime([
            FakeResponse("tool_use", [tool_call(args={"item_id": "ITEM-01", "extra": True})]),
            FakeResponse("end_turn", [text_block("ready")]),
            FakeResponse("end_turn", [text_block('{"did":[]}')]),
        ])
        result, _ = ns["run_subagent"]("check", "rules", {"ITEM-01"})
        check(any(item.startswith("invalid_tool_request:") for item in result["failed"]), "extra tool args rejected")
        ns = runtime([
            FakeResponse("tool_use", [tool_call()]),
            FakeResponse("end_turn", [text_block("ready")]),
            FakeResponse("end_turn", [text_block('{"did":[{"item_id":"ITEM-01","finding":"  "}]}')]),
        ])
        result, _ = ns["run_subagent"]("check", "rules", {"ITEM-01"})
        check("unparseable_summary" in result["failed"], "empty finding rejected")
        check(result["status"] == "partial", "empty finding cannot complete task")
        ns = runtime([FakeResponse("refusal", [text_block("no")])])
        result, _ = ns["run_subagent"]("check", "rules", {"ITEM-01"})
        check(result["status"] == "incomplete", "refusal is not a completed task")
        ns = runtime([FakeResponse("max_tokens", [text_block("partial")])])
        try:
            ns["call"]("system", "user")
        except RuntimeError:
            check(True, "single call requires a complete response")
        else:
            check(False, "single call requires a complete response")

    def test_bad_summary_and_not_found_are_not_success(self):
        ns = runtime([
            FakeResponse("tool_use", [tool_call(item_id="ITEM-99")]),
            FakeResponse("end_turn", [text_block("ready")]),
            FakeResponse("end_turn", [text_block("not json")]),
        ])
        result, _ = ns["run_subagent"]("check", "rules", {"ITEM-99"})
        check(result["status"] == "partial", "malformed summary is partial")
        check("unparseable_summary" in result["failed"], "malformed summary recorded")
        check(result["not_found"] == ["ITEM-99"], "host owns not_found classification")

if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(SubagentContractTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)
    print(f"offline assertions passed: {checks}")
