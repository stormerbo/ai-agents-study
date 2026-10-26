"""Focused whole-lesson checks for the ReAct control-flow example."""
from __future__ import annotations

import contextlib
import io
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/agent-paradigms/02-react-loop.mdx"


def complete_example() -> tuple[str, str]:
    text = LESSON.read_text()
    section = text.split("## 完整可运行代码", 1)[1].split("## 常见坑", 1)[0]
    code = re.search(r"^```python\s*\n(.*?)^```\s*$", section, re.M | re.S)
    output = re.search(r"^```text\s*\n(.*?)^```\s*$", section, re.M | re.S)
    if code is None or output is None:
        raise AssertionError("complete example must have Python and adjacent text-output fences")
    return code.group(1), output.group(1).rstrip("\n")


class ReactLoopW6Tests(unittest.TestCase):
    def test_example_is_offline_and_covers_host_owned_limits(self):
        source, _ = complete_example()
        compile(source, str(LESSON), "exec")
        for forbidden in ("ANTHROPIC_AUTH_TOKEN", "urllib.request", "ANTHROPIC_BASE_URL"):
            self.assertNotIn(forbidden, source)
        for required in ("def run_react(", "max_tool_calls", "completed_without_text", "repeated_action", "invalid_tool_batch"):
            self.assertIn(required, source)
        self.assertNotIn('status = "completed" if answer', source)
        self.assertIn('{"role": "assistant", "content": blocks}', source)

    def test_published_output_matches_full_offline_run(self):
        source, expected = complete_example()
        namespace = {"__name__": "lesson_fixture"}
        exec(compile(source, str(LESSON), "exec"), namespace)
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            namespace["main"]()
        self.assertEqual(output.getvalue().rstrip("\n"), expected)

    def test_repeated_action_is_blocked_before_second_dispatch(self):
        source, _ = complete_example()
        namespace = {"__name__": "lesson_fixture"}
        exec(compile(source, str(LESSON), "exec"), namespace)
        def repeated(_history):
            return {"stop_reason": "tool_use", "content": [{
                "type": "tool_use", "id": "call-1", "name": "get_weather",
                "input": {"city": "北京", "day": "明天"},
            }]}
        dispatched: list[dict] = []
        result = namespace["run_react"](repeated, max_turns=5, max_tool_calls=5, dispatch_log=dispatched)
        self.assertEqual(result["status"], "repeated_action")
        self.assertEqual(result["tool_calls"], 1)
        self.assertEqual(len(dispatched), 1)

    def test_invalid_tool_batch_is_rejected_before_any_dispatch(self):
        source, _ = complete_example()
        namespace = {"__name__": "lesson_fixture"}
        exec(compile(source, str(LESSON), "exec"), namespace)
        def duplicate_ids(_history):
            return {"stop_reason": "tool_use", "content": [
                {"type": "tool_use", "id": "dup", "name": "get_weather", "input": {"city": "北京", "day": "明天"}},
                {"type": "tool_use", "id": "dup", "name": "get_weather", "input": {"city": "上海", "day": "明天"}},
            ]}
        dispatched: list[dict] = []
        result = namespace["run_react"](duplicate_ids, max_turns=5, max_tool_calls=5, dispatch_log=dispatched)
        self.assertEqual(result["status"], "invalid_tool_batch")
        self.assertEqual(dispatched, [])


    def test_empty_end_turn_is_not_reported_as_task_success(self):
        source, _ = complete_example()
        namespace = {"__name__": "lesson_fixture"}
        exec(compile(source, str(LESSON), "exec"), namespace)
        result = namespace["run_react"](
            lambda _history: {"stop_reason": "end_turn", "content": []},
            max_turns=1,
            max_tool_calls=1,
        )
        self.assertEqual(result["status"], "completed_without_text")

    def test_tool_budget_rejects_whole_batch_before_dispatch(self):
        source, _ = complete_example()
        namespace = {"__name__": "lesson_fixture"}
        exec(compile(source, str(LESSON), "exec"), namespace)
        response = {"stop_reason": "tool_use", "content": [
            {"type": "tool_use", "id": "a", "name": "get_weather", "input": {"city": "北京", "day": "明天"}},
            {"type": "tool_use", "id": "b", "name": "get_weather", "input": {"city": "上海", "day": "明天"}},
        ]}
        dispatched: list[dict] = []
        result = namespace["run_react"](
            lambda _history: response,
            max_turns=1,
            max_tool_calls=1,
            dispatch_log=dispatched,
        )
        self.assertEqual(result["status"], "tool_budget_exhausted")
        self.assertEqual(dispatched, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
