"""Offline decision model for MCP remote-token boundaries.

This module assumes claims have already passed cryptographic JWT validation.
It is a teaching example, not an OAuth client or token verifier.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class Decision:
    status: int
    reason: str
    subject: str | None = None


def authorize_http(
    claims: Mapping[str, object] | None,
    *,
    expected_issuer: str,
    expected_audience: str,
    required_scopes: set[str],
    now: int,
) -> Decision:
    """Classify verified claims as unauthenticated, forbidden, or allowed."""
    if claims is None:
        return Decision(401, "authentication_required")
    if claims.get("iss") != expected_issuer:
        return Decision(401, "invalid_issuer")
    audience = claims.get("aud")
    if isinstance(audience, str):
        audiences = {audience}
    elif isinstance(audience, list) and all(isinstance(item, str) for item in audience):
        audiences = set(audience)
    else:
        audiences = set()
    if expected_audience not in audiences:
        return Decision(401, "invalid_audience")
    exp = claims.get("exp")
    if not isinstance(exp, int) or exp <= now:
        return Decision(401, "expired_or_missing_expiry")
    subject = claims.get("sub")
    if not isinstance(subject, str) or not subject:
        return Decision(401, "missing_subject")
    raw_scope = claims.get("scope", "")
    scopes = set(raw_scope.split()) if isinstance(raw_scope, str) else set()
    if not required_scopes.issubset(scopes):
        return Decision(403, "insufficient_scope", subject)
    return Decision(200, "authorized", subject)


def stdio_child_env(parent_env: Mapping[str, str], allowed_names: set[str]) -> dict[str, str]:
    """Pass only explicitly approved environment values to a local child."""
    return {name: parent_env[name] for name in allowed_names if name in parent_env}
