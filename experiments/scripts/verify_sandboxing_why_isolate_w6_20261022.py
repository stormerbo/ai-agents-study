"""Offline whole-lesson checks for why-isolate; no network/provider calls."""
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
META = ROOT / "src/content/chapters/sandboxing/meta.ts"
RESOURCES = ROOT / "src/content/curriculum/resources.ts"


class WhyIsolateW6(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = LESSON.read_text()
        cls.meta = META.read_text()
        cls.resources = RESOURCES.read_text()
        cls.python_blocks = re.findall(r"^```python\s*\n([\s\S]*?)^```\s*$", cls.text, re.M)

    def test_all_lesson_python_fences_compile(self):
        self.assertEqual(len(self.python_blocks), 1)
        for index, source in enumerate(self.python_blocks, 1):
            compile(source, f"why-isolate-python-{index}", "exec")

    def test_complete_demo_stdout_matches_published_output_and_cleans_its_fixture(self):
        match = re.search(r"本地运行输出(?:（[^）]*）)?：\s*```text\n([\s\S]*?)\n```", self.text)
        self.assertIsNotNone(match, "the complete local demo output is missing")
        with tempfile.TemporaryDirectory(prefix="why-isolate-w6-") as tmp:
            sentinel_dir = Path(tmp) / "sandbox-demo"
            sentinel_dir.mkdir()
            sentinel = sentinel_dir / "preserve.txt"
            sentinel.write_text("preserve me")
            env = os.environ.copy()
            env["TMPDIR"] = tmp
            result = subprocess.run(
                [sys.executable, "-c", self.python_blocks[0]],
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
                timeout=10,
                check=True,
            )
            self.assertEqual(result.stdout.rstrip("\n"), match.group(1))
            self.assertEqual(sentinel.read_text(), "preserve me")
            self.assertEqual(sorted(path.name for path in Path(tmp).iterdir()), ["sandbox-demo"])

    def test_lesson_uses_route_links_instead_of_stale_chapter_ordinals(self):
        self.assertNotRegex(self.text, r"第\s*\d+\s*[章节]")
        for route in (
            "/chapters/computer-use/what-differs",
            "/chapters/computer-use/safety-and-scope",
            "/chapters/agent-loop/tool-registry",
            "/chapters/agent-security/injection-escalation",
            "/chapters/multimodal/how-images-enter-context",
            "/chapters/sandboxing/isolation-levels",
            "/chapters/sandboxing/least-privilege",
            "/chapters/sandboxing/execution-policy",
        ):
            self.assertIn(route, self.text)

    def test_title_and_threat_model_do_not_make_isolation_an_absolute_rule(self):
        front_title = re.search(r"^title: (.+)$", self.text, re.M).group(1)
        meta_section = self.meta.split("id: 'sandboxing/why-isolate'", 1)[1].split("id: 'sandboxing/isolation-levels'", 1)[0]
        self.assertIn("title: '隔离解决什么问题'", meta_section)
        self.assertEqual(front_title, "隔离解决什么问题")
        self.assertIn("提示和工具注册表都不保证执行环境的可达范围", self.text)
        self.assertIn("不是攻击成功率或生产漏洞率", self.text)
        for control in ("身份认证", "工具授权", "对象级授权", "隔离"):
            self.assertIn(control, self.text)

    def test_historical_four_of_six_result_stays_fixture_bound(self):
        self.assertIn("朴素版放过 4/6 种攻击（仅本固定夹具）", self.text)
        self.assertIn("不代表其他路径检查或生产系统的漏洞率", self.text)
        self.assertIn("内嵌固定输入", self.text)

    def test_security_and_platform_facts_use_source_bound_checkpoints(self):
        section = self.meta.split("id: 'sandboxing/why-isolate'", 1)[1].split("id: 'sandboxing/isolation-levels'", 1)[0]
        for source_id in (
            "owasp-authorization-cheat-sheet",
            "owasp-ssrf-prevention",
            "linux-openat2-path-lookup",
            "python-tempfile",
        ):
            self.assertIn(source_id, self.resources)
            self.assertIn(source_id, section)
        for checkpoint_id in (
            "authorization-versus-isolation",
            "ssrf-is-not-sandboxing",
            "path-resolution-races",
            "temporary-fixture-cleanup",
        ):
            self.assertIn(f"id: '{checkpoint_id}'", section)

    def test_prompt_injection_and_blast_radius_are_conditioned_on_host_capabilities(self):
        self.assertIn("可能受攻击者影响", self.text)
        self.assertIn("是否成功取决于模型、上下文、工具权限和宿主控制", self.text)
        self.assertIn("实际影响范围取决于宿主身份、挂载、网络出口和执行器配置", self.text)
        self.assertIn("隔离执行环境本身不等于 SSRF 防护", self.text)


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(WhyIsolateW6)
    )
    print(f"providerCalls=0; externalNetworkCalls=0; tests={result.testsRun}; failures={len(result.failures) + len(result.errors)}")
    raise SystemExit(not result.wasSuccessful())
