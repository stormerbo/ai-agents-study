"""Offline W6 verifier for prompt-engineering/reliability; no provider calls."""
from __future__ import annotations

import contextlib
import io
import json
import os
import re
import sys
import types
import unittest
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/prompt-engineering/05-reliability.mdx"
TEXT = LESSON.read_text(encoding="utf-8")
FENCES = re.findall(r"^```python\n([\s\S]*?)^```\s*$", TEXT, re.M)


class FakeMessages:
    def __init__(self, responses=()):
        self.responses = list(responses)
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if not self.responses:
            raise AssertionError("unexpected fake provider call")
        return self.responses.pop(0)


class FakeClient:
    def __init__(self, responses=()):
        self.messages = FakeMessages(responses)


class PromptReliabilityW6(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.assertEqual = unittest.TestCase.assertEqual
        cls.assertIsNotNone = unittest.TestCase.assertIsNotNone
        cls.assertLessEqual = unittest.TestCase.assertLessEqual
        cls.assertRaises = unittest.TestCase.assertRaises
        cls.assertIn = unittest.TestCase.assertIn
        cls.assertNotIn = unittest.TestCase.assertNotIn
        cls.assertTrue = unittest.TestCase.assertTrue
        cls.assertFalse = unittest.TestCase.assertFalse
        cls.assertGreaterEqual = unittest.TestCase.assertGreaterEqual
        fixture_module = types.ModuleType("lesson_fixture")
        sys.modules["lesson_fixture"] = fixture_module
        cls.ns = vars(fixture_module)
        cls.clients = []
        cls.constructor_kwargs = []

        def make_client(**_kwargs):
            cls.constructor_kwargs.append(_kwargs)
            client = FakeClient()
            cls.clients.append(client)
            return client

        fake_sdk = types.SimpleNamespace(Anthropic=make_client)
        with patch.dict(
            sys.modules, {"anthropic": fake_sdk}
        ), patch.dict(os.environ, {"VERIFY_MODEL": "fixture-model"}):
            for index, code in enumerate(FENCES):
                exec(
                    compile(code, f"{LESSON}:fence-{index}", "exec"),
                    cls.ns,
                )

    def test_all_python_fences_compile_within_88_columns(self):
        self.assertEqual(len(FENCES), 2)
        for code in FENCES:
            compile(code, str(LESSON), "exec")
            self.assertLessEqual(max(map(len, code.splitlines())), 88)

    def test_sdk_credentials_use_one_correctly_named_argument(self):
        fake_sdk = types.SimpleNamespace(Anthropic=lambda **kwargs: kwargs)
        cases = [
            ({"ANTHROPIC_API_KEY": "fake-key"}, "api_key", "fake-key"),
            ({"ANTHROPIC_AUTH_TOKEN": "fake-token"}, "auth_token", "fake-token"),
            (
                {
                    "ANTHROPIC_API_KEY": "fake-key",
                    "ANTHROPIC_AUTH_TOKEN": "fake-token",
                },
                "api_key",
                "fake-key",
            ),
        ]
        for env, expected_name, expected_value in cases:
            namespace = {}
            with patch.dict(
                os.environ, {"VERIFY_MODEL": "fixture-model", **env}, clear=True
            ), patch.dict(sys.modules, {"anthropic": fake_sdk}):
                exec(compile(FENCES[0], str(LESSON), "exec"), namespace)
            options = namespace["client"]
            self.assertEqual(options.get(expected_name), expected_value)
            self.assertEqual(len(options), 1)

    def test_number_proxy_uses_exact_tokens_and_multiplicity(self):
        score = self.ns["proxy_score"]("增长 1%", "收入增长 12%")
        self.assertFalse(score["numbers_present"])
        repeated = self.ns["proxy_score"]("分别为 12% 和 12%", "收入为 12%")
        self.assertFalse(repeated["numbers_present"])

    def test_invoice_schema_rejects_unexpected_fields(self):
        payload = {
            "invoice_no": "INV-20261008",
            "issue_date": "2026-10-08",
            "items": [{"name": "咨询费", "amount": Decimal("10.00")}],
            "total": Decimal("10.00"),
            "untrusted_extra": "must not be silently dropped",
        }
        with self.assertRaises(self.ns["ValidationError"]):
            self.ns["Invoice"].model_validate(payload, strict=True)

    def test_currency_semantics_reject_one_cent_difference(self):
        invoice = self.ns["Invoice"](
            invoice_no="INV-20261008",
            issue_date="2026-10-08",
            items=[
                {"name": "咨询费", "amount": 1200.00},
                {"name": "差旅费", "amount": 356.50},
            ],
            total=1556.51,
        )
        with self.assertRaises(self.ns["ValidationFailed"]):
            self.ns["check_semantics"](invoice)


    def response(self, text, stop_reason="end_turn"):
        block = SimpleNamespace(type="text", text=text)
        return SimpleNamespace(stop_reason=stop_reason, content=[block])

    def test_extract_accepts_exact_invoice_and_does_not_echo_document(self):
        client = FakeClient([
            self.response(
                '{"invoice_no":"INV-20261008","issue_date":"2026-10-08",'
                '"items":[{"name":"咨询费","amount":1200.00},'
                '{"name":"差旅费","amount":356.50}],"total":1556.50}'
            )
        ])
        self.ns["client"] = client
        invoice = self.ns["extract"]("客户张三的发票原文")
        self.assertEqual(invoice.total, Decimal("1556.50"))
        self.assertEqual(len(client.messages.calls), 1)
        self.assertIn("客户张三的发票原文", client.messages.calls[0]["messages"][0]["content"])

    def test_extract_rejects_refusal_or_truncation_before_parsing(self):
        for reason in ("refusal", "max_tokens"):
            self.ns["client"] = FakeClient([
                self.response('敏感原文：客户张三', stop_reason=reason)
            ])
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                with self.assertRaisesRegex(RuntimeError, reason):
                    self.ns["extract"]("敏感原文：客户张三", max_attempts=1)
            self.assertNotIn("客户张三", output.getvalue())

    def test_extract_rejects_duplicate_json_keys_without_echoing_values(self):
        self.ns["client"] = FakeClient([
            self.response(
                '{"invoice_no":"INV-20261008","invoice_no":"PII-秘密",'
                '"issue_date":"2026-10-08","items":[],"total":0}'
            )
        ])
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            with self.assertRaisesRegex(RuntimeError, "1 次尝试"):
                self.ns["extract"]("敏感原文：客户张三", max_attempts=1)
        self.assertNotIn("PII-秘密", output.getvalue())
        self.assertNotIn("客户张三", output.getvalue())


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(PromptReliabilityW6)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print(
        f"providerCalls=0; externalNetworkCalls=0; tests={result.testsRun}; "
        f"failures={len(result.failures) + len(result.errors)}"
    )
    raise SystemExit(not result.wasSuccessful())
