"""Offline code-safety checks for the why-isolate lesson."""
from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/sandboxing/01-why-isolate.mdx"
LEAST_PRIVILEGE = ROOT / "src/content/chapters/sandboxing/03-least-privilege.mdx"


class WhyIsolateReview(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = LESSON.read_text()
        cls.least_privilege = LEAST_PRIVILEGE.read_text()
        cls.python_blocks = re.findall(r"^```python\s*\n([\s\S]*?)^```\s*$", cls.text, re.M)

    def test_demo_uses_a_unique_temporary_directory_and_never_deletes_a_fixed_path(self):
        self.assertIn("tempfile.mkdtemp(prefix=\"sandbox-demo-\")", self.python_blocks[0])
        self.assertIn("atexit.register(shutil.rmtree, ROOT, ignore_errors=True)", self.python_blocks[0])
        self.assertNotRegex(self.python_blocks[0], r"if os\.path\.exists\(ROOT\):\s*\n\s*shutil\.rmtree\(ROOT\)")

    def test_demo_preserves_a_preexisting_sandbox_demo_directory(self):
        self.assertEqual(len(self.python_blocks), 1)
        with tempfile.TemporaryDirectory(prefix="why-isolate-test-") as tmp:
            base = Path(tmp)
            sentinel_dir = base / "sandbox-demo"
            sentinel_dir.mkdir()
            sentinel = sentinel_dir / "preserve.txt"
            sentinel.write_text("preserve me")
            env = os.environ.copy()
            env["TMPDIR"] = str(base)
            run = subprocess.run(
                [sys.executable, "-c", self.python_blocks[0]],
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
                timeout=10,
            )
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertEqual(sentinel.read_text(), "preserve me")
            self.assertIn("朴素版放过 4/6 种攻击", run.stdout)
            self.assertEqual(sorted(p.name for p in base.iterdir()), ["sandbox-demo"])

    def test_sensitive_fixture_is_not_credential_shaped(self):
        self.assertIn("SENSITIVE_MARKER=fixture", self.text)
        self.assertNotIn("sk-live-", self.text)
        self.assertNotIn("API_KEY=", self.text)

    def test_realpath_demo_is_explicitly_static_and_not_a_race_safe_sandbox(self):
        self.assertRegex(self.text, r"realpath.{0,120}(TOCTOU|竞态|并发)")
        self.assertRegex(self.least_privilege, r"realpath.{0,160}(TOCTOU|竞态|并发)")

    def test_denial_logs_do_not_persist_raw_input_or_absolute_resolved_paths(self):
        code = self.python_blocks[0]
        self.assertIn('"target_scope": "outside-sandbox"', code)
        self.assertNotIn('"raw": rel', code)
        self.assertNotIn('"resolved": full', code)
        self.assertNotIn("raw_path", self.text)
        self.assertIn("默认不记录完整路径", self.text)

    def test_url_tools_distinguish_execution_isolation_from_egress_and_ssrf_controls(self):
        self.assertIn("隔离执行环境本身不等于 SSRF 防护", self.text)
        self.assertIn("连接层/出口策略", self.text)

    def test_checkpoint_limits_when_isolation_can_be_omitted(self):
        meta = (ROOT / "src/content/chapters/sandboxing/meta.ts").read_text()
        checkpoint = meta.split("id: 'sandboxing/why-isolate'", 1)[1].split("id: 'sandboxing/isolation-levels'", 1)[0]
        self.assertIn("无敏感数据、无外部副作用且输出范围受控", checkpoint)
        self.assertNotIn("几乎不需要隔离", checkpoint)

    def test_all_python_fences_compile(self):
        self.assertEqual(len(self.python_blocks), 1)
        for index, source in enumerate(self.python_blocks, 1):
            compile(source, f"why-isolate-python-{index}", "exec")


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(WhyIsolateReview)
    )
    print(f"providerCalls=0; externalNetworkCalls=0; tests={result.testsRun}; failures={len(result.failures) + len(result.errors)}")
    raise SystemExit(not result.wasSuccessful())
