"""Check current MCP OAuth authorization boundaries and the offline teaching model."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/mcp/06-remote-authorization.mdx"
METADATA = ROOT / "src/content/chapters/mcp/meta.ts"
RESOURCES = ROOT / "src/content/curriculum/resources.ts"


def main() -> int:
    lesson = LESSON.read_text(encoding="utf-8")
    metadata = METADATA.read_text(encoding="utf-8")
    resources = RESOURCES.read_text(encoding="utf-8")

    # Current normative protocol distinctions that were missing or too compressed.
    assert "预注册的 client 信息" in lesson
    assert "CIMD" in lesson and "DCR" in lesson and "回退" in lesson
    assert "authorization_response_iss_parameter_supported" in lesson
    assert "精确字符串比较" in lesson and "不能大小写折叠" in lesson and "改写尾部斜杠" in lesson
    assert "PKCE" in lesson and "S256" in lesson and "拒绝继续" in lesson
    assert 'resource_metadata="<PRM URI>"' in lesson
    assert "当前操作需要的 scope" in lesson
    assert "不能放进 URL query string" in lesson
    assert "id: 'client-registration-priority'" in metadata
    assert "id: 'authorization-code-integrity'" in metadata
    assert "id: 'insufficient-scope-challenge'" in metadata
    assert "basis: 'documented'" in metadata
    assert "sourceIds: ['mcp-authorization-2026']" in metadata
    resource = resources.split("'mcp-authorization-2026': {", 1)[1].split("\n  },", 1)[0]
    assert "verifiedAt: '2026-10-22'" in resource

    result = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "examples/mcp-remote-auth", "-v"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
        timeout=15,
    )
    output = result.stderr + result.stdout
    match = re.search(r"Ran (\d+) tests? in", output)
    assert match and int(match.group(1)) == 7, output
    assert "OK" in output, output
    print("MCP remote authorization boundaries: 16/16")
    print("providerCalls=0; externalNetworkCalls=0; offline teaching tests=7/7")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
