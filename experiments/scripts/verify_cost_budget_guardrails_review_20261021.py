"""Offline review checks for cost-and-latency/budget-guardrails.

This validates editorial boundaries, registered sources and the displayed local
examples. It does not call providers or reproduce archived provider usage.
"""

from __future__ import annotations

import contextlib
import io
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/cost-and-latency/05-budget-guardrails.mdx"
META = ROOT / "src/content/chapters/cost-and-latency/meta.ts"
RESOURCES = ROOT / "src/content/curriculum/resources.ts"


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    body = LESSON.read_text()
    meta = META.read_text()
    resources = RESOURCES.read_text()
    count = 0

    def ok(condition: bool, message: str) -> None:
        nonlocal count
        check(condition, message)
        count += 1

    ok("固定为 3000 token，30 轮累计输入是 9 万 token" in body,
       "fixed-input arithmetic must remain linear")
    ok("总和为 1,395,000 token" in body,
       "growing-context example must retain the corrected sum")
    ok("max_tokens` 通常限制模型生成的输出" in body,
       "output cap must be distinguished from task budget")
    ok("不等于请求总 token、整个任务预算或美元费用上限" in body,
       "max_tokens boundary is incomplete")
    ok("请求前预留资源" in body and "响应后以 provider-specific usage 对账" in body,
       "pre-call reserve and post-call reconciliation are both required")
    ok("不能假设成本为零" in body and "不能将 unknown 当 zero" in body,
       "unknown usage/timeout cannot be treated as zero")
    ok("预算耗尽后的行为取决于任务契约" in body,
       "partial completion must be task-contract dependent")
    ok("不能把部分结果伪装成成功" in body,
       "atomic/complete tasks must not silently succeed with partial output")
    ok("无进展检测" in body,
       "agent no-progress detection must be distinguished from dependency breaker")
    ok("OPEN" in body and "HALF_OPEN" in body and "冷却" in body,
       "breaker lifecycle must include open, cooldown and half-open")
    ok("provider/model、错误类别" in body and "高基数标识" in body,
       "metrics need denominator/low-cardinality dimensions")
    ok("P99 的 2 到 3 倍" not in body and "周同比翻倍" not in body,
       "unsupported fixed threshold rules remain")
    ok("L90 说" not in body and "L90" not in body,
       "unsupported lesson-local source label remains")
    ok("stop_reason: max_tokens` 定义为达到本次输出上限" in body,
       "max_tokens stop reason must be accurately scoped")
    ok("按目标 endpoint 的 usage 与费率定义校验" in body,
       "provider usage and price fields must be scoped")
    ok("不能把下列本地快照公式当成 provider 通用字段" in body,
       "historical normalized usage schema must be identified as local")
    ok("不能构成真正的请求前闸门" in body,
       "historical replay must not be presented as a live pre-call gate")
    ok("失败调用不计入模拟用量" in body,
       "toy simulation must disclose unmodeled failed-call usage")
    ok("正常跑完" not in body and "22 次无用调用" not in body,
       "stale simulation labels or failure count remain")
    ok("flowchart TB\\n" not in body,
       "Mermaid graph contains literal escape sequences")

    source_ids = (
        "openai-spend-limits",
        "anthropic-stop-reasons",
        "claude-pricing",
        "deepseek-chat-api",
        "aws-circuit-breaker",
        "azure-circuit-breaker",
    )
    for source_id in source_ids:
        ok(f"'{source_id}'" in meta, f"metadata missing source {source_id}")
        ok(f"id: '{source_id}'" in resources, f"source registry missing {source_id}")

    fences = re.findall(r"```python\n(.*?)\n```", body, re.S)
    ok(len(fences) == 2, "expected two complete Python examples")
    outputs: list[str] = []
    for index, fence in enumerate(fences, start=1):
        code = compile(fence, f"budget-guardrails-fence-{index}", "exec")
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            exec(code, {"__name__": "__main__"})
        outputs.append(output.getvalue())
        ok(bool(output.getvalue()), f"Python example {index} produced no output")

    first, second = outputs
    ok("持续成功但预算先到上限" in first,
       "first demo scenario label does not match its budget outcome")
    ok("第 20 轮故障未到达：预算先到上限" in first,
       "third demo scenario must disclose that the breaker failure is never reached")
    ok("熔断阈值 3" in first and "连续失败达到阈值" in first,
       "breaker toy demo output is incomplete")
    ok("预算 2000  -> ok        已用 1999" in second,
       "historical snapshot total does not match displayed output")
    ok("预算 1500  -> budget    已用 1377" in second,
       "historical replay's 1500 budget row changed")
    ok("预算 1200  -> budget    已用 824" in second,
       "historical replay's 1200 budget row changed")

    # Arithmetic is explicit so an accidental prose-only edit cannot alter it.
    ok(3_000 * 30 == 90_000, "fixed-input arithmetic check failed")
    ok(sum(range(3_000, 90_001, 3_000)) == 1_395_000,
       "growing-context arithmetic check failed")

    print(json.dumps({
        "status": "pass",
        "testsPassed": count,
        "testsFailed": 0,
        "testCount": count,
        "pythonFencesCompiledAndExecuted": len(fences),
        "providerCalls": 0,
        "historicalRunReproduced": False,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
