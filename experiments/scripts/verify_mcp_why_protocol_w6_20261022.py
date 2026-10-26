"""W6 full-lesson checks for the MCP protocol rationale and local examples."""
from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/mcp/01-why-protocol.mdx"
SERVER_LESSON = ROOT / "src/content/chapters/mcp/04-build-a-server.mdx"
META = ROOT / "src/content/chapters/mcp/meta.ts"
RESOURCES = ROOT / "src/content/curriculum/resources.ts"
OLD_VERIFIER = ROOT / "experiments/scripts/verify_mcp_why_protocol_review_20261020.py"

source = LESSON.read_text(encoding="utf-8")
server_source = SERVER_LESSON.read_text(encoding="utf-8")
meta = META.read_text(encoding="utf-8")
resources = RESOURCES.read_text(encoding="utf-8")
checks: list[str] = []


def check(condition: bool, name: str) -> None:
    if not condition:
        raise AssertionError(name)
    checks.append(name)


python_fences = re.findall(r"^```python\n(.*?)^```\s*$", source, re.M | re.S)
json_fences = re.findall(r"^```json\n(.*?)^```\s*$", source, re.M | re.S)
server_fences = re.findall(r"^```python\n(.*?)^```\s*$", server_source, re.M | re.S)
server = next(block for block in server_fences if "SUPPORTED_VERSIONS" in block)
duplicate_server = next(block for block in python_fences if "SUPPORTED_VERSIONS" in block)

check("N×M" in source and "最多 3 × 4 = 12" in source
      and "3 个 host 侧接入 + 4 个 server 适配 = 7" in source
      and "不等于工程工时必然按同一比例下降" in source,
      "integration-count example is explicitly a boundary-count model, not a labor estimate")
check("model-controlled" in meta and "其他 UI 交互模式" in meta,
      "documented tool interaction model preserves host UI flexibility")
scope_start = meta.index("id: 'mcp-scope'")
scope_end = meta.index("resourceIds: ['mcp-docs'", scope_start)
scope_excerpt = meta[scope_start:scope_end]
check("mcp-2026-tools-spec" in scope_excerpt,
      "the tool interaction qualification is linked to the official tools specification")
check("协议本身也包含授权与安全要求/建议" in meta
      and "具体的业务数据与动作授权" in meta,
      "protocol security guidance is separated from application authorization decisions")
check(len(json_fences) == 2, "both protocol wire examples are present")
wire = [json.loads(block) for block in json_fences]
check(wire[0]["method"] == "tools/call"
      and wire[0]["params"]["_meta"]["io.modelcontextprotocol/protocolVersion"] == "2026-07-28"
      and "io.modelcontextprotocol/clientCapabilities" in wire[0]["params"]["_meta"],
      "modern request carries required per-request protocol version and capabilities")
check(wire[1]["id"] == wire[0]["id"]
      and wire[1]["result"]["resultType"] == "complete"
      and wire[1]["result"]["_meta"]["io.modelcontextprotocol/serverInfo"]["name"] == "demo-server"
      and "不能作为安全凭据" in source,
      "response id/result metadata are correctly scoped and server identity is not trusted as auth")

for index, block in enumerate(python_fences):
    compile(block, f"{LESSON}:python-fence-{index}", "exec")
check(bool(python_fences), "every lesson Python fence compiles")
check(duplicate_server.strip() == server.strip(),
      "copied server example exactly matches the canonical server lesson")

# The earlier targeted review executes the actual stdio peer and host MRTR adapter.
old_run = subprocess.run([sys.executable, str(OLD_VERIFIER)], cwd=ROOT, text=True,
                         capture_output=True, check=True, timeout=20)
old_observation = json.loads(old_run.stdout)
check(old_observation == {"pythonFencesCompiled": 5, "serverRequestsChecked": 3},
      "previous stdio and host-adapter integration probe still passes")

# Exercise independent modern requests against the published server process.
meta_fields = {"io.modelcontextprotocol/protocolVersion": "2026-07-28",
               "io.modelcontextprotocol/clientCapabilities": {}}

def request(request_id: int, method: str, params: dict[str, object], version: str = "2026-07-28") -> dict[str, object]:
    request_meta = dict(meta_fields)
    request_meta["io.modelcontextprotocol/protocolVersion"] = version
    return {"jsonrpc": "2.0", "id": request_id, "method": method,
            "params": {**params, "_meta": request_meta}}


initial_args = {"to": "张三", "amount": 5000}
requests = [
    request(1, "tools/call", {"name": "get_weather", "arguments": {"city": "北京", "day": "明天"}}),
    request(2, "tools/call", {"name": "get_weather", "arguments": {"city": "北京", "day": "下周"}}),
    request(3, "tools/call", {"name": "unknown", "arguments": {}}),
    request(4, "tools/call", {"name": "transfer_money", "arguments": initial_args}),
    request(5, "tools/call", {"name": "transfer_money", "arguments": initial_args,
                               "inputResponses": {"confirm": {"action": "accept", "content": {"confirmed": True}}},
                               "requestState": json.dumps(initial_args, sort_keys=True, ensure_ascii=False)}),
    {"jsonrpc": "2.0", "id": 6, "method": "tools/list", "params": {}},
    request(7, "tools/list", {}, version="unsupported-version"),
]
with tempfile.TemporaryDirectory(prefix="mcp-why-protocol-w6-") as temp_dir:
    server_path = Path(temp_dir, "server.py")
    server_path.write_text(server, encoding="utf-8")
    run = subprocess.run([sys.executable, str(server_path)], input="".join(
        json.dumps(item, ensure_ascii=False) + "\n" for item in requests), cwd=temp_dir,
        text=True, capture_output=True, check=True, timeout=10)
responses = [json.loads(line) for line in run.stdout.splitlines()]
check(len(responses) == len(requests), "stdio server returns one response per modern request")
check(responses[0]["result"]["resultType"] == "complete"
      and responses[0]["result"]["isError"] is False,
      "successful tool execution is a complete MCP result")
check(responses[1]["result"]["isError"] is True,
      "tool-domain failure stays inside a successful JSON-RPC result as isError")
check(responses[2]["error"]["code"] == -32602,
      "unknown tool is returned as a top-level JSON-RPC protocol error")
check(responses[3]["result"]["resultType"] == "input_required"
      and responses[4]["result"]["resultType"] == "complete"
      and "不会发生真实转账" in responses[4]["result"]["content"][0]["text"],
      "MRTR input request is retried to completion without a real side effect")
check(responses[5]["error"]["code"] == -32602,
      "missing required per-request metadata is rejected")
check(responses[6]["error"]["code"] == -32022,
      "unsupported protocol version is rejected distinctly")

print(json.dumps({"checks": checks, "count": len(checks), "providerCalls": 0,
                  "externalNetworkCalls": 0}, ensure_ascii=False))
