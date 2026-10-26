"""Whole-lesson checks for the framework capabilities lesson."""

from __future__ import annotations

import ast
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/agent-frameworks/01-what-frameworks-give.mdx"


def fences(text: str, language: str) -> list[str]:
    return [body for kind, body in re.findall(r"```([\w+-]+)\n([\s\S]*?)\n```", text) if kind == language]


def main() -> None:
    text = LESSON.read_text(encoding="utf-8")
    python_blocks = fences(text, "python")
    output_blocks = fences(text, "text")
    assert len(python_blocks) == 1, f"expected one self-contained Python example, got {len(python_blocks)}"
    assert len(output_blocks) == 2, f"expected one constructed illustration and one exact output block, got {len(output_blocks)}"

    code = python_blocks[0]
    ast.parse(code, filename="framework-schema-example.py")
    assert "ChatAnthropic" not in code and "OPENAI_API_KEY" not in code
    assert "__main__" in code, "the example should not print or perform work on import"

    with tempfile.TemporaryDirectory(prefix="framework-schema-w6-") as temp_dir:
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
    assert result.returncode == 0, result.stderr
    assert result.stdout.rstrip("\n") == output_blocks[-1].rstrip("\n"), "published output differs from execution"
    assert "langchain=0.3.7" in result.stdout
    assert "langchain-core=0.3.63" in result.stdout
    assert "pydantic=2.9.2" in result.stdout
    assert 'plain.day={"title": "Day", "type": "string"}' in result.stdout
    assert 'literal.day={"enum": ["明天", "后天"], "title": "Day", "type": "string"}' in result.stdout

    for claim in ("唯一依据", "故障排查只能靠猜", "各家都做得最成熟", "通常只要十几分钟", "半小时内能做完"):
        assert claim not in text, f"unqualified broad claim remains: {claim}"
    assert "非穷尽" in text or "不穷尽" in text, "the four-part framework taxonomy needs a scope qualifier"
    assert "历史摘要" in text and "无法独立复核" in text, "the Chapter 4 result needs its evidence boundary"
    print("PASS: the isolated LangChain schema example runs without provider access")
    print("PASS: published output exactly matches execution")
    print("PASS: taxonomy, observability, timing, and historical-result claims are bounded")


if __name__ == "__main__":
    main()
