"""Offline checks for the confidence lesson's numerical and input contracts."""

from pathlib import Path
import math
import re


LESSON = Path("src/content/chapters/evaluation/10-confidence.mdx")
SOURCE = LESSON.read_text()
FENCES = re.findall(r"^```python\s*\n([\s\S]*?)^```\s*$", SOURCE, re.M)
assert FENCES, "expected executable Python examples"
NAMESPACE = {"__name__": "confidence_lesson"}
exec("\n".join(FENCES), NAMESPACE)


def test_wilson_rejects_empty_or_invalid_counts():
    for args in [(0, 0), (-1, 10), (11, 10), (1.5, 10)]:
        try:
            NAMESPACE["wilson"](*args)
        except (ValueError, TypeError):
            continue
        raise AssertionError(f"wilson must reject invalid counts: {args}")


def test_wilson_all_successes_has_nonzero_uncertainty():
    lo, hi = NAMESPACE["wilson"](40, 40)
    assert 0.91 < lo < 0.92 and hi == 1.0


def test_clopper_pearson_boundaries_and_validation():
    cp = NAMESPACE["clopper_pearson"]
    lo, hi = cp(40, 40)
    assert 0.911 < lo < 0.913 and hi == 1.0
    lo, hi = cp(0, 40)
    assert lo == 0.0 and 0.08 < hi < 0.09
    for args in [(0, 0), (-1, 10), (11, 10), (1.5, 10), (3, 10, 1)]:
        try:
            cp(*args)
        except (ValueError, TypeError):
            continue
        raise AssertionError(f"clopper_pearson must reject invalid arguments: {args}")

    isolated = {}
    exec(FENCES[0], isolated)
    assert 0.911 < isolated["clopper_pearson"](40, 40)[0] < 0.913


def test_sample_size_validates_inputs_and_reproduces_table():
    needed = NAMESPACE["samples_needed"]
    assert [needed(0.9, width / 100) for width in (1, 2, 5, 10)] == [13830, 3458, 554, 139]
    for args in [(-0.1, 0.1), (1.1, 0.1), (0.5, 0), (0.5, 1.1)]:
        try:
            needed(*args)
        except ValueError:
            continue
        raise AssertionError(f"samples_needed must reject invalid arguments: {args}")


def test_all_success_lower_bound_is_one_sided_and_validated():
    runs = NAMESPACE["runs_for_lower_bound"]
    assert runs(0.95, 0.95) == 59
    for args in [(0, 0.95), (1, 0.95), (0.95, 1), (0.95, 0)]:
        try:
            runs(*args)
        except ValueError:
            continue
        raise AssertionError(f"runs_for_lower_bound must reject invalid arguments: {args}")


def test_lesson_explains_zero_event_risk_and_repeated_looks():
    assert "零事件" in SOURCE and "单侧" in SOURCE
    assert "固定样本量" in SOURCE and "反复查看" in SOURCE
    assert "每次评测追加一条记录，需要看结论时对汇总后的 `n` 重算区间" not in SOURCE


def test_every_python_fence_runs_in_isolation():
    for index, fence in enumerate(FENCES):
        try:
            exec(fence, {})
        except Exception as error:
            raise AssertionError(f"Python fence {index + 1} is not self-contained: {error}") from error


if __name__ == "__main__":
    tests = [
        test_wilson_rejects_empty_or_invalid_counts,
        test_wilson_all_successes_has_nonzero_uncertainty,
        test_clopper_pearson_boundaries_and_validation,
        test_sample_size_validates_inputs_and_reproduces_table,
        test_all_success_lower_bound_is_one_sided_and_validated,
        test_lesson_explains_zero_event_risk_and_repeated_looks,
        test_every_python_fence_runs_in_isolation,
    ]
    for test in tests:
        test()
    print(f"PASS {len(tests)} confidence review checks")
