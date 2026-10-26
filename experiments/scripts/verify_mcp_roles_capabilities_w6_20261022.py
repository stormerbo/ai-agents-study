#!/usr/bin/env python3
"""Offline whole-lesson checks for MCP roles and capabilities."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/mcp/02-roles-and-capabilities.mdx"
source = LESSON.read_text(encoding="utf-8")
checks = 0


def check(condition: bool, message: str) -> None:
    global checks
    checks += 1
    if not condition:
        raise AssertionError(message)


fence = chr(96) * 3
blocks: list[tuple[str, str]] = []
language: str | None = None
body: list[str] = []
for line in source.splitlines():
    if language is None and line.startswith(fence):
        language = line[len(fence):].strip()
        body = []
    elif language is not None and line.strip() == fence:
        blocks.append((language, "\n".join(body)))
        language = None
    elif language is not None:
        body.append(line)

python_blocks = [body for lang, body in blocks if lang == "python"]
json_blocks = [body for lang, body in blocks if lang == "json"]
check(len(python_blocks) == 2, f"expected two Python fences, got {len(python_blocks)}")
check(len(json_blocks) == 6, f"expected six JSON wire examples, got {len(json_blocks)}")

namespaces: list[dict[str, object]] = []
for index, code in enumerate(python_blocks):
    compiled = compile(code, f"lesson-python-fence-{index + 1}", "exec")
    namespace: dict[str, object] = {"__name__": f"lesson_fence_{index}"}
    exec(compiled, namespace)
    namespaces.append(namespace)
    check(True, f"Python fence {index + 1} compiles")

for index, wire in enumerate(json_blocks):
    check(isinstance(json.loads(wire), dict), f"JSON example {index + 1} parses")

permitted = namespaces[0]["permitted"]
check(permitted("github", "get_issue") == "allow", "allowlisted tool is allowed")
check(permitted("tickets", "close_ticket") == "confirm", "confirmation tool requires confirmation")
check(permitted("tickets", "delete_all") == "deny", "unlisted tool is denied")
check(permitted([], "get_issue") == "deny", "unhashable server value fails closed")
check(permitted("github", []) == "deny", "unhashable tool value fails closed")

handle = namespaces[1]["handle"]
meta = {
    "io.modelcontextprotocol/protocolVersion": "2026-07-28",
    "io.modelcontextprotocol/clientCapabilities": {},
}


def request(method: str, params: object = None, version: str = "2026-07-28") -> dict[str, object]:
    if params is None:
        params = {}
    if isinstance(params, dict):
        params.setdefault("_meta", {
            "io.modelcontextprotocol/protocolVersion": version,
            "io.modelcontextprotocol/clientCapabilities": {},
        })
    return {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}


discovery = handle(request("server/discover"))
check(discovery["result"]["resultType"] == "complete", "discover is a complete result")
check(discovery["result"]["supportedVersions"] == ["2026-07-28"], "only implemented era is advertised")
check(discovery["result"]["capabilities"] == {"tools": {}}, "only implemented capability is advertised")
listing = handle(request("tools/list"))
check(listing["result"]["resultType"] == "complete", "tools/list is complete")
check({item["name"] for item in listing["result"]["tools"]} == {"get_weather", "transfer_money"}, "tool list matches implementation")

unsupported = handle(request("tools/list", version="2025-11-25"))
check(unsupported["error"]["code"] == -32022, "legacy-era request is rejected")
check(unsupported["error"]["data"]["supported"] == ["2026-07-28"], "version error lists actual support")
check(handle({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})["error"]["code"] == -32602, "missing required metadata is rejected")
check(handle([])["error"]["code"] == -32600, "non-object request is rejected")
check(handle(request("tools/list", []))["error"]["code"] == -32602, "non-object params are rejected")
check(handle(request("tools/list", {"_meta": []}))["error"]["code"] == -32602, "non-object metadata is rejected")

weather = handle(request("tools/call", {"name": "get_weather", "arguments": {"city": "北京", "day": "明天"}}))
check(json.loads(weather["result"]["content"][0]["text"]) == 31, "weather fixture returns expected value")
check(handle(request("tools/call", {"name": "get_weather", "arguments": {"city": [], "day": "明天"}}))["error"]["code"] == -32602, "malformed weather arguments are rejected")
check(handle(request("tools/call", {"name": "get_weather", "arguments": []}))["error"]["code"] == -32602, "non-object arguments are rejected")
check(handle(request("tools/call", {"name": "missing", "arguments": {}}))["error"]["code"] == -32602, "unknown tool is rejected")

transfer = {"name": "transfer_money", "arguments": {"to": "acct-7", "amount": 12}}
approval = handle(request("tools/call", transfer))
check(approval["result"]["resultType"] == "input_required", "transfer simulation asks before continuing")
check("confirm" in approval["result"]["inputRequests"], "input request has a stable key")
for amount in (True, 0, -1, float("nan"), float("inf"), "12"):
    result = handle(request("tools/call", {
        "name": "transfer_money",
        "arguments": {"to": "acct-7", "amount": amount},
    }))
    check(result["error"]["code"] == -32602, f"invalid amount rejected: {amount!r}")
for responses in ([], {"confirm": None}, {"confirm": []}, {"confirm": {"action": "accept", "content": []}}):
    result = handle(request("tools/call", {**transfer, "inputResponses": responses}))
    check(result["error"]["code"] == -32602, "malformed input response rejected")
declined = handle(request("tools/call", {
    **transfer, "inputResponses": {"confirm": {"action": "decline"}},
}))
check("未确认" in declined["result"]["content"][0]["text"], "decline does not act")
accepted = handle(request("tools/call", {
    **transfer, "inputResponses": {"confirm": {"action": "accept", "content": {"confirmed": True}}},
}))
check("没有执行真实转账" in accepted["result"]["content"][0]["text"], "confirmation demo has no side effect")

for phrase in (
    "不是 MCP 对所有 host 强制规定的执行流程",
    "mimeType` 是可选字段",
    "server 必须实现",
    "arguments` 列表是可选的",
    "不保证只有一条或只有",
    "恶意指令带进模型上下文",
    "resultType",
):
    check(phrase in source, f"audited lesson boundary present: {phrase}")
for obsolete in (
    "风险接近于零",
    "不能阻止它决定调用",
    "模型自己分不出哪个来自哪类能力",
    "SUPPORTED_VERSIONS = [\"2026-07-28\", \"2025-11-25\"]",
):
    check(obsolete not in source, f"obsolete overclaim removed: {obsolete}")
check("import requests" not in source and "urllib.request" not in source, "no network client appears in examples")
print(f"PASS: {checks}/{checks} checks; pythonFences={len(python_blocks)}, jsonExamples={len(json_blocks)}, providerCalls=0, externalNetworkCalls=0")
