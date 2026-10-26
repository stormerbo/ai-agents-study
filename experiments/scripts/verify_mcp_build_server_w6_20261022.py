"""Offline W6 checks for MCP tool names, execution errors, and host result mapping."""
from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/mcp/04-build-a-server.mdx"
META = ROOT / "src/content/chapters/mcp/meta.ts"
RESOURCES = ROOT / "src/content/curriculum/resources.ts"
SOURCE = LESSON.read_text(encoding="utf-8")
PYTHON_FENCES = re.findall(r"^```python\n(.*?)^```\s*$", SOURCE, re.M | re.S)
SERVER = next(block for block in PYTHON_FENCES if "SUPPORTED_VERSIONS" in block)
HOST_ADAPTER = next(block for block in PYTHON_FENCES if "def handle_tool_use" in block)

checks: list[str] = []

def check(condition: bool, name: str) -> None:
    if not condition:
        raise AssertionError(name)
    checks.append(name)


# MCP's tool-name recommendations are SHOULD-level and permit dots; do not
# generalize a provider-specific regex into a protocol MUST.
checkpoint = META.read_text(encoding="utf-8")
resource_registry = RESOURCES.read_text(encoding="utf-8")
checkpoint_start = checkpoint.index("id: 'server-minimum'")
checkpoint_excerpt = checkpoint[checkpoint_start:checkpoint.index("        },", checkpoint_start)]
check("MCP 2026-07-28" in checkpoint_excerpt and "SHOULD" in checkpoint_excerpt
      and "不是 `^[a-zA-Z0-9_-]+$` 这样的 MUST 正则" in checkpoint_excerpt
      and "`_`/`-`/`.`" in checkpoint_excerpt,
      "checkpoint distinguishes MCP name recommendations from provider-specific regex")
check("mcp-2026-tools-spec" in checkpoint_excerpt and "mcp-2026-spec" in checkpoint_excerpt,
      "documented checkpoint cites official base and tools specifications")
check("2026-10-22" in resource_registry[resource_registry.index("'mcp-2026-tools-spec'"):resource_registry.index("'mcp-2026-tools-spec'") + 700],
      "tools source verification date is current")

for index, block in enumerate(PYTHON_FENCES):
    compile(block, f"{LESSON}:python-fence-{index}", "exec")
check(bool(PYTHON_FENCES), "all embedded Python fences compile")

# Run the published client and server together from a clean temporary directory.
CLIENT = next(block for block in PYTHON_FENCES if "class Client" in block)
with tempfile.TemporaryDirectory(prefix="mcp-build-server-w6-") as temp_dir:
    Path(temp_dir, "mcp_server.py").write_text(SERVER, encoding="utf-8")
    Path(temp_dir, "mcp_client.py").write_text(CLIENT, encoding="utf-8")
    client_run = subprocess.run([sys.executable, "mcp_client.py"], cwd=temp_dir, text=True,
                                capture_output=True, check=True, timeout=10)
check("补上确认后重调" in client_run.stdout and "本示例未连接转账系统" in client_run.stdout
      and "isError" in client_run.stdout,
      "published client/server complete MRTR round-trip and display MCP tool errors")

# Run the real documented stdio server with valid, unavailable, and malformed inputs.
requests = []
for request_id, city, day in ((1, "北京", "明天"), (2, "广州", "明天"), (3, "北京", "下周")):
    requests.append({"jsonrpc": "2.0", "id": request_id, "method": "tools/call",
                     "params": {"name": "get_weather", "arguments": {"city": city, "day": day},
                                "_meta": {"io.modelcontextprotocol/protocolVersion": "2026-07-28",
                                          "io.modelcontextprotocol/clientCapabilities": {"elicitation": {}}}}})
requests.append({"jsonrpc": "2.0", "id": 4, "method": "tools/call",
                 "params": {"name": "get_weather", "arguments": [],
                            "_meta": {"io.modelcontextprotocol/protocolVersion": "2026-07-28",
                                      "io.modelcontextprotocol/clientCapabilities": {"elicitation": {}}}}})
for request_id, amount in ((5, True), (6, float("nan"))):
    requests.append({"jsonrpc": "2.0", "id": request_id, "method": "tools/call",
                     "params": {"name": "transfer_money", "arguments": {"to": "张三", "amount": amount},
                                "_meta": {"io.modelcontextprotocol/protocolVersion": "2026-07-28",
                                          "io.modelcontextprotocol/clientCapabilities": {"elicitation": {}}}}})
run = subprocess.run([sys.executable, "-c", SERVER], input="".join(json.dumps(x, ensure_ascii=False) + "\n" for x in requests),
                     text=True, capture_output=True, check=True)
responses = [json.loads(line) for line in run.stdout.splitlines()]
check(len(responses) == 6, "server emits one response per request")
check(responses[0]["result"].get("isError", False) is False, "valid tool execution is not marked as error")
check(responses[1]["result"].get("isError") is True, "business/input failure uses MCP result isError")
check(responses[2]["result"].get("isError") is True,
      "tool input validation failure remains a tool execution error")
check(responses[3]["error"]["code"] == -32602, "non-object tool arguments are rejected before dispatch")
check(all(response["result"].get("isError") is True for response in responses[4:]),
      "boolean and non-finite amounts fail as tool input errors")

# Exercise the real adapter against a deterministic fake transport response.
namespace: dict[str, object] = {"json": json}
exec(HOST_ADAPTER, namespace)
class FakeClient:
    def send(self, *_args, **_kwargs):
        return {"result": {"resultType": "complete", "isError": True, "content": [
            {"type": "text", "text": "first"}, {"type": "image", "data": "ignored-by-text-only-bridge"},
            {"type": "text", "text": "second"}]}}

mapped = namespace["handle_tool_use"]({"id": "call-1", "name": "get_weather", "input": {}}, FakeClient())
model_result = mapped["tool_result"]
check(model_result.get("is_error") is True, "host adapter forwards MCP execution error to model")
check(model_result["content"] == "first\nsecond", "host adapter safely joins multiple text blocks")
check("只把文本块传给模型" in SOURCE,
      "host adapter documents its text-only content mapping")

print(json.dumps({"checks": checks, "count": len(checks), "providerCalls": 0, "externalNetworkCalls": 0}, ensure_ascii=False))
