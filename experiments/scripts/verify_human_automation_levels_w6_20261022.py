"""W6 whole-lesson checks for automation-level decision boundaries."""
from __future__ import annotations

import contextlib
import io
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/human-in-the-loop/01-automation-levels.mdx"
PRIOR = ROOT / "experiments/scripts/verify_human_automation_levels_review_20261021.py"


class AutomationLevelsW6(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = LESSON.read_text(encoding="utf-8")
        cls.fences = re.findall(r"^```python\s*\n([\s\S]*?)^```\s*$", cls.text, re.M)
        cls.namespaces = []
        for index, source in enumerate(cls.fences):
            namespace = {"__name__": "w6_fixture"}
            exec(compile(source, f"automation-levels-w6-{index}", "exec"), namespace)
            cls.namespaces.append(namespace)

    def test_prior_review_verifier_remains_green(self):
        result = subprocess.run([sys.executable, str(PRIOR)], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("PASS 16/16", result.stdout)

    def test_both_complete_python_fences_compile_and_execute(self):
        self.assertEqual(len(self.fences), 2)
        output = io.StringIO()
        namespace = {"__name__": "__main__"}
        with contextlib.redirect_stdout(output):
            exec(compile(self.fences[1], "automation-policy-simulation", "exec"), namespace)
        self.assertIn("A 有 7 次审批", output.getvalue())
        self.assertIn("仅就这个合成任务", output.getvalue())

    def test_amount_required_tool_does_not_default_missing_amount_to_zero(self):
        policy = self.namespaces[0]["needs_approval"]
        tool = {"name": "refund", "amount_required": True, "reversible": False, "impact_scope": 1, "data_sensitivity": 0}
        principal = {"allowed_tools": {"refund"}}
        limits = {"max_auto_scope": 1, "max_auto_amount_fen": 100_000, "max_auto_sensitivity": 1,
                  "preapproved_irreversible_tools": {"refund"}}
        self.assertEqual(policy(tool, {}, principal, limits)[0], "deny")

    def test_malformed_trusted_policy_metadata_fails_closed(self):
        needs_approval = self.namespaces[0]["needs_approval"]
        tool = {"name": "refund", "amount_required": True, "reversible": False, "impact_scope": True, "data_sensitivity": 0}
        principal = {"allowed_tools": {"refund"}}
        limits = {"max_auto_scope": 1, "max_auto_amount_fen": 100_000, "max_auto_sensitivity": 1,
                  "preapproved_irreversible_tools": {"refund"}}
        self.assertEqual(needs_approval(tool, {"amount_fen": 50}, principal, limits)[0], "deny")

    def test_lesson_states_model_and_approval_are_not_authorization(self):
        self.assertIn("没有权限的动作应拒绝，不能靠用户点一次确认来补齐授权", self.text)
        self.assertIn("不能把模型对说明文字的响应当成强制控制", self.text)
        self.assertIn("必须由宿主在受保护动作执行路径中调用", self.text)

    def test_historical_model_observation_remains_unverified(self):
        self.assertIn("当前仓库没有逐次原始请求/响应", self.text)
        self.assertIn("不能证明模型总体上是否能识别可逆性", self.text)
        self.assertIn("不能说明模型通常能否识别可逆性", self.text)


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(AutomationLevelsW6)
    )
    print(f"providerCalls=0; externalNetworkCalls=0; tests={result.testsRun}; failures={len(result.failures) + len(result.errors)}")
    raise SystemExit(not result.wasSuccessful())
