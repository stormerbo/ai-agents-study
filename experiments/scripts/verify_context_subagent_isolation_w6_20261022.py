"""W6 regression for malformed Anthropic tool-use ids; no provider calls."""
from __future__ import annotations

import os
import re
import sys
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/context-engineering/05-subagent-isolation.mdx"
source = LESSON.read_text()
matches = re.findall(r"^```python\s*\n(# subagent_cost\.py[\s\S]*?)^```\s*$", source, re.M)
if len(matches) != 1:
    raise SystemExit(f"expected one complete Python sample, found {len(matches)}")
code = matches[0]
compile(code, str(LESSON), "exec")


class Block:
    def __init__(self, kind, **kwargs):
        self.type = kind
        self.__dict__.update(kwargs)


class Response:
    def __init__(self, stop_reason, content=()):
        self.stop_reason = stop_reason
        self.content = list(content)
        self.usage = types.SimpleNamespace(
            input_tokens=1,
            output_tokens=1,
            cache_read_input_tokens=0,
            cache_creation_input_tokens=0,
        )


class Messages:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = 0

    def create(self, **_kwargs):
        self.calls += 1
        return self.responses.pop(0)


def tool_call(item_id, tool_id):
    return Block("tool_use", id=tool_id, name="check_item", input={"item_id": item_id})


def run_with_tool_batch(blocks):
    fake_anthropic = types.ModuleType("anthropic")
    fake_anthropic.Anthropic = lambda **_kwargs: types.SimpleNamespace(messages=Messages([]))
    old_module = sys.modules.get("anthropic")
    sys.modules["anthropic"] = fake_anthropic
    keys = ("VERIFY_MODEL", "ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN")
    old_env = {key: os.environ.get(key) for key in keys}
    os.environ["VERIFY_MODEL"] = "fixture"
    os.environ["ANTHROPIC_API_KEY"] = "synthetic-fixture-key"
    os.environ.pop("ANTHROPIC_AUTH_TOKEN", None)
    namespace = {"__name__": "w6_fixture"}
    try:
        exec(compile(code, str(LESSON), "exec"), namespace)
    finally:
        for key, value in old_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        if old_module is None:
            sys.modules.pop("anthropic", None)
        else:
            sys.modules["anthropic"] = old_module

    messages = Messages([
        Response("tool_use", blocks),
        Response("end_turn", [Block("text", text="done")]),
        Response("end_turn", [Block("text", text='{"did": []}')]),
    ])
    namespace["client"].messages = messages
    dispatches = []
    namespace["check_item"] = lambda item_id: (dispatches.append(item_id) or ({"code": "fixture", "rules": []}, False))
    result, _ = namespace["run_subagent"]("check", "rules", {"ITEM-01", "ITEM-02"})
    return namespace, result, messages.calls, dispatches


class MalformedToolUseIdTests(unittest.TestCase):
    def test_duplicate_ids_reject_batch_before_dispatch(self):
        namespace, result, calls, dispatches = run_with_tool_batch([
            tool_call("ITEM-01", "tool-duplicate"),
            tool_call("ITEM-02", "tool-duplicate"),
        ])
        self.assertEqual(dispatches, [], "no tool may run when response ids are ambiguous")
        self.assertEqual(calls, 1, "an invalid tool batch must stop before another model request")
        self.assertEqual(result["status"], "incomplete")
        self.assertEqual(result["pending"], ["ITEM-01", "ITEM-02"])
        self.assertIn("invalid_tool_use_ids", result["failed"])

    def test_missing_id_rejects_batch_before_dispatch(self):
        namespace, result, calls, dispatches = run_with_tool_batch([tool_call("ITEM-01", None)])
        self.assertEqual(dispatches, [], "no tool may run without a correlation id")
        self.assertEqual(calls, 1)
        self.assertEqual(result["status"], "incomplete")
        self.assertIn("invalid_tool_use_ids", result["failed"])

    def test_usage_counts_reject_boolean_and_negative_values(self):
        namespace, _result, _calls, _dispatches = run_with_tool_batch([])
        valid = types.SimpleNamespace(
            input_tokens=2,
            output_tokens=3,
            cache_read_input_tokens=5,
            cache_creation_input_tokens=7,
        )
        self.assertEqual(namespace["total_tokens"](types.SimpleNamespace(usage=valid)), 17)
        for field, value in (
            ("input_tokens", True),
            ("output_tokens", -1),
            ("cache_read_input_tokens", False),
            ("cache_creation_input_tokens", -1),
        ):
            usage = types.SimpleNamespace(**vars(valid))
            setattr(usage, field, value)
            with self.subTest(field=field, value=value):
                with self.assertRaises(RuntimeError):
                    namespace["total_tokens"](types.SimpleNamespace(usage=usage))


if __name__ == "__main__":
    unittest.main(verbosity=2)
