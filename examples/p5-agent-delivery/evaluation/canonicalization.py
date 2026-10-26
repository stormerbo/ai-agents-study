"""Versioned RFC 8785 JCS helpers for Stage 5 evidence digests."""

from __future__ import annotations

import hashlib
import json
from typing import Any

import rfc8785


HASH_PROFILE = "jcs-rfc8785-v1"


def canonical_json_bytes(value: Any) -> bytes:
    """Serialize a JSON value with RFC 8785; reject values outside JCS/I-JSON."""
    try:
        return rfc8785.dumps(value)
    except (rfc8785.CanonicalizationError, TypeError, ValueError, OverflowError) as exc:
        raise ValueError("value cannot be represented by the jcs-rfc8785-v1 profile") from exc


def parse_json_strict(raw: str | bytes) -> Any:
    """Parse JSON without duplicate keys or extensions, then enforce JCS/I-JSON."""
    def reject_constant(value: str) -> None:
        raise ValueError(f"invalid JSON numeric constant: {value}")

    def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON object key: {key}")
            result[key] = value
        return result

    try:
        value = json.loads(raw, object_pairs_hook=unique_object, parse_constant=reject_constant)
        canonical_json_bytes(value)
        return value
    except (json.JSONDecodeError, UnicodeDecodeError, TypeError) as exc:
        raise ValueError("input is not valid jcs-rfc8785-v1 JSON") from exc


def canonical_sha256(value: Any) -> str:
    """Return the lower-case SHA-256 digest of the JCS UTF-8 representation."""
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()
