from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/capstone/03-hardening.mdx"
OLD_VERIFIER = ROOT / "experiments/scripts/verify_capstone_hardening_review_20261020.py"
text = LESSON.read_text()
checks = []

def check(name, condition):
    checks.append((name, bool(condition)))

check("full_lesson_review_retains_fourteen_checklist_topics", "上面这张清单有 14 项" in text)
check("lesson_explains_nine_automated_checks_expand_one_topic", "默认值、策略与注册表一致、工具集与范围表一致三条自动断言" in text)
check("lesson_reconciles_sixteen_records_with_fourteen_topics", "自动检查 9 条、人工 5 条、跳过 2 条，共 16 条输出记录" in text)
run = subprocess.run([sys.executable, str(OLD_VERIFIER)], cwd=ROOT, capture_output=True, text=True)
check("preserved_issue_scoped_verifier_passes", run.returncode == 0 and "9/9" in run.stdout)

failed = [name for name, passed in checks if not passed]
for name, passed in checks:
    print(f"{'PASS' if passed else 'FAIL'} {name}")
if run.stdout:
    print(run.stdout, end="")
if run.stderr:
    print(run.stderr, end="", file=sys.stderr)
print(f"{len(checks) - len(failed)}/{len(checks)} W6 scope checks")
if failed:
    print("\n".join(failed), file=sys.stderr)
    raise SystemExit(1)
