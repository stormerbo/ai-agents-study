"""Offline regression checks for the ablation lesson's runnable examples."""

from pathlib import Path
import re


LESSON = Path("src/content/chapters/evaluation/06-ablation.mdx")
FENCES = re.findall(r"^```python\s*\n([\s\S]*?)^```\s*$", LESSON.read_text(), re.M)
assert len(FENCES) >= 2, f"expected the two ablation examples, got {len(FENCES)} Python fences"

namespace = {}
exec(FENCES[0] + "\n" + FENCES[1], namespace)


def test_truncated_output_is_incomplete_not_a_quality_score():
    result = namespace["metric_fn"](
        {
            "text": "TC-01 | 金额 | 已退款 | P0",
            "status": "incomplete",
            "stop_reason": "max_tokens",
        }
    )
    assert result == {"status": "incomplete", "score": None}


def test_full_factorial_reports_main_and_interaction_contrasts():
    rows = [
        {"keep": (), "mean": 7.0, "observations": [{"status": "complete"}]},
        {"keep": ("角色",), "mean": 8.0, "observations": [{"status": "complete"}]},
        {"keep": ("格式",), "mean": 8.0, "observations": [{"status": "complete"}]},
        {
            "keep": ("角色", "格式"),
            "mean": 8.0,
            "observations": [{"status": "complete"}],
        },
    ]
    effects = namespace["factorial_effects"](rows, ["角色", "格式"])
    assert effects["main_effects"] == {"角色": 0.5, "格式": 0.5}
    assert effects["interactions"] == {("角色", "格式"): -1.0}


def test_missing_factorial_cell_fails_closed():
    rows = [
        {"keep": (), "mean": 7.0, "observations": [{"status": "complete"}]},
        {"keep": ("角色",), "mean": 8.0, "observations": [{"status": "complete"}]},
        {"keep": ("格式",), "mean": 8.0, "observations": [{"status": "complete"}]},
    ]
    try:
        namespace["factorial_effects"](rows, ["角色", "格式"])
    except ValueError as error:
        assert "missing factorial conditions" in str(error)
    else:
        raise AssertionError("incomplete factorial table must not produce interaction estimates")


def test_scoring_separates_eight_quality_checks_from_completion():
    valid = "\n".join(
        f"TC-{i:02d} | 金额 {i} 元 | {'测试后退款成功' if i == 1 else '预期结果'} | {'P0' if i <= 3 else 'P1' if i <= 8 else 'P2'}"
        for i in range(1, 16)
    )
    result = namespace["metric_fn"]({"text": valid, "status": "complete", "stop_reason": "end_turn"})
    assert result == {"status": "complete", "score": 8}
    assert namespace["metric_fn"]({"text": valid, "status": "complete"}) == {
        "status": "complete",
        "score": 8,
    }
    malformed = valid.replace(" | 测试后退款成功 | ", " | 测试后退款成功 ", 1)
    assert namespace["metric_fn"](
        {"text": malformed, "status": "complete"}
    ) == {"status": "complete", "score": 6}
    banned_in_input = valid.replace("金额 1 元", "金额测试 1 元", 1)
    assert namespace["metric_fn"](
        {"text": banned_in_input, "status": "complete"}
    ) == {"status": "complete", "score": 7}


def test_ablation_records_incomplete_runs_without_scoring_them():
    calls = []

    def run_fn(prompt):
        calls.append(prompt)
        stop_reason = "max_tokens" if len(calls) == 1 else "end_turn"
        return {
            "text": "",
            "status": "incomplete" if stop_reason == "max_tokens" else "complete",
            "stop_reason": stop_reason,
            "output_tokens": 12,
        }

    results = namespace["ablate"](
        {"角色": "role", "格式": "format"},
        run_fn,
        namespace["metric_fn"],
        repeats=2,
    )
    assert len(results) == 4
    assert sum(item["status"] == "incomplete" for row in results for item in row["observations"]) == 1
    first_condition = next(row for row in results if row["observations"][0]["status"] == "incomplete")
    assert first_condition["mean"] == 1


def test_factorial_effects_rejects_a_missing_cell():
    rows = [
        {"keep": (), "mean": 7.0},
        {"keep": ("角色",), "mean": 8.0},
        {"keep": ("格式",), "mean": 8.0},
    ]
    try:
        namespace["factorial_effects"](rows, ["角色", "格式"])
    except ValueError as error:
        assert "missing factorial conditions" in str(error)
    else:
        raise AssertionError("incomplete factorial table must not produce interaction estimates")


def test_factorial_effects_rejects_unequal_complete_sample_counts():
    rows = [
        {
            "keep": (),
            "mean": 7.0,
            "observations": [{"status": "complete"}, {"status": "complete"}],
        },
        {
            "keep": ("角色",),
            "mean": 8.0,
            "observations": [{"status": "complete"}, {"status": "complete"}],
        },
        {
            "keep": ("格式",),
            "mean": 8.0,
            "observations": [{"status": "complete"}, {"status": "complete"}],
        },
        {
            "keep": ("角色", "格式"),
            "mean": 8.0,
            "observations": [
                {"status": "complete"},
                {"status": "incomplete"},
            ],
        },
    ]
    try:
        namespace["factorial_effects"](rows, ["角色", "格式"])
    except ValueError as error:
        assert "unequal complete sample counts" in str(error)
    else:
        raise AssertionError("unbalanced completion counts must not be averaged as comparable cells")


if __name__ == "__main__":
    tests = [
        test_truncated_output_is_incomplete_not_a_quality_score,
        test_full_factorial_reports_main_and_interaction_contrasts,
        test_missing_factorial_cell_fails_closed,
        test_scoring_separates_eight_quality_checks_from_completion,
        test_ablation_records_incomplete_runs_without_scoring_them,
        test_factorial_effects_rejects_a_missing_cell,
        test_factorial_effects_rejects_unequal_complete_sample_counts,
    ]
    for test in tests:
        test()
    print(f"PASS {len(tests)} ablation review checks")
