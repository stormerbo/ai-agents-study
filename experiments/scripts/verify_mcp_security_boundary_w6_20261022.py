"""Regression checks for MCP security-boundary SSRF distinctions."""

from pathlib import Path

lesson = Path("src/content/chapters/mcp/05-security-boundary.mdx").read_text(encoding="utf-8")
resources = Path("src/content/curriculum/resources.ts").read_text(encoding="utf-8")
metadata = Path("src/content/chapters/mcp/meta.ts").read_text(encoding="utf-8")

assert "授权服务器元数据" in lesson and "SSRF" in lesson
assert "MCP client" in lesson and "主动抓取 URL" in lesson
assert "不能推出 server 的出站网络范围" in lesson
assert "不是协议保证" in lesson
resource = resources.split("'mcp-security-best-practices-2026': {", 1)[1].split("\n  },", 1)[0]
assert "SSRF" in resource and "出口" in resource
assert "verifiedAt: '2026-10-22'" in resource
assert "id: 'remote-ssrf-boundary'" in metadata
assert "basis: 'documented'" in metadata and "sourceIds: ['mcp-security-best-practices-2026']" in metadata

print("MCP security-boundary SSRF distinctions: 8/8")
