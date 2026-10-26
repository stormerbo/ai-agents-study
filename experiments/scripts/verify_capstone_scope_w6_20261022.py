"""Whole-lesson checks for the capstone scope lesson; offline only."""
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/capstone/01-scope.mdx"
RUNNER = ROOT / "examples/p5-agent-delivery/runner.py"
RUNBOOK = ROOT / "examples/p5-agent-delivery/RUNBOOK.md"
DATA = ROOT / "docs/DATA.md"
TEXT = LESSON.read_text(encoding="utf-8")
runner = RUNNER.read_text(encoding="utf-8")
runbook = RUNBOOK.read_text(encoding="utf-8")
data = DATA.read_text(encoding="utf-8")
checks = []

def check(name, condition):
    checks.append((name, bool(condition)))

check("lesson_scopes_one_predeclared_smoke_case_not_one_global_invocation", "一个预先固定的在线 smoke 用例" in TEXT and "最多一次有界在线 smoke" not in TEXT)
check("lesson_reports_per_task_caps_and_single_run_evidence_scope", "每个 smoke 任务受最大模型轮数和单轮输出 token 上限约束" in TEXT and "每份在线报告只描述该次合成任务运行" in TEXT)
check("runner_caps_match_task_and_response_claim", "MAX_ROUNDS = 4" in runner and "MAX_OUTPUT_TOKENS = 512" in runner and '"max_rounds": MAX_ROUNDS' in runner and '"max_output_tokens_per_round": MAX_OUTPUT_TOKENS' in runner)
check("runbook_distinguishes_task_wakeups_from_new_smoke_tasks", re.search(r"Each invocation claims and advances\s+one bounded wake-up", runbook) and "new idempotency key for another smoke" in runbook)
check("historical_tool_input_totals_match_the_local_data_ledger", "678/1326/2623/4945" in TEXT and "8/20/44/86 个工具对应请求总 input 678/1326/2623/4945" in data and "54.7 input token" in TEXT and "两端差值约 54.7 input token/新增工具" in data and "8 道选择题每档报告 8/8" in TEXT and "历史摘要报告 8/20/44/86 个候选下均 8/8" in data)
check("local_cost_sensitivity_remains_a_scenario_not_a_provider_bill", "第 18 章约 62% 是固定工具数与每轮重复输入假设下的本地计算，不是通用 API 账单占比" in TEXT and "约 62%" in data)

existing = subprocess.run([sys.executable, str(ROOT / "experiments/scripts/verify_capstone_scope_review_20261020.py")], cwd=ROOT, capture_output=True, text=True)
check("preserved_scope_contract_passes", existing.returncode == 0 and "5/5 checks passed" in existing.stdout)

fences = re.findall(r"^```python\s*\n(.*?)^```\s*$", TEXT, re.M | re.S)
check("one_complete_python_fence", len(fences) == 1)
if fences:
    compile(fences[0], str(LESSON), "exec")
    with tempfile.TemporaryDirectory(prefix="capstone-scope-w6-") as temp:
        script = Path(temp) / "scope.py"
        script.write_text(fences[0], encoding="utf-8")
        example = subprocess.run([sys.executable, str(script)], cwd=temp, capture_output=True, text=True)
    check("example_executes_and_detects_tool_scope_drift", example.returncode == 0 and "refund_order" in example.stdout and "active_tools" in example.stdout)
else:
    example = None

failed = [name for name, passed in checks if not passed]
for name, passed in checks:
    print(f"{'PASS' if passed else 'FAIL'} {name}")
print(f"{len(checks) - len(failed)}/{len(checks)} W6 scope checks")
if existing.stdout:
    print(existing.stdout, end="")
if existing.stderr:
    print(existing.stderr, end="", file=sys.stderr)
if failed:
    print("\n".join(failed), file=sys.stderr)
    raise SystemExit(1)
