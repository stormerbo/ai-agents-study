from __future__ import annotations

import contextlib
import io
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LESSON_PATH = ROOT / "src/content/chapters/agent-security/04-exfiltration.mdx"
META_PATH = ROOT / "src/content/chapters/agent-security/meta.ts"
RESOURCES_PATH = ROOT / "src/content/curriculum/resources.ts"
LEGACY_VERIFIER = ROOT / "experiments/scripts/verify_agent_security_exfiltration_review_20261020.py"
LESSON = LESSON_PATH.read_text(encoding="utf-8")
META = META_PATH.read_text(encoding="utf-8")
RESOURCES = RESOURCES_PATH.read_text(encoding="utf-8")


def fences(language: str) -> list[str]:
    marker = chr(96) * 3
    return [
        match.group(1)
        for match in re.finditer(
            rf"^{marker}{re.escape(language)}[^\n]*\n([\s\S]*?)^{marker}[ \t]*$",
            LESSON,
            re.M,
        )
    ]


def symbol_block(text: str, name: str) -> str:
    match = re.search(rf"  '{re.escape(name)}': \{{([\s\S]*?)\n  \}},", text)
    if not match:
        raise AssertionError(f"resource {name!r} was not found")
    return match.group(1)


def checkpoint_block(checkpoint_id: str) -> str:
    match = re.search(
        rf"          id: '{re.escape(checkpoint_id)}',([\s\S]*?)\n        \}},",
        META,
    )
    if not match:
        raise AssertionError(f"checkpoint {checkpoint_id!r} was not found")
    return match.group(1)


class ExfiltrationW6Review(unittest.TestCase):
    def test_chapter_cross_references_are_valid_and_specific(self) -> None:
        self.assertNotIn("第 16 节", LESSON)
        self.assertNotIn("L86-92", LESSON)
        self.assertIn("/chapters/sandboxing/execution-policy", LESSON)
        self.assertIn("/chapters/sandboxing/least-privilege", LESSON)
        self.assertIn("ERR-189", LESSON)

    def test_synthetic_customer_data_is_unmistakable(self) -> None:
        self.assertIn("所有值均为合成占位数据，不对应真实个人或客户记录", LESSON)
        self.assertIn("PERSON_SYNTHETIC", LESSON)
        self.assertNotIn("❌ 外泄成功", LESSON)
        self.assertIn("玩具模型判定成功", LESSON)
        self.assertNotIn("13800138000", LESSON)
        self.assertNotIn("张三", LESSON)

    def test_browser_csp_scope_is_explicit(self) -> None:
        self.assertIn("img-src", LESSON)
        self.assertIn("connect-src", LESSON)
        self.assertIn("不是服务端网络出口防火墙", LESSON)
        self.assertIn("2026-09-16 标为 Working Draft", LESSON)
        checkpoint = checkpoint_block("csp-browser-request-scope")
        self.assertIn("basis: 'documented'", checkpoint)
        self.assertIn("sourceIds: ['w3c-csp3']", checkpoint)

    def test_ssrf_guidance_ties_validation_to_the_actual_request(self) -> None:
        self.assertIn("DNS 重绑定或检查与使用时差", LESSON)
        self.assertIn("禁止重定向或逐跳复核", LESSON)
        checkpoint = checkpoint_block("ssrf-validate-connection-target")
        self.assertIn("basis: 'documented'", checkpoint)
        self.assertIn("sourceIds: ['owasp-ssrf-prevention']", checkpoint)

    def test_anthropic_request_state_is_separate_from_data_retention(self) -> None:
        self.assertIn("本地模型也可能完全不经过外部模型服务", LESSON)
        checkpoint = checkpoint_block("anthropic-messages-and-retention-scope")
        self.assertIn("anthropic-working-with-messages", checkpoint)
        self.assertIn("anthropic-api-data-retention", checkpoint)
        self.assertIn("不能单独推出服务端保留时长", checkpoint)

    def test_registered_sources_are_current_and_clearly_scoped(self) -> None:
        ssrf = symbol_block(RESOURCES, "owasp-ssrf-prevention")
        csp = symbol_block(RESOURCES, "w3c-csp3")
        messages = symbol_block(RESOURCES, "anthropic-working-with-messages")
        retention = symbol_block(RESOURCES, "anthropic-api-data-retention")
        for block in (ssrf, csp, messages, retention):
            self.assertIn("verifiedAt: '2026-10-22'", block)
        self.assertIn("Working Draft", csp)
        self.assertIn("功能资格", retention)

    def test_python_fixture_compiles_without_provider_or_network_clients(self) -> None:
        blocks = fences("python")
        self.assertEqual(len(blocks), 1)
        code = blocks[0]
        compile(code, str(LESSON_PATH), "exec")
        for forbidden in ("requests.", "urlopen", "httpx.", "anthropic.", "OpenAI("):
            self.assertNotIn(forbidden, code)

    def test_python_fixture_output_matches_the_published_output(self) -> None:
        code_blocks = fences("python")
        output_blocks = fences("text")
        self.assertEqual(len(code_blocks), 1)
        self.assertEqual(len(output_blocks), 1)
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            exec(compile(code_blocks[0], str(LESSON_PATH), "exec"), {"__name__": "__main__"})
        self.assertEqual(output.getvalue(), output_blocks[0])

    def test_boolean_fixture_exercises_the_declared_branches(self) -> None:
        code = fences("python")[0]
        namespace: dict[str, object] = {"__name__": "exfiltration_w6_fixture"}
        exec(compile(code, str(LESSON_PATH), "exec"), namespace)
        model = namespace["try_exfiltrate"]
        self.assertTrue(model(True, True, True)[0])  # type: ignore[operator]
        self.assertFalse(model(False, True, True)[0])  # type: ignore[operator]
        self.assertFalse(model(True, False, True)[0])  # type: ignore[operator]
        self.assertFalse(model(True, True, False)[0])  # type: ignore[operator]

    def test_legacy_review_verifier_remains_green_after_claim_wording_change(self) -> None:
        result = subprocess.run(
            [sys.executable, str(LEGACY_VERIFIER)],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("Ran 4 tests", result.stderr)


if __name__ == "__main__":
    unittest.main()
