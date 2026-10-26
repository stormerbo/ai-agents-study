"""Whole-lesson offline checks for what-counts-as-agent; no provider calls."""
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/what-is-an-agent/02-what-counts-as-agent.mdx"
TEXT = LESSON.read_text(encoding="utf-8")


def main() -> int:
    checks: list[tuple[str, bool]] = []

    def check(name: str, passed: bool) -> None:
        checks.append((name, bool(passed)))

    check("incomplete_contract_example_is_labeled_non_runnable", "示意代码片段，未实跑" in TEXT.split("def process_contract", 1)[0][-100:])
    check("incomplete_hybrid_example_is_labeled_non_runnable", "示意代码片段，未实跑" in TEXT.split("def handle_ticket", 1)[0][-120:])
    check(
        "historical_increment_is_not_attributed_to_replayed_context",
        "不能把 619 对 365 token 的差值归因于上下文重发" in TEXT
        and "没有保存逐次请求、响应与 usage 明细" in TEXT,
    )
    check(
        "two_step_probe_does_not_claim_quadratic_growth",
        "不构成多轮累计输入呈平方增长的证据" in TEXT
        and "完整历史每轮重发且上下文随轮次增长等条件" in TEXT,
    )

    values = {}
    for label, pattern in {
        "single": r"\| \*\*单次调用[^|]*\| 1 \| \*\*(\d+)\*\*",
        "workflow": r"\| \*\*workflow[^|]*\| 2 \| \*\*(\d+)\*\*",
        "agent": r"\| \*\*agent[^|]*\| 2 轮 \| \*\*(\d+)\*\*",
    }.items():
        match = re.search(pattern, TEXT)
        values[label] = int(match.group(1)) if match else None
    check("historical_cost_values_are_present", values == {"single": 365, "workflow": 619, "agent": 1625})
    check(
        "displayed_cost_multipliers_round_from_displayed_values",
        values["single"] is not None
        and round(values["workflow"] / values["single"], 1) == 1.7
        and round(values["agent"] / values["single"], 1) == 4.5,
    )
    runs = (1659, 1520, 1697)
    mean = sum(runs) / len(runs)
    check("agent_average_matches_rounded_historical_summary", round(mean) == values["agent"])
    check(
        "reported_run_spread_is_about_six_percent",
        max(abs(value - mean) / mean * 100 for value in runs) < 7
        and "波动约 ±6%" in TEXT,
    )
    check(
        "unreproducible_historical_evidence_remains_explicit",
        "逐次请求、响应与 usage 明细" in TEXT
        and "这组实验只说明" in TEXT
        and "不能证明任意 workflow 都能精确预报账单" in TEXT,
    )
    check(
        "workflow_and_agent_are_defined_by_control_flow_with_host_boundary",
        "本文沿用这套区分" in TEXT
        and "宿主程序仍负责校验状态、权限、预算，并决定是否执行" in TEXT
        and "不能仅凭子任务是否动态来判定" in TEXT,
    )
    check(
        "trace_is_not_presented_as_complete_or_required_raw_capture",
        "不保证包含完整状态，也不自动证明根因" in TEXT
        and "不是在要求生产环境完整留存原文" in TEXT
        and "按数据策略做最小化、脱敏和访问控制" in TEXT,
    )

    trace_match = re.search(r"\`\`\`json\s*(\{.*?\})\s*\`\`\`", TEXT, re.S)
    try:
        trace = json.loads(trace_match.group(1)) if trace_match else {}
    except json.JSONDecodeError:
        trace = {}
    steps = trace.get("steps", [])
    check(
        "illustrative_trace_json_is_well_formed_and_pairs_tool_result",
        len(steps) == 2
        and steps[0].get("stop_reason") == "tool_use"
        and steps[0].get("model_output", [{}])[-1].get("id")
        == steps[0].get("tool_result", {}).get("tool_use_id")
        and steps[1].get("stop_reason") == "end_turn",
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
