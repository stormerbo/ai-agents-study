from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/multi-agent/05-alternatives.mdx"
META = ROOT / "src/content/chapters/multi-agent/meta.ts"
text = LESSON.read_text(encoding="utf-8")
meta = META.read_text(encoding="utf-8")
checks: list[str] = []


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)
    checks.append(message)


fences = re.findall(r"```python\s*\n(.*?)\n```", text, re.S)
check(len(fences) == 4, f"found {len(fences)} Python fences")
for index, source in enumerate(fences):
    compile(source, f"{LESSON.name}:python-fence-{index}", "exec")
    checks.append(f"Python fence {index} compiles")

check("14.4 倍支持这个选择" in text, "14.4x comparison is explicitly scoped")
check("不能量化工具与 agent 的成本差距" in text, "cross-boundary result not used as tool/agent cost evidence")
check("旧报告只留有汇总数字" in text, "historical experiment trace limitation disclosed")
check("按顺序执行 worker" in text and "没有实现并行" in text, "serial harness not described as parallel")
check("没有测量延迟" in text, "historical harness not used for latency claims")
check("只有 `stop_reason == \"end_turn\"` 且提取到非空文本时才返回" in text, "non-final and empty responses are excluded")
check("usage.get(\"output_tokens\", 0)" in fences[-1], "output tokens measured separately")
check("input_tokens" in fences[-1], "input tokens measured separately")
check("硬约束存活" not in text, "substring-based hard-constraint scoring removed")
check("机制解释：多智能体只把" not in text, "unsupported input-only multiplier explanation removed")
check("3 倍”可作为团队筛查阈值" not in text, "arbitrary 3x screening value removed")
check("筛查值应由团队按风险和服务目标预先设定" in text, "thresholds remain product-specific")
check("14 倍量级" not in text, "unsupported 14x architecture comparison removed")
check("贵 8 倍" not in text, "unsupported fixed cost multiplier removed")
check("20% 时，按需取比全量预加载更省" not in meta, "retrieval threshold no longer generalized in checkpoint")
check("角色设定不会改变模型的推理能力" not in meta, "role prompt not claimed to have no behavior effect")
check("90% 的成功率" not in meta, "single-agent score not treated as multi-agent ceiling")
check("单 agent 和候选方案对同一任务集做配对比较" in text, "paired task-set comparison prescribed")
check("以任务/用户为抽样单位" in text, "sampling unit limitation stated")
check("本例只汇总给定延迟记录，不模拟调度" in text, "illustrative fixture not treated as scheduler measurement")
check("调用方仍可能需要模型来选择" in text, "deterministic tool does not imply model-free caller")
check("实际并发且子任务可独立推进时" in text, "parallel benefit is conditional on actual independent concurrency")
check("质量、覆盖、风险边界或时延" in text, "architecture decision includes multiple outcome dimensions")
check("没有任何一步由模型决定" in text, "workflow example is bounded to fixed control flow")

# Execute the legacy response parser against a local empty-final-response fixture.
legacy_ns: dict[str, object] = {}
exec(fences[-1], legacy_ns)
legacy_os = legacy_ns["os"]
legacy_urllib = legacy_ns["urllib"]
legacy_os.environ.update({
    "VERIFY_MODEL": "fixture-model",
    "ANTHROPIC_BASE_URL": "http://127.0.0.1:1",
    "ANTHROPIC_AUTH_TOKEN": "fixture-key",
})


class EmptyFinalResponse:
    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return b'{"stop_reason":"end_turn","content":[],"usage":{"input_tokens":0,"output_tokens":0}}'


legacy_urllib.request.urlopen = lambda *_args, **_kwargs: EmptyFinalResponse()
try:
    legacy_ns["call"]([], "fixture")
except RuntimeError as error:
    check("no text" in str(error).lower(), "empty end_turn response is rejected")
else:
    check(False, "empty end_turn response is rejected")

# Execute only the fully local, constructed paired-metrics example (Python fence 2).
paired = subprocess.run(
    [sys.executable, "-c", fences[2]],
    check=True,
    capture_output=True,
    text=True,
)
check("single: {'tasks': 4, 'passed': 2, 'input_tokens': 4000, 'output_tokens': 790, 'mean_seconds': 2.2}" in paired.stdout,
      "constructed single-agent metrics output matches")
check("multi: {'tasks': 4, 'passed': 3, 'input_tokens': 11100, 'output_tokens': 1950, 'mean_seconds': 2.55}" in paired.stdout,
      "constructed multi-agent metrics output matches")
check("'only_multi_passed': 1" in paired.stdout and "'only_single_passed': 0" in paired.stdout,
      "paired discordant outcomes match constructed fixture")

# Execute the fixed workflow example (Python fence 1).
workflow = subprocess.run(
    [sys.executable, "-c", fences[1]],
    check=True,
    capture_output=True,
    text=True,
)
check("订单服务延迟上升" in workflow.stdout and "缓存未设上限" in workflow.stdout,
      "fixed workflow output matches its bounded example")

print(f"{len(checks)} checks passed; providerCalls=0")
