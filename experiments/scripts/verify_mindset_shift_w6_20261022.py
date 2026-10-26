"""Whole-lesson offline checks for mindset-shift; no provider calls."""
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/what-is-an-agent/03-mindset-shift.mdx"
TEXT = LESSON.read_text(encoding="utf-8")
FENCES = re.findall(r"```python\s*(.*?)```", TEXT, re.S)


def run_code(source: str) -> str:
    with tempfile.NamedTemporaryFile("w", suffix=".py", encoding="utf-8") as f:
        f.write(source)
        f.flush()
        result = subprocess.run(
            [sys.executable, f.name], text=True, capture_output=True, check=True, cwd=ROOT
        )
    return result.stdout


def main() -> int:
    checks: list[tuple[str, bool]] = []

    def check(name: str, passed: bool) -> None:
        checks.append((name, bool(passed)))

    check("all_five_python_fences_are_present", len(FENCES) == 5)
    compile_ok = True
    for source in FENCES:
        try:
            compile(source, str(LESSON), "exec")
        except SyntaxError:
            compile_ok = False
    check("all_python_fences_compile", compile_ok)

    check(
        "raw_text_example_is_an_observed_failure_not_an_unexplained_assert",
        'raw text equal: False' in run_code(FENCES[0])
        and 'assert raw == \'{"company":"字节跳动"}\'' not in FENCES[0],
    )
    check("incomplete_test_excerpt_is_labeled", "示意片段，未实跑" in FENCES[1].splitlines()[0])
    scorer_output = run_code(FENCES[2])
    check("offline_fixture_scorer_output_matches_claim", scorer_output == "fixture pass rate=100.0%\n")
    check(
        "scorer_sample_provenance_is_not_misrepresented",
        "# 样本：这里用构造 fixture 演示评分，不读取生产日志。" in FENCES[2]
        and "从生产日志里抽出来" not in FENCES[2],
    )
    check(
        "provider_error_excerpt_is_labeled_and_has_no_live_call_claim",
        "边界示意，未实跑" in TEXT.split("response = client.messages.create", 1)[0][-100:]
        and "片段只用于展示错误边界" in FENCES[3],
    )
    check("anthropic_handler_excerpt_is_labeled_pseudocode", "示意代码，未实跑" in FENCES[4].splitlines()[0])

    values = (0.99 ** 10 * 100, 0.99 ** 100 * 100, 0.999 ** 100 * 100)
    zero_failure_upper = (1 - 0.05 ** (1 / 30)) * 100
    check(
        "probability_examples_match_displayed_rounding",
        tuple(round(value, 1) for value in values) == (90.4, 36.6, 90.5)
        and round(zero_failure_upper, 1) == 9.5,
    )
    check(
        "provider_and_paper_scope_is_explicit",
        "这条说明适用于 Anthropic API" in TEXT
        and "不应自动推广为所有 provider 的同一实现机制" in TEXT
        and "不能证明所有模型、长度、提示方式、检索任务都有相同曲线" in TEXT,
    )
    check(
        "historical_marker_experiment_is_not_claimed_as_reproduction",
        "不是有效的 Lost-in-the-Middle 复现" in TEXT
        and "原始请求/逐次响应、精确模型版本和判分脚本未归档" in TEXT
        and "未知" in TEXT,
    )
    check(
        "api_generation_task_and_side_effect_success_are_separated",
        "传输与 API" in TEXT
        and "生成结束状态" in TEXT
        and "业务效果" in TEXT
        and "API 在自己的协议层返回成功" in TEXT,
    )
    check(
        "privacy_and_sampling_guidance_has_explicit_bounds",
        "授权、最小化和脱敏" in TEXT
        and "不能把“最近 N 条”当成无偏代表样本" in TEXT,
    )

    failed = [name for name, passed in checks if not passed]
    for name, passed in checks:
        print(f"{'PASS' if passed else 'FAIL'} {name}")
    print(f"{len(checks) - len(failed)}/{len(checks)} W6 lesson checks")
    if failed:
        print("\n".join(failed))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
