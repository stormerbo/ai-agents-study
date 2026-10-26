from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/human-in-the-loop/01-automation-levels.mdx"
META = ROOT / "src/content/chapters/human-in-the-loop/meta.ts"
text = LESSON.read_text(encoding="utf-8")
meta = META.read_text(encoding="utf-8")
checks = 0


def check(condition: bool, message: str) -> None:
    global checks
    checks += 1
    if not condition:
        raise AssertionError(message)


fences = re.findall(r"```python\n(.*?)\n```", text, re.S)
check(len(fences) == 2, f"expected 2 Python fences, got {len(fences)}")
for index, source in enumerate(fences, 1):
    compile(source, f"automation-levels-fence-{index}", "exec")

with tempfile.TemporaryDirectory() as tmp:
    policy_path = Path(tmp) / "policy.py"
    policy_path.write_text(fences[0], encoding="utf-8")
    subprocess.run([sys.executable, str(policy_path)], check=True, capture_output=True, text=True)
    simulation_path = Path(tmp) / "simulation.py"
    simulation_path.write_text(fences[1], encoding="utf-8")
    result = subprocess.run([sys.executable, str(simulation_path)], check=True, capture_output=True, text=True)
output = result.stdout
rows = {}
for line in output.splitlines():
    parts = line.split()
    if len(parts) == 5 and parts[0] in {"A", "B", "C", "D"}:
        rows[parts[0]] = parts[2:]
check(rows.get("A") == ["7", "0", "0"], "A must be 7 pre-approvals, 0 post-reviews, 0 unapproved risk actions")
check(rows.get("B") == ["2", "0", "0"], "B must be 2 pre-approvals, 0 post-reviews, 0 unapproved risk actions")
check(rows.get("C") == ["1", "0", "1"], "C must be 1 pre-approval, 0 post-reviews, 1 unapproved risk action")
check(rows.get("D") == ["0", "1", "2"], "D must distinguish one post-review from two already executed risk actions")
check("D 任务结束后复核一次" in output, "D must name post-execution review accurately")
check("五档" in text and all(label in text for label in ["全自动", "事后复核", "关键点确认", "逐步确认", "人做主"]),
      "the lesson must consistently describe its five-part engineering taxonomy")
check("不是标准规定的唯一分类" in text, "the taxonomy must not be presented as universal")
check("没有权限的动作应拒绝" in text and "不能靠用户点一次确认来补齐授权" in text,
      "human approval must not replace authorization")
check("不是发给模型的参数字段" in text, "trusted reversibility metadata must be separate from model input schema")
check("当前仓库没有逐次原始请求/响应" in text and "不能证明模型总体上是否能识别可逆性" in text,
      "historical model observations must remain explicitly unverified")
check("不能说明模型通常能否识别可逆性" in text and "为什么不能指望模型自己判断" not in text,
      "the historical sample must not be framed as proof of model capability")
check("预先约定的评测结果、运行监控" in text,
      "policy relaxation must rely on evidence")
check("不是确定性" not in text and "可以互相替代" not in text,
      "do not claim approval and controls are interchangeable")
check("新模型、新工具或策略变更可以触发" in text and "自动决定" in text,
      "rollout changes must not be treated as automatic promotion/demotion")
check("五类人工介入方式" in meta and "不证明团队一定会降低阈值" in meta,
      "metadata checkpoints must match revised lesson and avoid causal claims")

print(f"PASS {checks}/{checks}; Python fences compiled={len(fences)}; policy assertions executed; simulation executed; providerCalls=0")
print(output)
