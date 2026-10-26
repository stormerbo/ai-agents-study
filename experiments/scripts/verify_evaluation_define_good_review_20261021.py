"""Offline contract checks for evaluation/define-good review (2026-10-21)."""
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
LESSON = (ROOT / "src/content/chapters/evaluation/01-define-good.mdx").read_text()
META = (ROOT / "src/content/chapters/evaluation/meta.ts").read_text()

checks = {
    "goals_constraints_and_signals_are_distinct": all(
        term in LESSON for term in ("任务结果", "安全与业务约束", "过程诊断", "运行约束")
    ),
    "proxy_metrics_are_not_claimed_as_ground_truth": all(
        phrase in LESSON for phrase in ("假阳性", "假阴性", "代理信号", "不证明")
    ),
    "repeated_followup_is_not_a_direct_failure_label": "追问是有用的**代理信号**" in LESSON,
    "historical_enum_observation_is_bounded": all(
        phrase in LESSON for phrase in ("逐次请求/响应", "不可独立重建", "待复验假设")
    ),
    "checkpoint_has_official_eval_source": "sourceIds: ['openai-evaluation-best-practices']" in META,
}

checks["criteria_table_has_five_matching_items"] = (
    "至少考虑以下五项" in LESSON
    and len(re.findall(r"^\| \*\*[^*]+\*\* \|", LESSON.split("最后给一份检查清单", 1)[1].split("第四条", 1)[0], flags=re.MULTILINE)) == 5
)
checks["evaluation_does_not_assume_full_automation"] = (
    "把「好」定义清楚，不等于把每个目标都自动化" in LESSON
    and "就是把它翻译成能自动判定的东西" not in LESSON
)
checks["metadata_covers_count_and_automation_boundary"] = (
    "criteria-count-and-automation-boundary" in META
    and "语义或主观目标仍可通过明确 rubric" in META
)

fences = re.findall(r"```python\n(.*?)\n```", LESSON, flags=re.DOTALL)
if fences:
    with tempfile.TemporaryDirectory(prefix="eval-define-good-") as temp_dir:
        script = Path(temp_dir) / "example.py"
        script.write_text(fences[0])
        completed = subprocess.run(
            [sys.executable, str(script)], capture_output=True, text=True, check=False
        )
    checks["only_example_runs_offline_and_exposes_proxy_errors"] = (
        completed.returncode == 0
        and "TP=1 FP=1 TN=0 FN=1" in completed.stdout
        and "不能估计总体误差率" in completed.stdout
    )
else:
    checks["only_example_runs_offline_and_exposes_proxy_errors"] = False

for name, passed in checks.items():
    print(f"{'PASS' if passed else 'FAIL'} {name}")
print(f"{sum(checks.values())}/{len(checks)} checks passed")
sys.exit(0 if all(checks.values()) else 1)
