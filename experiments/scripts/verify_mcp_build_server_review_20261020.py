"""Run deterministic protocol-shape checks for the MCP build-a-server lesson."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

LESSON = Path("src/content/chapters/mcp/04-build-a-server.mdx")
SOURCE = LESSON.read_text(encoding="utf-8")
PYTHON_FENCES = re.findall(r"^```python\n(.*?)^```\s*$", SOURCE, re.M | re.S)
SERVER = next(block for block in PYTHON_FENCES if "SUPPORTED_VERSIONS" in block)
for index, block in enumerate(PYTHON_FENCES):
    compile(block, f"{LESSON}:python-fence-{index}", "exec")

META = {
    "io.modelcontextprotocol/protocolVersion": "2026-07-28",
    "io.modelcontextprotocol/clientCapabilities": {"elicitation": {}},
}


def request(request_id: int, method: str, params: dict, version: str = "2026-07-28") -> dict:
    params = dict(params)
    params["_meta"] = {
        "io.modelcontextprotocol/protocolVersion": version,
        "io.modelcontextprotocol/clientCapabilities": {"elicitation": {}},
    }
    return {"jsonrpc": "2.0", "id": request_id, "method": method, "params": params}


requests = [
    request(1, "server/discover", {}),
    request(2, "tools/list", {}),
    request(3, "tools/call", {"name": "get_weather", "arguments": {"city": "北京", "day": "明天"}}),
    request(4, "tools/call", {"name": "transfer_money", "arguments": {"to": "张三", "amount": 5000}}),
    request(5, "tools/list", {}, version="2025-11-25"),
    {"jsonrpc": "2.0", "id": 6, "method": "tools/list", "params": {"_meta": {"io.modelcontextprotocol/protocolVersion": "2026-07-28"}}},
    request(7, "resources/subscribe", {}),
]
run = subprocess.run(
    [sys.executable, "-c", SERVER],
    input="".join(json.dumps(item, ensure_ascii=False) + "\n" for item in requests),
    text=True,
    capture_output=True,
    check=True,
)
responses = [json.loads(line) for line in run.stdout.splitlines()]
assert len(responses) == len(requests)
assert responses[0]["result"]["supportedVersions"] == ["2026-07-28"]
assert responses[0]["result"]["ttlMs"] >= 0
assert responses[0]["result"]["cacheScope"] == "public"
assert responses[1]["result"]["ttlMs"] >= 0
assert responses[1]["result"]["cacheScope"] == "public"
for response in responses[:4]:
    assert response["result"]["_meta"]["io.modelcontextprotocol/serverInfo"]["name"] == "demo-server"
assert responses[2]["result"]["resultType"] == "complete"
assert responses[3]["result"]["resultType"] == "input_required"
assert responses[4]["error"]["code"] == -32022
assert responses[5]["error"]["code"] == -32602
assert responses[6]["error"]["code"] == -32601

print(json.dumps({"pythonFencesCompiled": len(PYTHON_FENCES), "serverRequestsChecked": len(requests)}))
