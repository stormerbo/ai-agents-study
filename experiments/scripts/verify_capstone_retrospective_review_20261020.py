"""Offline contract checks for the capstone retrospective lesson."""

from pathlib import Path
import re
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/capstone/05-retrospective.mdx"
TEXT = LESSON.read_text(encoding="utf-8")


def extract_python_fences(text: str) -> list[str]:
    return re.findall(r"```python\s*\n(.*?)\n```", text, flags=re.DOTALL)


def main() -> int:
    checks = []
    fences = extract_python_fences(TEXT)
    assert len(fences) == 1, f"expected one Python fence, got {len(fences)}"
    code = fences[0]
    compile(code, str(LESSON), "exec")
    checks.append("one Python fence compiles")

    with tempfile.TemporaryDirectory(prefix="capstone-retrospective-") as temp_dir:
        script = Path(temp_dir) / "retrospective.py"
        script.write_text(code, encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(script)], capture_output=True, text=True, check=True
        )
    assert "示例集计数（不是项目证据健康分）" in result.stdout
    assert "unverified_claims': 1" in result.stdout
    checks.append("record validator runs and scopes its example counts")

    required = [
        "逐次响应和完整三轮脚本缺失",
        "未找到对应登记原始记录，已撤下",
        "不能冒充对旧样本的复现",
        "最终验收",
        "它本身不能证明系统可靠",
        "脚本可能复现的是错误判据",
        "依据来源、原始产物是否存在、能否重放、当前主张状态",
        '"replayability": "not-rerun"',
        '"replayability": "unavailable"',
    ]
    for phrase in required:
        assert phrase in TEXT, f"missing scope statement: {phrase}"
    checks.append("historical evidence limits and six-step capstone flow are explicit")

    flow = ["| 划范围 |", "| 搭骨架 |", "| 加固 |", "| 交付 |", "| 复盘 |", "| 最终验收 |"]
    positions = [TEXT.index(step) for step in flow]
    assert positions == sorted(positions), "capstone steps are out of order"
    checks.append("the six capstone steps are listed in the intended order")

    forbidden = [
        "同配置另有 2.37× 记录",
        "同配置另有 2.37x 记录",
        "数据都是对的",
        "7 次全部未复现",
        "A 0 条、B 2 条、C 2 条",
        "最后一节",
        "全书二十二章结束",
    ]
    for phrase in forbidden:
        assert phrase not in TEXT, f"stale or overconfident statement remains: {phrase}"
    checks.append("stale chapter counts and invalid evidence tiers are removed")

    print(f"PASS {len(checks)}/{len(checks)}")
    for check in checks:
        print(f"- {check}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
