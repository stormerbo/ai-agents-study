"""Offline W6 checks for the execution-policy lesson; no network/provider calls."""
from __future__ import annotations

import contextlib
import io
import re
import subprocess
import sys
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/sandboxing/05-execution-policy.mdx"
META = ROOT / "src/content/chapters/sandboxing/meta.ts"
RESOURCES = ROOT / "src/content/curriculum/resources.ts"


class ExecutionPolicyW6(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = LESSON.read_text()
        cls.meta = META.read_text()
        cls.resources = RESOURCES.read_text()
        cls.blocks = re.findall(r"^```python\s*\n([\s\S]*?)^```\s*$", cls.text, re.M)

    def test_all_python_fences_compile(self):
        self.assertEqual(len(self.blocks), 5)
        for index, source in enumerate(self.blocks, 1):
            compile(source, f"lesson-python-fence-{index}", "exec")

    def test_insecure_demo_stdout_matches_the_published_output(self):
        result = subprocess.run(
            [sys.executable, "-c", self.blocks[2]],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        match = re.search(r"本地运行输出：\s*```text\n([\s\S]*?)\n```", self.text)
        self.assertIsNotNone(match, "the complete demo output block is missing")
        self.assertEqual(result.stdout.rstrip("\n"), match.group(1))

    def test_attack_test_fence_runs_against_the_published_policy_module(self):
        module = types.ModuleType("policy")
        exec(compile(self.blocks[3], "published-policy-module", "exec"), module.__dict__)
        sys.modules["policy"] = module
        namespace = {"__name__": "published_policy_tests"}
        try:
            exec(compile(self.blocks[4], "published-policy-tests", "exec"), namespace)
            tests = [value for name, value in namespace.items()
                     if name.startswith("test_") and callable(value)]
            self.assertEqual(len(tests), 4)
            for test in tests:
                with self.subTest(test=test.__name__):
                    test()
        finally:
            sys.modules.pop("policy", None)

    def test_policy_prompt_section_is_consolidated_and_claims_are_bounded(self):
        self.assertEqual(self.text.count("## 策略和提示词的关系"), 1)
        self.assertNotIn("请求可以被说服，策略不能", self.text)
        self.assertNotIn("只有前者说明策略在工作", self.text)
        self.assertNotIn("所以它可以被穷举", self.text)
        self.assertIn("拒绝记录本身不能证明策略整体有效", self.text)
        self.assertIn("有限规则集合", self.text)
        self.assertIn("可能忘记", self.text)

    def test_platform_facts_have_source_bound_checkpoints(self):
        section = self.meta.split("id: 'sandboxing/execution-policy'", 1)[1].split("\n    },", 1)[0]
        for source_id in ("owasp-authorization-cheat-sheet", "owasp-logging-cheat-sheet",
                          "linux-cgroup-v2", "python-subprocess"):
            self.assertIn(source_id, self.resources)
            self.assertIn(source_id, section)
        for binding in (
            "sourceIds: ['owasp-authorization-cheat-sheet']",
            "sourceIds: ['owasp-logging-cheat-sheet']",
            "sourceIds: ['linux-cgroup-v2']",
            "sourceIds: ['python-subprocess']",
        ):
            self.assertIn(binding, section)
        self.assertIn("id: 'authorization-default-deny'", section)
        self.assertIn("id: 'audit-sensitive-fields'", section)
        self.assertIn("id: 'cgroup-controller-availability'", section)
        self.assertIn("id: 'subprocess-timeout-cleanup'", section)
        self.assertIn("其是否可用取决于内核支持", self.text)
        self.assertIn("Python `Popen.communicate(timeout=...)` 在等待超时时会抛出", self.text)
        self.assertIn("`TimeoutExpired`；该用法下子进程不会自动被杀", self.text)

    def test_lesson_limits_execution_and_audit_claims(self):
        self.assertIn("规则表便于评审，但不能证明覆盖所有执行路径", self.text)
        self.assertIn("/chapters/computer-use/safety-and-scope", self.text)
        self.assertIn("/chapters/sandboxing/least-privilege", self.text)
        self.assertIn("/chapters/prompt-engineering/structure-and-separation", self.text)
        self.assertIn("日志接收端本身", self.text)
        self.assertIn("进程树", self.text)
        self.assertIn("对象级授权", self.text)


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(ExecutionPolicyW6)
    )
    print(f"providerCalls=0; externalNetworkCalls=0; tests={result.testsRun}; failures={len(result.failures) + len(result.errors)}")
    raise SystemExit(not result.wasSuccessful())
