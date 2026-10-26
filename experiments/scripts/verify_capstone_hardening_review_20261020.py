from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/capstone/03-hardening.mdx"
SKELETON = ROOT / "src/content/chapters/capstone/02-skeleton.mdx"
text = LESSON.read_text()
skeleton = SKELETON.read_text()
checks = []

def check(name, condition):
    checks.append((name, bool(condition)))

fences = re.findall(r"^```python\s*\n(.*?)^```\s*$", text, re.M | re.S)
skeleton_fences = re.findall(r"^```python\s*\n(.*?)^```\s*$", skeleton, re.M | re.S)
for index, code in enumerate(fences, start=1):
    compile(code, f"capstone-hardening-fence-{index}", "exec")
for index, code in enumerate(skeleton_fences, start=1):
    compile(code, f"capstone-skeleton-fence-{index}", "exec")
check("lesson_and_skeleton_python_fences_compile", bool(fences) and bool(skeleton_fences))

agent_code = next((code for code in skeleton_fences if "def run(plan, approved_ids=(), denied_ids=()):" in code and "CASES =" in code), None)
check("hardening_import_targets_current_full_skeleton", agent_code is not None)
check("checklist_has_14_items", sum(1 for line in text.split("## 清单从哪来", 1)[1].split("## 这张表怎么读", 1)[0].splitlines() if line.startswith("| ") and "|---" not in line and "| 章 |" not in line) == 14)
manual_block = re.search(r"MANUAL = \[([\s\S]*?)\n\]", fences[0])
skip_block = re.search(r"SKIP = \[([\s\S]*?)\n\]", fences[0])
check("manual_and_skip_rows_are_explicit", bool(manual_block) and bool(skip_block) and sum(1 for line in manual_block.group(1).splitlines() if line.strip().startswith("(")) == 5 and sum(1 for line in skip_block.group(1).splitlines() if line.strip().startswith("(")) == 2)
check("major_claims_are_scoped", "不能外推总体能力、覆盖率或上线质量" in text and "不是普遍优先级" in text and "不构成生产就绪判据" in text and "按用户、租户、对象和请求上下文授权" in text)
check("logging_guidance_has_authoritative_reference", "OWASP Logging Cheat Sheet" in text and "脱敏/省略并限制访问与保留" in text)
check("tool_result_handling_is_not_claimed_as_tested", "本例没有真实模型回合" in text and "未验证结果回流时的来源标注与处理控制" in text)

with tempfile.TemporaryDirectory() as tmp:
    temp = Path(tmp)
    (temp / "capstone_agent.py").write_text(agent_code or "")
    (temp / "hardening.py").write_text(fences[0])
    run = subprocess.run([sys.executable, "hardening.py"], cwd=temp, capture_output=True, text=True, check=True)
output = run.stdout
check("local_checks_pass_and_known_gaps_fail_closed", all(token in output for token in [
    "✅ 策略对未列入 allowlist 的工具默认拒绝",
    "✅ 轨迹包含步骤和工具定位字段",
    "❌ 缺口 审批请求包含明确目标与影响范围",
    "❌ 缺口 有版本号常量",
    "✅ 六条固定冒烟用例通过",
    "✅ 任务预算上限会停止超限循环",
    "✅ 重复批准路径保持幂等",
]))
check("no_other_automatic_check_failed", output.count("❌ 缺口") == 2)

failed = [name for name, passed in checks if not passed]
for name, passed in checks:
    print(f"{'PASS' if passed else 'FAIL'} {name}")
print(f"{len(checks) - len(failed)}/{len(checks)}")
if failed:
    print("\n".join(failed), file=sys.stderr)
    raise SystemExit(1)
