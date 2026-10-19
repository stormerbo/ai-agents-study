"""Bearer mapping is demo-only, DB membership/roles are checked each request."""
from dataclasses import dataclass
from hmac import compare_digest

from fastapi import HTTPException

from .config import DEMO_TOKENS


@dataclass(frozen=True)
class Principal:
    tenant_id: str
    caller_id: str
    roles: tuple[str, ...]


def bearer_identity(authorization: str | None) -> tuple[str, str]:
    scheme, _, supplied = (authorization or "").partition(" ")
    # Compare every candidate with bytes (including non-ASCII supplied tokens).
    # Avoid an early-return match that reveals the mapping's position.
    matched = None
    for token, identity in DEMO_TOKENS.items():
        equal = compare_digest(supplied.encode("utf-8"), token.encode("utf-8"))
        if equal:
            matched = identity
    if scheme.casefold() != "bearer" or matched is None:
        raise HTTPException(401, detail={"code": "unauthenticated", "message": "Valid bearer token required"},
                            headers={"WWW-Authenticate": "Bearer"})
    return matched


def authenticate(conn, authorization: str | None) -> Principal:
    tenant_id, caller_id = bearer_identity(authorization)
    # This share lock linearizes this request with revocation/role changes.
    row = conn.execute(
        "SELECT active, roles FROM caller_identities WHERE tenant_id=%s AND caller_id=%s FOR SHARE",
        (tenant_id, caller_id),
    ).fetchone()
    if row is None or not row["active"] or "caller" not in row["roles"]:
        raise HTTPException(403, detail={"code": "access_revoked", "message": "Current caller access required"})
    return Principal(tenant_id, caller_id, tuple(row["roles"]))
