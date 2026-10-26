#!/usr/bin/env python3
"""Whole-lesson W6 checks for latency claims, source identity, and examples."""
from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/cost-and-latency/02-latency-sources.mdx"
META = ROOT / "src/content/chapters/cost-and-latency/meta.ts"
RESOURCES = ROOT / "src/content/curriculum/resources.ts"
DATA = ROOT / "docs/DATA.md"
text = LESSON.read_text(encoding="utf-8")
meta = META.read_text(encoding="utf-8")
resources = RESOURCES.read_text(encoding="utf-8")
checks = 0


def check(condition: bool, label: str) -> None:
    global checks
    checks += 1
    if not condition:
        raise AssertionError(label)


def resource_block(resource_id: str) -> str:
    match = re.search(rf"'{re.escape(resource_id)}': \{{(.*?)\n  \}}", resources, re.DOTALL)
    check(match is not None, f"resource is missing: {resource_id}")
    assert match is not None
    return match.group(1)


# Full-lesson epistemic boundaries and measurement definitions.
check("无法独立复现" in text and "原始逐次请求与响应" in text, "historical timing summary is not clearly unreproducible")
check("不能推断" in text and "不应标成纯 prefill 时长" in text, "timing observations are generalized beyond what client timing can show")
check("TTFT" in text and "TPOT" in text and "首个可见文本时间" in text and "任务端到端延迟" in text, "the four measurement boundaries are incomplete")
check("串行阶段求和" in text and "并行分支取最长" in text and "汇合开销" in text, "critical-path model omits serial/parallel overhead")
check("monotonic clock" in text and "任务级 deadline" in text and "幂等与取消语义" in text, "trace and deadline guidance is incomplete")
check("不能把内部思考内容暴露为进度" in text and "并不保证缩短最终任务时间" in text, "perceived-latency advice leaks reasoning or promises task-time reduction")
check("保存逐次原始时间戳" in text and "request ID" in text, "the controlled latency experiment lacks raw per-request evidence")

# Verify that each documented source is the exact source named by its metadata.
for source_id in ("openai-latency-optimization", "anthropic-reduce-latency", "claude-streaming", "pd-serve-paper"):
    check(f"'{source_id}'" in meta, f"checkpoint does not cite {source_id}")
    block = resource_block(source_id)
    check("verifiedAt: '2026-10-22'" in block, f"source date is stale for {source_id}")

paper = resource_block("pd-serve-paper")
check("DistServe: Disaggregating Prefill and Decoding for Goodput-optimized Large Language Model Serving" in paper, "paper title does not match DistServe metadata")
check("https://arxiv.org/abs/2401.09670" in paper, "DistServe resource URL points to a different paper")

# Both complete Python fences must compile and run, with exact expected observations.
fences = re.findall(r"```python\s*\n(.*?)\n```", text, re.DOTALL)
check(len(fences) == 2, f"expected two Python fences; got {len(fences)}")
outputs: list[str] = []
for code in fences:
    compile(code, str(LESSON), "exec")
    with tempfile.NamedTemporaryFile("w", suffix=".py", encoding="utf-8") as handle:
        handle.write(code)
        handle.flush()
        outputs.append(subprocess.run([sys.executable, handle.name], capture_output=True, text=True, check=True).stdout)
check("n= 4" in outputs[0] and "首事件时间范围：0.64–1.22s" in outputs[0], "historical summary output is incorrect")
check("展示值相减所得残差中位数：2.19s；范围：0.35–6.78s" in outputs[0], "displayed residual statistics are incorrect")
check("短输入短输出: 记录生成=0.59s；记录总计-首事件=0.60s" in outputs[0], "first rounding discrepancy is not reproduced")
check("长输入短输出: 记录生成=0.36s；记录总计-首事件=0.35s" in outputs[0], "second rounding discrepancy is not reproduced")
check("首个可见文本事件序号： 2" in outputs[1], "event classifier does not skip thinking and tool-JSON deltas")
check("text_delta" in text and "input_json_delta" in text and "thinking_delta" in text, "Anthropic stream event example is incomplete")

print(f"latency-sources-w6: {checks}/{checks} checks passed; 2 Python fences executed; providerCalls=0; externalNetworkCalls=0")
