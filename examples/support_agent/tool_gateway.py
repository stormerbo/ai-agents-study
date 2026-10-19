"""Allowlist and fail-closed schema subset shared by every milestone."""
from typing import Any
from .providers import _value, _plain

ALLOWED_TOOLS = {"lookup_order", "search_policy"}
MAX_TOOL_CALLS = 4


def provider_tools(mcp_tools: list[Any]) -> list[dict[str, Any]]:
    """Map only the project's read-only MCP tools to Anthropic tool definitions."""
    mapped = []
    for item in mcp_tools:
        name = _value(item, "name")
        schema = _plain(_value(item, "inputSchema", _value(item, "input_schema")))
        if name not in ALLOWED_TOOLS:
            continue
        if not isinstance(schema, dict) or schema.get("type") != "object":
            raise ValueError(f"Unsupported MCP input schema for {name}")
        mapped.append({
            "name": name,
            "description": _value(item, "description", "Read-only synthetic fixture lookup."),
            "input_schema": schema,
        })
    return mapped


def validate_tool_arguments(schema: dict[str, Any], arguments: Any) -> tuple[bool, str]:
    """Fail closed for the small JSON Schema subset used by these fixture tools."""
    if schema.get("type") != "object" or not isinstance(arguments, dict):
        return False, "arguments must be a JSON object"
    properties = schema.get("properties")
    required = schema.get("required", [])
    if not isinstance(properties, dict) or not isinstance(required, list):
        return False, "unsupported object schema"
    unsupported = set(schema) - {"type", "properties", "required", "additionalProperties", "title", "description"}
    if unsupported:
        return False, "unsupported schema keywords: " + ", ".join(sorted(unsupported))
    missing = [name for name in required if name not in arguments]
    if missing:
        return False, "missing required field: " + ", ".join(missing)
    if schema.get("additionalProperties") is False:
        unknown = set(arguments) - set(properties)
        if unknown:
            return False, "unknown field: " + ", ".join(sorted(unknown))
    for name, value in arguments.items():
        rule = properties.get(name)
        if not isinstance(rule, dict):
            return False, f"unsupported field: {name}"
        unsupported_rule = set(rule) - {"type", "enum", "title", "description"}
        if unsupported_rule:
            return False, f"unsupported field schema for {name}"
        expected_type = rule.get("type")
        if expected_type == "string" and not isinstance(value, str):
            return False, f"{name} must be a string"
        if expected_type == "integer" and (not isinstance(value, int) or isinstance(value, bool)):
            return False, f"{name} must be an integer"
        if expected_type == "boolean" and not isinstance(value, bool):
            return False, f"{name} must be a boolean"
        if expected_type == "number" and (not isinstance(value, (int, float)) or isinstance(value, bool)):
            return False, f"{name} must be a number"
        if expected_type not in {"string", "integer", "boolean", "number"}:
            return False, f"unsupported field type for {name}"
        if "enum" in rule and value not in rule["enum"]:
            return False, f"{name} is outside the allowed enum"
    return True, ""
