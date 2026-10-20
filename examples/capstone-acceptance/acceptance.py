"""Evidence gate for the final project; passing fixtures is not release evidence."""
from dataclasses import dataclass

REQUIRED_GATES = {
    "live_model_normal", "invalid_tool_args", "midflow_approval", "restart_after_approval",
    "concurrent_approval", "revoked_identity_or_changed_args", "delivery_race",
    "cross_tenant_retrieval", "http_timeout_single_task", "lease_expiry_fencing",
    "external_response_lost", "receiver_without_idempotency", "cancel_before_after_claim",
    "rate_limit_and_budget", "stream_cut_usage_unknown", "delete_and_acl_revoke",
    "refusal_truncation_partial_tool_failure", "provider_migration",
}
REQUIRED_KINDS = {
    "live_model_normal": "live",
    "stream_cut_usage_unknown": "live",
    "refusal_truncation_partial_tool_failure": "live",
    "provider_migration": "live",
    "receiver_without_idempotency": "manual",
    "invalid_tool_args": "integration",
    "midflow_approval": "integration",
    "restart_after_approval": "integration",
    "concurrent_approval": "integration",
    "revoked_identity_or_changed_args": "integration",
    "delivery_race": "integration",
    "cross_tenant_retrieval": "integration",
    "http_timeout_single_task": "integration",
    "lease_expiry_fencing": "integration",
    "external_response_lost": "integration",
    "cancel_before_after_claim": "integration",
    "rate_limit_and_budget": "integration",
    "delete_and_acl_revoke": "integration",
}


@dataclass(frozen=True)
class Evidence:
    gate_id: str
    status: str  # passed, failed, unverified
    kind: str  # live, integration, offline, fixture, manual
    locator: str


def decide(evidence: list[Evidence]) -> dict:
    by_id = {item.gate_id: item for item in evidence}
    duplicate_ids = len(by_id) != len(evidence)
    missing = sorted(REQUIRED_GATES - set(by_id))
    unexpected = sorted(set(by_id) - REQUIRED_GATES)
    if duplicate_ids or unexpected:
        return {"decision": "invalid-report", "missing": missing, "unexpected": unexpected}
    invalid = sorted(
        g.gate_id for g in evidence
        if g.status not in {"passed", "failed", "unverified"}
        or g.kind not in {"live", "integration", "offline", "fixture", "manual"}
        or not g.locator
    )
    if invalid:
        return {"decision": "invalid-report", "invalid": invalid}
    failed = sorted(g.gate_id for g in evidence if g.status == "failed")
    if failed:
        return {"decision": "blocked", "failed": failed}
    if missing:
        return {"decision": "incomplete", "missing": missing, "unexpected": []}
    unverified = sorted(g.gate_id for g in evidence if g.status == "unverified")
    if unverified:
        return {"decision": "insufficient-evidence", "unverified": unverified}
    wrong_kind = sorted(
        gate for gate, required_kind in REQUIRED_KINDS.items()
        if by_id[gate].kind != required_kind
    )
    if wrong_kind:
        return {"decision": "insufficient-evidence", "unverified": wrong_kind}
    return {"decision": "ready-for-human-acceptance", "missing": [], "unexpected": []}
