"""Run MCP protocol smoke checks or one bounded, synthetic live-agent drill."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path
from urllib.parse import urlparse

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from controlled_agent import run_agent
from fixtures import FIXTURE_VERSION

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
SERVER = HERE / "server.py"
PROMPT = "请分别调用订单查询和政策查询工具：查询合成订单 A-1001 的状态，并检索退货政策。回答时分别引用两个工具返回的原文，不要猜测。"
SYSTEM = "你是售后只读助手。只使用提供的只读工具回答；工具返回合成数据。不要声称执行过写入操作。证据不足时明确说明。"


def load_local_env() -> None:
    """Load only the project's ignored local env file without echoing values."""
    path = ROOT / ".env.local"
    if not path.is_file():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("\"'")
        if key and key not in os.environ:
            os.environ[key] = value


def provider_host() -> str | None:
    base_url = os.environ.get("ANTHROPIC_BASE_URL")
    if not base_url:
        return "api.anthropic.com"
    return urlparse(base_url).hostname


def write_report(report: dict) -> Path:
    output = ROOT / "verify-output" / "stage3-mcp"
    output.mkdir(parents=True, exist_ok=True)
    path = output / ("live.json" if report["mode"] == "live" else "mcp-smoke.json")
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


async def with_mcp_client(run):
    # Do not pass provider credentials to the MCP child process.
    child_env = {"PATH": os.environ.get("PATH", ""), "PYTHONDONTWRITEBYTECODE": "1"}
    params = StdioServerParameters(
        command=sys.executable,
        args=[str(SERVER)],
        env=child_env,
    )
    async with stdio_client(params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            return await run(session)


async def mcp_smoke() -> dict:
    async def run(session):
        listed = await session.list_tools()
        names = sorted(tool.name for tool in listed.tools)
        order = await session.call_tool("lookup_order", {"order_id": "A-1001"})
        policy = await session.call_tool("search_policy", {"query": "退货 未使用"})
        return {
            "mode": "mcp-smoke",
            "status": "passed" if names == ["lookup_order", "search_policy"] and not order.is_error and not policy.is_error else "failed",
            "tools": names,
            "order_result": "\n".join(item.text for item in order.content if item.type == "text"),
            "policy_result": "\n".join(item.text for item in policy.content if item.type == "text"),
        }
    return await with_mcp_client(run)


async def live(*, max_rounds: int, max_tool_calls: int, max_output_tokens: int) -> dict:
    load_local_env()
    token = os.environ.get("ANTHROPIC_AUTH_TOKEN") or os.environ.get("ANTHROPIC_API_KEY")
    model = os.environ.get("VERIFY_MODEL")
    report = {
        "mode": "live",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "provider_host": provider_host(),
        "model": model,
        "sdk_versions": {},
        "prompt_id": "synthetic-order-and-policy-v1",
        "fixture_version": FIXTURE_VERSION,
        "budgets": {
            "max_rounds": max_rounds,
            "max_tool_calls": max_tool_calls,
            "max_output_tokens_per_round": max_output_tokens,
        },
        "status": "blocked_configuration",
    }
    if not token or not model:
        report["detail"] = "ANTHROPIC_AUTH_TOKEN (or ANTHROPIC_API_KEY) and VERIFY_MODEL are required."
        return report

    import anthropic

    report["sdk_versions"] = {"anthropic": anthropic.__version__, "mcp": version("mcp")}
    base_url = os.environ.get("ANTHROPIC_BASE_URL")
    client = anthropic.Anthropic(
        api_key=token,
        base_url=base_url,
        timeout=45.0,
        max_retries=0,
    )

    async def run(session):
        def model_call(messages, tools, max_tokens):
            return client.messages.create(
                model=model,
                max_tokens=max_tokens,
                system=SYSTEM,
                messages=messages,
                tools=tools,
            )

        return await run_agent(
            PROMPT,
            session,
            model_call,
            max_rounds=max_rounds,
            max_tool_calls=max_tool_calls,
            max_output_tokens=max_output_tokens,
        )

    try:
        result = await with_mcp_client(run)
        report["agent"] = result
        report["status"] = result["status"]
    except anthropic.APIStatusError as exc:
        report["status"] = "provider_http_error"
        report["http_status"] = exc.status_code
        report["error_type"] = type(exc).__name__
        report["request_id"] = getattr(exc, "request_id", None)
    except anthropic.APIConnectionError as exc:
        report["status"] = "provider_connection_error"
        report["error_type"] = type(exc).__name__
    except Exception as exc:  # Sanitize: no exception message, headers, URL query, or body.
        leaves = []
        pending = [exc]
        while pending:
            current = pending.pop()
            nested = getattr(current, "exceptions", None)
            if nested:
                pending.extend(nested)
            else:
                leaves.append(current)
        provider_status_error = next((item for item in leaves if isinstance(item, anthropic.APIStatusError)), None)
        provider_connection_error = next((item for item in leaves if isinstance(item, anthropic.APIConnectionError)), None)
        if provider_status_error is not None:
            report["status"] = "provider_http_error"
            report["http_status"] = provider_status_error.status_code
            report["error_type"] = type(provider_status_error).__name__
            report["request_id"] = getattr(provider_status_error, "request_id", None)
        elif provider_connection_error is not None:
            report["status"] = "provider_connection_error"
            report["error_type"] = type(provider_connection_error).__name__
        else:
            report["status"] = "runtime_error"
            report["error_type"] = type(exc).__name__
            report["cause_types"] = sorted({type(item).__name__ for item in leaves})
    finally:
        client.close()
    return report


async def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--mcp-smoke", action="store_true", help="test real MCP stdio tools/list and tools/call")
    group.add_argument("--live", action="store_true", help="run one bounded model-driven synthetic tool loop")
    parser.add_argument("--max-rounds", type=int, default=4)
    parser.add_argument("--max-tool-calls", type=int, default=4)
    parser.add_argument("--max-output-tokens", type=int, default=512)
    args = parser.parse_args()
    if min(args.max_rounds, args.max_tool_calls, args.max_output_tokens) < 1:
        parser.error("all budgets must be positive")
    report = await (
        mcp_smoke()
        if args.mcp_smoke
        else live(max_rounds=args.max_rounds, max_tool_calls=args.max_tool_calls, max_output_tokens=args.max_output_tokens)
    )
    path = write_report(report)
    print(json.dumps({"status": report["status"], "report": str(path.relative_to(ROOT))}, ensure_ascii=False))
    return 0 if report["status"] in {"passed", "completed"} else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
