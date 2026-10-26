"""W6 regression for the input-only scope of the historical budget replay."""
from __future__ import annotations

import contextlib
import io
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/cost-and-latency/05-budget-guardrails.mdx"


class InputBudgetScope(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.body = LESSON.read_text(encoding="utf-8")
        cls.fences = re.findall(r"```python\n(.*?)\n```", cls.body, re.S)

    def test_budget_variable_and_output_are_scoped(self):
        self.assertIn("INPUT_BUDGET = 2000", self.body)
        self.assertIn("`output_tokens` 不计入这条输入预算", self.body)
        self.assertIn("不是总 token、费用或完整任务预算", self.body)
        self.assertIn("输出 token 与美元费用需分别纳入任务预算", self.body)
        self.assertNotIn("\nBUDGET = 2000", self.body)

    def test_both_python_fences_compile_and_run(self):
        self.assertEqual(len(self.fences), 2)
        outputs = []
        for index, fence in enumerate(self.fences, 1):
            compiled = compile(fence, f"budget-guardrails-w6-{index}", "exec")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                exec(compiled, {"__name__": "__main__"})
            outputs.append(output.getvalue())
            self.assertTrue(output.getvalue())
        expected = (
            "归一化输入预算 2000  -> ok        已用输入 1999  完成 4 轮\n"
            "归一化输入预算 1500  -> budget    已用输入 1377  第 4 轮触发：累计 1377 + 本轮 622 > 1500\n"
            "归一化输入预算 1200  -> budget    已用输入 824   第 3 轮触发：累计 824 + 本轮 553 > 1200\n"
        )
        self.assertEqual(outputs[1], expected)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(InputBudgetScope)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print(f"providerCalls=0; externalNetworkCalls=0; tests={result.testsRun}; failures={len(result.failures) + len(result.errors)}")
    raise SystemExit(not result.wasSuccessful())
