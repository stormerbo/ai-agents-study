"""Offline checks for the LLM-as-judge lesson review (2026-10-21)."""
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
LESSON = (ROOT / "src/content/chapters/evaluation/08-llm-as-judge.mdx").read_text()
META = (ROOT / "src/content/chapters/evaluation/meta.ts").read_text()
DATA = (ROOT / "docs/DATA.md").read_text()
TRACKER = (ROOT / "docs/CURRICULUM-REVIEW-TRACKER.md").read_text()
RESOURCES = (ROOT / "src/content/curriculum/resources.ts").read_text()

fences = re.findall(r"```python\n(.*?)\n```", LESSON, flags=re.DOTALL)
outputs = []
return_codes = []
for code in fences:
    with tempfile.TemporaryDirectory(prefix="llm-judge-review-") as temp_dir:
        script = Path(temp_dir) / "example.py"
        script.write_text(code)
        completed = subprocess.run(
            [sys.executable, str(script)], capture_output=True, text=True, check=False
        )
    outputs.append(completed.stdout)
    return_codes.append(completed.returncode)

checks = {
    "lesson_withdraws_unverifiable_historical_inference": (
        "不能据此说偏见已被排除" in LESSON
        and "不能得出“位置偏差或冗长偏差未复现”" in LESSON
    ),
    "historical_aggregate_labeled_unverified": (
        "均未独立复核，不代表总体偏差率" in LESSON
    ),
    "swap_order_is_a_diagnostic_not_a_guarantee": (
        "不能保证消除位置影响" in LESSON
        and "稳定偏向某一槽位" in LESSON
    ),
    "human_reference_guidance_avoids_universal_sample_threshold": (
        "没有通用的「20 到 30 条」门槛" in LESSON
        and "配对差异" in LESSON
    ),
    "meta_checkpoint_has_primary_research_source": (
        "sourceIds: ['mt-bench-llm-judge', 'owasp-llm-prompt-injection']" in META
        and "'mt-bench-llm-judge': {" in RESOURCES
    ),
    "offline_example_runs_and_shows_order_sensitivity": (
        len(outputs) == 1
        and return_codes == [0]
        and "order_invariant" in outputs[0]
        and "order_sensitive" in outputs[0]
    ),
    "offline_example_rejects_ambiguous_label": (
        len(outputs) == 1
        and "invalid-output-rejected" in outputs[0]
        and "invalid judge label" in outputs[0]
    ),
    "no_live_provider_call_in_example": (
        "不调用 LLM" in LESSON
        and "urllib.request" not in "\n".join(fences)
        and "ANTHROPIC_AUTH_TOKEN" not in "\n".join(fences)
    ),
    "audit_tracker_records_scope_and_limits": (
        "evaluation/llm-as-judge" in TRACKER
        and "未重跑历史 provider 实验" in TRACKER
    ),
    "data_ledger_records_evidence_limit": (
        "LLM-as-judge 的位置偏见" in DATA
        and "无法独立复核" in DATA
    ),
}

for name, passed in checks.items():
    print(f"{'PASS' if passed else 'FAIL'} {name}")
print(f"{sum(checks.values())}/{len(checks)} checks passed")
sys.exit(0 if all(checks.values()) else 1)
