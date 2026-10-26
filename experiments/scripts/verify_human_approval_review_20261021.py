from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/human-in-the-loop/02-approval-design.mdx"
text = LESSON.read_text(encoding="utf-8")
meta = (ROOT / "src/content/chapters/human-in-the-loop/meta.ts").read_text(encoding="utf-8")
checks = 0


def check(condition: bool, message: str) -> None:
    global checks
    checks += 1
    if not condition:
        raise AssertionError(message)


fences = re.findall(r"```python\n(.*?)\n```", text, re.S)
check(len(fences) == 3, f"expected 3 Python fences, got {len(fences)}")
for index, source in enumerate(fences, 1):
    compile(source, f"lesson-python-fence-{index}", "exec")
check("approval fatigue" not in text.lower() or "不测真实用户行为、疲劳" in text,
      "fatigue claims need an explicit measurement boundary")
check("缩短 = 盲点的早期信号" not in text, "response-time heuristic must not assert blind approval")
check("单个 wrapper 本身不证明所有入口都无法绕过" in text,
      "central enforcement must not be described as proof of complete coverage")
check("审批 ID 只是查找记录的引用，不能当作授权凭据" in text,
      "approval references must not act as authorization")
check("unknown/reconciling" in text and "原子状态转换" in text,
      "approval lifecycle must represent concurrency and unknown external outcomes")
check("修改后同意" in text and "重新提交审批" in text,
      "changed proposals must require fresh approval")
check("批准后执行的就是同一组数据" in meta,
      "checkpoint must bind the reviewed preview to the executed proposal")
check("通过率或响应时间没有通用阈值" in meta and "99%" not in meta,
      "checkpoint must not present universal pass-rate or latency thresholds")

with tempfile.TemporaryDirectory() as tmp:
    script = Path(tmp) / "approval-simulation.py"
    script.write_text(fences[-1], encoding="utf-8")
    result = subprocess.run([sys.executable, str(script)], check=True, capture_output=True, text=True)
output = result.stdout
rows = {}
for line in output.splitlines():
    parts = line.split()
    if len(parts) == 5 and parts[0] in {"A", "B", "C", "D"}:
        rows[parts[0]] = parts[2:]
check(rows.get("A") == ["7", "0", "0"],
      "A must have 7 pre-action approvals, 0 post-reviews, and 0 unapproved risk actions")
check(rows.get("B") == ["2", "0", "0"],
      "B must have 2 pre-action approvals, 0 post-reviews, and 0 unapproved risk actions")
check(rows.get("C") == ["1", "0", "1"],
      "C must have 1 pre-action approval and 1 unapproved risk action")
check(rows.get("D") == ["0", "1", "2"] and "D 任务结束后复核一次" in output,
      "D must distinguish one after-the-fact review from its two unapproved actions")
check("不是实际用户负担或疲劳" in output and "风险标签由作者设定" in output,
      "simulation output must state its evidence limitations")

print(f"PASS {checks}/{checks}; Python fences compiled={len(fences)}; simulation executed; providerCalls=0")
print(output)
