"""Run the retrieval/chunking MDX demo and verify its published output."""
from contextlib import chdir, redirect_stdout
from io import StringIO
from pathlib import Path
import re
import sys
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
LESSON_PATH = ROOT / "src/content/chapters/retrieval/02-chunking.mdx"
FIXTURE_PATH = "src/content/chapters/retrieval/01-why-retrieval.mdx"
SOURCE = LESSON_PATH.read_text()
FENCES = re.findall(r"^```python\s*\n([\s\S]*?)^```\s*$", SOURCE, re.M)
assert FENCES, "expected the lesson's runnable Python fence"
CODE = compile(FENCES[0], str(LESSON_PATH), "exec")


def run_demo():
    output = StringIO()
    namespace = {"__name__": "__main__"}
    with chdir(ROOT), patch.object(sys, "argv", ["chunk-demo.py", FIXTURE_PATH]):
        with redirect_stdout(output):
            exec(CODE, namespace)
    return output.getvalue(), namespace


class ChunkingDemoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.output, cls.namespace = run_demo()

    def test_demo_output_matches_the_published_fence_exactly(self):
        section = SOURCE.split("用法与实跑输出：", 1)[1]
        expected = re.search(r"```text\s*\n\$ python3[^\n]*\n([\s\S]*?)\n```", section)
        self.assertIsNotNone(expected, "expected output fence must follow the documented command")
        self.assertEqual(self.output.rstrip(), expected.group(1).rstrip())

    def test_demo_uses_the_current_fixture_and_expected_counts(self):
        self.assertIn("文件: %s" % FIXTURE_PATH, self.output)
        self.assertIn("固定 400 字符 / 无重叠            18        400           6%", self.output)
        self.assertIn("固定 400 字符 / 重叠 80          23        389           9%", self.output)
        self.assertIn("结构边界 / 软上限 800 字符          16        648          80%", self.output)

    def test_fixed_chunking_keeps_short_tail_and_overlap(self):
        fixed = self.namespace["fixed"]
        self.assertEqual(fixed("abcde", 4, 2), ["abcd", "cde"])
        self.assertEqual(fixed("abc", 4, 0), ["abc"])
        self.assertEqual(fixed("", 4, 0), [])

    def test_fixed_chunking_rejects_invalid_sizes(self):
        fixed = self.namespace["fixed"]
        for size, overlap in [(0, 0), (4, -1), (4, 4)]:
            with self.subTest(size=size, overlap=overlap):
                with self.assertRaises(ValueError):
                    fixed("abc", size, overlap)

    def test_structural_chunking_documents_soft_limit_and_validates_input(self):
        structural = self.namespace["structural"]
        chunks = structural("## A\n\nshort\n\n## B\n\nthis paragraph is longer than ten", 10)
        self.assertEqual(chunks, ["## A\n\nshort\n", "## B\n\nthis paragraph is longer than ten"])
        with self.assertRaises(ValueError):
            structural("text", 0)

    def test_punctuation_metric_is_a_lexical_proxy_with_empty_input_boundary(self):
        rate = self.namespace["sentence_end_rate"]
        self.assertEqual(rate([]), 0.0)
        self.assertEqual(rate(["内容。", "未完成"]), 0.5)
        self.assertIn("不能证明块语义完整", SOURCE)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(ChunkingDemoTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(0 if result.wasSuccessful() else 1)
