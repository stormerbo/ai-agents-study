"""W6 whole-lesson checks for the LLM-as-judge lesson."""
from __future__ import annotations

import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LESSON_PATH = ROOT / "src/content/chapters/evaluation/08-llm-as-judge.mdx"
LESSON = LESSON_PATH.read_text(encoding="utf-8")
DATA = (ROOT / "docs/DATA.md").read_text(encoding="utf-8")
META = (ROOT / "src/content/chapters/evaluation/meta.ts").read_text(encoding="utf-8")
RESOURCES = (ROOT / "src/content/curriculum/resources.ts").read_text(encoding="utf-8")
FENCES = re.findall(r"^```python\n([\s\S]*?)^```\s*$", LESSON, re.M)


class LlmJudgeW6(unittest.TestCase):
    def test_swapped_pair_conclusion_is_limited_to_the_observed_sample(self):
        self.assertNotIn("这正是没有位置偏见的证据", LESSON)
        self.assertIn("没有观察到换序导致的答案身份翻转", LESSON)
        self.assertIn("不能证明 judge 没有位置偏差", LESSON)
        self.assertIn("原始逐次响应", LESSON)

    def test_historical_counts_remain_unverified_and_not_population_rates(self):
        for phrase in ("历史登记数字", "0/12", "均未独立复核，不代表总体偏差率"):
            self.assertIn(phrase, LESSON)
        self.assertIn("0/12", DATA)
        self.assertIn("不能证明总体无位置偏差", DATA)

    def test_primary_source_registration_covers_reported_biases(self):
        self.assertIn("sourceIds: ['mt-bench-llm-judge', 'owasp-llm-prompt-injection']", META)
        self.assertIn("'mt-bench-llm-judge': {", RESOURCES)
        self.assertIn("https://arxiv.org/abs/2306.05685", RESOURCES)

    def test_complete_python_fence_executes_and_stdout_matches(self):
        self.assertEqual(len(FENCES), 1)
        code = FENCES[0]
        compile(code, str(LESSON_PATH), "exec")
        with tempfile.TemporaryDirectory(prefix="llm-judge-w6-") as tmp:
            script = Path(tmp) / "lesson_example.py"
            script.write_text(code, encoding="utf-8")
            completed = subprocess.run(
                [sys.executable, str(script)], capture_output=True, text=True, check=False
            )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(
            completed.stdout,
            "stable-content-choice {'status': 'order_invariant', 'winner_original': 'good', 'winner_swapped': 'good'}\n"
            "same-slot-choice {'status': 'order_sensitive', 'winner_original': 'good', 'winner_swapped': 'bad'}\n"
            "invalid-output-rejected invalid judge label: 'A or B'\n",
        )
        self.assertNotIn("urllib.request", code)

    def test_previous_ten_lesson_review_checks_still_pass(self):
        completed = subprocess.run(
            [sys.executable, str(ROOT / "experiments/scripts/verify_evaluation_llm_judge_review_20261021.py")],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn("10/10 checks passed", completed.stdout)


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(LlmJudgeW6)
    )
    print(
        f"providerCalls=0; externalNetworkCalls=0; tests={result.testsRun}; "
        f"failures={len(result.failures) + len(result.errors)}"
    )
    raise SystemExit(not result.wasSuccessful())
