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
TEXT = LESSON.read_text(encoding="utf-8")


def main() -> int:
    checks = []
    fences = re.findall(r"```python\s*\n(.*?)\n```", TEXT, flags=re.DOTALL)
    assert len(fences) == 3, f"expected three Python examples, got {len(fences)}"
    for index, code in enumerate(fences):
        compile(code, f"{LESSON}#fence-{index + 1}", "exec")
    checks.append("all three Python fences compile")

    main_example = next(code for code in fences if "def case_1_normal_flow" in code)
    with tempfile.TemporaryDirectory(prefix="capstone-skeleton-") as temp_dir:
        path = Path(temp_dir) / "skeleton.py"
        path.write_text(main_example, encoding="utf-8")
        run = subprocess.run(
            [sys.executable, str(path)], capture_output=True, text=True, check=True
        )
    assert "→ 8/8 通过" in run.stdout, run.stdout
    checks.append("local teaching model executes all eight scoped assertions")

    registry = REGISTRY.read_text(encoding="utf-8")
    p5 = P5_README.read_text(encoding="utf-8")
    p5_tests = P5_TESTS.read_text(encoding="utf-8")
    for name in ("lookup_order", "search_policy", "send_notice"):
        assert name in registry and name in TEXT, f"project tool mismatch: {name}"
    for marker in ("unknown", "approval", "lease", "provider"):
        assert marker in p5.lower(), f"P5 README missing expected boundary: {marker}"
    assert "test_" in p5_tests and "max_retries" in p5_tests
    checks.append("lesson distinguishes current P5/provider flow from in-memory sample")

    required_bounds = (
        "不能当作当前 P5 应用或生产骨架",
        "固定 `3000` 计数不是实际 token usage",
        "原始参数/结果记录",
        "不能单独保证外部副作用 exactly-once",
        "固定假设下的情景算术结果", "不是历史 provider 实测或账单倍率",
        "网络调用或外部副作用",
    )
    for phrase in required_bounds:
        assert phrase in TEXT, f"missing applicability boundary: {phrase}"
    stale_claims = (
        "30 轮比单轮输入侧涨 405 倍",
        "网络超时、JSON 解析失败、字段缺失。它们不影响协议",
        "这八条同时也是第 15 章那个",
        "单次调用最多生成多少 token",
    )
    assert not [phrase for phrase in stale_claims if phrase in TEXT]
    checks.append("unsafe recovery, logging, budget, and historical-cost claims are bounded")

    print(f"{len(checks)}/{len(checks)} checks passed")
    for check in checks:
        print(f"- {check}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
