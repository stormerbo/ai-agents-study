"""Whole-lesson accuracy checks for filesystem and network least privilege."""
from __future__ import annotations

import contextlib
import io
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/sandboxing/03-least-privilege.mdx"
META = ROOT / "src/content/chapters/sandboxing/meta.ts"
RESOURCES = ROOT / "src/content/curriculum/resources.ts"


class LeastPrivilegeW6(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = LESSON.read_text()
        cls.meta = META.read_text()
        cls.resources = RESOURCES.read_text()
        cls.python_blocks = re.findall(r"^```python\s*\n([\s\S]*?)^```\s*$", cls.text, re.M)
        cls.text_blocks = re.findall(r"^```text\s*\n([\s\S]*?)^```\s*$", cls.text, re.M)

    def test_internal_lesson_references_use_live_routes(self):
        self.assertNotRegex(self.text, r"第\s*\d+\s*(?:章|节)")
        for route in (
            "/chapters/sandboxing/isolation-levels",
            "/chapters/multimodal/how-images-enter-context",
            "/chapters/tool-calling/poka-yoke",
            "/chapters/agent-security/exfiltration",
        ):
            self.assertIn(route, self.text)

    def test_capability_interface_scope_is_not_called_impossible(self):
        self.assertRegex(self.text, r"句柄.{0,100}(权限|范围|生命周期)")
        self.assertIn("不能替代授权检查", self.text)
        self.assertIn("有效期与撤销", self.text)
        self.assertIn("不能保证「越界在结构上不可能」", self.text)
        self.assertNotIn("它的好处是**越界在结构上不可能**", self.text)

    def test_documented_path_and_url_checkpoints_bind_registered_sources(self):
        section = self.meta.split("id: 'sandboxing/least-privilege'", 1)[1].split("id: 'sandboxing/secrets'", 1)[0]
        expected = {
            "openat2-path-resolution-boundary": "sourceIds: ['linux-openat2-manpage', 'linux-openat2-path-lookup']",
            "protected-hardlinks-scope": "sourceIds: ['linux-fs-protected-hardlinks']",
            "ssrf-target-validation": "sourceIds: ['owasp-ssrf-prevention', 'python-ipaddress']",
        }
        for checkpoint, sources in expected.items():
            start = section.index(f"id: '{checkpoint}'")
            checkpoint_text = section[start:section.find('        },', start)]
            self.assertIn("basis: 'documented'", checkpoint_text)
            self.assertIn(sources, checkpoint_text)
            for source_id in re.findall(r"'([a-z0-9-]+)'", sources):
                self.assertIn(f"'{source_id}': {{", self.resources)

    def test_all_python_fences_compile(self):
        self.assertEqual(len(self.python_blocks), 5)
        for index, source in enumerate(self.python_blocks, 1):
            compile(source, f"least-privilege-python-{index}", "exec")

    def test_url_fixture_output_is_complete_and_matches_published_text(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            exec(self.python_blocks[3], {"__name__": "__main__"})
        self.assertEqual(len(self.text_blocks), 2)
        self.assertEqual(output.getvalue().rstrip("\n"), self.text_blocks[1].rstrip("\n"))


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(LeastPrivilegeW6)
    )
    print(f"providerCalls=0; externalDNSCalls=0; httpRequests=0; tests={result.testsRun}; failures={len(result.failures) + len(result.errors)}")
    raise SystemExit(not result.wasSuccessful())
