from __future__ import annotations

import ast
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/agent-deployment/04-ops-loop.mdx"
text = LESSON.read_text(encoding="utf-8")
checks = 0

def check(condition: bool, message: str) -> None:
    global checks
    checks += 1
    if not condition:
        raise AssertionError(message)

# Candidate incidents must be reviewed and sanitized before they become durable eval cases.
check("candidate" in text.lower() and "领域负责人" in text, "missing candidate triage and reviewer boundary")
check("脱敏" in text and "隐私" in text, "missing privacy handling before eval retention")
check("holdout" in text.lower() and "开发集" in text, "missing explicit dev/holdout separation")
check("95%" in text and ("示例阈值" in text or "不是通用门槛" in text), "95% must be framed as illustrative, not universal")
check("分母" in text and "人工介入率" in text, "metrics need explicit denominators")
check("固定数字" not in text or "构造" in text, "numeric operational guidance must be labeled")
check("回归重放覆盖率" in text and "当前有效回归用例数" in text, "regression replay metric needs an operational denominator")
check("模型/提示词/工具/编排版本" in text, "release-level comparison must bind evaluated artifacts")
check("归档或退役用例" in text and "保留来源、版本和处置记录" in text, "retirement must preserve audit history")
check("四周之后你就有" not in text, "four-week schedule must not guarantee a working loop")
check("普通软件的行为由代码决定，代码不变行为就不变" not in text, "agent/software comparison overstates ordinary software determinism")

# Execute each Python fence and compare its stdout with the following text fence byte-for-byte.
fences = re.findall(r"```python\n(.*?)\n```", text, re.S)
outputs = re.findall(r"```text\n(.*?)\n```", text, re.S)
check(len(fences) == 1 and len(outputs) >= 2, "expected one runnable Python fence and its output fence")
proc = subprocess.run([sys.executable, "-c", fences[0]], text=True, capture_output=True, cwd=ROOT, check=True)
check(proc.stdout.rstrip("\n") == outputs[-1], "Python example stdout does not match its adjacent text fence")
check("provider" not in proc.stdout.lower(), "demo output unexpectedly suggests a live provider call")
check('eligible_tasks = [task for task in TASKS if task["terminal"]' in fences[0], "nonterminal tasks must be excluded from task-level denominators")
check("usage_rows = [task for task in eligible_tasks" in fences[0] and "usage 缺失 0 条" in proc.stdout, "token averages must expose missing-usage count")
check("未终态任务 1 条，不计入任务完成率和人工接管率。" in proc.stdout, "unfinished tasks must not count as completed successes or interventions")
namespace = {"__name__": "offline_verifier"}
exec(compile(fences[0], "lesson-example.py", "exec"), namespace)
case, decision = namespace["admit_candidate"](namespace["CANDIDATES"][0])
check(decision == "进入开发回归集", "reviewed sanitized candidate should be admitted")
check(case["split"] == "development_regression" and case["first_seen_release"] == "v12", "admitted case must retain its split and first-seen release")
check(namespace["admit_candidate"](namespace["CANDIDATES"][1])[0] is None, "unsanitized candidate must not be admitted")
check(namespace["admit_candidate"](namespace["CANDIDATES"][2])[0] is None, "duplicate candidate must not be admitted")
check(namespace["format_ratio"](0, 0) == "0/0 = N/A（分母为 0）", "zero denominator must not become 0% or crash")
check(namespace["format_token_mean"](0, 0) == "N/A（无有效 usage）", "missing usage must not become a zero-token average")
print(f"agent-deployment/ops-loop verifier: {checks}/{checks} checks passed; providerCalls=0")
