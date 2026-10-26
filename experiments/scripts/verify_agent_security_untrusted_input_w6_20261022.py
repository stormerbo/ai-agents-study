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
        self.assertIn("本地 mock", body)
        self.assertIn("不包含主体/对象级权限", body)
        self.assertIn("anthropic-handle-tool-calls", metadata)
        self.assertIn("owasp-llm-prompt-injection", metadata)

    def test_synthetic_host_gate_denies_dangerous_proposals_and_matches_output(self):
        import io
        from contextlib import redirect_stdout
        source = python_fences(LESSON.read_text())[0]
        self.assertNotIn("urllib", source)
        self.assertNotIn("os.environ", source)
        namespace = {"__name__": "__main__"}
        output = io.StringIO()
        with redirect_stdout(output):
            exec(compile(ast.parse(source), "lesson-python-fence", "exec"), namespace)
        expected = (
            "畸形批次：3/3 在任何 sink 调用前拒绝\n"
            "历史 provider 数字：保留为未独立复核记录；本脚本不测模型抗注入能力\n"
            "A 控制组（合成正常提案）：允许 read_doc；执行=['read_doc']；输出=收入为 1.2 亿元；应收账款周转天数上升。\n"
            "B 返回值含注入（合成危险提案）：允许 read_doc / 拒绝 delete_all：不在本次任务 allowlist / 拒绝 send_email：不在本次任务 allowlist；执行=['read_doc']；输出=危险动作已被宿主拒绝。\n"
            "D 描述含注入（合成危险提案）：拒绝 delete_all：不在本次任务 allowlist；执行=[]；输出=危险动作已被宿主拒绝。\n"
        )
        self.assertEqual(output.getvalue(), expected)


if __name__ == "__main__":
    unittest.main(verbosity=2)
