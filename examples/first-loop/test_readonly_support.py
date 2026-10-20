import unittest

from readonly_support import MAX_OUTPUT_TOKENS, MAX_ROUNDS, run_agent


class ReadonlyAgentTests(unittest.TestCase):
    def test_tool_result_returns_to_model_before_final_answer(self):
        seen = []
        responses = iter([
            {"stop_reason": "tool_use", "content": [{"type": "tool_use", "id": "call-1", "name": "lookup_order", "input": {"order_id": "A-1001"}}]},
            {"stop_reason": "end_turn", "content": [{"type": "text", "text": "订单 A-1001 已发货。"}]},
        ])

        def model_call(messages, max_tokens):
            seen.append((messages, max_tokens))
            return next(responses)

        result = run_agent("A-1001 到哪了？", model_call)
        self.assertEqual(result, {"status": "completed", "text": "订单 A-1001 已发货。", "rounds": 2, "tool_calls": 1})
        self.assertEqual(seen[0][1], MAX_OUTPUT_TOKENS)
        self.assertEqual(seen[1][0][-1]["content"][0]["type"], "tool_result")

    def test_unknown_order_is_reported_as_tool_error_without_side_effect(self):
        seen = []
        responses = iter([
            {"stop_reason": "tool_use", "content": [{"type": "tool_use", "id": "call-x", "name": "lookup_order", "input": {"order_id": "A-9999"}}]},
            {"stop_reason": "end_turn", "content": [{"type": "text", "text": "fixture 中没有这笔订单。"}]},
        ])

        def model_call(messages, max_tokens):
            seen.append(messages)
            return next(responses)

        result = run_agent("查订单 A-9999", model_call)
        self.assertEqual(result["status"], "completed")
        failed_tool_result = seen[1][-1]["content"][0]
        self.assertTrue(failed_tool_result["is_error"])
        self.assertIn('"not_found"', failed_tool_result["content"])

    def test_rejects_a_model_response_truncated_by_output_limit(self):
        result = run_agent("查一下", lambda *_args, **_kwargs: {"stop_reason": "max_tokens", "content": []})
        self.assertEqual(result["status"], "truncated")
        self.assertEqual(result["text"], "")

    def test_preserves_valid_nonfinal_stop_reasons_as_distinct_states(self):
        cases = {
            "refusal": "refused",
            "pause_turn": "paused",
            "model_context_window_exceeded": "context_limit",
            "stop_sequence": "stopped",
        }
        for stop_reason, expected_status in cases.items():
            with self.subTest(stop_reason=stop_reason):
                result = run_agent("请求", lambda *_args, reason=stop_reason, **_kwargs: {"stop_reason": reason, "content": []})
                self.assertEqual(result["status"], expected_status)

    def test_stops_after_the_configured_number_of_rounds(self):
        calls = []

        def keeps_calling(messages, max_tokens):
            calls.append(messages)
            return {"stop_reason": "tool_use", "content": [{"type": "tool_use", "id": f"call-{len(calls)}", "name": "lookup_order", "input": {"order_id": "A-1001"}}]}

        result = run_agent("查订单", keeps_calling, max_rounds=2)
        self.assertEqual(result["status"], "max_rounds")
        self.assertEqual(result["rounds"], 2)
        self.assertEqual(len(calls), 2)
        self.assertEqual(MAX_ROUNDS, 4)


if __name__ == "__main__":
    unittest.main(verbosity=2)
