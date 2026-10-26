"""Check the regression lesson's CI event wiring and action pinning guidance."""

from __future__ import annotations

import re
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/evaluation/11-regression.mdx"
META = ROOT / "src/content/chapters/evaluation/meta.ts"
RESOURCES = ROOT / "src/content/curriculum/resources.ts"


class RegressionCiExampleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.lesson = LESSON.read_text(encoding="utf-8")
        cls.meta = META.read_text(encoding="utf-8")
        cls.resources = RESOURCES.read_text(encoding="utf-8")
        match = re.search(r"```yaml\s*\n(.*?)```", cls.lesson, re.DOTALL)
        if match is None:
            raise AssertionError("GitHub Actions YAML example is missing")
        cls.workflow = match.group(1)

    def test_workflow_triggers_include_pull_request(self) -> None:
        self.assertRegex(self.workflow, r"(?ms)^on:\s+push:\s+pull_request:\s+release:\s+types: \[published\]")

    def test_smoke_job_runs_on_push_and_pull_request(self) -> None:
        self.assertIn("if: github.event_name == 'push' || github.event_name == 'pull_request'", self.workflow)
        self.assertIn("--suite smoke", self.workflow)

    def test_full_regression_is_release_only(self) -> None:
        self.assertRegex(self.workflow, r"(?ms)regression:\s+if: github\.event_name == 'release'.*?--suite regression")
        self.assertIn("types: [published]", self.workflow)

    def test_tag_based_checkout_is_explicitly_non_immutable(self) -> None:
        self.assertIn("uses: actions/checkout@v4", self.workflow)
        self.assertIn("锁到完整 commit SHA", self.lesson)

    def test_pin_guidance_is_source_bound_in_metadata(self) -> None:
        self.assertIn("github-actions-trigger-and-pin", self.meta)
        self.assertIn("sourceIds: ['github-actions-events', 'github-actions-secure-use']", self.meta)

    def test_official_sources_are_registered_and_linked(self) -> None:
        self.assertIn("https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows", self.resources)
        self.assertIn("https://docs.github.com/en/actions/reference/security/secure-use", self.resources)
        self.assertIn("'github-actions-events'", self.meta)
        self.assertIn("'github-actions-secure-use'", self.meta)

    def test_published_transcript_matches_complete_executable_stdout(self) -> None:
        blocks = re.findall(r"```python\s*\n(.*?)```", self.lesson, re.DOTALL)
        example = next((block for block in blocks if "def ci_width" in block), None)
        self.assertIsNotNone(example)
        run = subprocess.run([sys.executable, "-c", example], cwd=ROOT, capture_output=True, text=True, check=True)
        transcripts = re.findall(r"```text\s*\n(.*?)```", self.lesson, re.DOTALL)
        transcript = next((block for block in transcripts if "三个候选改动" in block), None)
        self.assertEqual(transcript, run.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
