"""W6 whole-lesson checks for evaluation/provider-migration (2026-10-22)."""
from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/evaluation/12-provider-migration.mdx"
META = ROOT / "src/content/chapters/evaluation/meta.ts"
RESOURCES = ROOT / "src/content/curriculum/resources.ts"


class ProviderMigrationW6(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lesson = LESSON.read_text(encoding="utf-8")
        cls.meta = META.read_text(encoding="utf-8")
        cls.resources = RESOURCES.read_text(encoding="utf-8")

    def test_fixture_demo_output_matches_lesson(self):
        run = subprocess.run(
            [sys.executable, "examples/provider-migration/demo_migration_gate.py"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
            env={"PATH": "/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE": "1"},
        )
        expected = [
            "fixture: plain completed, refusal refusal, long truncated, lookup tool_call",
            "fixture decision: fixture-pass",
            "empty required suite: incomplete",
            "live-provider decision: unavailable (no live responses recorded)",
        ]
        self.assertEqual(run.stdout.strip().splitlines(), expected)
        for line in expected:
            self.assertIn(line, self.lesson)

    def test_fixture_output_does_not_approve_provider_migration(self):
        self.assertIn('"fixture_gate": "fixture-pass"', self.lesson)
        self.assertIn('"live_evidence": null', self.lesson)
        self.assertIn('"decision": "insufficient-evidence"', self.lesson)
        self.assertIn("不能批准 provider 迁移", self.lesson)

    def test_provider_tool_continuation_boundaries_are_explicit(self):
        self.assertIn("必须传回此前的 `reasoning_content`", self.lesson)
        self.assertIn("https://api.deepseek.com/beta", self.lesson)
        self.assertIn("不能据此推断 `/anthropic`", self.lesson)
        self.assertIn("迁移样例应把", self.lesson)

    def test_protocol_states_remain_distinct(self):
        for state in ("completed", "tool_call", "refusal", "truncated", "error", "unknown"):
            self.assertIn(f"`{state}`", self.lesson)
        self.assertIn("不要把未知状态默认为 `completed`", self.lesson)
        self.assertIn("多个调用、拒绝和文本可能共存", self.lesson)

    def test_tool_ids_and_authorization_are_separate_contracts(self):
        self.assertIn("`call_id`", self.lesson)
        self.assertIn("`tool_use_id`", self.lesson)
        self.assertIn("宿主在每次操作前按身份与对象授权", self.lesson)
        self.assertIn("拒绝发生在副作用之前", self.lesson)

    def test_usage_unknown_is_not_zero(self):
        self.assertIn("缺少 `input_tokens`、`output_tokens` 或缓存分项时用 `null` / `unknown`", self.lesson)
        self.assertIn("将未知写成零会让成本图表", self.lesson)

    def test_report_requires_versioned_live_evidence(self):
        for field in ("report_version", "dataset", "source", "candidate", "fixture_gate", "live_evidence", "decision", "missing"):
            self.assertIn(f'"{field}"', self.lesson)
        self.assertIn("原始响应定位", self.lesson)
        self.assertIn("数据集修订", self.lesson)

    def test_documented_sources_are_registered_and_linked(self):
        required = (
            "openai-responses-api",
            "openai-structured-outputs",
            "anthropic-tool-use",
            "deepseek-chat-api",
            "deepseek-tool-calls",
            "deepseek-thinking-mode",
            "owasp-authorization-cheat-sheet",
            "nist-design-of-experiments",
        )
        for resource_id in required:
            self.assertIn(f"'{resource_id}'", self.resources)
            self.assertIn(resource_id, self.meta)
        lesson_meta = self.meta.split("id: 'evaluation/provider-migration'", 1)[1].split("\n    },", 1)[0]
        self.assertIn("deepseek-tool-calls", lesson_meta)
        for url in (
            "https://developers.openai.com/api/docs/guides/function-calling",
            "https://developers.openai.com/api/docs/guides/structured-outputs",
            "https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview",
            "https://api-docs.deepseek.com/guides/tool_calls/",
            "https://api-docs.deepseek.com/guides/thinking_mode/",
            "https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html",
            "https://www.itl.nist.gov/div898/handbook/pri/section3/pri3.htm",
        ):
            self.assertIn(url, self.lesson)

    def test_live_sources_have_current_verification_dates(self):
        for resource_id in (
            "openai-structured-outputs",
            "anthropic-tool-use",
            "deepseek-tool-calls",
        ):
            section = self.resources.split(f"'{resource_id}': {{", 1)[1].split("\n  },", 1)[0]
            self.assertIn("verifiedAt: '2026-10-22'", section)

    def test_original_offline_suite_still_passes_without_provider_calls(self):
        run = subprocess.run(
            [sys.executable, "-m", "unittest", "discover", "-s", "examples/provider-migration", "-v"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
            env={"PATH": "/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE": "1"},
        )
        self.assertIn("Ran 8 tests", run.stderr)
        self.assertIn("OK", run.stderr)
        self.assertEqual(run.stdout, "")

    def test_source_references_track_the_supported_claims(self):
        self.assertIn("deepseek-tool-calls", self.meta)
        self.assertIn("anthropic-tool-use", self.meta)
        self.assertIn("openai-structured-outputs", self.meta)
        self.assertIn("nist-design-of-experiments", self.meta)


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(ProviderMigrationW6)
    )
    print(
        f"providerCalls=0; externalNetworkCalls=0; tests={result.testsRun}; "
        f"failures={len(result.failures) + len(result.errors)}"
    )
    raise SystemExit(not result.wasSuccessful())
