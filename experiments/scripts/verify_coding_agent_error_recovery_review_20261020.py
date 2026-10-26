"""Audit the historical recovery fixture and the replacement local controller demo."""

from pathlib import Path
import re
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/coding-agent/04-error-recovery.mdx"
OVERVIEW = ROOT / "src/content/chapters/coding-agent/01-why-coding-agent.mdx"
METADATA = ROOT / "src/content/chapters/coding-agent/meta.ts"
LEGACY_FIXTURE = ROOT / "experiments/fixtures/coding-recover-invalid-assertion.txt"
TEXT = LESSON.read_text(encoding="utf-8")


def main() -> int:
    checks = []
    broken_assertion = LEGACY_FIXTURE.read_text(encoding="utf-8").splitlines()[-1]
    try:
        compile(broken_assertion, str(LEGACY_FIXTURE), "exec")
    except SyntaxError:
        pass
    else:
        raise AssertionError("archived legacy assertion unexpectedly compiles")
    checks.append("legacy truncate fixture is syntactically invalid")

    fences = re.findall(r"```python\s*\n(.*?)\n```", TEXT, flags=re.DOTALL)
    assert len(fences) == 1, f"expected one Python fence, got {len(fences)}"
    code = fences[0]
    compile(code, str(LESSON), "exec")
    with tempfile.TemporaryDirectory(prefix="coding-recovery-review-") as temp_dir:
        demo = Path(temp_dir) / "repair_loop.py"
        demo.write_text(code, encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(demo)], capture_output=True, text=True, check=True
        )
    assert "'status': 'passed'" in result.stdout
    assert "'validations': 3" in result.stdout and "'proposals': 2" in result.stdout
    assert "'requested_new_direction': True" in result.stdout
    checks.append("bounded controller verifies each candidate and receives prior attempt summary")

    overview_text = OVERVIEW.read_text(encoding="utf-8")
    metadata_text = METADATA.read_text(encoding="utf-8")
    for phrase in (
        "不能支撑原正文的 4/5 模型成功率",
        "从第一轮起就把测试全文放入 prompt",
        "最多 `max_repairs + 1` 次验证",
        "不会在最后一轮生成尚未验证的新代码",
        "测试基础设施错误、测试失败、测试通过、模型 API 失败",
    ):
        assert phrase in TEXT, f"missing evidence boundary: {phrase}"
    stale_claims = (
        "修好的四个都恰好用了 2 轮",
        "模型五轮都没改对",
        "测试多的项目，agent 用起来更省力",
        "4/5 = 80%",
    )
    for source in (TEXT, overview_text):
        assert not [phrase for phrase in stale_claims if phrase in source]
    assert "修好的四个 fixture" not in metadata_text
    assert "不足以归因模型成功/失败" in overview_text
    assert "不能用于估计成功率" in metadata_text
    checks.append("lesson and metadata no longer generalize the invalid historical result")

    print(f"{len(checks)}/{len(checks)} checks passed")
    for check in checks:
        print(f"- {check}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
