"""Offline checks for the paired-comparison lesson review (2026-10-21)."""
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
LESSON_PATH = ROOT / "src/content/chapters/evaluation/07-paired-comparison.mdx"
LESSON = LESSON_PATH.read_text()
META = (ROOT / "src/content/chapters/evaluation/meta.ts").read_text()
TRACKER = (ROOT / "docs/CURRICULUM-REVIEW-TRACKER.md").read_text()
DATA = (ROOT / "docs/DATA.md").read_text()
RESOURCES = (ROOT / "src/content/curriculum/resources.ts").read_text()

fences = re.findall(r"```python\n(.*?)\n```", LESSON, flags=re.DOTALL)
scorer_code = next((code for code in fences if "def score(txt" in code), "")
scorer_namespace = {}
exec(scorer_code, scorer_namespace)
malformed_rows = []
for number in range(1, 16):
    priority = "P0" if number <= 3 else "P1" if number <= 8 else "P9"
    malformed_rows.append(f"TC-{number:02d} | 金额检查 | {priority}")
malformed_output = "\n".join(malformed_rows)
scorer_accepts_malformed = scorer_namespace["score"](malformed_output, "end_turn") == 7
example = next((code for code in fences if "def compare_paired" in code), "")
with tempfile.TemporaryDirectory(prefix="paired-comparison-review-") as temp_dir:
    script = Path(temp_dir) / "example.py"
    script.write_text(
        example
        + "\ntry:\n    compare_paired([('a', 1), ('b', 2)], [('a', 1), ('c', 2)])\n"
        + "except ValueError as error:\n    print('mismatch rejected:', error)\n"
        + "try:\n    compare_paired([('a', 1), ('a', 2)], [('a', 1), ('a', 2)])\n"
        + "except ValueError as error:\n    print('duplicate rejected:', error)\n"
    )
    completed = subprocess.run(
        [sys.executable, str(script)], capture_output=True, text=True, check=False
    )
outputs = [completed.stdout]
return_codes = [completed.returncode]

checks = {
    "historical_results_are_limited_to_arithmetic": (
        "逐次请求/响应" in LESSON
        and "不能推出真实质量相同或等价" in LESSON
        and "不能将它称为账单成本差" in LESSON
    ),
    "old_scorer_accepts_malformed_contract": scorer_accepts_malformed,
    "scorer_gap_is_explicit": (
        "没有检查每行是否恰好包含 4 个字段" in LESSON
        and "不等于完整满足提示中的输出契约" in LESSON
        and "P9" in LESSON
    ),
    "paired_precision_is_conditional": (
        "Var(B−A) = Var(B) + Var(A) − 2 Cov(A,B)" in LESSON
        and "负相关时反而可能更差" in LESSON
        and "这不是通用的“灵敏度提升”" in LESSON
    ),
    "test_uses_two_sided_exact_p_without_posthoc_direction": (
        "双侧精确检验：2 × min(P(X≤6), P(X≥6)) = 74/256 ≈ 0.289" in LESSON
        and "不能把观察到的“B 较高”事后选作单侧方向" in LESSON
        and "不存在不看目标效应" in LESSON
    ),
    "primary_sources_are_registered": (
        "sourceIds: ['nist-paired-observations', 'nist-sign-test']" in META
        and "'nist-paired-observations': {" in RESOURCES
        and "'nist-sign-test': {" in RESOURCES
        and "'nist-design-of-experiments': {" in RESOURCES
    ),
    "order_and_task_state_limits_are_taught": (
        "随机化是控制已知与未知混杂的设计手段，不是“能配对”的数学前提" in LESSON
        and "各自干净的环境" in LESSON
        and "依赖链整体才是一个配对样本" in LESSON
    ),
    "task_id_alignment_and_two_sided_code_run": (
        len(fences) == 2
        and return_codes == [0]
        and "mean difference 227.25" in outputs[0]
        and "paired SE 206.8 / independent-sample SE 248.6" in outputs[0]
        and "two-sided exact p=0.289" in outputs[0]
    ),
    "code_rejects_duplicate_and_mismatched_ids": (
        "mismatch rejected: A/B task ID sets differ; pairing is undefined" in outputs[0]
        and "duplicate rejected: duplicate task ID: a" in outputs[0]
    ),
    "tracker_records_review_scope": (
        "ERR-097" in TRACKER and "evaluation/paired-comparison" in TRACKER
        and "历史逐次响应、原始请求、完整 usage" in TRACKER
    ),
    "data_ledger_records_historical_limit": (
        "配对比较的 token 摘要" in DATA
        and "双侧精确符号检验" in DATA
    ),
}

for name, passed in checks.items():
    print(f"{'PASS' if passed else 'FAIL'} {name}")
print(f"{sum(checks.values())}/{len(checks)} checks passed")
sys.exit(0 if all(checks.values()) else 1)