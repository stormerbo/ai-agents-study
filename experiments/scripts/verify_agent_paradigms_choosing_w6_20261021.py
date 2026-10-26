from __future__ import annotations

import json
import pathlib
import re
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/agent-paradigms/05-choosing.mdx"
TEXT = LESSON.read_text(encoding="utf-8")
checks = []

def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)
    checks.append(message)

require("先讨论风险，再讨论控制流，是一种分析顺序" in TEXT, "analysis order is pedagogical, not mandatory")
require("影响范围、授权依据、可逆程度、幂等性与恢复路径" in TEXT, "risk considers scope, authorization, reversibility, idempotency, recovery")
require("不是“一律人工确认”的技术定律" in TEXT, "no blanket human confirmation rule")
require("条件 workflow 可以在观察后由代码路由" in TEXT, "deterministic conditional routing is a candidate")
require("是否存在回边不是判据" in TEXT and "DAG 也不等于“无分支”" in TEXT, "graph cycles are not a paradigm selection criterion")
require("Plan-Execute、ReAct 与 Reflection 不是一条必然递增的成本阶梯" in TEXT, "paradigms are not a universal cost ladder")
require("自我批评不能单独充当正确性证明" in TEXT, "reflection is not independent validation")
require("原始逐次响应未归档" in TEXT and "不能说明范式通常如何影响成本或准确率" in TEXT, "historical metrics remain non-generalizable")
require("本节「同一个实验换个对照会反转」" not in TEXT, "stale intra-lesson cross-reference removed")
require("流程伪代码，不可独立运行" in TEXT, "non-runnable sketch is labeled")
require("零模型成本" not in TEXT, "no blanket zero-cost claim")
require("ANTHROPIC_BASE_URL" not in TEXT and "urlopen" not in TEXT and "VERIFY_MODEL" not in TEXT, "provider/network code removed from offline sample")

python_fences = re.findall(r"^```python\n(.*?)^```\s*$", TEXT, re.MULTILINE | re.DOTALL)
require(len(python_fences) == 1, "one self-contained Python example fence")
program = python_fences[0]
compile(program, str(LESSON), "exec")
with tempfile.TemporaryDirectory(prefix="choosing-w6-") as directory:
    path = pathlib.Path(directory) / "fixture.py"
    path.write_text(program, encoding="utf-8")
    completed = subprocess.run([sys.executable, str(path)], capture_output=True, text=True, check=True)
expected = (
    "数据类型：本地合成夹具（不是模型实验或范式 benchmark）\n"
    "弱子串检查：PASS\n"
    "精确评分：答案=FAIL 轨迹=FAIL 终态=PASS\n"
    "正确夹具自检：PASS\n"
)
require(completed.stdout == expected, "offline example output exactly matches published contract")
require(completed.stderr == "", "offline example has no stderr")
require("import urllib" not in program and "import os" not in program, "offline sample has no provider/network or env dependency")

print(json.dumps({
    "status": "pass",
    "testsPassed": len(checks),
    "testsFailed": 0,
    "pythonFencesCompiled": 1,
    "stdoutMatchesPublishedOutput": True,
    "providerCalls": 0,
    "externalNetworkCalls": 0,
    "officialSourcesReviewed": 1,
    "historicalBenchmarksRerun": False,
    "checks": checks,
}, ensure_ascii=False, indent=2))
