"""Offline regression checks for the PDF-route lesson review; never calls a provider."""
from __future__ import annotations

import contextlib
import io
import json
import os
import re
import sys
import tempfile
import types
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/multimodal/02-document-routes.mdx"


class DocumentRoutesReview(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = LESSON.read_text()
        cls.fences = re.findall(r"^```python\s*\n([\s\S]*?)^```\s*$", cls.text, re.M)
        cls.harness = next(f for f in cls.fences if "document-route-results.jsonl" in f)

    def test_historical_provider_summary_is_not_a_supported_behavior_claim(self):
        self.assertRegex(self.text, r"(?is)历史.{0,100}(?:原始|逐次).{0,100}(?:没有归档|缺失).{0,100}(?:不能|无法).{0,30}(?:复核|推断)")
        for overclaim in (
            "PDF 的字节被收下了，然后被丢掉了",
            "输入 token 不可能只有 59",
            "图片路线贵 2.7 倍",
            "把失败从协议层降级到了模型自觉性层",
        ):
            self.assertNotIn(overclaim, self.text)

    def test_cost_and_route_selection_are_conditional_not_fixed_heuristics(self):
        self.assertIn("不能线性外推", self.text)
        self.assertIn("结构化校验", self.text)
        self.assertNotIn("def layout(words", self.text)
        self.assertNotIn("min_chars_per_page=100", self.text)

    def test_python_fences_compile(self):
        self.assertTrue(self.fences)
        for index, code in enumerate(self.fences, 1):
            compile(code, f"{LESSON}:python-fence-{index}", "exec")

    def test_code_fence_lines_fit_the_article_width(self):
        for fence_index, code in enumerate(self.fences, 1):
            long_lines = [
                (line_number, len(line))
                for line_number, line in enumerate(code.splitlines(), 1)
                if len(line) > 88
            ]
            with self.subTest(fence=fence_index):
                self.assertEqual(long_lines, [])

    def test_business_validator_rejects_invalid_rows_and_arithmetic(self):
        code = next(f for f in self.fences if "def validate_invoice_rows" in f)
        namespace: dict = {}
        exec(compile(code, f"{LESSON}:validator", "exec"), namespace)
        validate = namespace["validate_invoice_rows"]
        valid = [
            {"item": "Widget C", "quantity": "3", "unit_price": "12.50", "amount": "37.50"},
        ]
        self.assertEqual(validate(valid, "37.50"), (True, "ok"))
        self.assertEqual(
            validate([{**valid[0], "amount": "35.00"}], "35.00"),
            (False, "row_0_arithmetic"),
        )
        self.assertEqual(
            validate([{**valid[0], "unexpected": "field"}], "37.50"),
            (False, "row_0_schema"),
        )
        self.assertEqual(validate([], "0"), (False, "no_rows"))
        self.assertEqual(validate(None, "0"), (False, "rows_type"))
        self.assertEqual(validate([None], "0"), (False, "row_0_schema"))
        self.assertEqual(
            validate([{**valid[0], "quantity": "NaN"}], "37.50"),
            (False, "row_0_number"),
        )
        self.assertEqual(
            validate([{**valid[0], "quantity": "Infinity", "amount": "Infinity"}], "Infinity"),
            (False, "row_0_number"),
        )
        self.assertEqual(validate(valid, "NaN"), (False, "total_number"))
        self.assertEqual(validate(valid, None), (False, "total_number"))
        self.assertEqual(
            validate([{**valid[0], "quantity": True}], "37.50"),
            (False, "row_0_number"),
        )

        self.assertIn("真实发票可能包含税费、折扣、舍入规则", self.text)

    def test_json_scorer_rejects_duplicate_keys(self):
        code = next(f for f in self.fences if "def answer_is_correct" in f)
        match = re.search(r"(?ms)^def unique_object.*?(?=^def make_record)", code)
        self.assertIsNotNone(match)
        namespace: dict = {"json": json, "EXPECTED": {"amount": "37.50", "total": "119.50"}}
        exec(compile(match.group(), f"{LESSON}:scorer", "exec"), namespace)
        self.assertFalse(
            namespace["answer_is_correct"](
                '{"amount":"0","amount":"37.50","total":"119.50"}'
            )
        )

    def test_harness_uses_the_same_pdf_for_native_render_and_text_routes(self):
        class FakePage:
            def render(self, scale):
                self.scale = scale
                return SimpleNamespace(
                    to_pil=lambda: SimpleNamespace(
                        width=612,
                        height=792,
                        save=lambda buffer, format: buffer.write(b"fake-png-from-pdf"),
                    )
                )

        observed_pdfium_bytes = []
        observed_pdfplumber_bytes = []

        class FakePdfiumDocument:
            def __init__(self, pdf_bytes):
                self.pdf_bytes = pdf_bytes
                observed_pdfium_bytes.append(pdf_bytes)

            def __getitem__(self, index):
                return FakePage()

        class FakePdfPlumberDoc:
            pages = [SimpleNamespace(extract_text=lambda: "Invoice\nWidget C 37.50\nTotal 119.50")]

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

        class FakeMessages:
            calls = []

            def create(self, **kwargs):
                type(self).calls.append(kwargs)
                return SimpleNamespace(
                    model="fixture-model-snapshot",
                    stop_reason="end_turn",
                    content=[SimpleNamespace(type="text", text=json.dumps({"amount": "37.50", "total": "119.50"}))],
                    usage=SimpleNamespace(input_tokens=17, output_tokens=4),
                )

        fake_modules = {
            "anthropic": types.SimpleNamespace(Anthropic=lambda: SimpleNamespace(messages=FakeMessages())),
            "pypdfium2": types.SimpleNamespace(PdfDocument=FakePdfiumDocument),
            "pdfplumber": types.SimpleNamespace(
                open=lambda data: (observed_pdfplumber_bytes.append(data.getvalue()) or FakePdfPlumberDoc())
            ),
        }
        FakeMessages.calls = []
        namespace: dict = {"__name__": "lesson_fixture"}
        with patch.dict(sys.modules, fake_modules), patch.dict(
            os.environ, {"VERIFY_MODEL": "fixture-model"}
        ):
            exec(compile(self.harness, str(LESSON), "exec"), namespace)
            with tempfile.TemporaryDirectory() as tmp:
                previous = os.getcwd()
                os.chdir(tmp)
                try:
                    with contextlib.redirect_stdout(io.StringIO()):
                        namespace["__name__"] = "__main__"
                        exec(compile(self.harness, str(LESSON), "exec"), namespace)
                    rows = [json.loads(line) for line in Path("document-route-results.jsonl").read_text().splitlines()]
                finally:
                    os.chdir(previous)
        self.assertEqual(len(FakeMessages.calls), 3)
        self.assertEqual(len(rows), 3)
        self.assertEqual([r["route"] for r in rows], ["document", "rendered_image", "extracted_text"])
        pdf_block = FakeMessages.calls[0]["messages"][0]["content"][0]
        image_block = FakeMessages.calls[1]["messages"][0]["content"][0]
        text_block = FakeMessages.calls[2]["messages"][0]["content"][0]
        self.assertEqual(pdf_block["type"], "document")
        pdf_bytes = __import__("base64").b64decode(pdf_block["source"]["data"])
        self.assertEqual(observed_pdfium_bytes, [pdf_bytes])
        self.assertEqual(observed_pdfplumber_bytes, [pdf_bytes])
        self.assertEqual(image_block["type"], "image")
        self.assertEqual(text_block["type"], "text")
        self.assertIn("Widget C 37.50", text_block["text"])
        self.assertTrue(all(row["response_model"] == "fixture-model-snapshot" for row in rows))
        self.assertTrue(all(row["answer_correct"] for row in rows))
        incomplete = namespace["make_record"](
            "document",
            SimpleNamespace(
                model="fixture-model-snapshot",
                stop_reason="max_tokens",
                content=[],
                usage=SimpleNamespace(input_tokens=17),
            ),
        )
        self.assertEqual(incomplete["status"], "incomplete")
        self.assertFalse(incomplete["answer_correct"])
        self.assertEqual(incomplete["usage"]["output_tokens"], None)


if __name__ == "__main__":
    unittest.main(verbosity=2)
