"""Run deterministic shape checks for the MCP 2026-07-28 lesson examples."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path


LESSON = Path("src/content/chapters/mcp/03-stateless-2026.mdx")
SOURCE = LESSON.read_text(encoding="utf-8")
PYTHON_FENCES = re.findall(r"^```python\n(.*?)^```\s*$", SOURCE, re.M | re.S)
SERVER = next(block for block in PYTHON_FENCES if "SUPPORTED_VERSIONS" in block)
for index, block in enumerate(PYTHON_FENCES):
    compile(block, f"{LESSON}:python-fence-{index}", "exec")

META = {
    "io.modelcontextprotocol/protocolVersion": "2026-07-28",
    "io.modelcontextprotocol/clientCapabilities": {"elicitation": {}},
}


def request(request_id: int, method: str, params: dict) -> dict:
    return {"jsonrpc": "2.0", "id": request_id, "method": method, "params": params}


requests = [
    request(1, "server/discover", {"_meta": META}),
    request(2, "tools/list", {"_meta": META}),
    request(
        3,
        "tools/call",
        {"_meta": META, "name": "transfer_money", "arguments": {"to": "张三", "amount": 5000}},
    ),
    request(
        4,
        "tools/call",
        {
            "_meta": META,
            "name": "transfer_money",
            "arguments": {"to": "张三", "amount": 5000},
            "inputResponses": {"confirm": {"action": "accept", "content": {"confirmed": True}}},
        },
    ),
    request(
        5,
        "tools/list",
        {
            "_meta": {
                "io.modelcontextprotocol/protocolVersion": "2030-01-01",
                "io.modelcontextprotocol/clientCapabilities": {},
            }
        },
    ),
    request(6, "tools/list", {"_meta": {"io.modelcontextprotocol/protocolVersion": "2026-07-28"}}),
    request(
        7,
        "tools/list",
        {
            "_meta": {
                "io.modelcontextprotocol/protocolVersion": "2025-11-25",
                "io.modelcontextprotocol/clientCapabilities": {},
            }
        },
    ),
]
run = subprocess.run(
    [sys.executable, "-c", SERVER],
    input="".join(json.dumps(item, ensure_ascii=False) + "\n" for item in requests),
    text=True,
    capture_output=True,
    check=True,
)
responses = [json.loads(line) for line in run.stdout.splitlines()]
assert len(responses) == 7
for response in responses[:4]:
    assert response["result"]["_meta"]["io.modelcontextprotocol/serverInfo"]["name"] == "demo-server"
for response in responses[:2]:
    assert response["result"]["ttlMs"] == 0
    assert response["result"]["cacheScope"] == "public"
assert responses[2]["result"]["resultType"] == "input_required"
assert responses[3]["result"]["resultType"] == "complete"
assert "模拟完成" in responses[3]["result"]["content"][0]["text"]
assert "本示例没有执行转账" in responses[3]["result"]["content"][0]["text"]
assert responses[4]["error"]["code"] == -32022
assert responses[5]["error"]["code"] == -32602
assert responses[6]["error"]["code"] == -32022
assert responses[0]["result"]["supportedVersions"] == ["2026-07-28"]

subscription_section = SOURCE.split("### subscriptions/listen 的消息形态", 1)[1].split(
    "### 迁移：before / after", 1
)[0]
subscription_json = re.findall(r"^```json\n(.*?)^```\s*$", subscription_section, re.M | re.S)
messages = [json.loads(block) for block in subscription_json]
assert len(messages) == 3
assert messages[0]["params"]["notifications"]["resourceSubscriptions"] == [
    "file:///team/coding-standards.md"
]
assert messages[1]["method"] == "notifications/subscriptions/acknowledged"
assert messages[1]["params"]["_meta"]["io.modelcontextprotocol/subscriptionId"] == 21
assert messages[1]["params"]["notifications"] == messages[0]["params"]["notifications"]
assert "id" not in messages[2]
assert messages[2]["params"]["_meta"]["io.modelcontextprotocol/subscriptionId"] == 21

print(json.dumps({"pythonFencesCompiled": len(PYTHON_FENCES), "serverRequestsChecked": 7, "subscriptionMessagesParsed": 3}))
