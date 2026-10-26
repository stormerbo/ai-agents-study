"""Whole-lesson checks for the leaky-abstractions chapter."""

from __future__ import annotations

import ast
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/agent-frameworks/03-leaky-abstractions.mdx"
META = ROOT / "src/content/chapters/agent-frameworks/meta.ts"


def fences(text: str, language: str) -> list[str]:
    return [body for kind, body in re.findall(r"```([\w+-]+)\n([\s\S]*?)\n```", text) if kind == language]


def main() -> None:
    checks = 0

    def check(condition: bool, message: str) -> None:
        nonlocal checks
        checks += 1
        if not condition:
            raise AssertionError(message)

    text = LESSON.read_text(encoding="utf-8")
    meta = META.read_text(encoding="utf-8")
    python_blocks = fences(text, "python")
    text_blocks = fences(text, "text")
    check(len(python_blocks) == 1, "expected one complete Python schema example")
    check(len(text_blocks) == 1, "expected one published output block")
    code = python_blocks[0]
    ast.parse(code, filename="leaky-abstractions-example.py")
    check("if __name__ == \"__main__\":" in code, "example should not execute on import")
    check("ChatAnthropic" not in code and "OPENAI_API_KEY" not in code, "example must not configure a provider")
    check("langchain==0.3.7" in text and "langchain-core==0.3.63" in text, "package versions must be pinned")

    with tempfile.TemporaryDirectory(prefix="leaky-abstractions-w6-") as temp_dir:
        script = Path(temp_dir) / "lesson_example.py"
        script.write_text(code, encoding="utf-8")
        env = os.environ.copy()
        env["LANGCHAIN_TRACING_V2"] = "false"
        env["LANGSMITH_TRACING"] = "false"
        result = subprocess.run(
            [sys.executable, str(script)],
            check=False,
            capture_output=True,
            text=True,
            cwd=temp_dir,
            env=env,
        )
    check(result.returncode == 0, result.stderr)
    check(result.stdout.rstrip("\n") == text_blocks[0].rstrip("\n"), "published output must match execution exactly")
    check("langchain=0.3.7" in result.stdout, "unexpected LangChain version")
    check("langchain-core=0.3.63" in result.stdout, "unexpected langchain-core version")
    check("pydantic=2.9.2" in result.stdout, "unexpected Pydantic version")
    check('plain.day={"title": "Day", "type": "string"}' in result.stdout, "plain str output changed")
    check('described.day={"description": "只支持明天或后天", "title": "Day", "type": "string"}' in result.stdout, "docstring description output changed")
    check('literal.day={"enum": ["明天", "后天"], "title": "Day", "type": "string"}' in result.stdout, "Literal enum output changed")
    check("parse_docstring=True" in code, "docstring parsing path must be exercised")
    check("不用于证明 enum 导致成功率提高" in text, "historical 0/3 vs 3/3 must not be treated as causal evidence")
    check("频率排序" in text or "频率排序" in text, "frequency ranking must be explicitly bounded")
    check("不能盲目重放有副作用的操作" in text, "unknown outcomes must be discussed in replay-safety terms")
    check("应用层具备幂等保障" in text and "不能证明工具副作用安全" in text, "provider request safety must not be conflated with tool side-effect safety")
    check("幂等键、状态查询或对账" in text, "recovery options must be actionable")
    check("provider 请求重试" in text and "工具执行重试" in text, "provider retries and tool retries must be distinguished")
    check("安全证明" in text, "escape tests must not be presented as production safety proofs")
    check("langchain-core-063-tool-convert" in meta and "langchain-core-063-tool-base" in meta, "documented schema claims need pinned source IDs")
    check("basis: 'documented'" in meta, "schema checkpoint must be marked documented")
    check("四个最常见的下探触发点" not in meta, "unsupported frequency claim remains in curriculum metadata")
    check("迟早会成为负债" not in meta, "unsupported universal selection conclusion remains in metadata")

    print(f"PASS: {checks} whole-lesson checks")
    print("PASS: pinned LangChain schema example executed; stdout exactly matches the lesson")
    print("PASS: no provider request was made")


if __name__ == "__main__":
    main()
