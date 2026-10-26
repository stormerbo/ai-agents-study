from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/multi-agent/04-failure-modes.mdx"
META = ROOT / "src/content/chapters/multi-agent/meta.ts"
text = LESSON.read_text(encoding="utf-8")
meta = META.read_text(encoding="utf-8")
checks: list[str] = []


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)
    checks.append(message)


fences = re.findall(r"```python\s*\n(.*?)\n```", text, re.S)
check(len(fences) == 2, f"found {len(fences)} Python fences")
for index, source in enumerate(fences):
    compile(source, f"{LESSON.name}:python-fence-{index}", "exec")
    checks.append(f"Python fence {index} compiles")

handoff = subprocess.run([sys.executable, "-c", fences[0]], check=True, capture_output=True, text=True)
check("worker and supervisor handoff IDs/sources: valid" in handoff.stdout, "valid required-source fixtures pass")
check("wrong source fixture: rejected" in handoff.stdout, "wrong source fixture is detected")
check("semantic meaning and source truth: not evaluated" in handoff.stdout, "handoff checker discloses semantic limit")

metrics = subprocess.run([sys.executable, "-c", fences[1]], check=True, capture_output=True, text=True)
check('Q1 9.0%，Q2 9.5%' in metrics.stdout, "constructed overall rates use numerator/denominator totals")
probe_source = chr(10).join([
    "try:",
    "    aggregate_rate([{'period': 'Q1', 'region': '华东', 'refunds': True, 'orders': 1}])",
    "except ValueError:",
    "    print('boolean count rejected')",
    "else:",
    "    raise AssertionError('boolean count accepted')",
])
boolean_counts = subprocess.run(
    [sys.executable, "-c", fences[1] + chr(10) + probe_source],
    check=False,
    capture_output=True,
    text=True,
)
check(
    boolean_counts.returncode == 0 and "boolean count rejected" in boolean_counts.stdout,
    "boolean count values are rejected",
)
check("华东 12%→8%，华南 6%→11%" in metrics.stdout, "constructed regional trends match source rows")
check("semantic correctness、模型行为与业务授权：本例未测试" in metrics.stdout, "example discloses behavior and authorization limits")

check("不能据此估计约束丢失率" in text, "historical omission is not treated as a rate estimate")
check("不能据此说失败未复现，更不能称其为低频" in text, "substring scorer is not used to claim semantic compliance")
check("逐次请求/响应、提示、精确模型快照和判分记录没有归档" in text, "historical handoff experiment limitation is disclosed")
check("第 3 章第 5 节保留了一组历史摘要" in text and "不能把它称为费用或收益比" in text, "historical 8.1x summary is scoped and not called cost or benefit")
check("Q1 为 180/2,000 = 9%，Q2 为 190/2,000 = 9.5%" in text, "weighted rates are calculated from explicit counts")
check("换一个维度不保证矛盾消失" in text, "partitioning is not presented as a universal conflict fix")
check("不是所有多智能体拓扑共有的不变量" in text, "risks are scoped to topology and handoff design")
check("schema 能约束字段形状和类型，不能证明事实正确" in text, "schema structure is distinguished from semantic truth")
check("关键词" in text and "不能判定架构是否获益" in text, "heuristic signals are not presented as outcome proof")
check("原始请求/响应与评分未留存" in meta and "5 次工具全超时" not in meta, "metadata removes unsupported timeout anecdote")
check("anthropic-structured-outputs" in meta, "metadata links schema guarantee boundary to official source")
check("不声称多 agent 的故障都发生在边界上" in text, "lesson does not universalize failure location")

print(f"{len(checks)} checks passed; providerCalls=0")
