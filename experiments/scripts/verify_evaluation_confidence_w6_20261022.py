"""W6 whole-lesson checks for interval-width claims and rendered prose artifacts."""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LESSON_PATH = ROOT / "src/content/chapters/evaluation/10-confidence.mdx"
SOURCE = LESSON_PATH.read_text(encoding="utf-8")
RESOURCES = (ROOT / "src/content/curriculum/resources.ts").read_text(encoding="utf-8")
FENCES = re.findall(r"^```python\s*\n([\s\S]*?)^```\s*$", SOURCE, re.M)


def test_clopper_pearson_is_not_uniformly_wider_than_wilson():
    assert "没有固定的大小顺序" in SOURCE
    assert "后者给出的区间总是不窄于前者" not in SOURCE
    assert "0/95" in SOURCE and "3.81%" in SOURCE and "3.89%" in SOURCE
    assert len(FENCES) == 3
    namespace: dict[str, object] = {}
    exec(FENCES[0], namespace)
    exec(FENCES[1], namespace)
    cp = namespace["clopper_pearson"](0, 95)  # type: ignore[index,operator]
    wilson = namespace["wilson"](0, 95)  # type: ignore[index,operator]
    assert cp[0] == 0 and wilson[0] == 0
    assert cp[1] < wilson[1]
    assert abs(cp[1] * 100 - 3.8086) < 0.001
    assert abs(wilson[1] * 100 - 3.8865) < 0.001


def test_bootstrap_conclusion_is_scoped_to_ordinary_percentile_case():
    assert "全体观测值都相同时，普通 percentile bootstrap 会退化成零宽区间" in SOURCE
    assert "比例接近 0/1 时不要用 bootstrap" not in SOURCE
    assert "不等于所有 bootstrap 在比例接近边界时都无效" in SOURCE


def test_literal_backslash_n_artifact_is_removed():
    assert r"\n普通固定样本量检验" not in SOURCE
    assert "看到显著就停，普通固定样本量检验" in SOURCE


def test_all_published_python_fences_compile_and_execute_in_isolation():
    assert len(FENCES) == 3
    for index, fence in enumerate(FENCES, start=1):
        compile(fence, f"{LESSON_PATH}:python-fence-{index}", "exec")
        exec(fence, {})


def test_primary_source_registration_and_current_review_dates():
    for resource_id in (
        "nist-proportion-confidence-intervals",
        "nist-sample-size-proportions",
        "fda-adaptive-designs",
    ):
        start = RESOURCES.index(f"'{resource_id}': {{")
        block = RESOURCES[start : start + 1200]
        assert "verifiedAt: '2026-10-22'" in block, resource_id
    assert "sourceIds: ['nist-proportion-confidence-intervals']" in (
        ROOT / "src/content/chapters/evaluation/meta.ts"
    ).read_text(encoding="utf-8")


def test_previous_seven_check_review_remains_green():
    completed = subprocess.run(
        [sys.executable, str(ROOT / "experiments/scripts/verify_evaluation_confidence_review_20261021.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "PASS 7 confidence review checks" in completed.stdout


if __name__ == "__main__":
    tests = [
        test_clopper_pearson_is_not_uniformly_wider_than_wilson,
        test_bootstrap_conclusion_is_scoped_to_ordinary_percentile_case,
        test_literal_backslash_n_artifact_is_removed,
        test_all_published_python_fences_compile_and_execute_in_isolation,
        test_primary_source_registration_and_current_review_dates,
        test_previous_seven_check_review_remains_green,
    ]
    for test in tests:
        test()
    print(f"PASS {len(tests)} confidence W6 checks; providerCalls=0; externalNetworkCalls=0")
