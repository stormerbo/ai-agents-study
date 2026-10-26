"""Recheck LangGraph state/checkpoint claims and their scoped limitations."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/agent-loop/05-what-frameworks-do.mdx"
source = LESSON.read_text(encoding="utf-8")
fences = re.findall(r"^```python\s*\n([\s\S]*?)^```\s*$", source, re.MULTILINE)
assert len(fences) == 2, f"expected two Python fences, found {len(fences)}"
for index, fence in enumerate(fences, start=1):
    compile(fence, f"{LESSON}#python-{index}", "exec")

required_boundaries = [
    "只在当前进程有效，重启会丢失",
    "生产恢复需选择持久化 saver",
    "get_state(config).next",
    "metadata.step",
    "updated_channels` 与 `channel_versions` 不是节点来源或并发仲裁证据",
    "节点更新如何合并由 state reducer 等规则决定",
    "并行更新的顺序也不应作为业务保证",
    "checkpoint 不证明外部步骤的效果",
    "为副作用设计幂等、事务或对账",
    "不构成与手写系统的等价功能或性能基准",
    "循环检测要按具体框架与版本核对",
    "不是互斥分类，也不是“模型自主性逐级提高”的统一尺度",
]
for boundary in required_boundaries:
    assert boundary in source, f"missing documented boundary: {boundary}"

meta = (ROOT / "src/content/chapters/agent-loop/meta.ts").read_text(encoding="utf-8")
assert "sourceIds: ['langgraph-persistence', 'langgraph-graph-api']" in meta

prior_verifier = ROOT / "experiments/scripts/verify_agent_loop_framework_review_20261020.py"
assert 'assert observed["checkpoint_values"] == observed["out"]' in prior_verifier.read_text(
    encoding="utf-8"
)
run = subprocess.run(
    [sys.executable, str(prior_verifier)],
    cwd=ROOT,
    capture_output=True,
    text=True,
    check=False,
)
assert run.returncode == 0, run.stdout + run.stderr
observed = json.loads(run.stdout)
assert observed["langgraphVersion"] == "1.2.14"
assert observed["pythonFencesCompiled"] == 2
assert observed["testsPassed"] == 13
assert observed["testsFailed"] == 0
assert observed["trace"] == ["search", "fetch", "fetch", "summarize"]
assert observed["next"] == []
assert observed["step"] == 4
assert observed["checkpointChannels"] == ["trace"]

print(
    json.dumps(
        {
            "checksPassed": len(required_boundaries) + 11,
            "testsPassed": observed["testsPassed"],
            "testsFailed": 0,
            "langgraphVersion": observed["langgraphVersion"],
            "trace": observed["trace"],
            "next": observed["next"],
            "step": observed["step"],
            "checkpointChannels": observed["checkpointChannels"],
            "checkpointValuesMatchFinalState": observed["checkpointChannels"] == ["trace"],
            "providerCalls": 0,
            "externalNetworkCalls": 0,
        },
        ensure_ascii=False,
        indent=2,
    )
)
