"""Offline contract checks for the capstone skeleton lesson."""

from pathlib import Path
import re
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/capstone/02-skeleton.mdx"
P5_README = ROOT / "examples/p5-agent-delivery/README.md"
P5_TESTS = ROOT / "examples/p5-agent-delivery/tests/test_host_contract.py"
REGISTRY = ROOT / "examples/p4-durable-support/app/actions.py"
RUNNER = ROOT / "examples/p5-agent-delivery/runner.py"
P5_README = ROOT / "examples/p5-agent-delivery/README.md"
HOST = ROOT / "examples/p5-agent-delivery/host.py"
PROVIDER = ROOT / "examples/p5-agent-delivery/provider.py"
DATA = ROOT / "docs/DATA.md"
COST_LESSON = ROOT / "src/content/chapters/cost-and-latency/01-cost-model.mdx"
TEXT = LESSON.read_text(encoding="utf-8")


def main() -> int:
    checks: list[tuple[str, bool]] = []

    def check(name: str, condition: bool) -> None:
        checks.append((name, bool(condition)))

    fences = re.findall(r"^\x60{3}python\s*\n(.*?)^\x60{3}\s*$", TEXT, re.M | re.S)
    check("all_three_python_fences_compile", len(fences) == 3)
    for index, code in enumerate(fences):
        compile(code, f"{LESSON}#fence-{index + 1}", "exec")

    main_example = next(code for code in fences if "def case_1_normal_flow" in code)
    with tempfile.TemporaryDirectory(prefix="capstone-skeleton-w6-") as temp_dir:
        path = Path(temp_dir) / "skeleton.py"
        path.write_text(main_example, encoding="utf-8")
        run = subprocess.run([sys.executable, str(path)], capture_output=True, text=True, check=True)
    check("complete_local_teaching_model_passes_eight_scoped_assertions", "→ 8/8 通过" in run.stdout)

    registry = REGISTRY.read_text(encoding="utf-8")
    runner = RUNNER.read_text(encoding="utf-8")
    p5 = P5_README.read_text(encoding="utf-8")
    host = HOST.read_text(encoding="utf-8")
    provider = PROVIDER.read_text(encoding="utf-8")
    data = DATA.read_text(encoding="utf-8")
    cost_lesson = COST_LESSON.read_text(encoding="utf-8")

    check("documented_P5_tools_match_live_registry", all(name in registry and name in TEXT for name in ("lookup_order", "search_policy", "send_notice")))
    check("P5_live_caps_match_runner", "MAX_ROUNDS = 4" in runner and "MAX_OUTPUT_TOKENS = 512" in runner and "max_retries = 0" in provider and "max_retries=0" in p5)
    p5_normalized = " ".join(p5.split()).lower()
    check("durable_unknown_and_resume_boundaries_match_P5_docs", all(marker in p5_normalized for marker in ("durable response", "unknown", "must not retry", "approval resume", "local sink")) and "drive_provider_round" in host and "resume_agent_turn" in host)
    check("current_P5_registry_and_authorization_are_distinguished_from_demo", "resource_access" in registry and "validate_frozen" in registry and "不等于按身份、租户、对象授权" in TEXT)
    check("lesson_bounds_demo_approval_idempotency_and_trace", all(marker in TEXT for marker in ("同进程重复调用", "approved_ids", "进程内列表", "原始参数/结果记录")) and "def trace(" in TEXT and "数据分级" in TEXT)
    check("lesson_separates_fixed_demo_budget_from_provider_usage", all(marker in TEXT for marker in ("固定模拟值", "不是 provider 实际 usage", "单次调用参数", "任务级预算")))

    expected_scenario = "30 轮的上下文+schema token 为 23,070，是单轮无工具的上下文 57 的约 405 倍"
    corrected_boundary = "固定假设下的情景算术结果"
    check("405x_claim_is_correctly_classified_as_scenario_arithmetic", expected_scenario in cost_lesson and "405 倍是该章特定任务和计费口径的历史观察" not in TEXT and corrected_boundary in TEXT and "不是历史 provider 实测或账单倍率" in TEXT and "不是 provider 实际账单" in data)
    check("error_handling_conclusion_is_conditional_on_actual_side_effect_boundaries", "若路径已经包含网络调用或外部副作用" in TEXT and "未知" in TEXT and "对账" in TEXT)
    check("local_demo_run_is_not_a_provider_measurement", "非 provider、PostgreSQL 或生产安全测试" in TEXT and "不是 provider 实际 usage" in TEXT)
    check("local_sample_is_not_misreported_as_P5_acceptance_or_production_evidence", "不等同当前 capstone acceptance 的 gate 矩阵" in TEXT and "非 provider、PostgreSQL 或生产安全测试" in TEXT)

    failed = [name for name, passed in checks if not passed]
    for name, passed in checks:
        print(f"{'PASS' if passed else 'FAIL'} {name}")
    print(f"{len(checks) - len(failed)}/{len(checks)} W6 lesson checks")
    if run.stdout:
        print(run.stdout, end="")
    if failed:
        print("\n".join(failed), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
