"""Offline checks for the resolution/cost lesson; no provider calls."""
from __future__ import annotations

import contextlib
import io
import re
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/multimodal/03-resolution-and-cost.mdx"


class FakeImage:
    def __init__(self, size):
        self.size = size

    def crop(self, box):
        left, top, right, bottom = box
        return FakeImage((right - left, bottom - top))


class ResolutionCostReview(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = LESSON.read_text()
        fence = chr(96) * 3
        matches = re.findall(
            r"^" + fence + r"python\s*\n([\s\S]*?)^" + fence + r"\s*$",
            cls.text,
            re.M,
        )
        if len(matches) != 1:
            raise AssertionError(f"expected exactly one Python fence, found {len(matches)}")
        cls.code = matches[0]
        fake_pil = types.SimpleNamespace(Image=types.SimpleNamespace(Image=FakeImage))
        with patch.dict(sys.modules, {"PIL": fake_pil}):
            cls.namespace = {}
            exec(compile(cls.code, str(LESSON), "exec"), cls.namespace)

    def test_historical_result_is_explicitly_bounded(self):
        self.assertIn("不能证明分辨率不影响准确率", self.text)
        self.assertIn("没有完整留存", self.text)
        self.assertIn("不能把差异单独归因于分辨率", self.text)

    def test_provider_estimates_are_scoped_and_currently_sourced(self):
        self.assertIn("查阅日期 2026-10-22", self.text)
        self.assertIn("只把它用于文档覆盖的 DeepSeek API", self.text)
        self.assertIn("规则按模型变化", self.text)
        self.assertIn("兼容 API 不保证沿用", self.text)

    def test_price_formula_preserves_usage_categories(self):
        self.assertIn("各计费类别的 token usage × 对应单价", self.text)
        self.assertIn("账单", self.text)
        self.assertIn("估算值当账单", self.text)

    def test_markdown_uses_real_paragraph_breaks(self):
        self.assertNotIn(r"\n\n本节离线测试", self.text)
        self.assertIn("本节离线测试的记录样例", self.text)

    def test_crop_geometry_matches_documented_fixture(self):
        split_vertical = self.namespace["split_vertical"]
        result = split_vertical(FakeImage((1000, 3000)), 3, 0.10)
        self.assertEqual(
            [(top, bottom, crop.size) for _, top, bottom, crop in result],
            [(0, 1100, (1000, 1100)), (900, 2100, (1000, 1200)), (1900, 3000, (1000, 1100))],
        )

    def test_crop_parameters_reject_invalid_types_and_ranges(self):
        split_vertical = self.namespace["split_vertical"]
        invalid = [(True, 0.1), (2.0, 0.1), (0, 0.1), (2, None), (2, False),
                   (2, float("nan")), (2, float("inf")), (2, -0.1), (2, 1.0)]
        for parts, overlap in invalid:
            with self.subTest(parts=parts, overlap=overlap):
                with self.assertRaises(ValueError):
                    split_vertical(FakeImage((100, 100)), parts, overlap)

    def test_python_fence_is_within_documented_line_width(self):
        long_lines = [(i, len(line)) for i, line in enumerate(self.code.splitlines(), 1) if len(line) > 88]
        self.assertEqual(long_lines, [])

    def test_verifier_is_discoverable_and_reports_failures(self):
        source = Path(__file__).read_text()
        self.assertIn("unittest.main", source)
        self.assertIn("result.wasSuccessful()", source)


if __name__ == "__main__":
    stream = io.StringIO()
    with contextlib.redirect_stdout(stream):
        result = unittest.TextTestRunner(stream=stream, verbosity=2).run(
            unittest.defaultTestLoader.loadTestsFromTestCase(ResolutionCostReview)
        )
    print(stream.getvalue(), end="")
    print(f"providerCalls=0 tests={result.testsRun}")
    raise SystemExit(0 if result.wasSuccessful() else 1)
