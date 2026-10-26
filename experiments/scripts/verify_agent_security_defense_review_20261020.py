"""Offline checks for the defense-in-depth lesson's executable path-policy example."""
from __future__ import annotations

import ast
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/agent-security/05-defense-in-depth.mdx"
META = ROOT / "src/content/chapters/agent-security/meta.ts"
SOURCE = ROOT / "src/content/curriculum/resources.ts"


def python_fences(text: str) -> list[str]:
    return [m.group(1) for m in re.finditer(r"^```python\s*\n(.*?)^```\s*$", text, re.M | re.S)]


class DefenseInDepthReview(unittest.TestCase):
    def test_python_fences_compile_and_path_example_runs(self):
        fences = python_fences(LESSON.read_text())
        self.assertEqual(len(fences), 1)
        for fence in fences:
            compile(ast.parse(fence), str(LESSON), "exec")
        result = subprocess.run(
            [sys.executable, "-c", fences[0]], capture_output=True, text=True, check=True
        )
        decisions = [line.rsplit(" -> ", 1)[1] for line in result.stdout.splitlines() if " -> " in line]
        self.assertEqual(decisions, ["allow", "deny", "deny"])
        self.assertIn("TOCTOU", result.stdout)

    def test_lesson_avoids_absolute_boundary_and_audit_claims(self):
        body = LESSON.read_text()
        for obsolete in ("执行层是唯一的安全边界", "它是唯一能验证其它层在不在工作", "需要绕过代码，不是绕过语言"):
            self.assertNotIn(obsolete, body)
        for required in ("共因失效", "TOCTOU", "日志可能丢失", "不调用模型", "不构成生产级文件沙箱"):
            self.assertIn(required, body)

    def test_official_source_is_registered_and_linked_to_lesson(self):
        source = SOURCE.read_text()
        metadata = META.read_text()
        self.assertIn("'owasp-llm-prompt-injection':", source)
        self.assertIn("https://genai.owasp.org/llmrisk/llm01-prompt-injection/", source)
        self.assertIn("resourceIds: ['owasp-llm-prompt-injection', 'owasp-authorization-cheat-sheet'", metadata)


if __name__ == "__main__":
    unittest.main(verbosity=2)
