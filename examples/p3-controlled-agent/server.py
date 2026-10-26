"""MCP stdio server exposing only synthetic, read-only support lookups."""

from __future__ import annotations

import asyncio

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import CallToolRequestParams, CallToolResult, ListToolsResult, TextContent, Tool

from fixtures import lookup_order as _lookup_order
from fixtures import search_policy as _search_policy

TOOLS = [
    Tool(
        name="lookup_order",
        description="Read a synthetic order record by its fixture identifier.",
        inputSchema={
            "type": "object",
            "properties": {
                "order_id": {"type": "string", "enum": ["A-1001", "A-1002"]},
            },
            "required": ["order_id"],
            "additionalProperties": False,
        },
    ),
    Tool(
        name="search_policy",
        description="Search the small, versioned return-policy fixture.",
        inputSchema={
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
            "additionalProperties": False,
        },
    ),
]


async def list_tools(_ctx, _params) -> ListToolsResult:
    return ListToolsResult(tools=TOOLS)


async def call_tool(_ctx, params: CallToolRequestParams) -> CallToolResult:
    arguments = params.arguments or {}
    if params.name == "lookup_order":
        if set(arguments) != {"order_id"} or arguments.get("order_id") not in {"A-1001", "A-1002"}:
            return CallToolResult(content=[TextContent(type="text", text="Invalid tool arguments")], isError=True)
        result = _lookup_order(arguments["order_id"])
    elif params.name == "search_policy":
        if set(arguments) != {"query"} or not isinstance(arguments.get("query"), str):
            return CallToolResult(content=[TextContent(type="text", text="Invalid tool arguments")], isError=True)
        result = _search_policy(arguments["query"])
    else:
        return CallToolResult(content=[TextContent(type="text", text="Unknown tool")], isError=True)
    return CallToolResult(content=[TextContent(type="text", text=result)])


server = Server(
    "synthetic-after-sales-readonly",
    on_list_tools=list_tools,
    on_call_tool=call_tool,
)


async def _run_stdio() -> None:
    # MCP stdio owns stdout; keep diagnostics off the protocol stream.
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(_run_stdio())
