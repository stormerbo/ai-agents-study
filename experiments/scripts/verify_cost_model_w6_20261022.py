#!/usr/bin/env python3
"""Whole-lesson W6 checks for cost-model usage provenance, price sources, and output."""
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


# The lesson's model and all historical evidence must remain appropriately scoped.
check("不是四个互斥的账单项目" in text, "overlapping cost views are presented as additive billable categories")
check("每轮都提交完整的、随轮数增加的上下文" in text, "quadratic model assumptions are missing")
check("缺少可独立核验的逐次原始响应" in text, "historical token ratio lacks a provenance boundary")
check("不能据此确认各拓扑质量等价" in text, "historical multi-agent token ratios imply cost/quality equivalence")
check("不能把总量和它的明细再次相加" in text, "provider usage total/detail double-counting boundary is missing")
check("不是 provider 实测或账单" in text and "输出的情景单位" in text, "scenario arithmetic is presented as provider invoice evidence")

# Current official price references must be cited by the documented checkpoint.
for source_id, url in (
    ("claude-pricing", "https://platform.claude.com/docs/en/about-claude/pricing"),
    ("deepseek-models-pricing", "https://api-docs.deepseek.com/quick_start/pricing/"),
    ("openai-api-pricing", "https://developers.openai.com/api/docs/pricing"),
):
    check(f"'{source_id}'" in meta, f"checkpoint lacks source id {source_id}")
    block = re.search(rf"'{re.escape(source_id)}': \{{(.*?)\n  \}}", resources, re.DOTALL)
    check(block is not None, f"resource is not registered: {source_id}")
    assert block is not None
    check(url in block.group(1), f"resource URL differs for {source_id}")
    check("verifiedAt: '2026-10-22'" in block.group(1), f"resource verification date stale: {source_id}")

# The second program's complete stdout is executed; displayed lines are exact excerpts.
fences = re.findall(r"```python\s*\n(.*?)\n```", text, re.DOTALL)
check(len(fences) == 2, f"expected two Python fences, found {len(fences)}")
outputs: list[str] = []
for code in fences:
    compile(code, str(LESSON), "exec")
    with tempfile.NamedTemporaryFile("w", suffix=".py", encoding="utf-8") as script:
        script.write(code)
        script.flush()
        outputs.append(subprocess.run([sys.executable, script.name], capture_output=True, text=True, check=True).stdout)
output = outputs[1]
check("P50=483  P90=622  P99=622" in output, "nearest-rank output does not match recomputed sample")
check("工具定义情景估算 ≈ 240 token，占输入侧 1999 的 12.0%。" in output, "schema scenario output changed")
check("程序输出摘录（关键结果）：" in text, "partial stdout is labeled as complete output")
check("工具定义情景估算 ≈ 240 token，占输入侧 1999 的 12.0%。" in text, "displayed schema line does not match executable stdout")
check("上述本地程序输出：" not in text, "incomplete output block is still labeled complete")

print(f"cost-model-w6: {checks}/{checks} checks passed; 2 Python fences executed; providerCalls=0; externalNetworkCalls=0")
