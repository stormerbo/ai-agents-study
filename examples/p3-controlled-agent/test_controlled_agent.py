import unittest

from controlled_agent import (
    run_agent,
    validate_tool_arguments,
)


TOOLS = [
    {
        "name": "lookup_order",
        "description": "Query a synthetic order without changing it.",
        "inputSchema": {
            "type": "object",
            "properties": {"order_id": {"type": "string", "enum": ["A-1001", "A-1002"]}},
            "required": ["order_id"],
            "additionalProperties": False,
        },
    }
]


class FakeSession:
    def __init__(self):
        self.calls = []

    async def list_tools(self):
        return {"tools": TOOLS}

    async def call_tool(self, name, arguments):
        self.calls.append((name, arguments))
        return {"content": [{"type": "text", "text": '{"status":"shipped"}'}], "isError": False}


class ControlledAgentTests(unittest.IsolatedAsyncioTestCase):
    async def test_validated_tool_call_round_trips_and_then_finishes(self):
        session = FakeSession()
        responses = iter([
            {"stop_reason": "tool_use", "content": [{"type": "tool_use", "id": "call-1", "name": "lookup_order", "input": {"order_id": "A-1001"}}], "usage": {"input_tokens": 0, "output_tokens": 0}},
            {"stop_reason": "end_turn", "content": [{"type": "text", "text": "订单 A-1001 已发货。"}], "usage": {"input_tokens": 12, "output_tokens": 7}},
        ])
        result = await run_agent("A-1001 到哪了？", session, lambda messages, tools, max_tokens: next(responses))

        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["text"], "订单 A-1001 已发货。")
        self.assertEqual(session.calls, [("lookup_order", {"order_id": "A-1001"})])
        self.assertEqual(result["trace"][0]["tools"][0]["tool_result_id"], "call-1")
        self.assertEqual(result["usage"], {"input_tokens": 12, "output_tokens": 7})

    async def test_argument_schema_is_checked_before_mcp_execution(self):
        good, reason = validate_tool_arguments(TOOLS[0]["inputSchema"], {"order_id": "A-1001"})
        bad, reason_bad = validate_tool_arguments(TOOLS[0]["inputSchema"], {"order_id": "A-9999"})
        self.assertTrue(good, reason)
        self.assertFalse(bad)
        self.assertIn("enum", reason_bad)

    async def test_unknown_tool_fails_closed_without_calling_mcp(self):
        session = FakeSession()
        response = {"stop_reason": "tool_use", "content": [{"type": "tool_use", "id": "call-x", "name": "refund_order", "input": {"order_id": "A-1001"}}]}
        result = await run_agent("退款", session, lambda messages, tools, max_tokens: response)
        self.assertEqual(session.calls, [])
        self.assertEqual(result["status"], "tool_error")

    async def test_parallel_calls_receive_a_result_for_every_tool_use_id(self):
        session = FakeSession()
        response = {"stop_reason": "tool_use", "content": [
            {"type": "tool_use", "id": "call-ok", "name": "lookup_order", "input": {"order_id": "A-1001"}},
            {"type": "tool_use", "id": "call-bad", "name": "refund_order", "input": {}},
        ]}
        captured = []

        def model_call(messages, tools, max_tokens):
            captured.append(messages)
            return response

        result = await run_agent("查订单", session, model_call)
        self.assertEqual(result["status"], "tool_error")
        tool_results = captured[0][-1]["content"]
        self.assertEqual([item["tool_use_id"] for item in tool_results], ["call-ok", "call-bad"])
        self.assertTrue(tool_results[1]["is_error"])

    async def test_truncation_is_not_reported_as_completion(self):
        session = FakeSession()
        result = await run_agent("长答", session, lambda messages, tools, max_tokens: {"stop_reason": "max_tokens", "content": []})
        self.assertEqual(result["status"], "truncated")

    async def test_end_turn_refusal_block_is_reported_as_refused(self):
        session = FakeSession()
        response = {"stop_reason": "end_turn", "content": [{"type": "refusal", "refusal": "不能执行该请求。"}]}
        result = await run_agent("写入订单", session, lambda messages, tools, max_tokens: response)
        self.assertEqual(result["status"], "refused")
        self.assertIn("不能执行", result["text"])

    async def test_unknown_stop_reason_is_protocol_error(self):
        session = FakeSession()
        result = await run_agent("hello", session, lambda messages, tools, max_tokens: {"stop_reason": "new_reason", "content": []})
        self.assertEqual(result["status"], "protocol_error")

    async def test_round_limit_stops_tool_loop(self):
        session = FakeSession()
        response = {"stop_reason": "tool_use", "content": [{"type": "tool_use", "id": "call-1", "name": "lookup_order", "input": {"order_id": "A-1001"}}]}
        result = await run_agent("A-1001", session, lambda messages, tools, max_tokens: response, max_rounds=1)
        self.assertEqual(result["status"], "max_rounds")

    async def test_tool_call_budget_stops_before_the_next_mcp_call(self):
        session = FakeSession()
        response = {"stop_reason": "tool_use", "content": [
            {"type": "tool_use", "id": "call-1", "name": "lookup_order", "input": {"order_id": "A-1001"}},
            {"type": "tool_use", "id": "call-2", "name": "lookup_order", "input": {"order_id": "A-1002"}},
        ]}
        result = await run_agent("查询订单", session, lambda messages, tools, max_tokens: response, max_tool_calls=1)
        self.assertEqual(session.calls, [("lookup_order", {"order_id": "A-1001"})])
        self.assertEqual(result["status"], "max_tool_calls")


if __name__ == "__main__":
    unittest.main()
