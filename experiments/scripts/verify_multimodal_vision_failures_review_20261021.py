"""Offline checks for visual-error claims and checksum/scorer examples."""
from __future__ import annotations

import contextlib
import io
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/multimodal/04-when-vision-fails.mdx"


class VisionFailureReview(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = LESSON.read_text()
        blocks = re.findall(r"^```python\s*\n([\s\S]*?)^```\s*$", cls.text, re.M)
        cls.script = next(code for code in blocks if "historical_single_digit_pairs_rejected" in code)

    def test_historical_results_are_not_generalized(self):
        for phrase in (
            "不能证明错误率随信息密度上升",
            "逐次请求/响应、模型快照、完整 usage 与完整评分轨迹未归档",
            "并没有校验位",
            "不能用「约 1/10」概括碰撞率",
            "旧 grader 只做 JSON 片段解析与字段字符串比较",
        ):
            self.assertIn(phrase, self.text)
        for overclaim in (
            "唯一稳定复现的变量",
            "编号是有校验位的字母数字串",
            "错误率随信息密度上升，而分辨率与对比度都不影响它",
            "约有 1/10 的概率",
            "三重校验全过",
        ):
            self.assertNotIn(overclaim, self.text)

    def test_python_fence_fits_article_line_width(self):
        long_lines = [
            (index, len(line))
            for index, line in enumerate(self.script.splitlines(), 1)
            if len(line) > 88
        ]
        self.assertEqual(long_lines, [])

    def test_luhn_helpers_reject_non_ascii_or_non_string_input(self):
        namespace = {}
        exec(compile(self.script, f"{LESSON}:luhn-input", "exec"), namespace)
        check_digit = namespace["check_digit"]
        valid = namespace["valid"]
        for value in (None, True, "²", "１２"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    check_digit(value)
        self.assertFalse(valid("²0"))
        self.assertFalse(valid("１２"))

    def test_checksum_properties_and_collision_fixture(self):
        compile(self.script, f"{LESSON}:verification-script", "exec")
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            exec(compile(self.script, str(LESSON), "exec"), {"__name__": "__main__"})
        lines = output.getvalue().splitlines()
        published = re.search(r"预期输出：\s*```text\n([\s\S]*?)\n```", self.text)
        self.assertIsNotNone(published)
        self.assertEqual(output.getvalue().rstrip(), published.group(1))
        self.assertEqual(lines[0], "historical_single_digit_pairs_rejected=8/8")
        self.assertEqual(lines[1], "single_digit_mutations_detected_for_4_digit_bodies=450000/450000")
        self.assertEqual(lines[2], "two_digit_collision=valid(00000),valid(81000)")
        self.assertIn('"correct_cells": 2', output.getvalue())
        self.assertEqual(lines[-1], "missing_row=invalid_schema; truncated=max_tokens/incomplete")


if __name__ == "__main__":
    unittest.main(verbosity=2)
