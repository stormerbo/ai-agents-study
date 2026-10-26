"""Verify the remote-authorization lesson's local-vs-wire error boundary."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/mcp/06-remote-authorization.mdx"


def main() -> int:
    text = LESSON.read_text(encoding="utf-8")
    assert "**认证**（authentication）" in text
    assert "**认证（authentication**）" not in text
    assert "不是 MCP 规范规定的 HTTP 错误码或 Bearer challenge 参数" in text
    assert "规范 SHOULD 在 `WWW-Authenticate` Bearer challenge" in text
    assert "`error=\"insufficient_scope\"`" in text

    result = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "examples/mcp-remote-auth", "-v"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    output = result.stderr + result.stdout
    match = re.search(r"Ran (\d+) tests? in", output)
    assert match and int(match.group(1)) == 7, output
    assert "OK" in output, output
    print("PASS: Markdown syntax, local diagnostic/wire error distinction, and normative scope challenge wording")
    print("PASS: 7 offline teaching-model tests")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
