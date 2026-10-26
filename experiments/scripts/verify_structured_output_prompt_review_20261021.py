"""Offline review checks for structured-output/why-not-prompt-only."""
from __future__ import annotations

import contextlib
import io
import math
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/structured-output/01-why-not-prompt-only.mdx"


class PromptOnlyReview(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = LESSON.read_text(encoding="utf-8")
        cls.python_blocks = re.findall(r"^```python\s*\n([\s\S]*?)^```\s*$", cls.text, re.M)

    def test_historical_provider_data_is_not_presented_as_reproduced(self):
        self.assertIn("原始数据没有保存在当前工作树里", self.text)
        self.assertIn("无法独立复核", self.text)
        self.assertNotIn("提示式 JSON 稳得出乎意料", self.text)

    def test_provider_current_tool_docs_are_linked_and_scoped(self):
        self.assertIn("https://api-docs.deepseek.com/guides/tool_calls/", self.text)
        self.assertIn("V3.2 起支持 thinking mode 下的 tool use", self.text)
        self.assertIn("不能视为当前模型的兼容性结论", self.text)

    def test_parser_does_not_echo_untrusted_output_in_errors(self):
        source = self.python_blocks[0]
        self.assertIn('raise ValueError("输出里找不到可解析的 JSON")', source)
        self.assertNotIn("+ text[:120]", source)
        namespace = {"__name__": "review_fixture"}
        exec(compile(source, "lesson-parser", "exec"), namespace)
        marker = "PRIVATE_FIXTURE_MARKER"
        with self.assertRaises(ValueError) as caught:
            namespace["extract_json"](marker)
        self.assertNotIn(marker, str(caught.exception))

    def test_parser_fences_compile_and_documented_examples_run(self):
        self.assertEqual(len(self.python_blocks), 2)
        namespaces = []
        for index, source in enumerate(self.python_blocks):
            code = compile(source, f"lesson-python-{index}", "exec")
            namespace = {"__name__": "review_fixture"}
            exec(code, namespace)
            namespaces.append(namespace)
        extract_json = namespaces[0]["extract_json"]
        self.assertEqual(extract_json('[{"a": 1}, {"a": 2}]')[0], [{"a": 1}, {"a": 2}])
        self.assertEqual(extract_json('说明：{"a": 1}')[1], "sliced")
        classify = namespaces[1]["classify"]
        expected = {
            "end_turn": "最终响应：可以尝试解析",
            "max_tokens": "截断：未完成",
            "tool_use": "工具交接：不是最终 JSON",
            "stop_sequence": "停止串结束：需按任务契约判断是否完整",
            "refusal": "拒绝：不是正常 JSON 响应",
            "pause_turn": "服务端工具循环暂停：按 API 契约继续",
            "model_context_window_exceeded": "上下文窗口耗尽：未完成",
        }
        for reason, result in expected.items():
            self.assertEqual(classify(type("Response", (), {"stop_reason": reason})()), result)

    def test_each_python_fence_stdout_matches_the_following_text_fence(self):
        fences = re.findall(r"^```([^\n]*)\n([\s\S]*?)^```\s*$", self.text, re.M)
        for index, (language, source) in enumerate(fences[:-1]):
            if language != "python":
                continue
            next_language, expected = fences[index + 1]
            self.assertEqual(next_language, "text")
            output = io.StringIO()
            namespace = {"__name__": "__main__"}
            with contextlib.redirect_stdout(output):
                exec(compile(source, f"lesson-output-{index}", "exec"), namespace)
            self.assertEqual(output.getvalue(), expected)

    def test_output_token_limits_are_provider_specific(self):
        self.assertIn("Anthropic Messages", self.text)
        self.assertIn("OpenAI Chat Completions", self.text)
        self.assertIn("max_completion_tokens", self.text)
        self.assertIn("max_output_tokens", self.text)
        self.assertIn("不可见的推理 token 也计入上限", self.text)
        self.assertIn("https://platform.claude.com/docs/en/api/messages/create", self.text)
        self.assertIn("https://platform.openai.com/docs/api-reference/chat/object", self.text)
        self.assertIn("https://developers.openai.com/api/reference/resources/responses/methods/create", self.text)

    def test_chain_probability_and_zero_failure_bound_match_stated_assumptions(self):
        self.assertAlmostEqual(0.99**10, 0.9043820750088044)
        self.assertAlmostEqual(0.99**100, 0.3660323412732292)
        self.assertAlmostEqual(0.999**100, 0.904792147113709, places=12)
        self.assertAlmostEqual(1 - 0.05 ** (1 / 30), 0.09503385285530419)

    def test_endpoint_state_semantics_and_local_gate_are_distinguished(self):
        self.assertIn("tool_use` 也表示一次工具交接", self.text)
        self.assertIn("端到端交付率必须把未完成纳入", self.text)
        self.assertIn("所有副作用入口都强制经过该门禁", self.text)
        self.assertIn("它仍不证明内容真实或业务动作获准", self.text)


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(PromptOnlyReview)
    )
    print(
        "providerCalls=0; externalNetworkCalls=0; "
        f"tests={result.testsRun}; failures={len(result.failures) + len(result.errors)}"
    )
    raise SystemExit(not result.wasSuccessful())
