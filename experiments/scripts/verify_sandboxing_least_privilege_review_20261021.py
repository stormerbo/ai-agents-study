"""Offline accuracy review for filesystem containment and SSRF examples."""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/sandboxing/03-least-privilege.mdx"
META = ROOT / "src/content/chapters/sandboxing/meta.ts"
RESOURCES = ROOT / "src/content/curriculum/resources.ts"


class LeastPrivilegeReview(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = LESSON.read_text()
        cls.meta = META.read_text()
        cls.resources = RESOURCES.read_text()
        cls.blocks = re.findall(r"^```python\s*\n([\s\S]*?)^```\s*$", cls.text, re.M)

    def test_path_demo_discloses_realpath_check_open_race(self):
        self.assertRegex(self.text, r"TOCTOU|并发.*(替换|改名)|检查.*打开.*竞态")
        self.assertIn("openat2", self.text)
        self.assertIn("RESOLVE_BENEATH", self.text)

    def test_hardlink_scope_is_qualified(self):
        self.assertRegex(self.text, r"硬链接.{0,100}(同一文件系统|同一挂载|读取.*访问控制)")
        self.assertIn("Linux", self.text)
        self.assertNotIn("（默认值，防未授权硬链接）", self.text)

    def test_network_policy_rejects_non_global_and_limits_connection(self):
        self.assertIn("if not address.is_global:", self.text)
        self.assertIn("100.64.0.0/10", self.text)
        self.assertRegex(self.text, r"(443|端口).{0,80}(限制|固定|拒绝)")
        self.assertRegex(self.text, r"(自动跳转|redirect).{0,80}(禁用|重新校验|重新完整)")
        self.assertRegex(self.text, r"(连接|transport).{0,100}(已验证 IP|验证过的 IP|pin)")

    def test_allowlisted_host_is_also_limited_by_path_method_and_query(self):
        self.assertIn("ALLOWED_PATHS", self.text)
        self.assertIn("method != \"GET\"", self.text)
        self.assertIn("不允许的 path", self.text)
        self.assertIn("不接受 query", self.text)

    def test_legacy_network_example_is_not_mislabeled_as_offline(self):
        self.assertIn("2026-10-12 的旧代码虽称离线", self.text)
        self.assertIn("socket.getaddrinfo", self.text)
        self.assertIn("移除真实 resolver fallback", self.text)

    def test_policy_demo_does_not_claim_to_be_a_safe_fetcher(self):
        self.assertIn("不能单独充当安全下载器", self.text)
        self.assertIn("check_url", self.text)
        self.assertIn("externalDNSCalls=0; httpRequests=0", self.text)

    def test_filesystem_fixture_runs_expected_local_assertions(self):
        out = __import__("io").StringIO()
        with __import__("contextlib").redirect_stdout(out):
            exec(self.blocks[2], {"__name__": "__main__"})
        output = out.getvalue()
        self.assertIn("naive_secret_reads=4; checked_secret_reads=0; normal_read=pass", output)
        self.assertIn("它不防并发路径替换", output)

    def test_network_fixture_is_offline_and_denies_private_shared_and_bad_port(self):
        out = __import__("io").StringIO()
        with __import__("contextlib").redirect_stdout(out):
            exec(self.blocks[3], {"__name__": "__main__"})
        output = out.getvalue()
        self.assertIn("https://100.64.0.1/", output)
        self.assertIn("fixture assertions: allowed=3; denied=17; POST=denied; externalDNSCalls=0; httpRequests=0", output)
        self.assertNotIn("socket.getaddrinfo", self.blocks[3])

    def test_official_sources_are_registered_for_lesson(self):
        for resource_id in ("owasp-ssrf-prevention", "python-ipaddress", "linux-openat2-path-lookup"):
            self.assertIn(resource_id, self.resources)
            self.assertIn(resource_id, self.meta)
        self.assertIn("openat2", self.text)

    def test_all_python_fences_compile(self):
        self.assertGreaterEqual(len(self.blocks), 4)
        for i, source in enumerate(self.blocks, 1):
            compile(source, f"lesson-python-fence-{i}", "exec")


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(LeastPrivilegeReview)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print(f"providerCalls=0; tests={result.testsRun}; failures={len(result.failures) + len(result.errors)}")
    raise SystemExit(not result.wasSuccessful())
