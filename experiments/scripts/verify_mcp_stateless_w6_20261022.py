"""W6 regression checks for malformed input and overbroad claims in the MCP stateless lesson."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/mcp/03-stateless-2026.mdx"
SOURCE = LESSON.read_text(encoding="utf-8")
PYTHON_FENCES = re.findall(r"^```python\n(.*?)^```\s*$", SOURCE, re.M | re.S)
JSON_FENCES = re.findall(r"^```json\n(.*?)^```\s*$", SOURCE, re.M | re.S)
SERVER = next(block for block in PYTHON_FENCES if "SUPPORTED_VERSIONS" in block)
META = {
    "io.modelcontextprotocol/protocolVersion": "2026-07-28",
    "io.modelcontextprotocol/clientCapabilities": {},
}


def request(request_id: int, method: str, params: object) -> dict:
    return {"jsonrpc": "2.0", "id": request_id, "method": method, "params": params}


def request_line(request_id: int, method: str, params: object) -> str:
    return json.dumps(request(request_id, method, params), ensure_ascii=False)


def execute(lines: list[str]) -> list[dict]:
    run = subprocess.run(
        [sys.executable, "-c", SERVER],
        input="\n".join(lines) + "\n",
        text=True,
        capture_output=True,
        check=True,
    )
    return [json.loads(line) for line in run.stdout.splitlines()]


class StatelessLessonW6(unittest.TestCase):
    def test_published_code_and_json_examples_parse(self):
        self.assertEqual(len(PYTHON_FENCES), 3)
        for index, block in enumerate(PYTHON_FENCES):
            compile(block, f"{LESSON}:python-fence-{index}", "exec")
        self.assertGreaterEqual(len(JSON_FENCES), 8)
        for block in JSON_FENCES:
            json.loads(block)

    def test_jsonrpc_notification_receives_no_response(self):
        notification = {"jsonrpc": "2.0", "method": "notifications/cancelled", "params": {"requestId": 99}}
        self.assertEqual(execute([json.dumps(notification)]), [])

    def test_malformed_request_shapes_fail_closed_without_crashing(self):
        requests = [
            json.dumps(["not", "an", "object"]),
            request_line(2, "tools/list", []),
            request_line(3, "tools/list", {"_meta": []}),
            request_line(4, "tools/list", {"_meta": {**META, "io.modelcontextprotocol/protocolVersion": 20260728}}),
            request_line(5, "tools/list", {"_meta": {**META, "io.modelcontextprotocol/clientCapabilities": "tools"}}),
        ]
        responses = execute(requests)
        self.assertEqual(responses[0]["error"]["code"], -32600)
        for response in responses[1:]:
            self.assertEqual(response["error"]["code"], -32602)

    def test_tool_arguments_and_input_responses_are_validated(self):
        malformed_calls = [
            {"_meta": META, "name": "get_weather", "arguments": []},
            {"_meta": META, "name": "transfer_money", "arguments": {"to": "张三", "amount": 5000}, "inputResponses": []},
            {"_meta": META, "name": "transfer_money", "arguments": {"to": "张三", "amount": 5000}, "inputResponses": {"confirm": {"action": "accept", "content": {"confirmed": "false"}}}},
        ]
        responses = execute([
            request_line(index, "tools/call", params)
            for index, params in enumerate(malformed_calls, start=10)
        ])
        self.assertEqual([response["error"]["code"] for response in responses], [-32602] * len(malformed_calls))

    def test_transfer_example_never_claims_a_real_side_effect(self):
        responses = execute([
            request_line(20, "tools/call", {"_meta": META, "name": "transfer_money", "arguments": {"to": "张三", "amount": 5000}}),
            request_line(21, "tools/call", {"_meta": META, "name": "transfer_money", "arguments": {"to": "张三", "amount": 5000}, "inputResponses": {"confirm": {"action": "accept", "content": {"confirmed": True}}}}),
            request_line(22, "tools/call", {"_meta": META, "name": "transfer_money", "arguments": {"to": "张三", "amount": 5000}, "inputResponses": {"confirm": {"action": "decline", "content": {"confirmed": False}}}}),
        ])
        self.assertEqual(responses[0]["result"]["resultType"], "input_required")
        accepted = responses[1]["result"]["content"][0]["text"]
        declined = responses[2]["result"]["content"][0]["text"]
        self.assertIn("模拟", accepted)
        self.assertIn("未执行", declined)
        self.assertNotIn("已转账", accepted)

    def test_stateful_comparison_is_scoped_to_legacy_session_version(self):
        self.assertIn("legacy initialize/session", SOURCE)
        self.assertIn("不能把这个比较推广成", SOURCE)


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(StatelessLessonW6)
    )
    print(
        f"providerCalls=0; externalNetworkCalls=0; tests={result.testsRun}; "
        f"failures={len(result.failures) + len(result.errors)}"
    )
    raise SystemExit(not result.wasSuccessful())
