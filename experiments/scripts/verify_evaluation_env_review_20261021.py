"""Offline contract checks for evaluation/eval-env review (2026-10-21)."""
from pathlib import Path
import re
import json
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
LESSON = (ROOT / "src/content/chapters/evaluation/05-eval-env.mdx").read_text()
META = (ROOT / "src/content/chapters/evaluation/meta.ts").read_text()
DATA = (ROOT / "docs/DATA.md").read_text()

fences = re.findall(r"```python\n(.*?)\n```", LESSON, flags=re.DOTALL)
json_fences = re.findall(r"```json\n(.*?)\n```", LESSON, flags=re.DOTALL)
outputs = []
return_codes = []
for code in fences:
    with tempfile.TemporaryDirectory(prefix="eval-env-review-") as temp_dir:
        script = Path(temp_dir) / "example.py"
        script.write_text(code)
        completed = subprocess.run(
            [sys.executable, str(script)], capture_output=True, text=True, check=False
        )
    outputs.append(completed.stdout)
    return_codes.append(completed.returncode)

checks = {
    "environment_manifest_is_valid_json": (
        len(json_fences) == 1
        and json.loads(json_fences[0]).get("isolation") == "one in-memory environment per case"
    ),
    "run_configuration_covers_external_and_scoring_inputs": all(
        phrase in LESSON
        for phrase in ("fixture_version", "tool_schema_version", "grader_version", "随机种子")
    ),
    "synthetic_3_vs_5_is_not_mislabeled_as_a_live_model_result": all(
        phrase in LESSON for phrase in ("数据：合成", "无法独立复核", "不是实测模型准确率")
    ),
    "fixture_error_is_separate_from_model_scoring": all(
        phrase in LESSON for phrase in ("invalid_fixture", "expected_terminal", "评分器输入完整且有效")
    ),
    "legitimate_mutation_is_scored_against_terminal_state": (
        len(outputs) == 2
        and return_codes[0] == 0
        and '"expected-write": {"passed": true' in outputs[0]
        and '"stale-fixture": {"status": "invalid_fixture"' in outputs[0]
    ),
    "teardown_assertion_failure_reproduces_and_is_caught": (
        len(outputs) == 2
        and return_codes[1] == 0
        and "Observed: AssertionError: environment did not return to initial state" in outputs[1]
    ),
    "official_sources_are_attached_to_checkpoint": all(
        phrase in META for phrase in ("openai-evaluation-best-practices", "pytest-fixtures")
    ),
    "data_ledger_records_withdrawn_historical_claim": (
        "评测环境 3/5 退款记录" in DATA and "已从实测结论撤下" in DATA
    ),
}

for name, passed in checks.items():
    print(f"{'PASS' if passed else 'FAIL'} {name}")
print(f"{sum(checks.values())}/{len(checks)} checks passed")
sys.exit(0 if all(checks.values()) else 1)
