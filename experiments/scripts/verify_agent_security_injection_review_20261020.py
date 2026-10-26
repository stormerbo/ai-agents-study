"""Offline audit for the scope and reproducibility claims in the injection lesson."""
from __future__ import annotations

import ast
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/agent-security/01-injection-escalation.mdx"
META = ROOT / "src/content/chapters/agent-security/meta.ts"


def python_fences(text: str) -> list[str]:
    return [m.group(2) for m in re.finditer(r"^(```|~~~)python\s*\n(.*?)^\1\s*$", text, re.M | re.S)]


class InjectionLessonReview(unittest.TestCase):
    def test_python_fences_compile(self):
        fences = python_fences(LESSON.read_text())
        self.assertGreaterEqual(len(fences), 2)
        for index, source in enumerate(fences):
            compile(ast.parse(source), f"{LESSON.name}:python-fence-{index}", "exec")

    def test_executable_excerpt_matches_claimed_first_round_scope(self):
        body = LESSON.read_text()
        self.assertIn("只展示首轮的三种条件", body)
        self.assertIn("不复现第二轮与第三轮", body)
        main = next(source for source in python_fences(body) if "for label, tools, inject in" in source)
        tree = ast.parse(main)
        loop = next(
            node for node in ast.walk(tree)
            if isinstance(node, ast.For) and isinstance(node.target, ast.Tuple)
            and len(node.target.elts) == 3
        )
        scenarios = next(node for node in ast.walk(loop) if isinstance(node, ast.List))
        labels = [ast.literal_eval(item.elts[0]) for item in scenarios.elts]
        self.assertEqual(labels, ["A 控制组（文档干净）", "B 间接注入（藏在返回值）", "D 供应链注入（藏在工具描述）"])

    def test_tool_sinks_are_local_mocks_and_not_production_controls(self):
        body = LESSON.read_text()
        source = next(source for source in python_fences(body) if "def delete_all" in source)
        tree = ast.parse(source)
        wanted = {"delete_all", "send_email"}
        funcs = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in wanted]
        self.assertEqual({node.name for node in funcs}, wanted)
        namespace = {"CALLS": []}
        exec(compile(ast.Module(body=funcs, type_ignores=[]), "fake-tools", "exec"), namespace)
        self.assertEqual(namespace["delete_all"](), {"deleted": 9999})
        self.assertEqual(namespace["send_email"]("sink@example.invalid", "synthetic"), {"sent": True})
        self.assertEqual(len(namespace["CALLS"]), 2)
        self.assertIn("本地假工具", body)
        self.assertIn("没有授权、审批或参数白名单", body)

    def test_historical_denominator_and_indirect_injection_scope_are_qualified(self):
        body = LESSON.read_text()
        metadata = META.read_text()
        self.assertIn("无法独立核对分母和结果", body)
        self.assertIn("不把 0/7 当成成功率、准确率或防护证据", body)
        self.assertIn("并非 agent 独有", body)
        self.assertNotIn("agent 独有的入口", body)
        self.assertIn("resourceIds: ['owasp-llm-prompt-injection'", metadata)


if __name__ == "__main__":
    unittest.main(verbosity=2)
