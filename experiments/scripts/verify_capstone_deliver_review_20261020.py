from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/capstone/04-deliver.mdx"
META = ROOT / "src/content/chapters/capstone/meta.ts"
text = LESSON.read_text()
meta = META.read_text()
checks = []

def check(name, condition):
    checks.append((name, bool(condition)))

fences = re.findall(r"^```python\s*\n(.*?)^```\s*$", text, re.M | re.S)
for index, code in enumerate(fences, start=1):
    compile(code, f"capstone-deliver-fence-{index}", "exec")
check("all_python_fences_compile", bool(fences))
check("six_doc_sections_have_nonuniversal_order", "交付文档要有的六块" in text and "不是所有项目通用的优先级" in text)
check("trace_logging_is_minimized_and_referenced", "参数、模型输出与返回值要按数据分级选择性记录、脱敏或省略" in text and "OWASP Logging Cheat Sheet" in text)
check("approval_observation_is_sample_scoped", "特定 7 步合成任务" in text and "不能仅由可逆性决定" in text)
check("handoff_drill_requires_independent_participant", "安排一个未参与实现的人" in meta and "不等于独立交接" in meta and "不预设为半天" in meta)
check("renderer_is_explicitly_a_static_blank_outline", "只生成一份静态空白提纲" in text and "不会读取项目的范围表" in text)

# Execute the final complete Python fence with a deterministic project name and
# confirm it renders the six sections without claiming to collect project facts.
code = fences[-1]
with tempfile.TemporaryDirectory() as tmp:
    path = Path(tmp) / "handoff.py"
    path.write_text(code)
    result = subprocess.run([sys.executable, str(path)], capture_output=True, text=True, check=True)
    output = result.stdout
check("renderer_outputs_six_sections", all(f"## {title}" in output for title in ["1 怎么跑", "2 不做什么", "3 怎么验", "4 出事怎么查", "5 已知缺口", "6 判断依据"]))

failed = [name for name, passed in checks if not passed]
for name, passed in checks:
    print(f"{'PASS' if passed else 'FAIL'} {name}")
print(f"{len(checks) - len(failed)}/{len(checks)}")
if failed:
    raise SystemExit(1)
