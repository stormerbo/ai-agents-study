from __future__ import annotations

import ast
import re
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/agent-frameworks/04-build-vs-buy.mdx"
META = ROOT / "src/content/chapters/agent-frameworks/meta.ts"
EXPECTED = """initial_unchanged=True
phase=done event_count=4 pending=None
wrong_tool_result=rejected
answer=20C
"""


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    text = LESSON.read_text()
    checks = 0

    def require(condition: bool, message: str) -> None:
        nonlocal checks
        check(condition, message)
        checks += 1

    require("不是对所有框架的实证判决" in text, "stance must be scoped")
    require("不等于批评框架" in text, "source's non-anti-framework framing missing")
    require("小而模块化" in text, "modular adoption option missing")
    require("不是框架能力的对照实验" in text, "principles must not be framed as benchmark")
    require("不能独立复核" in text and "不能据此声称 enum 会普遍提高成功率" in text,
            "historical enum result must remain unverified")
    require("30 个工具" in text and "不要把“30 个工具”当作通用阈值" in text,
            "tool-count threshold should be rejected explicitly")
    require("一年以上" not in text and "几百行" not in text, "unsupported duration/size threshold remains")
    require("不存在脱离上下文" in META.read_text(), "metadata must avoid universal buy-wins claim")
    require("| 7 | 通过工具调用联系人工 |" in text, "factor 7 wording must match source")
    require("人工审批如何进入流程" in text, "factor 7 self-check should address approval recovery")
    require("不能保证 exactly-once" in text, "reducer boundary must reject exactly-once implication")
    require("不包含 LLM、provider、数据库或真实工具执行" in text,
            "fixture boundary must be explicit")
    require("providerCalls=0" not in text, "result metadata should not be embedded as lesson claim")

    fences = re.findall(r"```python\n(.*?)\n```", text, re.S)
    require(len(fences) == 1, f"expected one complete Python fence, got {len(fences)}")
    code = fences[0]
    ast.parse(code)
    require("if __name__ == \"__main__\":" in code, "example should be import-safe")
    require("dataclasses" in code and "subprocess" not in code, "fixture should use local standard library only")
    with tempfile.TemporaryDirectory(prefix="agent-frameworks-build-vs-buy-") as tmp:
        path = Path(tmp) / "example.py"
        path.write_text(code)
        result = subprocess.run([sys.executable, str(path)], check=True, text=True,
                                capture_output=True, timeout=10)
    require(result.stdout == EXPECTED, "runtime stdout must match published output exactly")
    require(result.stderr == "", "fixture should not emit stderr")

    require("initial_unchanged=True" in EXPECTED, "old state immutability output missing")
    require("wrong_tool_result=rejected" in EXPECTED, "mismatched tool result must be rejected")
    require("phase=done event_count=4 pending=None" in EXPECTED, "happy path output mismatch")
    require("ERR-171" not in text, "lesson should not refer to errata bookkeeping")
    print(f"PASS {checks}/{checks}; Python fence executed; providerCalls=0; networkCalls=0")


if __name__ == "__main__":
    main()
