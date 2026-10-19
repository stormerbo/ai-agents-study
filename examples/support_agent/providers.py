"""Anthropic Messages normalization, without SDK imports or capability claims."""
from dataclasses import dataclass
from typing import Any, Literal


def _value(obj: Any, key: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _plain(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, list):
        return [_plain(item) for item in value]
    if isinstance(value, dict):
        return {key: _plain(item) for key, item in value.items()}
    return value


@dataclass(frozen=True)
class ProviderOutcome:
    kind: Literal["final", "tool_calls", "refusal", "truncated", "transport_error"]
    stop_reason: str | None
    content: list[Any]
    usage: Any = None
    error_type: str | None = None


def normalize_response(response: Any) -> ProviderOutcome:
    """Keep refusal/truncation distinct and reject unknown protocol variants."""
    stop = _value(response, "stop_reason")
    blocks = list(_value(response, "content", []) or [])
    known = {"text", "tool_use", "refusal", "thinking", "redacted_thinking"}
    if any(_value(block, "type") not in known for block in blocks):
        raise ValueError("Unsupported provider content block")
    calls = [block for block in blocks if _value(block, "type") == "tool_use"]
    if stop == "max_tokens":
        kind = "truncated"
    elif stop == "refusal" or (stop == "end_turn" and any(_value(b, "type") == "refusal" for b in blocks)):
        kind = "refusal"
    elif stop == "end_turn" and not calls:
        kind = "final"
    elif stop == "tool_use" and calls:
        kind = "tool_calls"
    else:
        raise ValueError("Unsupported provider stop reason/content combination")
    return ProviderOutcome(kind, stop, blocks, _value(response, "usage"))


def transport_error(error: Exception) -> ProviderOutcome:
    """Do not persist error bodies, credentials or transport URLs."""
    return ProviderOutcome("transport_error", None, [], error_type=type(error).__name__)
