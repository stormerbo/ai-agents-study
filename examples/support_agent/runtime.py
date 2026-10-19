"""Bounded host loop; Stage 3 CLI and Stage 4 reuse this boundary."""
from __future__ import annotations
import inspect
from typing import Any
from .providers import _value, _plain, normalize_response, transport_error
from .tool_gateway import MAX_TOOL_CALLS, provider_tools, validate_tool_arguments

def _content_text(blocks: list[Any]) -> str:
    parts = []
    for block in blocks:
        kind = _value(block, "type")
        if kind == "text":
            parts.append(str(_value(block, "text", "")))
        elif kind == "refusal":
            parts.append(str(_value(block, "refusal", _value(block, "text", ""))))
    return "".join(parts)


def _mcp_text(result: Any) -> str:
    blocks = _value(result, "content", [])
    parts = [str(_value(block, "text", "")) for block in blocks if _value(block, "type") == "text"]
    return "\n".join(parts)


async def run_agent(
    user_text: str,
    session: Any,
    model_call: Any,
    *,
    max_rounds: int = 4,
    max_tool_calls: int = MAX_TOOL_CALLS,
    max_output_tokens: int = 512,
) -> dict[str, Any]:
    """Run the provider loop while delegating every real tool to the MCP peer."""
    if max_rounds < 1 or max_tool_calls < 1 or max_output_tokens < 1:
        raise ValueError("round, tool-call, and output budgets must be positive")
    listed = await session.list_tools()
    tools = provider_tools(list(_value(listed, "tools", [])))
    if not tools:
        return {"status": "protocol_error", "text": "", "rounds": 0, "tool_calls": 0, "trace": [], "usage": None}
    schemas = {tool["name"]: tool["input_schema"] for tool in tools}
    messages: list[dict[str, Any]] = [{"role": "user", "content": user_text}]
    trace: list[dict[str, Any]] = []
    usage_totals = {"input_tokens": 0, "output_tokens": 0}
    observed_usage = False
    tool_calls = 0

    for round_number in range(1, max_rounds + 1):
        try:
            response = model_call(messages, tools, max_output_tokens)
            if inspect.isawaitable(response):
                response = await response
        except Exception as exc:
            provider_transport = any(
                (cls.__module__.startswith("httpx") and cls.__name__ == "TransportError")
                or (cls.__module__.startswith("anthropic") and cls.__name__ in {"APIConnectionError", "APIStatusError"})
                for cls in type(exc).__mro__
            )
            if not isinstance(exc, (ConnectionError, TimeoutError, OSError)) and not provider_transport:
                raise
            outcome = transport_error(exc)
            trace.append({"round": round_number, "stop_reason": None, "error_type": outcome.error_type})
            return {"status": "transport_error", "text": "", "rounds": round_number, "tool_calls": tool_calls, "trace": trace, "usage": None}
        try:
            outcome = normalize_response(response)
        except ValueError:
            trace.append({"round": round_number, "stop_reason": _value(response, "stop_reason")})
            return {"status": "protocol_error", "text": "", "rounds": round_number, "tool_calls": tool_calls, "trace": trace, "usage": None}
        stop_reason = outcome.stop_reason
        blocks = outcome.content
        trace_row: dict[str, Any] = {"round": round_number, "stop_reason": stop_reason}
        usage = _value(response, "usage")
        if usage is not None:
            observed_usage = True
            for key in usage_totals:
                value = _value(usage, key)
                if isinstance(value, int) and not isinstance(value, bool):
                    usage_totals[key] += value
                else:
                    observed_usage = False
        if stop_reason == "max_tokens":
            trace.append(trace_row)
            return {"status": "truncated", "text": "", "rounds": round_number, "tool_calls": tool_calls, "trace": trace, "usage": usage_totals if observed_usage else None}
        if stop_reason == "refusal":
            trace.append(trace_row)
            return {"status": "refused", "text": _content_text(blocks), "rounds": round_number, "tool_calls": tool_calls, "trace": trace, "usage": usage_totals if observed_usage else None}
        if stop_reason == "end_turn":
            trace.append(trace_row)
            refusal = any(_value(block, "type") == "refusal" for block in blocks)
            return {"status": "refused" if refusal else "completed", "text": _content_text(blocks), "rounds": round_number, "tool_calls": tool_calls, "trace": trace, "usage": usage_totals if observed_usage else None}
        if stop_reason != "tool_use":
            trace.append(trace_row)
            return {"status": "protocol_error", "text": "", "rounds": round_number, "tool_calls": tool_calls, "trace": trace, "usage": usage_totals if observed_usage else None}

        calls = [block for block in blocks if _value(block, "type") == "tool_use"]
        if not calls:
            trace.append(trace_row)
            return {"status": "protocol_error", "text": "", "rounds": round_number, "tool_calls": tool_calls, "trace": trace, "usage": usage_totals if observed_usage else None}
        messages.append({"role": "assistant", "content": _plain(blocks)})
        results = []
        round_error = False
        budget_exhausted = False
        trace_row["tools"] = []
        for call in calls:
            name = _value(call, "name", "")
            call_id = _value(call, "id", "")
            arguments = _value(call, "input")
            event = {"tool_name": name, "tool_call_id": call_id, "arguments": _plain(arguments)}
            trace_row["tools"].append(event)
            if name not in schemas:
                event["tool_status"] = "unknown_tool"
                results.append({"type": "tool_result", "tool_use_id": call_id, "content": "Unknown tool", "is_error": True})
                round_error = True
                continue
            valid, reason = validate_tool_arguments(schemas[name], arguments)
            if not valid:
                event["argument_validation"] = "failed"
                event["tool_status"] = "invalid_arguments"
                event["error"] = reason
                results.append({"type": "tool_result", "tool_use_id": call_id, "content": reason, "is_error": True})
                round_error = True
                continue
            if tool_calls >= max_tool_calls:
                event["argument_validation"] = "passed"
                event["tool_status"] = "tool_budget_exhausted"
                budget_exhausted = True
                results.append({"type": "tool_result", "tool_use_id": call_id, "content": "Tool-call budget exhausted", "is_error": True})
                round_error = True
                continue
            tool_result = await session.call_tool(name, arguments)
            tool_calls += 1
            event["argument_validation"] = "passed"
            is_error = bool(_value(tool_result, "isError", _value(tool_result, "is_error", False)))
            result_text = _mcp_text(tool_result)
            results.append({"type": "tool_result", "tool_use_id": call_id, "content": result_text, "is_error": is_error})
            event["tool_status"] = "error" if is_error else "ok"
            event["tool_result_id"] = call_id
            if is_error:
                event["error"] = result_text[:300]
                round_error = True
        trace.append(trace_row)
        messages.append({"role": "user", "content": results})
        if round_error:
            status = "max_tool_calls" if budget_exhausted and all(event.get("tool_status") in {"ok", "tool_budget_exhausted"} for event in trace_row["tools"]) else "tool_error"
            return {"status": status, "text": "", "rounds": round_number, "tool_calls": tool_calls, "trace": trace, "usage": usage_totals if observed_usage else None}
    return {"status": "max_rounds", "text": "", "rounds": max_rounds, "tool_calls": tool_calls, "trace": trace, "usage": usage_totals if observed_usage else None}
