"""Verify the MCP integration-count explanation and host/client MRTR adapter."""
from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

LESSON = Path("src/content/chapters/mcp/01-why-protocol.mdx")
SERVER_LESSON = Path("src/content/chapters/mcp/04-build-a-server.mdx")
lesson_source = LESSON.read_text(encoding="utf-8")
server_source = SERVER_LESSON.read_text(encoding="utf-8")
lesson_fences = re.findall(r"^```python\n(.*?)^```\s*$", lesson_source, re.M | re.S)
json_fences = re.findall(r"^```json\n(.*?)^```\s*$", lesson_source, re.M | re.S)
server_fences = re.findall(r"^```python\n(.*?)^```\s*$", server_source, re.M | re.S)
for path, blocks in ((LESSON, lesson_fences), (SERVER_LESSON, server_fences)):
    for i, block in enumerate(blocks):
        compile(block, f"{path}:python-fence-{i}", "exec")

def server_block(blocks: list[str]) -> str:
    return next(block for block in blocks if "SUPPORTED_VERSIONS" in block)

server = server_block(server_fences)
assert server_block(lesson_fences).strip() == server.strip(), "duplicate server example drifted from canonical lesson"
wire_examples = [json.loads(block) for block in json_fences]
assert len(wire_examples) == 2
assert wire_examples[0]["method"] == "tools/call" and wire_examples[0]["id"] == wire_examples[1]["id"]
assert wire_examples[1]["result"]["_meta"]["io.modelcontextprotocol/serverInfo"]["name"] == "demo-server"
adapter = next(block for block in lesson_fences if "def handle_tool_use" in block)

class CompleteWithToolError:
    def send(self, _method: str, _params: dict[str, object]) -> dict[str, object]:
        return {"result": {"resultType": "complete", "isError": True,
                           "content": [{"type": "text", "text": "tool failed"}]}}

error_result = {"type": "tool_use", "id": "toolu_error", "name": "sample", "input": {}}
error_mapping = {}
exec(compile(adapter, "host-adapter-is-error", "exec"), error_mapping)
mapped_error = error_mapping["handle_tool_use"](error_result, CompleteWithToolError(), lambda _requests: {})
assert mapped_error["is_error"] is True and mapped_error["tool_use_id"] == "toolu_error"

with tempfile.TemporaryDirectory(prefix="mcp-why-protocol-") as temp_dir:
    server_path = Path(temp_dir, "mcp_server.py")
    server_path.write_text(server, encoding="utf-8")
    client_code = next(block for block in server_fences if "class Client" in block)
    client_code = client_code.replace('SERVER = [sys.executable, "mcp_server.py"]', f"SERVER = [sys.executable, {str(server_path)!r}]")
    client_ns: dict[str, object] = {"__name__": "client_example"}
    exec(compile(client_code, "mcp-client-example", "exec"), client_ns)

    adapter_ns: dict[str, object] = {}
    exec(compile(adapter, "host-adapter-example", "exec"), adapter_ns)
    raw_client = client_ns["Client"]()
    observed_ids: list[int] = []
    observed_params: list[dict[str, object]] = []

    class TrackingClient:
        def send(self, method: str, params: dict[str, object]) -> dict[str, object]:
            observed_params.append(dict(params))
            response = raw_client.send(method, params)
            observed_ids.append(response["id"])
            return response

    host_result = adapter_ns["handle_tool_use"](
        {"id": "toolu_1", "name": "transfer_money", "input": {"to": "张三", "amount": 5000}},
        TrackingClient(),
        lambda requests: {"confirm": {"action": "accept", "content": {"confirmed": True}}},
    )
    assert host_result["type"] == "tool_result" and host_result["tool_use_id"] == "toolu_1"
    assert "不会发生真实转账" in host_result["content"]
    assert len(observed_ids) == 2 and observed_ids[0] != observed_ids[1]
    assert observed_params[1]["name"] == observed_params[0]["name"]
    assert observed_params[1]["arguments"] == observed_params[0]["arguments"]
    assert observed_params[1]["inputResponses"]["confirm"]["content"]["confirmed"] is True
    assert observed_params[1]["requestState"] == json.dumps({"to": "张三", "amount": 5000}, sort_keys=True, ensure_ascii=False)

    error_result = adapter_ns["handle_tool_use"](
        {"id": "toolu_2", "name": "no_such_tool", "input": {}},
        TrackingClient(),
        lambda _requests: {},
    )
    assert error_result["tool_use_id"] == "toolu_2" and error_result["is_error"] is True
    raw_client.close()

# N×M → N+M is the labeled interface-count model, not a measured work reduction.
assert "最多 3 × 4 = 12" in lesson_source
assert "3 个 host 侧接入 + 4 个 server 适配 = 7" in lesson_source
assert "MCP 对上完全透明" not in lesson_source
assert "协议的价值为零" not in lesson_source

print(json.dumps({"pythonFencesCompiled": len(lesson_fences) + len(server_fences), "serverRequestsChecked": 3}, ensure_ascii=False))
