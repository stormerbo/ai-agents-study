"""Offline audit of scope, history labels, and code boundaries in the lesson."""
from __future__ import annotations

import ast
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/agent-security/02-tools-as-untrusted-input.mdx"
META = ROOT / "src/content/chapters/agent-security/meta.ts"


def python_fences(text: str) -> list[str]:
    return [m.group(2) for m in re.finditer(r"^(```|~~~)python\s*\n(.*?)^\1\s*$", text, re.M | re.S)]


class UntrustedInputLessonReview(unittest.TestCase):
    def test_python_fences_compile(self):
        body = LESSON.read_text()
        fences = python_fences(body)
        self.assertEqual(len(fences), 1)
        for index, source in enumerate(fences):
            compile(ast.parse(source), f"{LESSON.name}:python-fence-{index}", "exec")

    def test_indirect_injection_not_agent_exclusive(self):
        body = LESSON.read_text()
        self.assertIn("这类风险并非 agent 独有", body)
        self.assertNotIn("agent 独有的一类", body)
        self.assertIn("普通 RAG/LLM 应用也可能遇到", body)

    def test_historical_provider_results_are_not_claimed_as_verified(self):
        body = LESSON.read_text()
        self.assertIn("不能独立验证其逐字准确性", body)
        self.assertIn("不能据此当成稳定的模型行为", body)
        self.assertIn("没有独立重跑", body)
        self.assertIn("不构成安全保证", body)

    def test_controls_are_presented_as_scoped_not_guaranteed(self):
        body = LESSON.read_text()
        self.assertIn("不是 API 级信任标志或不可绕过的边界", body)
        self.assertIn("不能单凭命中判断恶意", body)
        self.assertIn("字符串规则无法穷举开放文本", body)
        self.assertIn("不能写成“模型改变不了规则”的绝对保证", body)
        self.assertIn("受访问控制保护的原始记录", body)

    def test_tool_sinks_are_described_as_local_mocks_and_sources_linked(self):
        body = LESSON.read_text()
        metadata = META.read_text()
        self.assertIn("不产生真实副作用", body)
        self.assertIn("不实现授权、审批或参数白名单", body)
        self.assertIn("anthropic-handle-tool-calls", metadata)
        self.assertIn("owasp-llm-prompt-injection", metadata)

    def test_agent_loop_executes_requested_tool_without_policy_gate(self):
        source = python_fences(LESSON.read_text())[0]
        namespace = {"__name__": "lesson_offline_test"}
        exec(compile(ast.parse(source), "lesson-python-fence", "exec"), namespace)
        responses = iter([
            {"stop_reason": "tool_use", "content": [{"type": "tool_use", "id": "tu-test", "name": "delete_all", "input": {}}]},
            {"stop_reason": "end_turn", "content": [{"type": "text", "text": "finished"}]},
        ])
        namespace["call"] = lambda messages, tools, max_tokens=3000: next(responses)
        calls, text = namespace["run"]("synthetic task", namespace["TOOLS"])
        self.assertEqual(calls, [("delete_all", {})])
        self.assertEqual(text, "finished")
        self.assertEqual(namespace["delete_all"](), {"deleted": 9999})


if __name__ == "__main__":
    unittest.main(verbosity=2)
