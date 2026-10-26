"""Offline regression checks for the evaluation-dataset lesson audit."""
from pathlib import Path
import re

LESSON = Path("src/content/chapters/evaluation/03-dataset.mdx")
SOURCE = LESSON.read_text()
FENCES = re.findall(r"^```python\s*\n([\s\S]*?)^```\s*$", SOURCE, re.M)
assert FENCES, "expected Python examples"
CODE = {}
for fence in FENCES:
    namespace = {"__name__": "lesson_example"}
    exec(fence, namespace)
    CODE.update(namespace)


def test_bad_substring_scorer_has_been_removed_and_risk_is_explained():
    assert "def correct(" not in "\n".join(FENCES)
    assert "15910" in SOURCE and "子串" in SOURCE
    assert "整个字段匹配" in SOURCE


def test_wilson_and_precision_planner_match_displayed_results():
    wilson = CODE["wilson_interval"]
    planning = CODE["approximate_n_for_margin"]
    low, high = wilson(19, 20)
    assert abs(low - 0.7638688) < 1e-6 and abs(high - 0.9911186) < 1e-6
    assert planning(.9, .10) == 25
    assert planning(.9, .05) == 98
    for invalid in ((0, 0), (21, 20), (1.5, 2)):
        try:
            wilson(*invalid)
        except ValueError:
            pass
        else:
            raise AssertionError(f"invalid Wilson inputs accepted: {invalid!r}")
    for invalid in ((0, .1), (.9, 0), (.9, 1.1)):
        try:
            planning(*invalid)
        except ValueError:
            pass
        else:
            raise AssertionError(f"invalid planning inputs accepted: {invalid!r}")

def test_source_guidance_is_not_absolute_or_misleading():
    forbidden = [
        "唯一健康方式",
        "一道全对的评测集，测不出任何改进",
        "20 道题能可靠地发现掉 20 个百分点这种事故",
        "同样精度下大约还要再乘 2",
        "如果是，说明这份集合已经失效",
        "最健康的信号是「通过率在 80% 到 95% 之间」",
    ]
    for phrase in forbidden:
        assert phrase not in SOURCE, f"unsupported generalization remains: {phrase}"


def test_sample_size_guidance_states_sampling_unit_and_design_parameters():
    for required in ("独立评测单位", "最小关心差异", "显著性水平", "检验功效", "配对"):
        assert required in SOURCE, f"missing comparison-design requirement: {required}"


def test_historical_run_is_labeled_as_unreproducible_and_bootstrap_scope_is_limited():
    for required in ("逐题原始响应", "历史摘要", "有放回 bootstrap", "不是模型真实波动"):
        assert required in SOURCE, f"missing evidence limitation: {required}"


def test_all_python_examples_compile_without_making_provider_calls():
    assert len(FENCES) >= 1
    for fence in FENCES:
        compile(fence, str(LESSON), "exec")
    assert "urlopen(" not in "\n".join(FENCES), "lesson regression script must remain offline"


if __name__ == "__main__":
    tests = [
        test_bad_substring_scorer_has_been_removed_and_risk_is_explained,
        test_wilson_and_precision_planner_match_displayed_results,
        test_source_guidance_is_not_absolute_or_misleading,
        test_sample_size_guidance_states_sampling_unit_and_design_parameters,
        test_historical_run_is_labeled_as_unreproducible_and_bootstrap_scope_is_limited,
        test_all_python_examples_compile_without_making_provider_calls,
    ]
    for test in tests:
        test()
    print(f"PASS {len(tests)} evaluation-dataset review checks")
