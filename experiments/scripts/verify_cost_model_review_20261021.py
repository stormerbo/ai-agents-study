#!/usr/bin/env python3
"""Offline review checks for cost attribution, provider usage, and toy arithmetic."""

from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/cost-and-latency/01-cost-model.mdx"
META = ROOT / "src/content/chapters/cost-and-latency/meta.ts"
RESOURCES = ROOT / "src/content/curriculum/resources.ts"
text = LESSON.read_text(encoding="utf-8")
meta = META.read_text(encoding="utf-8")
resources = RESOURCES.read_text(encoding="utf-8")
checks = 0


def check(condition: bool, label: str) -> None:
    global checks
    checks += 1
    if not condition:
        raise AssertionError(label)


# Cost categories must not double-count billable usage or imply universal traces.
check("分析视角会交叉" in text, "overlapping cost drivers are presented as disjoint billable categories")
check("工具定义是输入的一部分" in text, "tool schema is not identified as part of input usage")
check("不得把已含在 usage 的工具定义再加一遍" in text, "double-counting guard is missing")
check("只有当每轮提交完整且上下文逐轮增长" in text, "quadratic cost model lacks its full-resend assumption")
check("Stateless" in text and "server-side state" in text, "request-state alternatives are not covered")
check("轮数翻倍" in text and "不是每个 N 都精确成立" in text, "quadratic asymptotic is framed as exact")

# Old experiments are not used as verified quality, cost, or causal comparisons.
check("单次调用 365 token" in text and "workflow 619 token" in text and "agent 1625 token" in text, "historical implementation comparison was removed")
check("不可独立复核" in text, "historical comparison is not marked non-reproducible")
check("不能证明各方案任务质量等价" in text, "token comparison is treated as equal-quality cost evidence")
check("8.1 倍" in text and "token 比值当作费用倍数" in text, "multi-agent historical token ratio is overgeneralized")
check("678/1326/2623/4945" in text and "不是隔离测得的 schema token" in text, "tool count summary overclaims schema cost")

# Usage fields and billing formulas must be provider-scoped.
check("Anthropic Messages API" in text and "DeepSeek Chat API" in text and "OpenAI" in text, "provider-specific usage contracts are missing")
check("不得把 Anthropic 的字段公式套给其他 provider" in text, "Anthropic aggregation is treated as universal")
check("`prompt_cache_hit_tokens`" in text and "cached_tokens" in text, "DeepSeek/OpenAI cached usage distinctions are missing")
check("按账单费率分别计算未缓存、缓存读取、缓存写入与输出" in text, "usage isn't mapped to distinct billed rates")
check("输出 token rate 因 provider 与 model 而异" in text, "output pricing generalization is too broad")

# Scenario calculations are labeled and internally coherent.
check("不是 provider 账单" in text, "scenario table is presented as actual billed cost")
check("工具 schema 与上下文假设分开" in text, "scenario's input and schema components are ambiguous")
check("输出和工具定义保持不变" in text, "four-agent sensitivity case fails to state held-constant quantities")
check("不是多 agent 工作流的完整总成本" in text, "isolated sensitivity case is presented as real topology cost")
check("scenario_cost_units" in text, "toy code labels a synthetic arithmetic proxy as billed cost")
check("使用各次调用实际 usage" in text, "recommended cost method isn't trace-based")

# Percentile method and displayed output must agree on small n.
check("最近秩法" in text, "percentile method is not defined")
check("math.ceil" in text, "percentile implementation is not nearest-rank")
check("P50=483  P90=622  P99=622" in text, "displayed percentile values are incorrect")
check("statistics.quantiles" not in text, "unexpected alternative percentile method")

# Historical JSON is a normalized excerpt, not raw provider data.
check("规范化的历史记录摘要" in text, "four-call JSON is presented as raw provider trace")
check("原始逐次请求/响应未归档" in text, "missing original request/response caveat")
check("cache_read" in text and "provider 字段" in text, "normalized usage field mapping is ambiguous")

for source_id in (
    "claude-pricing",
    "claude-prompt-caching",
    "deepseek-chat-api",
    "deepseek-context-caching",
    "openai-prompt-caching",
):
    check(f"'{source_id}'" in meta, f"metadata missing source id: {source_id}")
    check(f"id: '{source_id}'" in resources, f"resource id not registered: {source_id}")

# Run each lesson Python fence and compare output with the displayed scenario table.
fences = re.findall(r"```python\s*\n(.*?)\n```", text, re.DOTALL)
check(len(fences) == 2, f"expected two Python fences, found {len(fences)}")
outputs = []
for code in fences:
    compile(code, str(LESSON), "exec")
    with tempfile.NamedTemporaryFile("w", suffix=".py", encoding="utf-8") as script:
        script.write(code)
        script.flush()
        outputs.append(subprocess.run([sys.executable, script.name], capture_output=True, text=True, check=True).stdout)
check("单轮，无工具" in outputs[0] and "59,070" not in outputs[0], "first scenario code labels non-billable proxy as invoice")
check("59070" in outputs[0] and "62.4%" in outputs[0], "scenario arithmetic changed unexpectedly")
check("P50=483" in outputs[1] and "P90=622" in outputs[1], "record percentile output disagrees with prose")
check("12.0%" in outputs[1], "tool token share differs from displayed scenario output")

print(f"cost-model-review: {checks}/{checks} checks passed; 2 Python fences executed; providerCalls=0")
