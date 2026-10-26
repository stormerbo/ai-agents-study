"""Verify the full evaluation/traces lesson scope offline."""

from __future__ import annotations

import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LESSON_PATH = ROOT / "src/content/chapters/evaluation/09-traces.mdx"
META_PATH = ROOT / "src/content/chapters/evaluation/meta.ts"
RESOURCES_PATH = ROOT / "src/content/curriculum/resources.ts"
LESSON = LESSON_PATH.read_text(encoding="utf-8")
META = META_PATH.read_text(encoding="utf-8")
RESOURCES = RESOURCES_PATH.read_text(encoding="utf-8")


def fenced_blocks(language: str) -> list[str]:
    return re.findall(rf"```{re.escape(language)}\s*\n(.*?)```", LESSON, re.DOTALL)


class EvaluationTracesW6(unittest.TestCase):
    def test_provider_sources_are_correctly_distinguished(self) -> None:
        self.assertIn("OpenAI Agents API 的 tracing 文档", LESSON)
        self.assertIn("Python Agents SDK", LESSON)
        self.assertIn("https://developers.openai.com/api/docs/guides/agents-api/tracing", LESSON)
        self.assertIn("https://openai.github.io/openai-agents-python/tracing/", LESSON)
        self.assertIn("openai-agents-sdk-tracing", META)
        self.assertIn("openai-agents-sdk-tracing", RESOURCES)

    def test_sensitive_capture_default_is_not_overgeneralized(self) -> None:
        self.assertIn("OpenTelemetry 的 GenAI 语义约定", LESSON)
        self.assertIn("建议默认不采集完整指令、输入和输出", LESSON)
        self.assertIn("这是约定建议，不保证各 SDK 的默认行为", LESSON)
        self.assertIn("`trace_include_sensitive_data` 默认开启", LESSON)
        self.assertIn("可设为 `False` 关闭这类内容捕获", LESSON)
        self.assertIn("不能只注册一个附加 redaction processor", LESSON)
        self.assertIn("默认 exporter 仍会运行", LESSON)
        checkpoint = META.split("id: 'what-a-trace-needs'", 1)[1].split("id: 'cost-attribution'", 1)[0]
        self.assertIn("默认值为 `True`", checkpoint)
        self.assertIn("OpenTelemetry GenAI 语义约定", checkpoint)

    def test_registered_sources_cover_the_documented_checkpoint(self) -> None:
        checkpoint = META.split("id: 'what-a-trace-needs'", 1)[1].split("id: 'cost-attribution'", 1)[0]
        for source_id in ("openai-agents-tracing", "openai-agents-sdk-tracing", "opentelemetry-genai-semconv"):
            self.assertIn(source_id, checkpoint)
        lesson_meta = META.split("id: 'evaluation/traces'", 1)[1].split("id: 'evaluation/confidence'", 1)[0]
        self.assertIn("openai-agents-sdk-tracing", lesson_meta)

    def test_all_published_python_fences_compile(self) -> None:
        fences = fenced_blocks("python")
        self.assertEqual(len(fences), 4)
        for index, fence in enumerate(fences, 1):
            compile(fence, f"{LESSON_PATH}:fence-{index}", "exec")

    def test_full_local_demo_matches_its_published_stdout_exactly(self) -> None:
        fence = next(block for block in fenced_blocks("python") if "def get_shipping" in block)
        published = next(block for block in fenced_blocks("text") if "=== 只有最终答案时" in block)
        result = subprocess.run(
            [sys.executable, "-c", fence],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertEqual(result.stdout.rstrip(), published.rstrip())
        self.assertIn("passed=False", result.stdout)
        self.assertIn("轨迹证明了值的来源与传播；还需检查契约和校验逻辑才能确认根因。", result.stdout)

    def test_eta_fixture_and_validator_have_a_narrow_claim(self) -> None:
        fence = next(block for block in fenced_blocks("python") if "def get_shipping" in block)
        namespace: dict[str, object] = {}
        exec(fence, namespace)
        validator = namespace["valid_rfc3339_timestamp"]
        self.assertFalse(validator(1288.5))
        self.assertFalse(validator("2026-10-21 14:03:21+08:00"))
        self.assertTrue(validator("2026-10-21T14:03:21+08:00"))
        self.assertIn("轨迹提供的是**可关联的执行证据**", LESSON)
        self.assertIn("它不能记录模型的完整内部推理，也不能单独证明根因", LESSON)

    def test_trace_to_case_never_copies_raw_input_or_invents_expected_behavior(self) -> None:
        fence = next(block for block in fenced_blocks("python") if "def trace_to_case(" in block)
        namespace: dict[str, object] = {}
        exec(fence, namespace)
        case = namespace["trace_to_case"](
            [{"is_error": True, "tool": "get_shipping", "task_input": "raw secret"}],
            case_id="case-001",
            redacted_input="脱敏后的订单查询",
            failure_summary="eta 字段类型不符合契约",
        )
        self.assertEqual(case["question"], "脱敏后的订单查询")
        self.assertNotIn("raw secret", repr(case))
        self.assertIn("预期行为待人工", case["expected"])
        self.assertIn("经审核的线上失败轨迹", case["source"])

    def test_usage_attribution_and_tool_latency_remain_separate(self) -> None:
        self.assertIn("不能把模型 usage 重复记到每个工具 span", LESSON)
        self.assertIn("usage 记到产生它的模型请求", LESSON)
        self.assertIn("耗时记到对应操作", LESSON)
        self.assertNotIn('usage["in"]', LESSON)

    def test_trace_sampling_and_eval_sampling_are_distinct(self) -> None:
        for phrase in (
            "审计必须全量",
            "审计不能采样",
            "成功的按 1% 到 10% 采",
            "每一条线上失败都应该变成一条评测用例",
            "每一条线上失败都该变成一条用例",
        ):
            self.assertNotIn(phrase, LESSON)
        self.assertIn("另行维护代表性生产样本", LESSON)
        self.assertIn("不能把便利采样当作代表性样本", LESSON)
        self.assertIn("保留纳入概率、分层与权重", LESSON)

    def test_sensitive_payload_controls_and_hash_limit_are_explicit(self) -> None:
        for phrase in ("白名单", "脱敏规则", "访问控制", "保留期限", "哈希不是数据检索地址", "不能保证匿名化"):
            self.assertIn(phrase, LESSON)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(EvaluationTracesW6)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print(
        f"providerCalls=0; externalNetworkCalls=0; tests={result.testsRun}; "
        f"failures={len(result.failures) + len(result.errors)}"
    )
    raise SystemExit(not result.wasSuccessful())
