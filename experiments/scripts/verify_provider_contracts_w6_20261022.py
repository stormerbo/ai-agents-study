"""Run the complete provider-contract classifier fixture suite offline."""
from __future__ import annotations

import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/llm-api-basics/06-provider-contracts.mdx"


class ProviderContractsW6(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        text = LESSON.read_text(encoding="utf-8")
        match = re.search(r"```python\n(.*?)\n```", text, re.S)
        if not match:
            raise AssertionError("expected one runnable Python fence")
        cls.code = match.group(1)

    def test_exactly_one_classifier_fixture_suite(self):
        self.assertEqual(len(re.findall(r"```python\n", LESSON.read_text(encoding="utf-8"))), 1)
        self.assertIn("test_only_tool_call_state_exposes_dispatchable_calls", self.code)

    def test_complete_embedded_suite_passes_offline(self):
        with tempfile.TemporaryDirectory() as directory:
            script = Path(directory) / "provider_contracts.py"
            script.write_text(self.code, encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(script)], capture_output=True, text=True, check=False
            )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("Ran 15 tests", result.stderr)
        self.assertIn("OK", result.stderr)

    def test_fail_closed_tool_dispatch_is_documented(self):
        self.assertIn('"tool_calls": tools if kind == "tool_calls" else []', self.code)
        self.assertIn("截断、拒绝、失败和未知状态中的部分调用只保留在 `raw`，不得派发。", LESSON.read_text(encoding="utf-8"))


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(ProviderContractsW6)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print(f"providerCalls=0; externalNetworkCalls=0; tests={result.testsRun}; failures={len(result.failures) + len(result.errors)}")
    raise SystemExit(not result.wasSuccessful())
