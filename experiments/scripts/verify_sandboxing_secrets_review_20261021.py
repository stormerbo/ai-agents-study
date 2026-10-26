"""Offline review checks for the credentials lesson; no provider calls."""
from __future__ import annotations

import contextlib
import io
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/sandboxing/04-secrets.mdx"
META = ROOT / "src/content/chapters/sandboxing/meta.ts"
RESOURCES = ROOT / "src/content/curriculum/resources.ts"


class SecretsReview(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = LESSON.read_text()
        cls.meta = META.read_text()
        cls.resources = RESOURCES.read_text()
        cls.blocks = re.findall(r"^```python\s*\n([\s\S]*?)^```\s*$", cls.text, re.M)

    def test_three_python_blocks_compile(self):
        self.assertEqual(len(self.blocks), 3)
        for index, source in enumerate(self.blocks, 1):
            compile(source, f"lesson-python-fence-{index}", "exec")

    def test_redaction_example_is_executable_and_bounded(self):
        namespace = {}
        exec(self.blocks[0], namespace)
        sample = '{"api_key": "sk-test-only-a1b2c3d4e5f6"}'
        self.assertIn("sk-***", namespace["redact"](sample))
        # The lesson explicitly limits this regex; other formats are not claimed covered.
        self.assertIn("其他供应商格式", self.text)

    def test_synthetic_leak_fixture_reports_three_paths(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            exec(self.blocks[1], {"__name__": "__main__"})
        output = out.getvalue()
        self.assertEqual(output.count("待发送对象含测试字符串：是"), 3)
        self.assertIn("不证明生产系统一定记录、保留或在每轮重发", output)
        self.assertIn("provider", self.text)

    def test_host_auth_fixture_rejects_forged_tenant_before_secret_lookup(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            exec(self.blocks[2], {})
        output = out.getvalue()
        self.assertIn("PASS forged tenant rejected before credential lookup", output)
        self.assertIn("PASS missing scope rejected before credential lookup", output)
        self.assertIn("PASS failure response/log omit raw credential and exception", output)
        self.assertIn("providerCalls=0", output)

    def test_metadata_references_official_security_sources(self):
        self.assertIn("owasp-secrets-management", self.resources)
        self.assertIn("aws-well-architected-secrets", self.resources)
        self.assertIn("owasp-logging-cheat-sheet", self.resources)
        self.assertIn("owasp-authorization-cheat-sheet", self.resources)
        lesson = self.meta.split("id: 'sandboxing/secrets'", 1)[1].split("id: 'sandboxing/execution-policy'", 1)[0]
        self.assertIn("owasp-secrets-management", lesson)
        self.assertIn("aws-well-architected-secrets", lesson)

    def test_retracted_absolute_claims_are_absent(self):
        for stale in ("后续每一轮都会重发", "日志会被长期保存", "额度是唯一"):
            self.assertNotIn(stale, self.text + self.meta)


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(SecretsReview)
    )
    print(f"providerCalls=0; tests={result.testsRun}; failures={len(result.failures) + len(result.errors)}")
    raise SystemExit(not result.wasSuccessful())
