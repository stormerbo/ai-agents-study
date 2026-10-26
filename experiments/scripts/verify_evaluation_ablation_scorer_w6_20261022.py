"""Regression checks for the ablation lesson's exact output-field grading."""

from pathlib import Path
import re


LESSON = Path("src/content/chapters/evaluation/06-ablation.mdx")
FENCES = re.findall(r"^```python\s*\n([\s\S]*?)^```\s*$", LESSON.read_text(), re.M)
assert len(FENCES) >= 2, f"expected the two ablation examples, got {len(FENCES)} Python fences"

namespace = {}
exec(FENCES[0] + "\n" + FENCES[1], namespace)
metric_fn = namespace["metric_fn"]

valid = "\n".join(
    f"TC-{i:02d} | 金额 {i} 元 | 预期结果 | {'P0' if i <= 3 else 'P1' if i <= 8 else 'P2'}"
    for i in range(1, 16)
)


def test_valid_ticket_rows_receive_all_eight_points():
    assert metric_fn({"text": valid, "status": "complete"}) == {
        "status": "complete",
        "score": 8,
    }


def test_ticket_number_must_be_an_exact_field_value():
    malformed = valid.replace("TC-01 |", "TC-01 extra |", 1)
    assert metric_fn({"text": malformed, "status": "complete"}) == {
        "status": "complete",
        "score": 7,
    }


def test_priority_must_be_an_exact_fourth_field_value():
    malformed = valid.replace(" | P0", " | invalid P0", 1)
    assert metric_fn({"text": malformed, "status": "complete"}) == {
        "status": "complete",
        "score": 7,
    }


def test_wrong_column_count_and_priority_are_both_scored():
    malformed = valid.replace(" | 预期结果 | P0", " | 预期结果 P0", 1)
    assert metric_fn({"text": malformed, "status": "complete"}) == {
        "status": "complete",
        "score": 6,
    }


def test_non_text_payload_is_a_completed_zero_score_not_an_exception():
    assert metric_fn({"text": None, "status": "complete"}) == {
        "status": "complete",
        "score": 0,
    }


if __name__ == "__main__":
    tests = [
        test_valid_ticket_rows_receive_all_eight_points,
        test_ticket_number_must_be_an_exact_field_value,
        test_priority_must_be_an_exact_fourth_field_value,
        test_wrong_column_count_and_priority_are_both_scored,
        test_non_text_payload_is_a_completed_zero_score_not_an_exception,
    ]
    for test in tests:
        test()
    print(f"PASS {len(tests)}/{len(tests)} ablation scorer checks; providerCalls=0; externalNetworkCalls=0")
