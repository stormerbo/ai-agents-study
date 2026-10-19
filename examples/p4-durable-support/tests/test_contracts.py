"""Offline provider fixtures; these never constitute provider observations."""
import asyncio

import pytest


def test_shared_provider_contract_exists():
    from support_agent.providers import normalize_response, transport_error

    for stop, blocks, expected in [
        ("end_turn", [{"type": "text", "text": "done"}], "final"),
        ("tool_use", [{"type": "tool_use", "id": "c1", "name": "lookup_order", "input": {}}], "tool_calls"),
        ("refusal", [], "refusal"),
        ("end_turn", [{"type": "refusal", "refusal": "no"}], "refusal"),
        ("max_tokens", [], "truncated"),
    ]:
        outcome = normalize_response({"stop_reason": stop, "content": blocks})
        assert outcome.kind == expected
        assert outcome.stop_reason == stop
    assert transport_error(ConnectionError("must not be logged")).kind == "transport_error"
    assert "must not" not in repr(transport_error(ConnectionError("must not be logged")))
    with pytest.raises(ValueError):
        normalize_response({"stop_reason": "mystery", "content": []})
    with pytest.raises(ValueError):
        normalize_response({"stop_reason": "tool_use", "content": []})
    with pytest.raises(ValueError):
        normalize_response({"stop_reason": "end_turn", "content": [{"type": "new_block"}]})
    with pytest.raises(ValueError):
        normalize_response({"stop_reason": "end_turn", "content": [{"type": "tool_use", "id": "x"}]})


def test_gateway_rejects_forbidden_and_invalid_calls_before_mcp():
    from support_agent.runtime import run_agent

    class Session:
        calls = []

        async def list_tools(self):
            return {"tools": [{"name": "lookup_order", "inputSchema": {
                "type": "object", "properties": {"order_id": {"type": "string"}},
                "required": ["order_id"], "additionalProperties": False,
            }}, {"name": "refund_order", "inputSchema": {"type": "object"}}]}

        async def call_tool(self, name, arguments):
            self.calls.append((name, arguments))
            raise AssertionError("must not invoke MCP")

    for name, arguments in [("refund_order", {}), ("lookup_order", {"order_id": 7})]:
        session = Session()
        result = asyncio.run(run_agent("synthetic", session, lambda *args: {
            "stop_reason": "tool_use", "content": [{"type": "tool_use", "name": name, "id": "c1", "input": arguments}],
        }))
        assert result["status"] == "tool_error"
        assert session.calls == []


def test_runtime_keeps_transport_failure_distinct():
    from support_agent.runtime import run_agent

    class Session:
        async def list_tools(self):
            return {"tools": [{"name": "search_policy", "inputSchema": {
                "type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"],
            }}]}

    def offline_transport(*args):
        raise ConnectionError("private transport details")

    result = asyncio.run(run_agent("synthetic", Session(), offline_transport))
    assert result["status"] == "transport_error"
    assert "private" not in str(result)


def test_payload_canonicalization_is_stable_and_rejects_identity():
    from app.models import TaskCreate, canonical_payload
    from pydantic import ValidationError

    assert canonical_payload(TaskCreate(prompt="合成订单")) == canonical_payload(TaskCreate(**{"release_id": "stage4-local-v1", "prompt": "合成订单"}))
    for field in ("tenant_id", "caller_id", "owner_id", "roles"):
        with pytest.raises(ValidationError):
            TaskCreate(prompt="synthetic", **{field: "forged"})


def test_sdk_transport_errors_are_distinct_and_sanitized():
    import httpx
    from support_agent.runtime import run_agent

    class Session:
        async def list_tools(self):
            return {"tools": [{"name": "search_policy", "inputSchema": {
                "type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"],
            }}]}

    def failing_call(*args):
        raise httpx.ConnectError("private connection detail")

    result = asyncio.run(run_agent("synthetic", Session(), failing_call))
    assert result["status"] == "transport_error"
    assert "private" not in str(result)


def test_integration_subprocess_environment_never_inherits_provider_secrets(monkeypatch):
    from conftest import subprocess_environment
    monkeypatch.setenv("ANTHROPIC_API_KEY", "synthetic-do-not-forward")
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-do-not-forward")
    monkeypatch.setenv("DATABASE_URL", "must-not-use-external-db")
    env = subprocess_environment()
    assert "ANTHROPIC_API_KEY" not in env
    assert "OPENAI_API_KEY" not in env
    assert "DATABASE_URL" not in env


def usage_loop(first_usage, second_usage):
    from support_agent.runtime import run_agent

    class Session:
        async def list_tools(self):
            return {"tools": [{"name": "search_policy", "inputSchema": {
                "type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"],
            }}]}

        async def call_tool(self, name, arguments):
            return {"content": [{"type": "text", "text": "synthetic policy"}], "isError": False}

    responses = iter([
        {"stop_reason": "tool_use", "content": [{"type": "tool_use", "id": "c1", "name": "search_policy", "input": {"query": "returns"}}], "usage": first_usage},
        {"stop_reason": "end_turn", "content": [{"type": "text", "text": "done"}], "usage": second_usage},
    ])
    return asyncio.run(run_agent("synthetic", Session(), lambda *args: next(responses)))


@pytest.mark.parametrize("incomplete", [None, {}, {"input_tokens": 1}, {"input_tokens": True, "output_tokens": 2}, {"input_tokens": -1, "output_tokens": 2}])
def test_missing_or_malformed_usage_then_valid_remains_unknown(incomplete):
    result = usage_loop(incomplete, {"input_tokens": 12, "output_tokens": 7})
    assert result["status"] == "completed"
    assert result["usage"] is None


@pytest.mark.parametrize("incomplete", [None, {}, {"output_tokens": 2}, {"input_tokens": 1, "output_tokens": "2"}, {"input_tokens": 1, "output_tokens": -2}])
def test_valid_then_missing_or_malformed_usage_remains_unknown(incomplete):
    result = usage_loop({"input_tokens": 12, "output_tokens": 7}, incomplete)
    assert result["status"] == "completed"
    assert result["usage"] is None


def test_complete_usage_sums_every_round():
    result = usage_loop({"input_tokens": 3, "output_tokens": 2}, {"input_tokens": 12, "output_tokens": 7})
    assert result["usage"] == {"input_tokens": 15, "output_tokens": 9}
