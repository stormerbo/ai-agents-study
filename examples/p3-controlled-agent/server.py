"""MCP stdio server exposing only synthetic, read-only support lookups."""

from __future__ import annotations

from typing import Literal

from mcp.server import MCPServer

from fixtures import lookup_order as _lookup_order
from fixtures import search_policy as _search_policy

mcp = MCPServer("synthetic-after-sales-readonly")


@mcp.tool()
def lookup_order(order_id: Literal["A-1001", "A-1002"]) -> str:
    """Read a synthetic order record by its fixture identifier."""
    return _lookup_order(order_id)


@mcp.tool()
def search_policy(query: str) -> str:
    """Search the small, versioned synthetic return-policy fixture."""
    return _search_policy(query)


if __name__ == "__main__":
    # MCP stdio owns stdout; keep diagnostics off the protocol stream.
    mcp.run()
