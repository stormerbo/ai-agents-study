"""W6 whole-lesson scope checks for structured-output/why-not-prompt-only."""
from __future__ import annotations

import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/structured-output/01-why-not-prompt-only.mdx"
META = ROOT / "src/content/chapters/structured-output/meta.ts"
PRIOR = ROOT / "experiments/scripts/verify_structured_output_prompt_review_20261021.py"


class PromptOnlyW6(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = LESSON.read_text(encoding="utf-8")

    def test_existing_issue_verifier_reports_its_actual_eight_checks(self):
        result = subprocess.run(
            [sys.executable, str(PRIOR)], cwd=ROOT, capture_output=True,
            text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("tests=8; failures=0", result.stdout)

    def test_python_fences_are_balanced_and_all_compile(self):
        fences = re.findall(r"^```([^\n]*)\n([\s\S]*?)^```\s*$", self.text, re.M)
        self.assertEqual(sum(1 for lang, _ in fences if lang == "python"), 2)
        self.assertEqual(sum(1 for lang, _ in fences if lang == "json"), 3)
        self.assertEqual(sum(1 for lang, _ in fences if lang == "text"), 3)
        for index, (lang, code) in enumerate(fences):
            if lang == "python":
                compile(code, f"structured-output-w6-{index}", "exec")

    def test_historical_model_claims_remain_unreproduced_and_narrow(self):
        self.assertIn("逐次请求、逐次响应、精确模型快照和可重算评分器", self.text)
        self.assertIn("不能证明今天的模型表现", self.text)
        self.assertIn("不能据此估计生产失败率", self.text)
        self.assertIn("不能视为当前模型的兼容性结论", self.text)
        self.assertIn("不要把 325 token 当成普遍固定成本", self.text)
        self.assertIn("不要据此判断工具调用普遍更慢或更快", self.text)

    def test_failure_taxonomy_requires_actual_response_and_endpoint_contract(self):
        for phrase in (
            "截断、拒绝、工具交接和正常结束是不同状态",
            "字段名及枚举值需按 endpoint 处理",
            "端到端交付率必须把未完成纳入",
            "tool_use` 也表示一次工具交接",
        ):
            self.assertIn(phrase, self.text)

    def test_local_validation_claim_is_conditional_on_all_side_effect_paths(self):
        self.assertIn("所有副作用入口都强制经过该门禁", self.text)
        self.assertIn("它仍不证明内容真实或业务动作获准", self.text)
        self.assertIn("提示可以改善格式倾向，但不构成硬保证", self.text)

    def test_current_provider_docs_are_not_conflated_with_old_request(self):
        self.assertIn("https://api-docs.deepseek.com/guides/tool_calls/", self.text)
        self.assertIn("https://api-docs.deepseek.com/guides/anthropic_api/", self.text)
        self.assertIn("V3.2 起支持 thinking mode 下的 tool use", self.text)
        self.assertIn("部署时应按具体 API 格式、模型与当前文档重测", self.text)

    def test_provider_token_limits_and_stop_fields_have_separate_contracts(self):
        for phrase in (
            "Anthropic Messages", "max_completion_tokens", "max_output_tokens",
            "finish_reason", "stop_reason", "不可见的推理 token 也计入上限",
        ):
            self.assertIn(phrase, self.text)

    def test_metadata_checkpoint_matches_the_lesson_boundary(self):
        meta = META.read_text(encoding="utf-8")
        start = meta.index("id: 'structured-output/why-not-prompt-only'")
        end = meta.index("\n    },\n    {", start)
        lesson_meta = meta[start:end]
        self.assertIn("prompt-level-vs-decoding", lesson_meta)
        self.assertIn("provider-output-token-limit", lesson_meta)
        self.assertIn("成功率相同且没有重试", lesson_meta)
        self.assertIn("拒绝、截断、传输错误仍要分流", lesson_meta)
        self.assertIn("本地 schema/业务校验", lesson_meta)

    def test_adjacent_lesson_is_present_and_cross_link_target_exists(self):
        next_lesson = ROOT / "src/content/chapters/structured-output/02-json-schema-strict.mdx"
        self.assertTrue(next_lesson.is_file())
        self.assertIn("JSON Schema 与约束解码", next_lesson.read_text(encoding="utf-8"))

    def test_numeric_probability_examples_and_exact_zero_failure_bound(self):
        self.assertAlmostEqual(0.99 ** 10, 0.9043820750088044)
        self.assertAlmostEqual(0.99 ** 100, 0.3660323412732292)
        self.assertAlmostEqual(0.999 ** 100, 0.904792147113709, places=12)
        self.assertAlmostEqual(1 - 0.05 ** (1 / 30), 0.09503385285530419)

    def test_local_code_handles_object_array_and_redacts_unparseable_input(self):
        python_blocks = re.findall(r"^```python\s*\n([\s\S]*?)^```\s*$", self.text, re.M)
        namespace = {"__name__": "w6_fixture"}
        exec(compile(python_blocks[0], "lesson-parser", "exec"), namespace)
        parse = namespace["extract_json"]
        self.assertEqual(parse('{"a": 1}')[0], {"a": 1})
        self.assertEqual(parse('[{"a": 1}, {"a": 2}]')[0], [{"a": 1}, {"a": 2}])
        marker = "SENSITIVE_W6_FIXTURE"
        with self.assertRaises(ValueError) as caught:
            parse(marker)
        self.assertNotIn(marker, str(caught.exception))


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(PromptOnlyW6)
    )
    print(
        f"providerCalls=0; externalNetworkCalls=0; tests={result.testsRun}; "
        f"failures={len(result.failures) + len(result.errors)}"
    )
    raise SystemExit(not result.wasSuccessful())
