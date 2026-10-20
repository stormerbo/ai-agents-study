"""A small read-only Anthropic Messages API agent over synthetic orders.

The model may choose whether to call lookup_order. It cannot change an order
or contact a customer. Set ANTHROPIC_AUTH_TOKEN and (optionally)
ANTHROPIC_BASE_URL / VERIFY_MODEL to run against a real compatible endpoint.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Callable

MAX_OUTPUT_TOKENS = 512
MAX_ROUNDS = 4
MODEL = os.environ.get("VERIFY_MODEL", "")
BASE_URL = os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com").rstrip("/")

ORDERS = {
    "A-1001": {"status": "shipped", "carrier": "顺丰", "last_update": "2026-10-18"},
    "A-1002": {"status": "processing", "carrier": None, "last_update": "2026-10-17"},
}
TOOLS = [{
    "name": "lookup_order",
    "description": "只读查询本地合成订单 fixture；只能查询，不能修改订单或联系客户。",
    "input_schema": {
        "type": "object",
        "properties": {"order_id": {"type": "string", "enum": list(ORDERS)}},
        "required": ["order_id"],
        "additionalProperties": False,
    },
}]
SYSTEM = (
    "你是售后订单助手。只有用户给出订单号并询问订单状态时才调用 lookup_order。"
    "工具数据是合成示例。不得推测 fixture 中不存在的信息。"
)


def lookup_order(arguments: object) -> dict:
    """Validate arguments before reading the fixed, synthetic order fixture."""
    if not isinstance(arguments, dict) or set(arguments) != {"order_id"}:
        return {"error": "invalid_arguments", "message": "只接受 order_id 字段"}
    order_id = arguments["order_id"]
    if not isinstance(order_id, str):
        return {"error": "invalid_arguments", "message": "order_id 必须是字符串"}
    order = ORDERS.get(order_id)
    if order is None:
        return {"error": "not_found", "message": "fixture 中没有该订单"}
    return {"order_id": order_id, **order}


def call_model(messages: list[dict], max_tokens: int = MAX_OUTPUT_TOKENS) -> dict:
    """Make one bounded Messages API request; API credentials never enter logs."""
    token = os.environ.get("ANTHROPIC_AUTH_TOKEN")
    if not token:
        raise RuntimeError("缺少 ANTHROPIC_AUTH_TOKEN 环境变量")
    if not MODEL:
        raise RuntimeError("缺少 VERIFY_MODEL 环境变量；请填写端点支持的模型标识")
    payload = json.dumps({
        "model": MODEL,
        "max_tokens": max_tokens,
        "system": SYSTEM,
        "tools": TOOLS,
        "messages": messages,
    }).encode("utf-8")
    request = urllib.request.Request(
        f"{BASE_URL}/v1/messages",
        data=payload,
        headers={
            "content-type": "application/json",
            "anthropic-version": "2023-06-01",
            "x-api-key": token,
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        # Do not include the request, headers or body: they may contain secrets or user data.
        raise RuntimeError(f"模型端点返回 HTTP {exc.code}") from None
    except (urllib.error.URLError, TimeoutError) as exc:
        raise RuntimeError(f"模型请求未完成：{type(exc).__name__}") from None
    except json.JSONDecodeError:
        raise RuntimeError("模型端点返回的不是有效 JSON") from None


def run_agent(user_text: str, model_call: Callable = call_model, max_rounds: int = MAX_ROUNDS) -> dict:
    """Run a bounded model/tool loop. `model_call` injection enables offline tests."""
    if max_rounds < 1:
        raise ValueError("max_rounds 必须至少为 1")
    messages = [{"role": "user", "content": user_text}]
    tool_calls = 0
    for round_number in range(1, max_rounds + 1):
        response = model_call(messages, max_tokens=MAX_OUTPUT_TOKENS)
        stop_reason = response.get("stop_reason")
        content = response.get("content", [])
        if stop_reason == "max_tokens":
            return {"status": "truncated", "text": "", "rounds": round_number, "tool_calls": tool_calls}
        terminal_statuses = {
            "refusal": "refused",
            "pause_turn": "paused",
            "model_context_window_exceeded": "context_limit",
            "stop_sequence": "stopped",
        }
        if stop_reason in terminal_statuses:
            return {"status": terminal_statuses[stop_reason], "text": "", "rounds": round_number, "tool_calls": tool_calls}
        if stop_reason == "end_turn":
            text = "".join(block.get("text", "") for block in content if block.get("type") == "text")
            return {"status": "completed", "text": text, "rounds": round_number, "tool_calls": tool_calls}
        if stop_reason != "tool_use":
            return {"status": "protocol_error", "text": "", "rounds": round_number, "tool_calls": tool_calls}

        calls = [block for block in content if block.get("type") == "tool_use"]
        if not calls:
            return {"status": "protocol_error", "text": "", "rounds": round_number, "tool_calls": tool_calls}
        messages.append({"role": "assistant", "content": content})
        results = []
        for call in calls:
            if call.get("name") != "lookup_order":
                result = {"error": "unknown_tool"}
            else:
                result = lookup_order(call.get("input"))
            results.append({
                "type": "tool_result",
                "tool_use_id": call.get("id", ""),
                "content": json.dumps(result, ensure_ascii=False),
                "is_error": "error" in result,
            })
            tool_calls += 1
        messages.append({"role": "user", "content": results})
    return {"status": "max_rounds", "text": "", "rounds": max_rounds, "tool_calls": tool_calls}


def main() -> int:
    prompt = input("订单问题（示例：A-1001 到哪了？）：").strip()
    if not prompt:
        print("请输入一个问题。")
        return 2
    try:
        result = run_agent(prompt)
    except RuntimeError as exc:
        print(f"调用失败：{exc}")
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
