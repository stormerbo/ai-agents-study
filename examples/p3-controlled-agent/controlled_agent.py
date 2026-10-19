"""Compatibility entry point for the shared support-agent implementation."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from support_agent.runtime import run_agent  # noqa: E402
from support_agent.tool_gateway import (  # noqa: E402
    ALLOWED_TOOLS, MAX_TOOL_CALLS, provider_tools, validate_tool_arguments,
)

__all__ = ["run_agent", "provider_tools", "validate_tool_arguments", "ALLOWED_TOOLS", "MAX_TOOL_CALLS"]
