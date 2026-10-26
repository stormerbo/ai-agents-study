"""Review the evaluation/traces lesson's evidence boundaries and runnable examples."""

from __future__ import annotations

import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/evaluation/09-traces.mdx"


def source() -> str:
    return LESSON.read_text(encoding="utf-8")


def python_fences() -> list[str]:
    return re.findall(r"```python\s*\n(.*?)```", source(), re.DOTALL)


class TraceLessonTests(unittest.TestCase):
    def test_no_universal_failure_ingestion_or_trace_retention_claim(self) -> None:
        text = source()
        for phrase in (
            "每一条线上失败都应该变成一条评测用例",
            "每一条线上失败都该变成一条用例",
            "审计必须全量",
            "审计不能采样",
            "成功的按 1% 到 10% 采",
            "14 天",
        ):
            self.assertNotIn(phrase, text)

    def test_sensitive_payload_and_sampling_boundaries_are_explicit(self) -> None:
        text = source()
        self.assertIn("脱敏", text)
        self.assertIn("访问控制", text)
        self.assertIn("不能把便利采样当作代表性样本", text)
        self.assertIn("哈希不是数据检索地址", text)

    def test_model_usage_is_attached_to_model_calls(self) -> None:
        text = source()
        self.assertIn("不能把模型 usage 重复记到每个工具 span", text)
        self.assertNotIn('usage["in"]', text)

    def test_all_python_fences_compile(self) -> None:
        for index, fence in enumerate(python_fences(), start=1):
            compile(fence, f"{LESSON}:python-fence-{index}", "exec")

    def test_complete_example_runs_and_limits_its_claim(self) -> None:
        fence = next(f for f in python_fences() if "def get_shipping" in f)
        result = subprocess.run(
            [sys.executable, "-c", fence],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertIn("工具契约要求 eta 是 RFC 3339 时间戳", result.stdout)
        self.assertIn("passed=False", result.stdout)
        self.assertIn("它证明数据流，不单独证明根因", result.stdout)
        self.assertNotIn("这个结论**只有轨迹能给出**", result.stdout)
        namespace: dict[str, object] = {}
        exec(fence, namespace)
        validator = namespace["valid_rfc3339_timestamp"]
        self.assertFalse(validator(1288.5))
        self.assertFalse(validator("2026-10-21 14:03:21+08:00"))
        self.assertTrue(validator("2026-10-21T14:03:21+08:00"))

    def test_transcript_includes_the_contract_failure_evidence(self) -> None:
        transcript = next(
            block for block in re.findall(r"```text\s*\n(.*?)```", source(), re.DOTALL)
            if "=== 有轨迹时 ===" in block
        )
        self.assertIn("契约校验 field=eta expected=RFC 3339 timestamp passed=False", transcript)
        self.assertIn("不单独证明根因", transcript)

    def test_trace_to_case_example_is_self_contained(self) -> None:
        text = source()
        self.assertIn("def trace_to_case(trace, case_id, redacted_input, failure_summary)", text)
        self.assertNotIn('ids[0]["task_input"]', text)
        fence = next(f for f in python_fences() if "def trace_to_case(" in f)
        namespace: dict[str, object] = {}
        exec(fence, namespace)
        case = namespace["trace_to_case"](
            [{"is_error": True, "tool": "get_shipping"}],
            case_id="case-001",
            redacted_input="脱敏后的订单查询",
            failure_summary="eta 字段类型不符合契约",
        )
        self.assertEqual(case["id"], "case-001")
        self.assertEqual(case["question"], "脱敏后的订单查询")
        self.assertIn("预期行为待人工", case["expected"])
        self.assertEqual(case["source"], "经审核的线上失败轨迹")


if __name__ == "__main__":
    unittest.main(verbosity=2)
