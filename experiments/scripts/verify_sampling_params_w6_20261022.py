"""Offline scope audit for API/SDK sampling migration contracts."""
from __future__ import annotations

import ast
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/llm-api-basics/02-sampling-params.mdx"
META = ROOT / "src/content/chapters/llm-api-basics/meta.ts"
RESOURCES = ROOT / "src/content/curriculum/resources.ts"
CLAIMS = ROOT / "experiments/claims.json"


class SamplingParamsW6(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = LESSON.read_text(encoding="utf-8")
        cls.meta = META.read_text(encoding="utf-8")
        cls.resources = RESOURCES.read_text(encoding="utf-8")
        cls.claims = CLAIMS.read_text(encoding="utf-8")

    def test_three_python_fences_parse(self):
        fences = re.findall(r"```python\n(.*?)\n```", self.text, re.S)
        self.assertEqual(len(fences), 3)
        for i, fence in enumerate(fences, 1):
            ast.parse(fence, filename=f"sampling-params-{i}.py")

    def test_api_version_removal_is_distinguished_from_older_versions(self):
        self.assertIn("API version `2026-10-21`", self.text)
        self.assertIn("即使值为默认值也会返回 400", self.text)
        self.assertIn("较早 API version", self.text)
        self.assertIn("Claude 4.7 及之后的模型与 Mythos Preview", self.text)
        self.assertNotIn("将 `temperature`、`top_p`、`top_k` 标为弃用：对 Claude 4.7", self.text)

    def test_sdk_body_escape_does_not_bypass_server_contract(self):
        self.assertIn("SDK 2.0.0 默认切换到 API version `2026-10-21`", self.text)
        self.assertIn("`extra_body` 仍会得到 400", self.text)
        self.assertIn("SDK 本地抛 `TypeError`", self.text)

    def test_legacy_example_uses_active_model_id(self):
        self.assertIn('model="claude-sonnet-4-6"', self.text)
        self.assertIn("旧 SDK + API version 2023-06-01", self.text)
        self.assertNotIn("claude-3-5-sonnet-20241022", self.text)

    def test_deepseek_claim_is_scoped_to_compatible_endpoint(self):
        self.assertIn("DeepSeek Anthropic-compatible endpoint", self.text)
        self.assertIn("top_k` 忽略", self.text)
        self.assertIn("top_p` 随模型/模式变化", self.text)
        self.assertIn("deepseek-anthropic-api", self.meta)
        self.assertIn("'deepseek-anthropic-api': {", self.resources)

    def test_effort_cache_rules_distinguish_message_and_prefix_layers(self):
        self.assertIn("改变 `output_config.effort` 会使 message cache 失效", self.text)
        self.assertIn("tool/system cache 是否同时失效取决于模型", self.text)
        self.assertIn("显式设置为模型默认值等同于省略", self.text)
        self.assertIn("per-message effort", self.text)
        self.assertIn("不能外推到兼容端点", self.text)
        self.assertIn("id: 'effort-cache-impact'", self.meta)

    def test_new_api_migration_resource_is_registered_and_referenced(self):
        self.assertIn("anthropic-api-version-2026-10-21", self.resources)
        self.assertIn("https://platform.claude.com/docs/en/api/migration-2026-10-21", self.resources)
        self.assertIn("anthropic-api-version-2026-10-21", self.meta)

    def test_source_bound_claims_cover_version_and_cache_boundaries(self):
        self.assertIn("llm-sampling-api-deprecation-scope-20261021", self.claims)
        self.assertIn("llm-sampling-effort-cache-boundary-20261022", self.claims)
        self.assertIn("exp-llm-sampling-params-w6-20261022", self.claims)

    def test_no_live_provider_execution_claim_is_added(self):
        self.assertIn("没有使用 provider 凭据发请求", self.text)
        self.assertIn("没有使用 provider 凭据发送请求", self.text)


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(SamplingParamsW6)
    )
    print(f"providerCalls=0; externalNetworkCalls=0; tests={result.testsRun}; failures={len(result.failures) + len(result.errors)}")
    raise SystemExit(not result.wasSuccessful())
