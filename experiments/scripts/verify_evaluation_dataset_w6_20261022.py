"""Offline whole-lesson freshness and executable-example checks."""
from __future__ import annotations

import re
import subprocess
import sys
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/evaluation/03-dataset.mdx"
META = ROOT / "src/content/chapters/evaluation/meta.ts"
RESOURCES = ROOT / "src/content/curriculum/resources.ts"
SOURCE = LESSON.read_text(encoding="utf-8")
META_SOURCE = META.read_text(encoding="utf-8")
RESOURCE_SOURCE = RESOURCES.read_text(encoding="utf-8")
FENCES = re.findall(r"^```python\s*\n([\s\S]*?)^```\s*$", SOURCE, re.M)


class DatasetLessonW6(unittest.TestCase):
    def test_openai_evals_product_lifecycle_is_currently_bounded(self):
        for phrase in (
            "截至 2026-10-22",
            "2026-10-31",
            "2026-11-30",
            "新项目的长期依赖",
            "重新核对",
        ):
            self.assertIn(phrase, SOURCE)

    def test_platform_lifecycle_has_documented_sources_and_sidebar_resource(self):
        self.assertIn("id: 'evaluation-platform-lifecycle'", META_SOURCE)
        self.assertIn("basis: 'documented'", META_SOURCE)
        self.assertIn("sourceIds: ['openai-api-deprecations', 'openai-evals-migration-promptfoo', 'openai-evaluation-best-practices']", META_SOURCE)
        self.assertIn("id: 'openai-api-deprecations'", RESOURCE_SOURCE)
        self.assertIn("https://developers.openai.com/api/docs/deprecations", RESOURCE_SOURCE)
        self.assertIn("id: 'openai-evals-migration-promptfoo'", RESOURCE_SOURCE)
        self.assertIn("https://developers.openai.com/cookbook/examples/evaluation/moving-from-openai-evals-to-promptfoo", RESOURCE_SOURCE)
        self.assertIn("verifiedAt: '2026-10-22'", RESOURCE_SOURCE)

    def test_python_example_compiles_and_exact_stdout_matches(self):
        self.assertEqual(len(FENCES), 1)
        code = FENCES[0]
        compile(code, str(LESSON), "exec")
        output = StringIO()
        namespace = {"__name__": "__main__"}
        with redirect_stdout(output):
            exec(compile(code, str(LESSON), "exec"), namespace)
        expected = (
            "19/20 Wilson 95% interval: 76.4%–99.1%\n"
            "p=.9, 90% confidence, ±10pp planning n: 25\n"
            "p=.9, 90% confidence, ±5pp planning n: 98\n"
        )
        self.assertEqual(output.getvalue(), expected)
        self.assertNotIn("urlopen(", code)

    def test_prior_dataset_contract_audit_still_passes(self):
        completed = subprocess.run(
            [sys.executable, str(ROOT / "experiments/scripts/verify_evaluation_dataset_review_20261021.py")],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn("PASS 6 evaluation-dataset review checks", completed.stdout)


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(DatasetLessonW6)
    )
    print(
        f"providerCalls=0; externalNetworkCalls=0; tests={result.testsRun}; "
        f"failures={len(result.failures) + len(result.errors)}"
    )
    raise SystemExit(not result.wasSuccessful())
