"""Execute the regression lesson's Python fence and verify its printed diffs."""

from __future__ import annotations

import re
import json
import math
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/evaluation/11-regression.mdx"


def run_lesson_example() -> str:
    source = LESSON.read_text(encoding="utf-8")
    python_fences = re.findall(r"```python\s*\n(.*?)```", source, re.DOTALL)
    example = next((fence for fence in python_fences if "def ci_width" in fence), None)
    if example is None:
        raise AssertionError("could not find the runnable regression example")
    result = subprocess.run(
        [sys.executable, "-c", example],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


class RegressionLessonExampleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.output = run_lesson_example()

    def test_two_repairs_report_both_recovered_cases(self) -> None:
        scenario = self.output.split("改动 B：", 1)[1].split("改动 C：", 1)[0]
        self.assertIn("修好 2 题、没有碰坏", scenario)
        self.assertIn("通过率 86.7% → 93.3%（Δ +6.7 个百分点）", scenario)
        self.assertIn("修好的用例：[3, 11]", scenario)

    def test_single_group_interval_is_not_used_as_a_version_gate(self) -> None:
        self.assertIn("不作版本差异裁决", self.output)
        self.assertNotIn("单次差异超过粗略参考带", self.output)

    def test_neutral_net_change_reports_two_repairs_and_two_regressions(self) -> None:
        scenario = self.output.split("改动 C：", 1)[1].split("=== 关键点 ===", 1)[0]
        self.assertIn("修好 2 题、碰坏 2 题", scenario)
        self.assertIn("退步的用例：[7, 8]", scenario)
        self.assertIn("修好的用例：[3, 11]", scenario)

    def test_lesson_transcript_matches_executable_case_diffs(self) -> None:
        source = LESSON.read_text(encoding="utf-8")
        transcripts = re.findall(r"```text\s*\n(.*?)```", source, re.DOTALL)
        transcript = next((text for text in transcripts if "基线：30 题通过 26 题" in text), None)
        self.assertIsNotNone(transcript, "the lesson should retain its worked transcript")
        b_example = transcript.split("改动 B：", 1)[1].split("改动 C：", 1)[0]
        c_example = transcript.split("改动 C：", 1)[1]
        self.assertIn("通过率 86.7% → 93.3%（Δ +6.7）", b_example)
        self.assertIn("修好的用例：[3, 11]", b_example)
        self.assertIn("修好 2 题、碰坏 2 题", c_example)

    def test_baseline_example_is_valid_json_with_consistent_wald_summary(self) -> None:
        source = LESSON.read_text(encoding="utf-8")
        blocks = re.findall(r"```json\s*\n(.*?)```", source, re.DOTALL)
        baseline = json.loads(next(block for block in blocks if '"baseline_summary"' in block))
        summary = baseline["baseline_summary"]
        self.assertEqual((summary["n"], summary["passed"]), (30, 26))
        p = summary["passed"] / summary["n"]
        half_width = 1.6449 * math.sqrt(p * (1 - p) / summary["n"])
        expected = [round(p - half_width, 3), round(p + half_width, 3)]
        self.assertEqual(summary["single_run_wald90"], expected)


if __name__ == "__main__":
    unittest.main(verbosity=2)
