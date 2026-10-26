"""Offline evidence and safety checks for the isolation-levels lesson."""
from __future__ import annotations

import re
import ast
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/sandboxing/02-isolation-levels.mdx"
META = ROOT / "src/content/chapters/sandboxing/meta.ts"
RESOURCES = ROOT / "src/content/curriculum/resources.ts"


class IsolationLevelsReview(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = LESSON.read_text()
        cls.meta = META.read_text()
        cls.resources = RESOURCES.read_text()
        cls.python_blocks = re.findall(r"^```python\s*\n([\s\S]*?)^```\s*$", cls.text, re.M)
        cls.bash_blocks = re.findall(r"^```bash\s*\n([\s\S]*?)^```\s*$", cls.text, re.M)

    def test_l1_blocklist_example_demonstrates_the_claimed_escape(self):
        self.assertIn("catch_warnings", self.text)
        self.assertIn("__import__", self.text)
        self.assertIn("只读当前 pid", self.text)

    def test_l1_escape_demo_runs_with_only_a_read_only_pid_effect(self):
        module = ast.parse(self.python_blocks[0])
        function = next(node for node in module.body if isinstance(node, ast.FunctionDef) and node.name == "l1_blacklist")
        source = "import time, warnings\n" + ast.unparse(function) + "\nprint(l1_blacklist()[2])\n"
        run = subprocess.run(
            [sys.executable, "-c", source],
            capture_output=True,
            text=True,
            timeout=5,
        )
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertRegex(run.stdout, r"黑名单绕过成功：.*只读当前 pid=\d+")

    def test_docker_run_mounts_the_runner_that_it_executes(self):
        self.assertGreaterEqual(len(self.bash_blocks), 1)
        command = self.bash_blocks[0]
        self.assertIn("dst=/app/runner.py,readonly", command)
        self.assertIn("python /app/runner.py", command)

    def test_network_none_probe_does_not_depend_on_eth_interface_naming(self):
        self.assertIn("def t_no_default_route()", self.text)
        self.assertIn("/proc/net/ipv6_route", self.text)
        self.assertIn("无非 loopback 默认路由", self.text)
        self.assertNotIn("startswith('eth')", self.text)

    def test_rlimit_and_preexec_fn_platform_threading_limits_are_disclosed(self):
        self.assertIn("resource` 模块仅适用于 Unix", self.text)
        self.assertIn("preexec_fn", self.text)
        self.assertIn("preexec_fn 在多线程父进程中不安全且可能死锁", self.text)

    def test_terminology_separates_linux_caps_from_object_capabilities(self):
        self.assertIn("Linux capabilities", self.text)
        self.assertIn("object capability", self.text)

    def test_historical_timings_are_not_presented_as_same_workload_comparison(self):
        self.assertIn("不是“同一段代码”在四种环境中的性能对照", self.text)
        self.assertIn("不能拿来比较隔离开销", self.text)

    def test_virtual_machine_strength_and_lifetime_claims_are_qualified(self):
        self.assertIn("边界仍依赖 hypervisor", self.text)
        self.assertNotIn("绝不要「全局共享 + 清理」", self.text)
        self.assertNotIn("最安全（状态不会跨任务泄漏）", self.text)

    def test_official_sources_are_registered_for_this_lesson(self):
        lesson_meta = self.meta.split("id: 'sandboxing/isolation-levels'", 1)[1].split("id: 'sandboxing/least-privilege'", 1)[0]
        for resource_id in ("docker-none-network", "docker-run-container", "python-resource-limits", "python-subprocess"):
            self.assertIn(resource_id, self.resources)
            self.assertIn(resource_id, lesson_meta)

    def test_all_python_fences_compile(self):
        self.assertGreaterEqual(len(self.python_blocks), 3)
        for index, source in enumerate(self.python_blocks, 1):
            compile(source, f"isolation-lesson-python-{index}", "exec")


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(IsolationLevelsReview)
    )
    print(f"providerCalls=0; externalNetworkCalls=0; tests={result.testsRun}; failures={len(result.failures) + len(result.errors)}")
    raise SystemExit(not result.wasSuccessful())
