from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/capstone/05-retrospective.mdx"
DATA = ROOT / "docs/DATA.md"
LESSON_TEXT = LESSON.read_text(encoding="utf-8")
DATA_TEXT = DATA.read_text(encoding="utf-8")
checks = []

def check(name, condition):
    checks.append((name, bool(condition)))

check("historical_two_ratios_are_not_extended_with_unregistered_237", "同配置另有 2.37× 记录" not in LESSON_TEXT and "未找到对应登记原始记录，已撤下" in LESSON_TEXT)
check("cost_claim_matches_the_authoritative_data_ledger", "1.91×" in LESSON_TEXT and "1.99×" in LESSON_TEXT and "不能外推" in LESSON_TEXT and "没有对应的登记原始记录，已撤下" in DATA_TEXT)
check("example_does_not_list_237_as_a_historical_observation", "同配置另有 2.37x 记录" not in LESSON_TEXT and "unsupported 2.37x claim withdrawn" in LESSON_TEXT)

old = subprocess.run([sys.executable, str(ROOT / "experiments/scripts/verify_capstone_retrospective_review_20261020.py")], cwd=ROOT, capture_output=True, text=True)
check("preserved_review_verifier_passes", old.returncode == 0 and "PASS 5/5" in old.stdout)

fences = re.findall(r"^```python\s*\n(.*?)^```\s*$", LESSON_TEXT, re.M | re.S)
check("only_complete_python_fence_is_present", len(fences) == 1)
if fences:
    compile(fences[0], str(LESSON), "exec")
    with tempfile.TemporaryDirectory(prefix="capstone-retro-w6-") as temp:
        script = Path(temp) / "retrospective.py"
        script.write_text(fences[0], encoding="utf-8")
        run = subprocess.run([sys.executable, str(script)], cwd=temp, capture_output=True, text=True)
    check("example_executes_and_scopes_sample_summary", run.returncode == 0 and "unverified_claims': 1" in run.stdout and "不是项目证据健康分" in run.stdout)
else:
    run = None

for phrase in ["不能冒充对旧样本的复现", "它本身不能证明系统可靠", "脚本可能复现的是错误判据", "最终验收"]:
    check(f"whole_lesson_boundary:{phrase}", phrase in LESSON_TEXT)

failed = [name for name, passed in checks if not passed]
for name, passed in checks:
    print(f"{'PASS' if passed else 'FAIL'} {name}")
print(f"{len(checks) - len(failed)}/{len(checks)}")
if old.stdout:
    print(old.stdout, end="")
if old.stderr:
    print(old.stderr, end="", file=sys.stderr)
if failed:
    print("\n".join(failed), file=sys.stderr)
    raise SystemExit(1)
