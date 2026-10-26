import contextlib
import io
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/reading-source/04-compare.mdx"
META = ROOT / "src/content/chapters/reading-source/meta.ts"
RESOURCES = ROOT / "src/content/curriculum/resources.ts"
source = LESSON.read_text()
meta = META.read_text()
resources = RESOURCES.read_text()
checks = 0


def check(condition, message):
    global checks
    assert condition, message
    checks += 1


fences = re.findall(r"^```python\n([\s\S]*?)^```\s*$", source, re.M)
check(len(fences) == 1, f"expected one Python fence, found {len(fences)}")
namespace = {"__name__": "__main__"}
captured = io.StringIO()
with contextlib.redirect_stdout(captured):
    exec(compile(fences[0], str(LESSON), "exec"), namespace)
output = captured.getvalue()
check("required: ['city', 'day', 'passengers']" in output, output)
check("required: （未声明）" in output, output)
check("按 schema 字面，properties 中字段并非必填" in output, output)

tool = namespace["book_flight"]
for invalid in (
    {"city": "北京"},
    {"city": "北京", "day": "下周", "passengers": 1},
):
    try:
        tool.invoke(invalid)
    except Exception as error:
        check(type(error).__name__ == "ValidationError", repr(error))
    else:
        check(False, f"LangChain accepted invalid arguments: {invalid}")

schema = namespace["C_MCP"]["inputSchema"]
check("required" not in schema, "constructed MCP example should omit required")
check("MCP server 仍须校验声明的 schema" in source, "server validation duty must be explicit")
check("也可能作为工具执行错误被拒绝" in source, "business validation error boundary must be explicit")
check("https://modelcontextprotocol.io/specification/2026-07-28/server/tools" in source, "MCP citation must be version-pinned")
check("mcp-input-schema-contract" in meta and "sourceIds: ['mcp-2026-tools-spec', 'json-schema-object-reference']" in meta, "documented checkpoint must reference sources")
check("id: 'mcp-2026-tools-spec'" in resources and "https://modelcontextprotocol.io/specification/2026-07-28/server/tools" in resources, "resource registry must contain version-pinned source")
check("LangChain/Pydantic 会按生成的 schema 做结构校验" in source, "validation claim must stay scoped")
check("历史摘要" in source or "构造数据，未实跑" in source, "synthetic MCP schema must remain labeled")

print(json.dumps({"checks": checks, "passed": checks, "pythonFencesCompiled": len(fences), "providerCalls": 0, "fixtureOnly": True}, ensure_ascii=False))
