"""Offline gate for capstone evidence reports and signed holdout receipts.

The configured evidence root contains a versioned manifest, frozen materials,
and gate artifacts. The gate checks their structure, provenance, and bytes; it
does not authenticate the local producer. An unsigned manifest and artifact
can be fabricated by an operator with write access, so this is not proof that a
provider call or human review actually occurred. Version 2 requires a distinct
official blind-holdout gate and checks its candidate, image, dataset, registry
event, budget, and scorer bindings. V5 is structural-only and remains
unverified; V6 can verify signed receipts when the caller supplies independent
root/status/freshness/sequence inputs from its trusted operational channel.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import base64
import hashlib
import json
from decimal import Decimal, InvalidOperation
from pathlib import Path
import re
import sqlite3
import sys
from typing import Any, Protocol

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

P5_EVALUATION_DIR = Path(__file__).resolve().parents[1] / "p5-agent-delivery" / "evaluation"
if str(P5_EVALUATION_DIR) not in sys.path:
    sys.path.insert(0, str(P5_EVALUATION_DIR))
from canonicalization import HASH_PROFILE, canonical_json_bytes, canonical_sha256, parse_json_strict
from registry_receipt_verifier import (
    verify_dual_witness_receipt_chain,
    verify_registry_receipts,
    verify_registry_status_snapshot,
)
from registry_sequence_floor import SequenceFloorConflict, SqliteSequenceFloorStore

REPORT_VERSION = 2
OFFICIAL_HOLDOUT_RESULT_SCHEMA = "official-blind-holdout-evidence-envelope-v5"
OFFICIAL_HOLDOUT_RESULT_SCHEMA_V6 = "official-blind-holdout-evidence-envelope-v6"
MANIFEST_NAME = "evidence-manifest.json"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
REQUIRED_HOLDOUT_STOP_CONDITIONS = {
    "budget",
    "deadline",
    "side-effect",
    "permission-boundary",
    "evidence-missing",
    "label-leak",
    "identity-mismatch",
}
HOLDOUT_EVIDENCE_ENVELOPE_FIELDS = {
    "gate_id", "kind", "status", "release_id", "blind", "registry", "report_sha256",
}
COMMIT_RE = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
IMAGE_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
KINDS = {"live", "integration", "manual", "holdout", "offline", "fixture", "replay"}
STATUSES = {"passed", "failed", "unverified"}
MATERIAL_HASH_FIELDS = {
    "lockfile": "lockfile_sha256",
    "prompt": "prompt_sha256",
    "tool_schema": "tool_schema_sha256",
    "dataset": "dataset_sha256",
    "scorer": "scorer_sha256",
}

REQUIRED_GATES = {
    "live_model_normal", "invalid_tool_args", "midflow_approval", "restart_after_approval",
    "concurrent_approval", "revoked_identity_or_changed_args", "delivery_race",
    "cross_tenant_retrieval", "http_timeout_single_task", "lease_expiry_fencing",
    "external_response_lost", "receiver_without_idempotency", "cancel_before_after_claim",
    "rate_limit_and_budget", "stream_cut_usage_unknown", "delete_and_acl_revoke",
    "refusal_truncation_partial_tool_failure", "provider_migration",
    "official_blind_holdout",
}
REQUIRED_KINDS = {
    "live_model_normal": "live",
    "stream_cut_usage_unknown": "live",
    "refusal_truncation_partial_tool_failure": "live",
    "provider_migration": "live",
    "official_blind_holdout": "holdout",
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
    status: str
    kind: str
    locator: str
    sha256: str
    release_id: str
    run_id: str


@dataclass(frozen=True)
class AcceptanceReport:
    version: int
    release_id: str
    run_id: str
    commit_sha: str
    lockfile_sha256: str
    prompt_sha256: str
    tool_schema_sha256: str
    dataset_sha256: str
    scorer_sha256: str
    provider: str
    model: str
    executed_at: str
    evidence: list[Evidence]
    candidate_sha256: str | None = None
    image_digest: str | None = None
    holdout_version: str | None = None
    executor_sha256: str | None = None


@dataclass(frozen=True)
class RegistryVerificationInputs:
    """Verifier-owned inputs, supplied independently from the evidence artifact."""

    environment_id: str
    log_id: str
    permitted_signer_key_id: str
    trusted_root: dict
    status_source: "KeyStatusSource"
    key_status_source_id: str
    current_time_utc: str
    assurance_profile: str
    max_freshness_seconds: int
    clock_skew_seconds: int
    sequence_floor_store: SqliteSequenceFloorStore
    append_authority_domain_id: str
    signing_key_custodian_domain_id: str
    witness_source: "WitnessReceiptSource | None" = None
    witness_source_id: str | None = None
    trusted_witness: dict | None = None
    terminal_witness_receipt_sha256: str | None = None
    trusted_anchor: dict | None = None
    anchor_source: "KeyAnchorSource | None" = None
    anchor_source_id: str | None = None
    risk_approval_attestation: dict | None = None
    handoff_review_attestation: dict | None = None
    trusted_risk_owner: dict | None = None
    trusted_independent_reviewer: dict | None = None
    handoff_record_sha256: str | None = None

    def __post_init__(self) -> None:
        if any(not isinstance(value, str) or not value.strip() for value in (
            self.environment_id, self.log_id, self.permitted_signer_key_id, self.current_time_utc,
            self.append_authority_domain_id, self.signing_key_custodian_domain_id,
        )):
            raise ValueError("registry verifier identities and clock must be non-empty strings")
        if self.assurance_profile not in {"local-reference", "single-authority-v1", "dual-witness-v1"}:
            raise ValueError("registry assurance profile is unsupported")
        if not isinstance(self.trusted_root, dict):
            raise ValueError("registry trusted root must be an object")
        if (self.assurance_profile == "dual-witness-v1"
                and (self.witness_source is None or not _nonempty(self.witness_source_id)
                     or not callable(getattr(self.witness_source, "fetch_latest_witness_chain", None))
                     or not isinstance(self.trusted_witness, dict))):
            raise ValueError("dual-witness verification requires a pinned source and witness key")
        if (self.witness_source is None) != (self.witness_source_id is None):
            raise ValueError("witness source and pinned source id must be configured together")
        if self.trusted_witness is not None and not isinstance(self.trusted_witness, dict):
            raise ValueError("trusted witness configuration must be an object")
        if (not _nonempty(self.key_status_source_id)
                or not callable(getattr(self.status_source, "fetch_latest_status", None))):
            raise ValueError("registry key-status source and pinned source id are required")
        if type(self.max_freshness_seconds) is not int or self.max_freshness_seconds < 1:
            raise ValueError("maximum status freshness must be a positive integer")
        if (type(self.clock_skew_seconds) is not int
                or not 0 <= self.clock_skew_seconds <= 300):
            raise ValueError("clock skew must be an integer between zero and 300 seconds")
        if not isinstance(self.sequence_floor_store, SqliteSequenceFloorStore):
            raise ValueError("sequence floor store must be a trusted verifier-owned instance")
        if self.trusted_anchor is not None and not isinstance(self.trusted_anchor, dict):
            raise ValueError("trusted anchor configuration must be an object")
        if (self.anchor_source is None) != (self.anchor_source_id is None):
            raise ValueError("anchor source and pinned source id must be configured together")
        if self.anchor_source is not None and (
            not _nonempty(self.anchor_source_id)
            or not callable(getattr(self.anchor_source, "fetch_anchor", None))
        ):
            raise ValueError("anchor source and pinned source id are required")
        for value in (
            self.risk_approval_attestation, self.handoff_review_attestation,
            self.trusted_risk_owner, self.trusted_independent_reviewer,
        ):
            if value is not None and not isinstance(value, dict):
                raise ValueError("governance attestations and signer pins must be objects")
        if self.handoff_record_sha256 is not None and (
            not isinstance(self.handoff_record_sha256, str)
            or not SHA256_RE.fullmatch(self.handoff_record_sha256)
        ):
            raise ValueError("handoff record digest must be a lowercase SHA-256")


class RegistryStatusUnavailable(RuntimeError):
    """A fresh authenticated status/floor could not be established this run."""


class KeyStatusSource(Protocol):
    """Fetch the latest status snapshot from a verifier-configured trusted source."""

    def fetch_latest_status(
        self, environment_id: str, log_id: str, trust_bundle_sha256: str
    ) -> dict: ...


class WitnessReceiptSource(Protocol):
    """Fetch the current independent witness chain for one exact run."""

    def fetch_latest_witness_chain(self, environment_id: str, log_id: str, run_id: str) -> dict: ...


class KeyAnchorSource(Protocol):
    """Fetch an independently recorded anchor for one exact committed receipt."""

    def fetch_anchor(
        self, environment_id: str, log_id: str, run_id: str, sequence: int,
        event_id: str, receipt_sha256: str,
    ) -> dict | None: ...


# The holdout gate checks structural bindings only; external registry authenticity needs a trusted verifier.


def _invalid(reason: str, **details: object) -> dict:
    return {"decision": "invalid-report", "reason": reason, **details}


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _canonical_sha256(value: Any) -> str | None:
    try:
        return canonical_sha256(value)
    except (TypeError, ValueError):
        return None


def _valid_hashed_reference(payload: Any, reference_key: str, digest_key: str) -> bool:
    if not isinstance(payload, dict) or not _nonempty(payload.get(reference_key)):
        return False
    digest = payload.get(digest_key)
    return isinstance(digest, str) and bool(SHA256_RE.fullmatch(digest))


def _valid_termination_evidence(payload: Any) -> bool:
    evidence = payload.get("termination_evidence") if isinstance(payload, dict) else None
    return (
        _valid_hashed_reference(evidence, "runtime_audit_ref", "runtime_audit_sha256")
        and _valid_hashed_reference(
            evidence, "capability_revocation_ref", "capability_revocation_sha256"
        )
    )


def _official_holdout_report_sha256(payload: dict) -> str | None:
    report_body = {
        key: value for key, value in payload.items()
        if key not in HOLDOUT_EVIDENCE_ENVELOPE_FIELDS
    }
    if payload.get("schema") == OFFICIAL_HOLDOUT_RESULT_SCHEMA_V6:
        report_body["schema"] = OFFICIAL_HOLDOUT_RESULT_SCHEMA
        for key in ("trust_bundle", "trust_bundle_root_signature", "trust_bundle_sha256"):
            report_body.pop(key, None)
        registry = report_body.get("registry")
        if isinstance(registry, dict):
            registry = dict(registry)
            registry.pop("receipt_chain", None)
            registry.pop("pre_compromise_anchors", None)
            report_body["registry"] = registry
    return _canonical_sha256(report_body)


def _utc_timestamp(value: Any) -> bool:
    if not isinstance(value, str) or not value:
        return False
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None and parsed.utcoffset() == timezone.utc.utcoffset(parsed)


def _decimal_usd(value: Any) -> Decimal | None:
    if not isinstance(value, str):
        return None
    try:
        amount = Decimal(value)
    except (InvalidOperation, ValueError):
        return None
    return amount if amount.is_finite() else None


def _safe_locator(locator: Any) -> bool:
    if not isinstance(locator, str) or not locator or "\x00" in locator:
        return False
    if "\\" in locator or "://" in locator or ":" in locator:
        return False
    path = Path(locator)
    return not path.is_absolute() and ".." not in path.parts and path.parts != ()


def _resolve_file(root: Path, locator: Any) -> Path | None:
    if not _safe_locator(locator):
        return None
    try:
        candidate = (root / locator).resolve(strict=True)
        if candidate == root or root not in candidate.parents or not candidate.is_file():
            return None
        return candidate
    except (OSError, RuntimeError, ValueError):
        return None


def _read_json(path: Path) -> dict | None:
    try:
        value = parse_json_strict(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError):
        return None
    return value if isinstance(value, dict) else None


def _validate_provenance(report: AcceptanceReport, manifest: dict) -> str | None:
    if not _nonempty(report.release_id) or not _nonempty(report.run_id):
        return "missing-report-provenance"
    if (not isinstance(report.commit_sha, str) or not COMMIT_RE.fullmatch(report.commit_sha)
            or not _nonempty(report.provider) or not _nonempty(report.model)
            or not _utc_timestamp(report.executed_at)):
        return "invalid-report-provenance"
    for field in MATERIAL_HASH_FIELDS.values():
        value = getattr(report, field, None)
        if not isinstance(value, str) or not SHA256_RE.fullmatch(value):
            return "invalid-report-material-hash"
    if report.executor_sha256 is not None and (
        not isinstance(report.executor_sha256, str) or not SHA256_RE.fullmatch(report.executor_sha256)
    ):
        return "invalid-report-executor-hash"
    candidate_fields = (report.candidate_sha256, report.image_digest, report.holdout_version)
    if any(value is not None for value in candidate_fields):
        if not isinstance(report.candidate_sha256, str) or not SHA256_RE.fullmatch(report.candidate_sha256):
            return "invalid-candidate-hash"
        if not isinstance(report.image_digest, str) or not IMAGE_DIGEST_RE.fullmatch(report.image_digest):
            return "invalid-image-digest"
        if not _nonempty(report.holdout_version):
            return "missing-holdout-version"
    fields = (
        "release_id", "run_id", "commit_sha", "provider", "model", "executed_at",
        "candidate_sha256", "image_digest", "holdout_version",
        *MATERIAL_HASH_FIELDS.values(),
    )
    if any(manifest.get(field) != getattr(report, field) for field in fields):
        return "report-manifest-provenance-mismatch"
    return None


def _validate_payload_v5(payload: dict, evidence: Evidence, report: AcceptanceReport) -> bool:
    common = {
        "gate_id": evidence.gate_id,
        "kind": evidence.kind,
        "status": evidence.status,
        "release_id": report.release_id,
        "run_id": report.run_id,
    }
    if any(payload.get(field) != expected for field, expected in common.items()):
        return False
    if evidence.kind == "live":
        return (
            _nonempty(payload.get("provider"))
            and payload.get("provider") == report.provider
            and _nonempty(payload.get("model"))
            and payload.get("model") == report.model
            and _utc_timestamp(payload.get("executed_at"))
            and payload.get("executed_at") == report.executed_at
        )
    if evidence.kind == "integration":
        results = payload.get("run_results")
        if (not _nonempty(payload.get("command")) or not isinstance(results, list)
                or not results or any(
                    not isinstance(row, dict) or not _nonempty(row.get("test_id"))
                    or not isinstance(row.get("status"), str)
                    or row.get("status") not in STATUSES for row in results
                )):
            return False
        # A mixed set with any failing case is failed; absent failures, any
        # unverified case makes the aggregate unverified.
        aggregate_status = (
            "failed" if any(row["status"] == "failed" for row in results)
            else "unverified" if any(row["status"] == "unverified" for row in results)
            else "passed"
        )
        return payload["status"] == aggregate_status
    if evidence.kind == "manual":
        record = payload.get("record")
        return (
            _nonempty(payload.get("reviewer_id"))
            and _utc_timestamp(payload.get("reviewed_at"))
            and isinstance(record, dict)
            and _nonempty(record.get("review_id"))
            and isinstance(record.get("decision"), str)
            and record.get("decision") in {"accepted", "rejected"}
            and _nonempty(record.get("rationale"))
            and ((record["decision"] == "accepted" and evidence.status == "passed")
                 or (record["decision"] == "rejected" and evidence.status == "failed"))
        )
    if evidence.kind == "holdout":
        registry = payload.get("registry")
        budget = payload.get("budget")
        task_count = payload.get("independent_task_count")
        if not isinstance(registry, dict) or not isinstance(budget, dict):
            return False
        if (
            not isinstance(report.candidate_sha256, str)
            or not SHA256_RE.fullmatch(report.candidate_sha256)
            or not isinstance(report.image_digest, str)
            or not IMAGE_DIGEST_RE.fullmatch(report.image_digest)
            or not _nonempty(report.holdout_version)
            or not isinstance(report.executor_sha256, str)
            or not SHA256_RE.fullmatch(report.executor_sha256)
        ):
            return False
        events = registry.get("events")
        outcome = payload.get("outcome")
        terminal_type = "aborted" if outcome == "aborted" else "consumed"
        required_events = ("authorized", "reserved", terminal_type)
        event_chain_valid = (
            isinstance(events, list)
            and len(events) == len(required_events)
            and all(isinstance(event, dict) for event in events)
            and all(
                event.get("previous_event_id") == (
                    None if index == 0 else events[index - 1].get("event_id")
                )
                for index, event in enumerate(events)
            )
        )
        frozen_spec = payload.get("frozen_spec")
        frozen_spec_sha256 = _canonical_sha256(frozen_spec)
        criteria = payload.get("quality_criteria")
        budget = payload.get("budget")
        owner_id = frozen_spec.get("owner_id") if isinstance(frozen_spec, dict) else None
        executor_id = frozen_spec.get("executor_id") if isinstance(frozen_spec, dict) else None
        recovery_operator_id = frozen_spec.get("recovery_operator_id") if isinstance(frozen_spec, dict) else None
        if (
            payload.get("schema") != OFFICIAL_HOLDOUT_RESULT_SCHEMA
            or payload.get("hash_profile") != HASH_PROFILE
            or not isinstance(payload.get("report_sha256"), str)
            or not SHA256_RE.fullmatch(payload.get("report_sha256", ""))
            or payload.get("report_sha256") != _official_holdout_report_sha256(payload)
            or payload.get("blind") is not True
            or payload.get("holdout_version") != report.holdout_version
            or payload.get("candidate_sha256") != report.candidate_sha256
            or payload.get("image_digest") != report.image_digest
            or payload.get("scorer_sha256") != report.scorer_sha256
            or payload.get("executor_sha256") != report.executor_sha256
            or not isinstance(frozen_spec, dict)
            or frozen_spec.get("hash_profile") != HASH_PROFILE
            or frozen_spec_sha256 is None
            or payload.get("frozen_spec_sha256") != frozen_spec_sha256
            or frozen_spec.get("holdout_version") != report.holdout_version
            or frozen_spec.get("run_id") != report.run_id
            or frozen_spec.get("authorization_event_id") != payload.get("authorization_event_id")
            or frozen_spec.get("candidate_sha256") != report.candidate_sha256
            or frozen_spec.get("image_digest") != report.image_digest
            or frozen_spec.get("dataset_sha256") != report.dataset_sha256
            or frozen_spec.get("scorer_sha256") != report.scorer_sha256
            or frozen_spec.get("executor_sha256") != report.executor_sha256
            or not _nonempty(owner_id)
            or not _nonempty(executor_id)
            or not _nonempty(recovery_operator_id)
            or len({owner_id, executor_id, recovery_operator_id}) != 3
            or not isinstance(criteria, dict)
            or frozen_spec.get("minimum_task_count") != criteria.get("minimum_task_count")
            or frozen_spec.get("minimum_pass_rate_bps") != criteria.get("minimum_pass_rate_bps")
            or frozen_spec.get("require_all_tasks_pass") != criteria.get("require_all_tasks_pass")
            or frozen_spec.get("stop_conditions") != payload.get("stop_conditions")
            or type(frozen_spec.get("minimum_task_count")) is not int
            or not 1 <= frozen_spec["minimum_task_count"] <= frozen_spec.get("max_cases", 0)
            or type(frozen_spec.get("minimum_pass_rate_bps")) is not int
            or not 0 <= frozen_spec["minimum_pass_rate_bps"] <= 10_000
            or type(frozen_spec.get("require_all_tasks_pass")) is not bool
            or not isinstance(budget, dict)
            or frozen_spec.get("max_budget_usd") != budget.get("authorized_max_usd")
            or type(frozen_spec.get("max_cases")) is not int
            or frozen_spec["max_cases"] < 1
            or type(payload.get("case_limit")) is not int
            or frozen_spec.get("max_cases") != payload.get("case_limit")
            or type(frozen_spec.get("max_output_bytes")) is not int
            or frozen_spec["max_output_bytes"] < 1
            or type(payload.get("max_output_bytes")) is not int
            or frozen_spec.get("max_output_bytes") != payload.get("max_output_bytes")
            or not _utc_timestamp(frozen_spec.get("deadline_utc"))
            or frozen_spec.get("deadline_utc") != payload.get("deadline_utc")
            or not _nonempty(registry.get("registry_id"))
            or registry.get("append_only") is not True
            or not event_chain_valid
            or not isinstance(events, list) or len(events) != len(required_events)
            or [event.get("type") for event in events if isinstance(event, dict)] != list(required_events)
            or not all(
                isinstance(event, dict)
                and _nonempty(event.get("event_id"))
                and event.get("holdout_version") == report.holdout_version
                and event.get("candidate_sha256") == report.candidate_sha256
                and event.get("image_digest") == report.image_digest
                and event.get("dataset_sha256") == report.dataset_sha256
                and event.get("scorer_sha256") == report.scorer_sha256
                and event.get("executor_sha256") == report.executor_sha256
                and event.get("frozen_spec_sha256") == frozen_spec_sha256
                and event.get("hash_profile") == HASH_PROFILE
                and event.get("run_id") == report.run_id
                and _utc_timestamp(event.get("appended_at"))
                for event in events
            )
            or events[0].get("actor_id") != owner_id
            or events[0].get("actor_role") != "owner"
            or events[1].get("actor_id") != executor_id
            or events[1].get("actor_role") != "executor"
            or not (
                (events[2].get("actor_id") == executor_id and events[2].get("actor_role") == "executor")
                or (
                    events[2].get("actor_id") == recovery_operator_id
                    and events[2].get("actor_role") == "recovery_operator"
                    and _valid_termination_evidence(payload)
                    and (
                        outcome == "aborted"
                        or _valid_hashed_reference(
                            payload.get("recovery_evidence"),
                            "usage_ledger_ref",
                            "usage_ledger_sha256",
                        )
                    )
                )
            )
            or payload.get("authorization_event_id") != events[0].get("event_id")
            or payload.get("reservation_event_id") != events[1].get("event_id")
            or payload.get("terminal_event_id") != events[2].get("event_id")
            or events[2].get("report_sha256") != payload.get("report_sha256")
            or len({event["event_id"] for event in events}) != len(required_events)
        ):
            return False
        if outcome in {"passed", "failed"}:
            metrics = payload.get("metrics")
            if (
                not _nonempty(payload.get("output_seal_id"))
                or not isinstance(payload.get("output_sha256"), str)
                or not SHA256_RE.fullmatch(payload.get("output_sha256", ""))
                or payload.get("output_sha256") != payload.get("results_sha256")
                or not isinstance(payload.get("results_sha256"), str)
                or not SHA256_RE.fullmatch(payload.get("results_sha256", ""))
                or not isinstance(payload.get("metrics_sha256"), str)
                or not SHA256_RE.fullmatch(payload.get("metrics_sha256", ""))
                or not isinstance(metrics, dict)
                or _canonical_sha256(metrics) != payload.get("metrics_sha256")
                or not isinstance(task_count, int) or isinstance(task_count, bool) or task_count < 1
                or type(payload.get("sample_size")) is not int
                or payload.get("sample_size") != task_count
                or type(metrics.get("task_count")) is not int
                or metrics.get("task_count") != task_count
                or type(metrics.get("passed_tasks")) is not int
                or metrics.get("passed_tasks") != payload.get("passed_tasks")
                or type(metrics.get("pass_rate_bps")) is not int
                or metrics.get("pass_rate_bps") != payload.get("pass_rate_bps")
                or _canonical_sha256(metrics.get("quality_criteria"))
                != _canonical_sha256(payload.get("quality_criteria"))
                or not isinstance(metrics.get("token_usage"), dict)
                or _canonical_sha256(metrics.get("token_usage"))
                != _canonical_sha256(payload.get("token_usage"))
                or any(
                    type(metrics["token_usage"].get(key)) is not int
                    or metrics["token_usage"][key] < 0
                    for key in ("input_tokens", "output_tokens")
                )
                or metrics.get("cost_usd") != budget.get("actual_usd")
                or not _utc_timestamp(payload.get("executed_at"))
                or payload.get("executed_at") != report.executed_at
            ):
                return False
        elif outcome == "aborted":
            attempted = payload.get("attempted_tasks")
            has_seal_reference = any(
                field in payload for field in ("output_seal_id", "output_sha256", "results_sha256")
            )
            if (
                payload.get("decision") != "aborted"
                or not _valid_termination_evidence(payload)
                or type(attempted) is not int
                or not 0 <= attempted <= frozen_spec["max_cases"]
                or not _nonempty(payload.get("failure_type"))
                or (has_seal_reference and (
                    not _nonempty(payload.get("output_seal_id"))
                    or not isinstance(payload.get("output_sha256"), str)
                    or not SHA256_RE.fullmatch(payload.get("output_sha256", ""))
                    or payload.get("output_sha256") != payload.get("results_sha256")
                    or not isinstance(payload.get("results_sha256"), str)
                    or not SHA256_RE.fullmatch(payload.get("results_sha256", ""))
                ))
            ):
                return False
        else:
            return False
        authorized_budget = _decimal_usd(budget.get("authorized_max_usd"))
        actual_cost = _decimal_usd(budget.get("actual_usd"))
        cost_unknown = outcome == "aborted" and payload.get("cost_status") == "unknown"
        if (
            authorized_budget is None or authorized_budget <= 0
            or (cost_unknown and budget.get("actual_usd") is not None)
            or (not cost_unknown and (
                payload.get("cost_status") != "known"
                or actual_cost is None or actual_cost < 0 or actual_cost > authorized_budget
            ))
            or not isinstance(payload.get("stop_conditions"), list)
            or not payload["stop_conditions"]
            or not all(_nonempty(item) for item in payload["stop_conditions"])
            or not REQUIRED_HOLDOUT_STOP_CONDITIONS.issubset(payload["stop_conditions"])
        ):
            return False
        event_times = [
            datetime.fromisoformat(event["appended_at"].replace("Z", "+00:00"))
            for event in events
        ]
        if any(later < earlier for earlier, later in zip(event_times, event_times[1:])):
            return False
        if outcome in {"passed", "failed"}:
            criteria = payload.get("quality_criteria")
            passed_tasks = payload.get("passed_tasks")
            pass_rate_bps = payload.get("pass_rate_bps")
            minimum_tasks = criteria.get("minimum_task_count") if isinstance(criteria, dict) else None
            minimum_rate = criteria.get("minimum_pass_rate_bps") if isinstance(criteria, dict) else None
            require_all = criteria.get("require_all_tasks_pass") if isinstance(criteria, dict) else None
            if (
                type(passed_tasks) is not int or not 0 <= passed_tasks <= task_count
                or type(pass_rate_bps) is not int
                or pass_rate_bps != passed_tasks * 10_000 // task_count
                or type(minimum_tasks) is not int or not 1 <= minimum_tasks <= task_count
                or type(minimum_rate) is not int or not 0 <= minimum_rate <= 10_000
                or type(require_all) is not bool
            ):
                return False
            quality_passed = (
                task_count >= minimum_tasks
                and passed_tasks * 10_000 >= minimum_rate * task_count
                and (not require_all or passed_tasks == task_count)
            )
            expected_quality = "passed" if quality_passed else "failed"
            if payload.get("quality_decision") != expected_quality or outcome != expected_quality:
                return False
        expected_status = {"passed": "passed", "failed": "failed", "aborted": "unverified"}.get(outcome)
        return expected_status == evidence.status
    if evidence.kind in {"fixture", "replay", "offline"}:
        return _nonempty(payload.get("source"))
    return False


def _normalize_v6_payload(payload: dict) -> dict | None:
    if payload.get("schema") != OFFICIAL_HOLDOUT_RESULT_SCHEMA_V6:
        return None
    registry = payload.get("registry")
    if not isinstance(registry, dict):
        return None
    normalized = dict(payload)
    normalized["schema"] = OFFICIAL_HOLDOUT_RESULT_SCHEMA
    normalized_registry = dict(registry)
    normalized_registry.pop("receipt_chain", None)
    normalized_registry.pop("pre_compromise_anchors", None)
    normalized["registry"] = normalized_registry
    for field in ("trust_bundle", "trust_bundle_root_signature", "trust_bundle_sha256"):
        normalized.pop(field, None)
    return normalized


def _validate_payload(payload: dict, evidence: Evidence, report: AcceptanceReport) -> bool:
    candidate = _normalize_v6_payload(payload) if payload.get("schema") == OFFICIAL_HOLDOUT_RESULT_SCHEMA_V6 else payload
    return candidate is not None and _validate_payload_v5(candidate, evidence, report)


ASSURANCE_ATTESTATION_PROFILE = "ed25519-jcs-assurance-attestation-v1"
ASSURANCE_SIGNER_FIELDS = {
    "subject_id", "role", "key_id", "public_key", "fingerprint_sha256",
    "policy_version", "status", "not_before_utc", "not_after_utc",
}
RISK_APPROVAL_FIELDS = {
    "schema", "approval_id", "subject_id", "role", "decision", "frozen_spec_sha256",
    "assurance_profile", "append_authority_domain_id", "signing_key_custodian_domain_id",
    "append_authority_compromise_in_scope", "witness_authority_domain_id",
    "witness_root_fingerprint_sha256", "policy_version", "approved_at_utc",
    "expires_at_utc", "signature_profile", "key_id", "signature",
}
HANDOFF_REVIEW_FIELDS = {
    "schema", "review_id", "subject_id", "role", "decision", "frozen_spec_sha256",
    "handoff_sha256", "policy_version", "reviewed_at_utc", "expires_at_utc",
    "signature_profile", "key_id", "signature",
}
BASE64URL_32_RE = re.compile(r"^[A-Za-z0-9_-]{43}$")
BASE64URL_64_RE = re.compile(r"^[A-Za-z0-9_-]{86}$")


def _decode_governance_signature(value: Any) -> bytes:
    if not isinstance(value, str) or not BASE64URL_64_RE.fullmatch(value):
        raise ValueError("governance attestation signature encoding is invalid")
    try:
        decoded = base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
    except (ValueError, base64.binascii.Error) as exc:
        raise ValueError("governance attestation signature encoding is invalid") from exc
    if base64.urlsafe_b64encode(decoded).rstrip(b"=").decode("ascii") != value:
        raise ValueError("governance attestation signature encoding is not canonical")
    return decoded


def _verify_governance_attestation(
    attestation: Any,
    signer_pin: Any,
    *,
    schema: str,
    role: str,
    decision: str,
    signed_at_field: str,
    current_time: datetime,
) -> dict:
    if not isinstance(attestation, dict) or not isinstance(signer_pin, dict):
        raise RegistryStatusUnavailable("signed governance attestation or verifier signer pin is missing")
    expected_fields = RISK_APPROVAL_FIELDS if role == "risk_owner" else HANDOFF_REVIEW_FIELDS
    if set(attestation) != expected_fields:
        raise ValueError("governance attestation has missing or unknown fields")
    if set(signer_pin) != ASSURANCE_SIGNER_FIELDS:
        raise RegistryStatusUnavailable("verifier governance signer pin has missing or unknown fields")
    if (signer_pin.get("role") != role or signer_pin.get("status") != "active"
            or not all(_nonempty(signer_pin.get(field)) for field in (
                "subject_id", "key_id", "policy_version", "not_before_utc", "not_after_utc",
            ))):
        raise RegistryStatusUnavailable("verifier governance signer is not active or authorized")
    if (not _utc_timestamp(signer_pin["not_before_utc"])
            or not _utc_timestamp(signer_pin["not_after_utc"])):
        raise RegistryStatusUnavailable("verifier governance signer validity interval is invalid")
    pin_start = datetime.fromisoformat(signer_pin["not_before_utc"].replace("Z", "+00:00"))
    pin_end = datetime.fromisoformat(signer_pin["not_after_utc"].replace("Z", "+00:00"))
    if pin_start >= pin_end or current_time < pin_start or current_time >= pin_end:
        raise RegistryStatusUnavailable("verifier governance signer pin is not currently valid")
    public_key_text = signer_pin.get("public_key")
    fingerprint = signer_pin.get("fingerprint_sha256")
    if (not isinstance(public_key_text, str) or not BASE64URL_32_RE.fullmatch(public_key_text)
            or not isinstance(fingerprint, str) or not SHA256_RE.fullmatch(fingerprint)):
        raise RegistryStatusUnavailable("verifier governance signer key pin is malformed")
    try:
        public_key_bytes = base64.urlsafe_b64decode(
            public_key_text + "=" * (-len(public_key_text) % 4)
        )
    except (ValueError, base64.binascii.Error) as exc:
        raise RegistryStatusUnavailable("verifier governance signer key pin is malformed") from exc
    if (len(public_key_bytes) != 32
            or base64.urlsafe_b64encode(public_key_bytes).rstrip(b"=").decode("ascii") != public_key_text
            or hashlib.sha256(public_key_bytes).hexdigest() != fingerprint):
        raise RegistryStatusUnavailable("verifier governance signer key fingerprint does not match")
    if (attestation.get("schema") != schema or attestation.get("role") != role
            or attestation.get("decision") != decision
            or attestation.get("subject_id") != signer_pin["subject_id"]
            or attestation.get("key_id") != signer_pin["key_id"]
            or attestation.get("policy_version") != signer_pin["policy_version"]
            or attestation.get("signature_profile") != ASSURANCE_ATTESTATION_PROFILE):
        raise ValueError("governance attestation identity, policy, or decision does not match")
    signed_at = attestation.get(signed_at_field)
    expires_at = attestation.get("expires_at_utc")
    if not _utc_timestamp(signed_at) or not _utc_timestamp(expires_at):
        raise ValueError("governance attestation time is invalid")
    signed_at_dt = datetime.fromisoformat(signed_at.replace("Z", "+00:00"))
    expires_at_dt = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
    if signed_at_dt > current_time or expires_at_dt <= signed_at_dt:
        raise RegistryStatusUnavailable("governance attestation is future-dated or expired")
    if current_time >= expires_at_dt:
        raise RegistryStatusUnavailable("governance attestation has expired")
    if signed_at_dt < pin_start or signed_at_dt >= pin_end:
        raise RegistryStatusUnavailable("governance attestation was signed outside the pinned key interval")
    body = {key: value for key, value in attestation.items() if key != "signature"}
    try:
        Ed25519PublicKey.from_public_bytes(public_key_bytes).verify(
            _decode_governance_signature(attestation["signature"]),
            canonical_json_bytes(body),
        )
    except InvalidSignature as exc:
        raise ValueError("governance attestation signature is invalid") from exc
    except (TypeError, ValueError) as exc:
        if isinstance(exc, ValueError) and str(exc).startswith("governance attestation"):
            raise
        raise ValueError("governance attestation cannot be verified") from exc
    return body


def _verify_assurance_attestations(
    payload: dict, frozen_spec: dict, report: AcceptanceReport, inputs: RegistryVerificationInputs
) -> dict:
    if not _nonempty(inputs.handoff_record_sha256):
        raise RegistryStatusUnavailable("independently pinned handoff record digest is missing")
    frozen_digest = canonical_sha256(frozen_spec)
    if payload.get("frozen_spec_sha256") != frozen_digest:
        raise ValueError("governance attestations do not bind the recomputed frozen spec")
    now = datetime.fromisoformat(inputs.current_time_utc.replace("Z", "+00:00"))
    approval = _verify_governance_attestation(
        inputs.risk_approval_attestation,
        inputs.trusted_risk_owner,
        schema="stage5-assurance-approval-v1",
        role="risk_owner",
        decision="approved",
        signed_at_field="approved_at_utc",
        current_time=now,
    )
    review = _verify_governance_attestation(
        inputs.handoff_review_attestation,
        inputs.trusted_independent_reviewer,
        schema="stage5-handoff-review-attestation-v1",
        role="independent_reviewer",
        decision="accepted",
        signed_at_field="reviewed_at_utc",
        current_time=now,
    )
    if approval["subject_id"] == review["subject_id"]:
        raise ValueError("risk owner and independent handoff reviewer must be distinct")
    expected_approval = {
        "frozen_spec_sha256": frozen_digest,
        "assurance_profile": inputs.assurance_profile,
        "append_authority_domain_id": inputs.append_authority_domain_id,
        "signing_key_custodian_domain_id": inputs.signing_key_custodian_domain_id,
        "append_authority_compromise_in_scope": inputs.assurance_profile == "dual-witness-v1",
        "witness_authority_domain_id": frozen_spec.get("witness_authority_domain_id"),
        "witness_root_fingerprint_sha256": frozen_spec.get("witness_root_fingerprint_sha256"),
    }
    if any(approval.get(key) != value for key, value in expected_approval.items()):
        raise ValueError("risk approval does not bind the verified assurance profile")
    events = payload.get("registry", {}).get("events")
    if not isinstance(events, list) or not events:
        raise ValueError("governance attestation has no authorized registry event")
    authorization_at = events[0].get("appended_at") if isinstance(events[0], dict) else None
    terminal_at = events[-1].get("appended_at") if isinstance(events[-1], dict) else None
    if not _utc_timestamp(authorization_at) or not _utc_timestamp(terminal_at):
        raise ValueError("holdout authorization or terminal event time is invalid")
    authorization_dt = datetime.fromisoformat(authorization_at.replace("Z", "+00:00"))
    terminal_dt = datetime.fromisoformat(terminal_at.replace("Z", "+00:00"))
    approval_at = datetime.fromisoformat(approval["approved_at_utc"].replace("Z", "+00:00"))
    review_at = datetime.fromisoformat(review["reviewed_at_utc"].replace("Z", "+00:00"))
    if approval_at > authorization_dt:
        raise ValueError("risk approval was signed after holdout authorization")
    if review_at < terminal_dt:
        raise ValueError("independent review predates the holdout terminal event")
    if (review.get("frozen_spec_sha256") != frozen_digest
            or review.get("handoff_sha256") != inputs.handoff_record_sha256):
        raise ValueError("independent review does not bind the pinned handoff and frozen spec")
    return {
        "risk_owner_subject_id": approval["subject_id"],
        "reviewer_subject_id": review["subject_id"],
        "frozen_spec_sha256": frozen_digest,
        "handoff_sha256": inputs.handoff_record_sha256,
        "profile": inputs.assurance_profile,
    }


def _verify_v6_registry(
    payload: dict, report: AcceptanceReport, inputs: RegistryVerificationInputs
) -> dict:
    frozen_spec = payload.get("frozen_spec")
    registry = payload.get("registry")
    if not isinstance(frozen_spec, dict) or not isinstance(registry, dict):
        raise ValueError("v6 frozen spec or registry is missing")
    frozen_values = {
        "registry_environment_id": inputs.environment_id,
        "registry_log_id": inputs.log_id,
        "permitted_signer_key_id": inputs.permitted_signer_key_id,
        "assurance_profile": inputs.assurance_profile,
        "append_authority_domain_id": inputs.append_authority_domain_id,
        "signing_key_custodian_domain_id": inputs.signing_key_custodian_domain_id,
        "trust_bundle_sha256": payload.get("trust_bundle_sha256"),
        "receipt_hash_profile": "jcs-rfc8785-v1",
        "receipt_signature_profile": "ed25519-jcs-receipt-v1",
    }
    if any(frozen_spec.get(key) != value for key, value in frozen_values.items()):
        raise ValueError("v6 registry verifier scope does not match frozen spec")
    if payload.get("trust_bundle_sha256") != frozen_spec.get("trust_bundle_sha256"):
        raise ValueError("v6 trust bundle digest is not bound by frozen spec")
    if inputs.assurance_profile == "local-reference":
        raise RegistryStatusUnavailable("local-reference cannot be accepted as official holdout evidence")
    max_age = frozen_spec.get("max_status_age_seconds")
    max_skew = frozen_spec.get("clock_skew_seconds")
    if (type(max_age) is not int or max_age < 1 or type(max_skew) is not int or max_skew < 0
            or max_age > inputs.max_freshness_seconds or max_skew > inputs.clock_skew_seconds):
        raise ValueError("v6 frozen freshness policy exceeds verifier policy")

    scope = {
        "environment_id": inputs.environment_id,
        "log_id": inputs.log_id,
        "trust_bundle_sha256": frozen_spec["trust_bundle_sha256"],
    }
    try:
        snapshot = inputs.status_source.fetch_latest_status(**scope)
    except Exception as exc:
        raise RegistryStatusUnavailable("latest key-status source could not be reached") from exc
    if not isinstance(snapshot, dict):
        raise RegistryStatusUnavailable("latest key-status source returned a malformed snapshot")
    if (snapshot.get("source_id") != inputs.key_status_source_id
            or any(snapshot.get(key) != value for key, value in scope.items())):
        raise RegistryStatusUnavailable("latest key-status snapshot source or scope does not match")
    fetched_at = snapshot.get("fetched_at_utc")
    if not _utc_timestamp(fetched_at) or not _utc_timestamp(inputs.current_time_utc):
        raise RegistryStatusUnavailable("key-status source fetch time or verifier clock is invalid")
    fetched_at_dt = datetime.fromisoformat(fetched_at.replace("Z", "+00:00"))
    now_dt = datetime.fromisoformat(inputs.current_time_utc.replace("Z", "+00:00"))
    fetch_age = (now_dt - fetched_at_dt).total_seconds()
    if fetch_age < -inputs.clock_skew_seconds or fetch_age > min(max_age, inputs.max_freshness_seconds):
        raise RegistryStatusUnavailable("key-status source response is stale or from the future")
    status_statement = snapshot.get("statement")
    status_root_signature = snapshot.get("root_signature")
    if not isinstance(status_statement, dict) or not isinstance(status_root_signature, dict):
        raise RegistryStatusUnavailable("latest key-status snapshot is missing signed status data")
    persisted_sequence = inputs.sequence_floor_store.read(scope)
    minimum_sequence = max(1, persisted_sequence)
    try:
        status_checkpoint = verify_registry_status_snapshot(
            trust_bundle=payload.get("trust_bundle"),
            trust_bundle_root_signature=payload.get("trust_bundle_root_signature"),
            trust_bundle_sha256=frozen_spec["trust_bundle_sha256"],
            trusted_root=inputs.trusted_root,
            environment_id=inputs.environment_id,
            log_id=inputs.log_id,
            permitted_signer_key_id=inputs.permitted_signer_key_id,
            key_status_statement=status_statement,
            key_status_root_signature=status_root_signature,
            current_time_utc=inputs.current_time_utc,
            max_freshness_seconds=min(max_age, inputs.max_freshness_seconds),
            minimum_status_sequence=minimum_sequence,
            clock_skew_seconds=min(max_skew, inputs.clock_skew_seconds),
        )
        minimum_sequence = status_checkpoint["key_status_sequence"]
        if minimum_sequence > persisted_sequence:
            inputs.sequence_floor_store.advance(
                scope,
                expected=persisted_sequence,
                new_sequence=minimum_sequence,
            )
    except SequenceFloorConflict as exc:
        raise RegistryStatusUnavailable("concurrent verifier advanced status floor") from exc
    except ValueError as exc:
        message = str(exc).lower()
        if any(term in message for term in (
            "expired", "future", "fresh", "sequence is below", "freshness", "sequence rollback",
        )):
            raise RegistryStatusUnavailable(str(exc)) from exc
        raise

    summaries = registry.get("events")
    entries = registry.get("receipt_chain")
    if (not isinstance(summaries, list) or not isinstance(entries, list)
            or len(summaries) != len(entries) or not summaries):
        raise ValueError("v6 event summaries and signed receipt chain do not align")
    for index, (summary, entry) in enumerate(zip(summaries, entries, strict=True)):
        if not isinstance(summary, dict) or not isinstance(entry, dict):
            raise ValueError(f"v6 event {index} is malformed")
        event = entry.get("event")
        if not isinstance(event, dict) or event.get("payload") != summary:
            raise ValueError(f"v6 event {index} payload differs from domain summary")
        bindings = {
            "event_id": summary.get("event_id"),
            "event_type": summary.get("type"),
            "actor_subject_id": summary.get("actor_id"),
            "actor_role": summary.get("actor_role"),
            "registry_recorded_at": summary.get("appended_at"),
        }
        if any(event.get(field) != value for field, value in bindings.items()):
            raise ValueError(f"v6 event {index} metadata differs from domain summary")

    revoked_keys = {
        item.get("key_id") for item in status_statement.get("revoked_keys", [])
        if isinstance(item, dict) and _nonempty(item.get("key_id"))
    }
    verified_anchors = []
    if any(
        isinstance(entry.get("receipt"), dict)
        and entry["receipt"].get("key_id") in revoked_keys
        for entry in entries
    ):
        if inputs.anchor_source is None or not _nonempty(inputs.anchor_source_id):
            raise RegistryStatusUnavailable("independent anchor source is not configured")
        for entry in entries:
            receipt = entry.get("receipt")
            if not isinstance(receipt, dict) or receipt.get("key_id") not in revoked_keys:
                continue
            event = entry.get("event")
            if not isinstance(event, dict):
                raise ValueError("v6 receipt event is malformed")
            receipt_digest = canonical_sha256(entry)
            try:
                response = inputs.anchor_source.fetch_anchor(
                    environment_id=inputs.environment_id,
                    log_id=inputs.log_id,
                    run_id=report.run_id,
                    sequence=receipt.get("sequence"),
                    event_id=receipt.get("event_id"),
                    receipt_sha256=receipt_digest,
                )
            except Exception as exc:
                raise RegistryStatusUnavailable("independent anchor source could not be reached") from exc
            if response is None:
                continue
            if (not isinstance(response, dict)
                    or response.get("source_id") != inputs.anchor_source_id
                    or not isinstance(response.get("anchor"), dict)):
                raise RegistryStatusUnavailable("anchor source identity or response is invalid")
            verified_anchors.append(response["anchor"])

    try:
        verification = verify_registry_receipts(
            entries=entries,
            run_id=report.run_id,
            environment_id=inputs.environment_id,
            log_id=inputs.log_id,
            trust_bundle=payload.get("trust_bundle"),
            trust_bundle_root_signature=payload.get("trust_bundle_root_signature"),
            trust_bundle_sha256=frozen_spec["trust_bundle_sha256"],
            trusted_root=inputs.trusted_root,
            permitted_signer_key_id=inputs.permitted_signer_key_id,
            key_status_statement=status_statement,
            key_status_root_signature=status_root_signature,
            current_time_utc=inputs.current_time_utc,
            max_freshness_seconds=min(max_age, inputs.max_freshness_seconds),
            minimum_status_sequence=status_checkpoint["key_status_sequence"],
            clock_skew_seconds=min(max_skew, inputs.clock_skew_seconds),
            pre_compromise_anchors=verified_anchors,
            pre_compromise_anchor_schema="stage5-pre-compromise-anchor-v1",
            trusted_anchor=inputs.trusted_anchor,
        )
    except SequenceFloorConflict as exc:
        raise RegistryStatusUnavailable("concurrent verifier advanced status floor") from exc
    except ValueError as exc:
        message = str(exc).lower()
        if any(term in message for term in (
            "expired", "future", "fresh", "sequence is below", "freshness", "sequence rollback",
            "uses an unknown or unpermitted signer", "revoked-key history requires",
            "external trusted anchor configuration is missing",
            "anchor authority/key id is not pinned", "trusted anchor key fingerprint mismatch",
            "anchor does not bind", "anchor scope does not match", "anchor time is not after",
        )):
            raise RegistryStatusUnavailable(str(exc)) from exc
        raise
    if inputs.assurance_profile == "dual-witness-v1":
        if (inputs.witness_source is None or not _nonempty(inputs.witness_source_id)
                or not isinstance(inputs.trusted_witness, dict)
                or not isinstance(inputs.terminal_witness_receipt_sha256, str)
                or not SHA256_RE.fullmatch(inputs.terminal_witness_receipt_sha256)):
            raise RegistryStatusUnavailable("dual-witness source, trust pin, or handoff terminal digest is missing")
        if (frozen_spec.get("witness_authority_domain_id") != inputs.trusted_witness.get("authority_id")
                or frozen_spec.get("witness_root_fingerprint_sha256") != inputs.trusted_witness.get("fingerprint_sha256")):
            raise ValueError("dual-witness identity or root fingerprint differs from frozen spec")
        try:
            witness_snapshot = inputs.witness_source.fetch_latest_witness_chain(
                environment_id=inputs.environment_id,
                log_id=inputs.log_id,
                run_id=report.run_id,
            )
        except Exception as exc:
            raise RegistryStatusUnavailable("latest witness chain source could not be reached") from exc
        required_witness_snapshot_fields = {
            "source_id", "environment_id", "log_id", "run_id", "fetched_at_utc", "witness_receipts",
        }
        if (not isinstance(witness_snapshot, dict)
                or set(witness_snapshot) != required_witness_snapshot_fields
                or witness_snapshot.get("source_id") != inputs.witness_source_id
                or witness_snapshot.get("environment_id") != inputs.environment_id
                or witness_snapshot.get("log_id") != inputs.log_id
                or witness_snapshot.get("run_id") != report.run_id):
            raise RegistryStatusUnavailable("latest witness chain source identity or scope does not match")
        witness_fetched_at = witness_snapshot.get("fetched_at_utc")
        if not _utc_timestamp(witness_fetched_at):
            raise RegistryStatusUnavailable("witness chain fetch time is invalid")
        witness_age = (
            datetime.fromisoformat(inputs.current_time_utc.replace("Z", "+00:00"))
            - datetime.fromisoformat(witness_fetched_at.replace("Z", "+00:00"))
        ).total_seconds()
        if witness_age < -inputs.clock_skew_seconds or witness_age > min(max_age, inputs.max_freshness_seconds):
            raise RegistryStatusUnavailable("witness chain response is stale or from the future")
        witness_receipts = witness_snapshot.get("witness_receipts")
        if not isinstance(witness_receipts, list) or not witness_receipts:
            raise RegistryStatusUnavailable("latest witness source has no committed receipt chain")
        try:
            witness_verification = verify_dual_witness_receipt_chain(
                authority_entries=entries,
                witness_receipts=witness_receipts,
                run_id=report.run_id,
                environment_id=inputs.environment_id,
                log_id=inputs.log_id,
                append_authority_domain_id=inputs.append_authority_domain_id,
                signing_key_custodian_domain_id=inputs.signing_key_custodian_domain_id,
                trusted_witness=inputs.trusted_witness,
                current_time_utc=inputs.current_time_utc,
                clock_skew_seconds=min(max_skew, inputs.clock_skew_seconds),
            )
        except ValueError:
            raise
        if witness_verification["terminal_witness_receipt_sha256"] != inputs.terminal_witness_receipt_sha256:
            raise ValueError("terminal witness receipt digest differs from independently reviewed handoff")
        verification["witness"] = witness_verification
    elif inputs.witness_source is not None:
        raise ValueError("witness source is configured for a non-dual-witness assurance profile")
    verification["governance"] = _verify_assurance_attestations(payload, frozen_spec, report, inputs)
    return verification


def _verify_materials(root: Path, report: AcceptanceReport, manifest: dict) -> bool:
    materials = manifest.get("materials")
    if not isinstance(materials, dict):
        return False
    for material_name, hash_field in MATERIAL_HASH_FIELDS.items():
        record = materials.get(material_name)
        if not isinstance(record, dict):
            return False
        locator = record.get("locator")
        path = _resolve_file(root, locator)
        if path is None:
            return False
        try:
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
        except OSError:
            return False
        expected = getattr(report, hash_field)
        if digest != expected or record.get("sha256") != expected:
            return False
    return True


def decide(
    report: AcceptanceReport,
    evidence_root: str | Path,
    registry_verification: RegistryVerificationInputs | None = None,
) -> dict:
    """Validate report provenance and evidence within a configured local root.

    Artifact status and kind are checked in the decoded evidence payload and
    cross-checked with the report and manifest. Local claims are not signed or
    otherwise authenticated; this function cannot prove real-world execution.
    """
    if not isinstance(report, AcceptanceReport):
        return _invalid("invalid-report-type")
    if registry_verification is not None and not isinstance(registry_verification, RegistryVerificationInputs):
        return _invalid("invalid-registry-verification-inputs")
    if type(report.version) is not int or report.version != REPORT_VERSION:
        return _invalid("unsupported-report-version")
    try:
        root = Path(evidence_root).resolve(strict=True)
    except (OSError, RuntimeError, TypeError, ValueError):
        return _invalid("invalid-evidence-root")
    manifest = _read_json(root / MANIFEST_NAME)
    if manifest is None:
        return _invalid("missing-or-invalid-evidence-manifest")
    if type(manifest.get("version")) is not int or manifest.get("version") != REPORT_VERSION:
        return _invalid("unsupported-manifest-version")
    provenance_error = _validate_provenance(report, manifest)
    if provenance_error:
        return _invalid(provenance_error)
    if not _verify_materials(root, report, manifest):
        return _invalid("invalid-frozen-materials")

    evidence = report.evidence
    if not isinstance(evidence, list) or any(not isinstance(item, Evidence) for item in evidence):
        return _invalid("invalid-evidence-list")
    by_id = {item.gate_id: item for item in evidence if isinstance(item.gate_id, str)}
    duplicate_ids = len(by_id) != len(evidence)
    missing = sorted(REQUIRED_GATES - set(by_id))
    unexpected = sorted(set(by_id) - REQUIRED_GATES)
    if duplicate_ids or unexpected:
        return _invalid("duplicate-or-unexpected-gates", missing=missing, unexpected=unexpected)

    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list):
        return _invalid("invalid-manifest-artifacts")
    by_locator: dict[str, dict] = {}
    for artifact in artifacts:
        if not isinstance(artifact, dict) or not _safe_locator(artifact.get("locator")):
            return _invalid("invalid-manifest-artifact")
        locator = artifact["locator"]
        if locator in by_locator:
            return _invalid("duplicate-manifest-locator", locator=locator)
        by_locator[locator] = artifact

    invalid_gates: list[str] = []
    structurally_valid_v5_holdouts: list[str] = []
    structurally_valid_v6_holdouts: list[str] = []
    verified_v6_holdouts: list[str] = []
    verified: dict[str, tuple[Evidence, dict, dict]] = {}
    for item in evidence:
        gate_id = item.gate_id if isinstance(item.gate_id, str) else "<invalid>"
        if (not _nonempty(item.gate_id) or not isinstance(item.status, str)
                or item.status not in STATUSES or not isinstance(item.kind, str)
                or item.kind not in KINDS or not _nonempty(item.release_id)
                or not _nonempty(item.run_id) or item.release_id != report.release_id
                or item.run_id != report.run_id or not isinstance(item.sha256, str)
                or not SHA256_RE.fullmatch(item.sha256)):
            invalid_gates.append(gate_id)
            continue
        artifact = by_locator.get(item.locator) if isinstance(item.locator, str) else None
        path = _resolve_file(root, item.locator)
        if artifact is None or path is None:
            invalid_gates.append(gate_id)
            continue
        try:
            content = path.read_bytes()
            payload = parse_json_strict(content.decode("utf-8"))
        except (OSError, UnicodeError, ValueError):
            invalid_gates.append(gate_id)
            continue
        if not isinstance(payload, dict):
            invalid_gates.append(gate_id)
            continue
        digest = hashlib.sha256(content).hexdigest()
        if (digest != item.sha256 or digest != artifact.get("sha256")
                or type(artifact.get("bytes")) is not int or len(content) != artifact.get("bytes")
                or artifact.get("gate_id") != item.gate_id
                or artifact.get("release_id") != report.release_id
                or artifact.get("run_id") != report.run_id
                or artifact.get("kind") != item.kind
                or artifact.get("status") != item.status
                or not _validate_payload(payload, item, report)):
            invalid_gates.append(gate_id)
            continue
        verified[item.gate_id] = (item, artifact, payload)
        if (
            item.gate_id == "official_blind_holdout"
            and payload.get("schema") == OFFICIAL_HOLDOUT_RESULT_SCHEMA
        ):
            structurally_valid_v5_holdouts.append(item.gate_id)
        if (
            item.gate_id == "official_blind_holdout"
            and payload.get("schema") == OFFICIAL_HOLDOUT_RESULT_SCHEMA_V6
        ):
            structurally_valid_v6_holdouts.append(item.gate_id)
            if registry_verification is not None:
                try:
                    _verify_v6_registry(payload, report, registry_verification)
                except RegistryStatusUnavailable:
                    pass
                except (OSError, sqlite3.Error):
                    pass
                except ValueError:
                    invalid_gates.append(gate_id)
                else:
                    verified_v6_holdouts.append(item.gate_id)
    if invalid_gates:
        return _invalid("invalid-evidence", gates=sorted(set(invalid_gates)))

    failed = sorted(item.gate_id for item in evidence if item.status == "failed")
    if failed:
        return {"decision": "blocked", "failed": failed}
    if missing:
        return {"decision": "incomplete", "missing": missing, "unexpected": []}
    wrong_kind = sorted(
        gate for gate, required_kind in REQUIRED_KINDS.items()
        if verified[gate][1].get("kind") != required_kind
    )
    unverified = sorted({
        *(item.gate_id for item in evidence if item.status == "unverified"),
        *structurally_valid_v5_holdouts,
        *(gate for gate in structurally_valid_v6_holdouts if gate not in verified_v6_holdouts),
        *wrong_kind,
    })
    if unverified:
        return {"decision": "insufficient-evidence", "unverified": unverified}
    return {"decision": "ready-for-human-acceptance", "missing": [], "unexpected": []}


def build_acceptance_matrix(
    report: AcceptanceReport,
    evidence_root: str | Path,
    registry_verification: RegistryVerificationInputs | None = None,
) -> dict:
    """Return per-gate structural states without implying authenticated evidence."""
    decision = decide(report, evidence_root, registry_verification)
    evidence_items = report.evidence if isinstance(report, AcceptanceReport) and isinstance(report.evidence, list) else []
    by_gate = {
        item.gate_id: item for item in evidence_items
        if isinstance(item, Evidence) and isinstance(item.gate_id, str)
    }
    present_gates = set(by_gate)
    missing = REQUIRED_GATES - present_gates
    unverified = set(decision.get("unverified", []))
    invalid_gates = set(decision.get("gates", []))
    invalid_report = decision["decision"] == "invalid-report"
    rows = []
    for gate_id in sorted(REQUIRED_GATES):
        item = by_gate.get(gate_id)
        if gate_id in missing:
            state = "missing"
        elif invalid_report:
            state = "invalid-report" if gate_id in invalid_gates else "not-evaluated"
        elif gate_id in unverified or (item is not None and item.status == "unverified"):
            state = "unverified"
        elif item is not None and item.status == "failed":
            state = "failed"
        else:
            state = "passed"
        rows.append({
            "gate_id": gate_id,
            "required_kind": REQUIRED_KINDS.get(gate_id),
            "evidence_kind": item.kind if item is not None else None,
            "evidence_status": item.status if item is not None else None,
            "artifact": item.locator if item is not None else None,
            "state": state,
        })
    return {
        "schema": "capstone-acceptance-matrix-v1",
        "decision": decision["decision"],
        "gates": rows,
        "authenticated": False,
        "evidence_scope": "local structural validation only; external registry and real-world execution are not authenticated",
    }
