"""Full-scope editorial, source, and fixture checks for coding-agent/why-coding-agent."""
from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/coding-agent/01-why-coding-agent.mdx"
META = ROOT / "src/content/chapters/coding-agent/meta.ts"
RESOURCES = ROOT / "src/content/curriculum/resources.ts"
LEGACY_FIXTURE = ROOT / "experiments/fixtures/coding-recover-invalid-assertion.txt"
checks = 0


def check(condition: bool, message: str) -> None:
    global checks
    checks += 1
    if not condition:
        raise AssertionError(message)


lesson = LESSON.read_text(encoding="utf-8")
meta = META.read_text(encoding="utf-8")
resources = RESOURCES.read_text(encoding="utf-8")

# Scope: deterministic checks are useful for some coding tasks, not unique to them.
for phrase in (
    "许多代码任务恰好有可执行的项目检查",
    "这不是 coding agent 独有的优势",
    "其他 agent 也可能用状态检查、确定性 grader、LLM grader 或人工评审",
    "有效性取决于规格、断言和执行环境",
    "并不总是低或即时",
):
    check(phrase in lesson, f"bounded claim missing: {phrase}")
for stale in (
    "大多数 agent 的成败要靠外部判断",
    "它是验证信号较强、且常能程序化运行的一类 agent",
    "只能靠人读",
    "通常比让它「直接心算」可靠得多",
    "coding agent 相对其他形态最实质的优势",
    "每次都看得到上一次的真实结果",
):
    check(stale not in lesson, f"overgeneralized or obsolete statement remains: {stale}")

# Distinguish a common execution loop from a universal definition.
for phrase in (
    "本书在这里用它指一个常见执行结构",
    "每个任务必然多次调用”不是定义的一部分",
    "最后一个候选必须经过验证",
    "返回未通过状态",
):
    check(phrase in lesson, f"loop boundary missing: {phrase}")

# Keep examples conditional and make their validation limits explicit.
for phrase in (
    "下面是几种形态，不是“写代码总比直接生成结果可靠”的通用结论",
    "但仍要检查公式、输入和边界条件",
    "自然语言仍然是需求与评审依据",
    "可编辑性、复用性与体积取决于具体实现和交付场景",
    "不是仓库的完整镜像",
):
    check(phrase in lesson, f"example or context boundary missing: {phrase}")

# Run the complete local fixture, not just a syntax check.
fences = re.findall(r"^```python\s*\n([\s\S]*?)^```\s*$", lesson, re.MULTILINE)
check(len(fences) == 1, f"expected one Python fixture, got {len(fences)}")
code = fences[0]
compile(code, str(LESSON), "exec")
with tempfile.TemporaryDirectory(prefix="coding-agent-why-w6-") as directory:
    path = Path(directory) / "fixture.py"
    path.write_text(code, encoding="utf-8")
    ran = subprocess.run([sys.executable, "-I", str(path)], capture_output=True, text=True)
    check(ran.returncode == 0, f"fixture failed: {ran.stderr}")
    check(not ran.stdout and not ran.stderr, "assertion fixture should be silent")
check(code.count("assert ") == 5, "expected the five documented behavior assertions")
check("leaky_result = {\"orders\": [row[\"id\"] for row in rows]}" in code, "weak shape-only counterexample changed")
check('"o-2" not in export_order_ids(rows, "alice", grants)' in code, "cross-user denial assertion missing")

# Historical recovery evidence is still bounded and links to its detailed audit.
fixture = LEGACY_FIXTURE.read_text(encoding="utf-8").splitlines()[-1]
try:
    compile(fixture, str(LEGACY_FIXTURE), "exec")
except SyntaxError:
    pass
else:
    raise AssertionError("archived truncate assertion should remain syntactically invalid")
checks += 1
check("现有证据不足以归因模型成功/失败" in lesson, "historical result must remain unverified")
check("[验证与恢复：报错之后该给它什么](./error-recovery)" in lesson, "cross-lesson audit link missing")

# Verify the official source is registered and attached to this lesson.
check("'anthropic-demystifying-evals': {" in resources, "Anthropic eval source is not registered")
check("resourceIds: ['open-deep-research', 'aider', 'anthropic-demystifying-evals']" in meta, "lesson resource IDs are stale")
check("https://www.anthropic.com/research/demystifying-evals-for-ai-agents" in lesson, "official source link missing")
check("title: 'Coding Agent 为什么值得单独看'" in meta, "lesson title metadata is stale")
check("title: Coding Agent 为什么值得单独看" in lesson, "lesson title frontmatter is stale")

print(f"{checks}/{checks} checks passed; pythonFences=1; fixture=passed; providerCalls=0; externalNetworkCalls=0")
