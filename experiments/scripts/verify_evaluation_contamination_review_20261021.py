"""Offline checks for contamination guidance, historical arithmetic, and helpers."""
from pathlib import Path
import contextlib
import io
import re

LESSON = Path("src/content/chapters/evaluation/04-contamination.mdx")
SOURCE = LESSON.read_text()
FENCES = re.findall(r"^```python\s*\n([\s\S]*?)^```\s*$", SOURCE, re.M)
assert FENCES, "expected runnable Python examples"
CODE = {}
for fence in FENCES:
    namespace = {}
    exec(fence, namespace)
    CODE.update(namespace)


def test_versioned_historical_fixture_is_self_contained():
    fixture = __import__("json").loads(
        Path("experiments/fixtures/evaluation-contamination-historical-counts.json").read_text()
    )
    assert fixture["provenance"]["rawProviderResponsesAvailable"] is False
    assert fixture["provenance"]["fixtureKind"] == "transcribed-local-log-summary"
    assert fixture["batches"]["A"]["answerCounts"] == {"A": 2, "B": 12, "C": 6, "D": 0}
    assert fixture["batches"]["B"]["answerCounts"] == {"A": 2, "B": 14, "C": 3, "D": 0}


def test_historical_answer_counts_and_exact_null_match_the_fixture():
    fixture = __import__("json").loads(
        Path("experiments/fixtures/evaluation-contamination-historical-counts.json").read_text()
    )
    batch_a = fixture["batches"]["A"]
    batch_b = fixture["batches"]["B"]
    assert batch_a["generatedCount"] == batch_b["generatedCount"] == 20
    assert sum(batch_a["answerCounts"].values()) == batch_a["analysisN"] == batch_a["parsedCount"] == 20
    assert sum(batch_b["answerCounts"].values()) == batch_b["analysisN"] == batch_b["parsedCount"] == 19
    assert batch_a["parsedCount"] / batch_a["generatedCount"] == 1
    assert batch_b["parsedCount"] / batch_b["generatedCount"] == 0.95
    assert batch_a["answerCounts"]["B"] == 12
    assert batch_b["answerCounts"]["B"] == 14
    assert batch_b["answerCounts"]["C"] == 3
    assert batch_b["answerCounts"]["D"] == 0
    assert "Pearson χ²=16.80" in SOURCE
    assert "Pearson χ²=25.00" in SOURCE
    assert "0.000871" in SOURCE and "0.0000207" in SOURCE
    code = next(fence for fence in FENCES if "answer_distribution" in fence)
    assert '"batch A": ["A"] * 2 + ["B"] * 12 + ["C"] * 6' in code
    assert '"batch B": ["A"] * 2 + ["B"] * 14 + ["C"] * 3' in code


def test_answer_distribution_matches_both_batches_and_rejects_bad_data():
    distribution = CODE["answer_distribution"]
    counts_a, chi_a, p_a = distribution(["A"] * 2 + ["B"] * 12 + ["C"] * 6)
    counts_b, chi_b, p_b = distribution(["A"] * 2 + ["B"] * 14 + ["C"] * 3)
    assert counts_a == {"A": 2, "B": 12, "C": 6}
    assert counts_b == {"A": 2, "B": 14, "C": 3}
    assert round(chi_a, 2) == 16.8 and abs(p_a - 0.0008710159) < 1e-9
    assert round(chi_b, 2) == 25.0 and abs(p_b - 0.0000207091) < 1e-9
    for invalid in ([], ["A", "E"], ["A", None]):
        try:
            distribution(invalid)
        except ValueError:
            pass
        else:
            raise AssertionError(f"invalid answers accepted: {invalid!r}")


def test_documented_python_demo_output_matches_the_lesson():
    fence = next(fence for fence in FENCES if '"batch A"' in fence and "answer_distribution" in fence)
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        exec(compile(fence, str(LESSON), "exec"), {"__name__": "__main__"})
    rendered = output.getvalue()
    assert "batch A: n=20 labels={'A': 2, 'B': 12, 'C': 6}" in rendered
    assert "batch B: n=19 labels={'A': 2, 'B': 14, 'C': 3}" in rendered
    expected_match = re.search(r"```text\s*\n(batch A: n=20[\s\S]*?)\n```", SOURCE)
    assert expected_match, "the lesson must publish the demo's expected output"
    assert rendered.strip() == expected_match.group(1).strip()


def test_ngram_helper_flags_only_visible_overlap_candidates():
    leakage = CODE["ngram_leakage"]
    assert leakage(["abcdefghijk"], ["abcdefghijk"], n=4) == {
        "candidateCount": 1, "analyzableCount": 1, "indices": [0]
    }
    assert leakage(["abcdefghijk"], ["zzzzzzzzzzz"], n=4) == {
        "candidateCount": 0, "analyzableCount": 1, "indices": []
    }


def test_balance_rejects_invalid_labels_and_makes_answer_positions_uniform():
    balance = CODE["balance"]
    cases = [
        {"options": {"A": "a", "B": "b", "C": "c", "D": "d"}, "answer": "B"}
        for _ in range(4)
    ]
    result = balance(cases)
    assert [item["answer"] for item in result] == list("ABCD")
    assert [item["answer"] for item in cases] == ["B"] * 4
    assert result[0]["options"]["A"] == "b"
    for bad_cases, labels in [([], "ABCD"), (cases, ""), ([{"options": {}, "answer": "Z"}], "ABCD")]:
        try:
            balance(bad_cases, labels)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid balance inputs must fail closed")


def test_leakage_helpers_validate_inputs_and_only_flag_candidates():
    leakage = CODE["ngram_leakage"]
    try:
        leakage(["test"], ["train"], n=0)
    except ValueError:
        pass
    else:
        raise AssertionError("n must be positive")
    assert "候选" in SOURCE and "不能证明" in SOURCE
    assert "不能作为泄漏检验" in SOURCE


def test_prose_avoids_absolute_leakage_and_holdout_claims():
    forbidden = [
        "唯一能对抗「迭代泄漏」",
        "它是三类里最出名、却最少发生在自己项目上的",
        "凡是这类改动能让分数跳变的，中间就夹着泄漏",
        "它已经不再度量任何东西",
        "随机打乱标签后重跑一遍",
    ]
    for phrase in forbidden:
        assert phrase not in SOURCE, f"unsupported absolute statement remains: {phrase}"


if __name__ == "__main__":
    tests = [
        test_versioned_historical_fixture_is_self_contained,
        test_historical_answer_counts_and_exact_null_match_the_fixture,
        test_answer_distribution_matches_both_batches_and_rejects_bad_data,
        test_documented_python_demo_output_matches_the_lesson,
        test_ngram_helper_flags_only_visible_overlap_candidates,
        test_balance_rejects_invalid_labels_and_makes_answer_positions_uniform,
        test_leakage_helpers_validate_inputs_and_only_flag_candidates,
        test_prose_avoids_absolute_leakage_and_holdout_claims,
    ]
    for test in tests:
        test()
    print(f"PASS {len(tests)} contamination review checks")
