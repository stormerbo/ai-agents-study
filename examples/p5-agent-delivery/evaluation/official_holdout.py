"""Orchestrate one externally authorized blind-holdout run.

This module implements local orchestration contracts. A trusted registry,
isolated candidate runtime, and independent scorer must be supplied by
deployment infrastructure; the repository's fixture runner is not an
implementation of those services.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import json
import re
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Literal, Protocol

from canonicalization import HASH_PROFILE, canonical_sha256


SHA256 = re.compile(r"[0-9a-f]{64}\Z")
IMAGE_DIGEST = re.compile(r"sha256:[0-9a-f]{64}\Z")
REQUIRED_STOP_CONDITIONS = frozenset({
    "budget",
    "deadline",
    "side-effect",
    "permission-boundary",
    "evidence-missing",
    "label-leak",
    "identity-mismatch",
})
OFFICIAL_HOLDOUT_RESULT_SCHEMA = "official-blind-holdout-run-result-v4"
REGISTRY_EVENT_FIELDS = frozenset({
    "event_id",
    "actor_id",
    "actor_role",
    "recorded_at_utc",
    "previous_event_id",
    "run_id",
    "holdout_version",
    "frozen_spec_sha256",
    "candidate_sha256",
    "image_digest",
    "dataset_sha256",
    "scorer_sha256",
    "executor_sha256",
    "hash_profile",
})


class HoldoutRunError(RuntimeError):
    """A reserved holdout run stopped without producing a passing report."""


@dataclass(frozen=True)
class HoldoutRunSpec:
    holdout_version: str
    run_id: str
    authorization_event_id: str
    owner_id: str
    executor_id: str
    recovery_operator_id: str
    assurance_profile: str
    append_authority_domain_id: str
    signing_key_custodian_domain_id: str
    witness_authority_domain_id: str | None
    witness_root_fingerprint_sha256: str | None
    candidate_sha256: str
    image_digest: str
    dataset_sha256: str
    scorer_sha256: str
    executor_sha256: str
    max_budget_usd: str
    max_cases: int
    minimum_task_count: int
    minimum_pass_rate_bps: int
    require_all_tasks_pass: bool
    max_output_bytes: int
    deadline_utc: str
    stop_conditions: tuple[str, ...]
    hash_profile: str = HASH_PROFILE


class HoldoutSessionCapability:
    """Opaque single-use secret; common dataclass/JSON logging cannot serialize its value."""

    __slots__ = ("__value", "__presented")

    def __init__(self, value: str) -> None:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("session capability must be a non-empty string")
        object.__setattr__(self, "_HoldoutSessionCapability__value", value)
        object.__setattr__(self, "_HoldoutSessionCapability__presented", False)

    def __setattr__(self, name: str, value: Any) -> None:
        if hasattr(self, name):
            raise AttributeError("session capability is immutable")
        object.__setattr__(self, name, value)

    def reveal_for_custodian(self) -> str:
        """Present the token once, only at the trusted data-plane call site."""
        if self.__presented:
            raise RuntimeError("session capability has already been presented")
        object.__setattr__(self, "_HoldoutSessionCapability__presented", True)
        return self.__value

    def __repr__(self) -> str:
        return "HoldoutSessionCapability(<redacted>)"

    def __deepcopy__(self, memo: dict[int, Any]) -> str:
        return "<redacted>"

    def __reduce_ex__(self, protocol: int) -> Any:
        raise TypeError("session capability cannot be pickled")


@dataclass(frozen=True)
class HoldoutReservation:
    """Registry metadata plus an opaque capability that cannot be JSON serialized."""

    event_id: str
    spec_sha256: str
    session_capability: HoldoutSessionCapability = field(repr=False)
    registry_snapshot: RegistrySnapshot | None = None


@dataclass(frozen=True)
class HoldoutRuntimeIdentity:
    run_id: str
    reservation_event_id: str
    candidate_sha256: str
    image_digest: str
    dataset_sha256: str
    scorer_sha256: str
    executor_sha256: str


@dataclass(frozen=True)
class PublicHoldoutAttempt:
    """One prompt delivered to the isolated runner without a dataset case id or label."""

    attempt_id: str
    public_input: dict[str, Any]


@dataclass(frozen=True)
class CandidateOutput:
    attempt_id: str
    output: dict[str, Any]


@dataclass(frozen=True)
class SealedHoldoutOutputs:
    """Public candidate outputs sealed by the data plane before scorer access."""

    seal_id: str
    run_id: str
    reservation_event_id: str
    frozen_spec_sha256: str
    candidate_sha256: str
    image_digest: str
    dataset_sha256: str
    scorer_sha256: str
    output_sha256: str
    attempt_ids: tuple[str, ...]
    outputs: tuple[CandidateOutput, ...]


@dataclass(frozen=True)
class ScoredAttempt:
    attempt_id: str
    passed: bool


class HoldoutDataSession(Protocol):
    """Single-use question session; never returns labels or the full case list.

    A retry of a read/record operation for the same attempt must return the same
    prompt or accept only the identical output. Closing seals an immutable
    manifest and repeated close calls return the same seal identity.
    """

    def next_attempt(self) -> PublicHoldoutAttempt | None: ...

    def record_output(self, attempt_id: str, output: dict[str, Any]) -> None: ...

    def close_and_seal(self) -> SealedHoldoutOutputs: ...


class HoldoutDataPlane(Protocol):
    """Trusted custodian boundary, separate from registry and candidate runtime.

    Opening is idempotent by reservation event id and binds the returned session
    to the complete frozen run identity. The capability is presented only to
    this trusted boundary, never to CandidateRuntime. A lost response must be
    recoverable or revocable by that event id without issuing a second capability.
    """

    def open_session(
        self,
        capability: str,
        runtime_identity: HoldoutRuntimeIdentity,
        spec: HoldoutRunSpec,
    ) -> HoldoutDataSession: ...

    def reconcile_seal(
        self,
        reservation_event_id: str,
        runtime_identity: HoldoutRuntimeIdentity,
        spec: HoldoutRunSpec,
    ) -> SealedHoldoutOutputs | None:
        """Return the durable seal, or None only when the custodian confirms no seal exists."""

    def abort_session(self, reservation_event_id: str) -> None:
        """Idempotently revoke every capability for this reservation and confirm closure."""


@dataclass(frozen=True)
class RegistryEventSnapshot:
    event_id: str
    state: Literal["authorized", "reserved", "consumed", "aborted", "failed"]
    payload_sha256: str
    payload: dict[str, Any]


@dataclass(frozen=True)
class RegistrySnapshot:
    """Sanitized read-only event chain returned by reconcile; never a local authority."""

    run_id: str
    state: Literal["not_found", "authorized", "reserved", "consumed", "aborted", "failed"]
    events: tuple[RegistryEventSnapshot, ...]


class HoldoutRegistry(Protocol):
    """Adapter contract; reconcile returns the full authorized event chain if present."""

    def reconcile(self, run_id: str) -> RegistrySnapshot: ...

    def reserve(self, spec: HoldoutRunSpec) -> HoldoutReservation: ...

    def append_terminal(
        self,
        reservation_event_id: str,
        terminal_event_id: str,
        state: str,
        report: dict[str, Any],
    ) -> None: ...

    def recover_abort(
        self,
        run_id: str,
        reservation_event_id: str,
        terminal_event_id: str,
        reason: str,
        no_execution_evidence_ref: str,
        no_execution_evidence_sha256: str,
    ) -> RegistryEventSnapshot: ...


class CandidateRuntime(Protocol):
    candidate_sha256: str
    image_digest: str
    max_output_bytes: int

    def execute(
        self,
        attempt_id: str,
        public_input: dict[str, Any],
        deadline_utc: str,
        remaining_budget_usd: str,
    ) -> dict[str, Any]: ...


class Scorer(Protocol):
    """Independent scorer; scoring is idempotent by seal id + scorer hash + output hash."""

    scorer_sha256: str

    def score_sealed(self, outputs: SealedHoldoutOutputs) -> tuple[ScoredAttempt, ...]: ...

    def reconcile_sealed(
        self, seal_id: str, scorer_sha256: str, output_sha256: str
    ) -> tuple[ScoredAttempt, ...] | None:
        """Return the durable score, or None only when no score was committed."""


def executor_bundle_sha256() -> str:
    """Bind the orchestrator, subprocess adapter, and hash profile as one executor."""
    directory = Path(__file__).resolve().parent
    digest = hashlib.sha256()
    for name in ("official_holdout.py", "subprocess_candidate.py", "canonicalization.py"):
        encoded_name = name.encode("utf-8")
        content = (directory / name).read_bytes()
        digest.update(len(encoded_name).to_bytes(4, "big"))
        digest.update(encoded_name)
        digest.update(len(content).to_bytes(8, "big"))
        digest.update(content)
    return digest.hexdigest()


def _canonical_hash(value: Any) -> str:
    return canonical_sha256(value)


def _report_sha256(report: dict[str, Any]) -> str:
    """Hash the canonical result body before it is attached to a registry event."""
    return _canonical_hash({key: value for key, value in report.items() if key != "report_sha256"})


def _decimal_amount(value: Any) -> Decimal | None:
    if not isinstance(value, str):
        return None
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None
    return amount if amount.is_finite() else None


def _format_amount(value: Decimal) -> str:
    return format(value, "f")


def canonical_run_spec_sha256(spec: HoldoutRunSpec) -> str:
    """Return the stable hash the external registry must bind to a reservation."""
    return _canonical_hash(spec.__dict__)


def _validate_reservation_snapshot(spec: HoldoutRunSpec, reservation: HoldoutReservation) -> None:
    snapshot = reservation.registry_snapshot
    if not isinstance(snapshot, RegistrySnapshot):
        raise HoldoutRunError("registry reservation response omitted its event snapshot")
    expected_spec_hash = canonical_run_spec_sha256(spec)
    if snapshot.run_id != spec.run_id or snapshot.state != "reserved":
        raise HoldoutRunError("registry snapshot does not confirm this run as reserved")
    if len(snapshot.events) != 2:
        raise HoldoutRunError("registry reservation snapshot must contain exactly authorized and reserved events")

    authorization, reserved = snapshot.events
    expected_events = (
        (authorization, "authorized", spec.authorization_event_id, None, "owner"),
        (reserved, "reserved", reservation.event_id, spec.authorization_event_id, "executor"),
    )
    previous_time: datetime | None = None
    expected_identity = {
        "run_id": spec.run_id,
        "holdout_version": spec.holdout_version,
        "frozen_spec_sha256": expected_spec_hash,
        "candidate_sha256": spec.candidate_sha256,
        "image_digest": spec.image_digest,
        "dataset_sha256": spec.dataset_sha256,
        "scorer_sha256": spec.scorer_sha256,
        "executor_sha256": spec.executor_sha256,
        "hash_profile": spec.hash_profile,
    }
    expected_actor_ids = (spec.owner_id, spec.executor_id)
    for index, (event, expected_state, expected_id, expected_previous_id, expected_role) in enumerate(expected_events):
        payload = event.payload
        if event.state != expected_state or event.event_id != expected_id:
            raise HoldoutRunError("registry event state or id does not match the frozen run")
        if not isinstance(payload, dict) or set(payload) != REGISTRY_EVENT_FIELDS:
            raise HoldoutRunError("registry event payload is not the required sanitized allowlist shape")
        if payload.get("event_id") != expected_id:
            raise HoldoutRunError("registry event payload id does not match its event envelope")
        if payload.get("actor_role") != expected_role or payload.get("actor_id") != expected_actor_ids[index]:
            raise HoldoutRunError("registry event actor identity is invalid")
        if payload.get("previous_event_id") != expected_previous_id:
            raise HoldoutRunError("registry event chain is broken")
        if any(payload.get(key) != value for key, value in expected_identity.items()):
            raise HoldoutRunError("registry event does not bind the complete frozen run identity")
        if not SHA256.fullmatch(event.payload_sha256) or event.payload_sha256 != _canonical_hash(payload):
            raise HoldoutRunError("registry event payload hash does not match its sanitized payload")
        occurred_at = _utc_datetime(payload.get("recorded_at_utc"))
        if occurred_at is None or (previous_time is not None and occurred_at < previous_time):
            raise HoldoutRunError("registry event timestamps are invalid or out of order")
        previous_time = occurred_at


def _terminal_event_id(spec: HoldoutRunSpec) -> str:
    identity = f"{spec.holdout_version}\0{spec.run_id}".encode("utf-8")
    return "terminal-" + hashlib.sha256(identity).hexdigest()


def _utc_datetime(value: str) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, ValueError):
        return None
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        return None
    return parsed.astimezone(timezone.utc)


def _validate_spec(spec: HoldoutRunSpec) -> None:
    if (
        not isinstance(spec.holdout_version, str)
        or not spec.holdout_version.strip()
        or not isinstance(spec.run_id, str)
        or not spec.run_id.strip()
        or not isinstance(spec.authorization_event_id, str)
        or not spec.authorization_event_id.strip()
    ):
        raise HoldoutRunError("holdout version and run id are required")
    principals = (spec.owner_id, spec.executor_id, spec.recovery_operator_id)
    if (
        any(not isinstance(value, str) or not value.strip() for value in principals)
        or len(set(principals)) != len(principals)
    ):
        raise HoldoutRunError("owner, executor, and recovery operator must be distinct frozen principals")
    if spec.assurance_profile not in {"local-reference", "single-authority-v1", "dual-witness-v1"}:
        raise HoldoutRunError("unsupported assurance profile")
    if any(not isinstance(value, str) or not value.strip() for value in (
        spec.append_authority_domain_id, spec.signing_key_custodian_domain_id,
    )):
        raise HoldoutRunError("append authority and signing-key custodian domains are required")
    if spec.assurance_profile == "dual-witness-v1":
        if (not isinstance(spec.witness_authority_domain_id, str)
                or not spec.witness_authority_domain_id.strip()
                or spec.witness_authority_domain_id in {
                    spec.append_authority_domain_id, spec.signing_key_custodian_domain_id,
                }):
            raise HoldoutRunError("dual-witness authority must use an independent trust domain")
        if (not isinstance(spec.witness_root_fingerprint_sha256, str)
                or not SHA256.fullmatch(spec.witness_root_fingerprint_sha256)):
            raise HoldoutRunError("dual-witness profile requires a pinned witness-root SHA-256 fingerprint")
    elif spec.witness_authority_domain_id is not None or spec.witness_root_fingerprint_sha256 is not None:
        raise HoldoutRunError("witness fields are only allowed for dual-witness profile")
    if any(
        not isinstance(value, str) or not SHA256.fullmatch(value)
        for value in (spec.candidate_sha256, spec.dataset_sha256, spec.scorer_sha256, spec.executor_sha256)
    ):
        raise HoldoutRunError("candidate, dataset, scorer, and executor hashes must be SHA-256")
    if not isinstance(spec.image_digest, str) or not IMAGE_DIGEST.fullmatch(spec.image_digest):
        raise HoldoutRunError("candidate image digest must be immutable")
    max_budget = _decimal_amount(spec.max_budget_usd)
    if max_budget is None or max_budget <= 0:
        raise HoldoutRunError("a positive finite budget is required")
    if isinstance(spec.max_cases, bool) or not isinstance(spec.max_cases, int) or spec.max_cases < 1:
        raise HoldoutRunError("a positive integer case limit is required")
    if (
        isinstance(spec.minimum_task_count, bool)
        or not isinstance(spec.minimum_task_count, int)
        or not 1 <= spec.minimum_task_count <= spec.max_cases
    ):
        raise HoldoutRunError("minimum task count must be within the case limit")
    if (
        isinstance(spec.minimum_pass_rate_bps, bool)
        or not isinstance(spec.minimum_pass_rate_bps, int)
        or not 0 <= spec.minimum_pass_rate_bps <= 10_000
    ):
        raise HoldoutRunError("pass-rate threshold must be an integer from 0 to 10000 basis points")
    if not isinstance(spec.require_all_tasks_pass, bool):
        raise HoldoutRunError("all-tasks-pass criterion must be boolean")
    deadline = _utc_datetime(spec.deadline_utc)
    if deadline is None:
        raise HoldoutRunError("deadline must be an ISO-8601 UTC timestamp")
    if deadline <= datetime.now(timezone.utc):
        raise HoldoutRunError("deadline has already expired")
    if isinstance(spec.max_output_bytes, bool) or not isinstance(spec.max_output_bytes, int) or spec.max_output_bytes < 1:
        raise HoldoutRunError("a positive integer output size limit is required")
    if (
        type(spec.stop_conditions) is not tuple
        or not spec.stop_conditions
        or len(spec.stop_conditions) > 32
        or any(not isinstance(item, str) or not item.strip() or len(item) > 80 for item in spec.stop_conditions)
        or not REQUIRED_STOP_CONDITIONS.issubset(spec.stop_conditions)
        or len(set(spec.stop_conditions)) != len(spec.stop_conditions)
    ):
        raise HoldoutRunError("stop conditions must include all required stop conditions and be unique bounded strings")
    if spec.hash_profile != HASH_PROFILE:
        raise HoldoutRunError("unsupported frozen hash profile")


def _public_input(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise HoldoutRunError("case public input must be an object")
    try:
        encoded = json.dumps(value, ensure_ascii=False, allow_nan=False)
        copied = json.loads(encoded)
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise HoldoutRunError("case public input must be JSON serializable") from exc
    return copied


def execute_official_holdout(
    *,
    spec: HoldoutRunSpec,
    registry: HoldoutRegistry,
    data_plane: HoldoutDataPlane,
    candidate: CandidateRuntime,
    scorer: Scorer,
) -> dict[str, Any]:
    """Consume one registry reservation and append exactly one terminal result.

    The registry must atomically enforce single-use reservation. The candidate
    receives only each attempt's public input. The data-plane session is closed
    and its outputs sealed before the separately supplied scorer can see them.
    Any failure after reservation is terminally recorded as aborted; this
    function never retries a candidate call or releases the reservation.
    """
    _validate_spec(spec)
    actual_executor_sha256 = executor_bundle_sha256()
    if spec.executor_sha256 != actual_executor_sha256:
        raise HoldoutRunError("executor hash does not match the frozen run spec")
    candidate_sha256 = getattr(candidate, "candidate_sha256", None)
    image_digest = getattr(candidate, "image_digest", None)
    if candidate_sha256 != spec.candidate_sha256 or image_digest != spec.image_digest:
        raise HoldoutRunError("candidate runtime identity does not match the frozen run spec")
    candidate_output_limit = getattr(candidate, "max_output_bytes", None)
    if (
        isinstance(candidate_output_limit, bool)
        or not isinstance(candidate_output_limit, int)
        or candidate_output_limit != spec.max_output_bytes
    ):
        raise HoldoutRunError("candidate output limit does not match the frozen run spec")
    scorer_sha256 = getattr(scorer, "scorer_sha256", None)
    if scorer_sha256 != spec.scorer_sha256:
        raise HoldoutRunError("scorer hash does not match the frozen run spec")
    try:
        reservation = registry.reserve(spec)
    except BaseException as exc:
        raise HoldoutRunError("reservation outcome is unknown; reconcile by run id before retry") from exc
    event_id = getattr(reservation, "event_id", None)
    if not isinstance(event_id, str) or not event_id.strip():
        raise HoldoutRunError("reservation outcome is unknown; reconcile by run id before retry")
    terminal_event_id = _terminal_event_id(spec)

    attempted = 0
    spent = Decimal("0")
    max_budget = _decimal_amount(spec.max_budget_usd)
    assert max_budget is not None
    cost_status = "unknown"
    terminal_append_started = False
    data_session: HoldoutDataSession | None = None
    sealed_outputs: SealedHoldoutOutputs | None = None
    data_session_sealed = False
    seal_outcome_unknown = False
    score_outcome_unknown = False
    try:
        if reservation.spec_sha256 != canonical_run_spec_sha256(spec):
            raise HoldoutRunError("reservation does not bind the frozen run spec")
        _validate_reservation_snapshot(spec, reservation)
        session_capability = getattr(reservation, "session_capability", None)
        if not isinstance(session_capability, HoldoutSessionCapability):
            raise HoldoutRunError("registry reservation omitted its one-time data capability")
        runtime_identity = HoldoutRuntimeIdentity(
            run_id=spec.run_id,
            reservation_event_id=event_id,
            candidate_sha256=spec.candidate_sha256,
            image_digest=spec.image_digest,
            dataset_sha256=spec.dataset_sha256,
            scorer_sha256=spec.scorer_sha256,
            executor_sha256=spec.executor_sha256,
        )
        session_open_failed = False
        try:
            data_session = data_plane.open_session(
                session_capability.reveal_for_custodian(), runtime_identity, spec
            )
        except BaseException:
            # Do not retain the transport exception: it may echo request credentials.
            session_open_failed = True
        if session_open_failed:
            raise RuntimeError("data custodian session open failed")
        if data_session is None:
            raise HoldoutRunError("data custodian did not open a holdout session")

        outputs: list[tuple[str, dict[str, Any], dict[str, int | float]]] = []
        seen_attempt_ids: set[str] = set()
        total_input_tokens = 0
        total_output_tokens = 0
        while True:
            attempt = data_session.next_attempt()
            if attempt is None:
                break
            if attempted >= spec.max_cases:
                raise HoldoutRunError("data custodian exceeded the predeclared case limit")
            if (
                not isinstance(attempt, PublicHoldoutAttempt)
                or not isinstance(attempt.attempt_id, str)
                or not attempt.attempt_id.strip()
                or attempt.attempt_id in seen_attempt_ids
            ):
                raise HoldoutRunError("data custodian returned an invalid or duplicate attempt")
            seen_attempt_ids.add(attempt.attempt_id)
            attempted += 1
            attempt_id = attempt.attempt_id
            deadline = _utc_datetime(spec.deadline_utc)
            if deadline is None or deadline <= datetime.now(timezone.utc):
                raise HoldoutRunError("deadline expired before candidate execution")
            cost_status = "unknown"
            remaining_budget = _format_amount(max_budget - spent)
            raw_result = candidate.execute(
                attempt_id,
                _public_input(attempt.public_input),
                spec.deadline_utc,
                remaining_budget,
            )
            if deadline <= datetime.now(timezone.utc):
                raise HoldoutRunError("candidate execution exceeded the deadline")
            if not isinstance(raw_result, dict) or not isinstance(raw_result.get("output"), dict):
                raise HoldoutRunError("candidate returned an invalid result")
            cost = _decimal_amount(raw_result.get("cost_usd"))
            input_tokens = raw_result.get("input_tokens")
            output_tokens = raw_result.get("output_tokens")
            latency = raw_result.get("latency_ms")
            if cost is None or cost < 0:
                raise HoldoutRunError("candidate returned invalid cost")
            spent += cost
            cost_status = "known"
            if any(isinstance(count, bool) or not isinstance(count, int) or count < 0 for count in (input_tokens, output_tokens)):
                raise HoldoutRunError("candidate token usage is missing or invalid")
            if isinstance(latency, bool) or not isinstance(latency, int) or latency < 0:
                raise HoldoutRunError("candidate returned invalid latency")
            try:
                encoded_output = json.dumps(raw_result["output"], ensure_ascii=False, allow_nan=False).encode("utf-8")
            except (TypeError, ValueError) as exc:
                raise HoldoutRunError("candidate output is not finite JSON") from exc
            if len(encoded_output) > spec.max_output_bytes:
                raise HoldoutRunError("candidate output size exceeded the predeclared limit")
            if spent > max_budget:
                raise HoldoutRunError("predeclared budget exceeded")
            safe_output = json.loads(encoded_output)
            data_session.record_output(attempt_id, safe_output)
            total_input_tokens += input_tokens
            total_output_tokens += output_tokens
            outputs.append((
                attempt_id,
                safe_output,
                {
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "cost_usd": _format_amount(cost),
                    "latency_ms": latency,
                },
            ))

        if not outputs:
            raise HoldoutRunError("reserved holdout is empty")
        close_response_lost = False
        try:
            sealed_outputs = data_session.close_and_seal()
        except BaseException:
            close_response_lost = True
        if close_response_lost:
            reconciliation_failed = False
            try:
                sealed_outputs = data_plane.reconcile_seal(event_id, runtime_identity, spec)
            except BaseException:
                reconciliation_failed = True
            if reconciliation_failed:
                seal_outcome_unknown = True
                raise RuntimeError("custodian seal reconciliation unavailable")
            if sealed_outputs is None:
                raise RuntimeError("custodian confirms no durable seal exists")
        if not isinstance(sealed_outputs, SealedHoldoutOutputs):
            seal_outcome_unknown = True
            raise RuntimeError("custodian seal response is invalid")
        data_session_sealed = True
        expected_output_hash = _canonical_hash([
            {"attempt_id": attempt_id, "output": output}
            for attempt_id, output, _usage in outputs
        ])
        expected_attempt_ids = tuple(attempt_id for attempt_id, _output, _usage in outputs)
        if (
            not isinstance(sealed_outputs, SealedHoldoutOutputs)
            or not isinstance(sealed_outputs.seal_id, str)
            or not sealed_outputs.seal_id.strip()
            or sealed_outputs.run_id != spec.run_id
            or sealed_outputs.reservation_event_id != event_id
            or sealed_outputs.frozen_spec_sha256 != canonical_run_spec_sha256(spec)
            or sealed_outputs.candidate_sha256 != spec.candidate_sha256
            or sealed_outputs.image_digest != spec.image_digest
            or sealed_outputs.dataset_sha256 != spec.dataset_sha256
            or sealed_outputs.scorer_sha256 != spec.scorer_sha256
            or sealed_outputs.attempt_ids != expected_attempt_ids
            or len(sealed_outputs.outputs) != len(expected_attempt_ids)
            or sealed_outputs.output_sha256 != expected_output_hash
            or tuple(output.attempt_id for output in sealed_outputs.outputs) != expected_attempt_ids
            or _canonical_hash([
                {"attempt_id": output.attempt_id, "output": output.output}
                for output in sealed_outputs.outputs
            ]) != expected_output_hash
        ):
            raise HoldoutRunError("sealed outputs do not match the candidate output ledger")

        score_response_lost = False
        try:
            scores = scorer.score_sealed(sealed_outputs)
        except BaseException:
            score_response_lost = True
        if score_response_lost:
            reconciliation_failed = False
            try:
                scores = scorer.reconcile_sealed(
                    sealed_outputs.seal_id, spec.scorer_sha256, sealed_outputs.output_sha256
                )
            except BaseException:
                reconciliation_failed = True
            if reconciliation_failed:
                score_outcome_unknown = True
                raise RuntimeError("scorer result reconciliation unavailable")
            if scores is None:
                retry_failed = False
                try:
                    scores = scorer.score_sealed(sealed_outputs)
                except BaseException:
                    retry_failed = True
                if retry_failed:
                    reconciliation_failed = False
                    try:
                        scores = scorer.reconcile_sealed(
                            sealed_outputs.seal_id, spec.scorer_sha256, sealed_outputs.output_sha256
                        )
                    except BaseException:
                        reconciliation_failed = True
                    if reconciliation_failed:
                        score_outcome_unknown = True
                        raise RuntimeError("scorer result reconciliation unavailable")
                    if scores is None:
                        raise RuntimeError("scorer confirmed no result after idempotent retry")
        if not isinstance(scores, tuple) or len(scores) != len(expected_attempt_ids):
            raise HoldoutRunError("scorer returned an incomplete result set")
        score_by_attempt: dict[str, bool] = {}
        for score in scores:
            if (
                not isinstance(score, ScoredAttempt)
                or score.attempt_id not in seen_attempt_ids
                or score.attempt_id in score_by_attempt
                or not isinstance(score.passed, bool)
            ):
                raise HoldoutRunError("scorer returned invalid, duplicate, or unknown attempt results")
            score_by_attempt[score.attempt_id] = score.passed
        if set(score_by_attempt) != seen_attempt_ids:
            raise HoldoutRunError("scorer result set does not match the sealed attempts")
        task_results = []
        for attempt_id, _output, usage in outputs:
            task_results.append({
                "case_id": attempt_id,
                "passed": score_by_attempt[attempt_id],
                "token_usage": {"input_tokens": usage["input_tokens"], "output_tokens": usage["output_tokens"]},
                "cost_usd": usage["cost_usd"],
                "latency_ms": usage["latency_ms"],
            })

        output_hash = sealed_outputs.output_sha256
        passed_tasks = sum(result["passed"] for result in task_results)
        pass_rate_bps = passed_tasks * 10_000 // len(task_results)
        quality_passed = (
            len(task_results) >= spec.minimum_task_count
            and passed_tasks * 10_000 >= spec.minimum_pass_rate_bps * len(task_results)
            and (not spec.require_all_tasks_pass or passed_tasks == len(task_results))
        )
        quality_criteria = {
            "minimum_task_count": spec.minimum_task_count,
            "minimum_pass_rate_bps": spec.minimum_pass_rate_bps,
            "require_all_tasks_pass": spec.require_all_tasks_pass,
        }
        token_usage = {
            "input_tokens": total_input_tokens,
            "output_tokens": total_output_tokens,
        }
        cost_usd = _format_amount(spent)
        metrics = {
            "task_count": len(task_results),
            "passed_tasks": passed_tasks,
            "pass_rate_bps": pass_rate_bps,
            "quality_criteria": quality_criteria,
            "token_usage": token_usage,
            "cost_usd": cost_usd,
        }
        metrics_sha256 = _canonical_hash(metrics)
        executed_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
        report = {
            "schema": OFFICIAL_HOLDOUT_RESULT_SCHEMA,
            "hash_profile": HASH_PROFILE,
            "decision": "completed",
            "holdout_version": spec.holdout_version,
            "run_id": spec.run_id,
            "authorization_event_id": spec.authorization_event_id,
            "frozen_spec": spec.__dict__,
            "frozen_spec_sha256": canonical_run_spec_sha256(spec),
            "reservation_event_id": event_id,
            "terminal_event_id": terminal_event_id,
            "candidate_sha256": spec.candidate_sha256,
            "image_digest": spec.image_digest,
            "dataset_sha256": spec.dataset_sha256,
            "scorer_sha256": spec.scorer_sha256,
            "executor_sha256": spec.executor_sha256,
            "executed_at": executed_at,
            "task_count": len(task_results),
            "case_limit": spec.max_cases,
            "deadline_utc": spec.deadline_utc,
            "stop_conditions": list(spec.stop_conditions),
            "passed_tasks": passed_tasks,
            "pass_rate_bps": pass_rate_bps,
            "quality_criteria": quality_criteria,
            "metrics": metrics,
            "metrics_sha256": metrics_sha256,
            "quality_decision": "passed" if quality_passed else "failed",
            "task_results": task_results,
            "token_usage": token_usage,
            "max_output_bytes": spec.max_output_bytes,
            "output_seal_id": sealed_outputs.seal_id,
            "output_sha256": output_hash,
            "results_sha256": output_hash,
            "cost_usd": cost_usd,
            "cost_status": "known",
            "budget_usd": _format_amount(max_budget),
            "usage_status": "complete",
        }
        report["report_sha256"] = _report_sha256(report)
        terminal_append_started = True
        registry.append_terminal(event_id, terminal_event_id, "consumed", report)
        return report
    except BaseException as exc:
        if terminal_append_started:
            raise HoldoutRunError("terminal outcome is unknown; reconcile the registry before any new run") from exc
        if seal_outcome_unknown:
            raise HoldoutRunError("seal outcome is unknown; reconcile by reservation id before any new run") from None
        if score_outcome_unknown:
            raise HoldoutRunError("score outcome is unknown; reconcile the same seal before any new run") from None
        if not data_session_sealed:
            try:
                # Key revocation by reservation id also covers a lost open_session
                # response where no local session handle was returned.
                data_plane.abort_session(event_id)
            except BaseException as abort_error:
                raise HoldoutRunError(
                    "data-session revocation outcome is unknown; reconcile before any new run"
                ) from abort_error
        abort_report = {
            "schema": OFFICIAL_HOLDOUT_RESULT_SCHEMA,
            "hash_profile": HASH_PROFILE,
            "decision": "aborted",
            "holdout_version": spec.holdout_version,
            "run_id": spec.run_id,
            "authorization_event_id": spec.authorization_event_id,
            "frozen_spec": spec.__dict__,
            "frozen_spec_sha256": canonical_run_spec_sha256(spec),
            "reservation_event_id": event_id,
            "terminal_event_id": terminal_event_id,
            "candidate_sha256": spec.candidate_sha256,
            "image_digest": spec.image_digest,
            "dataset_sha256": spec.dataset_sha256,
            "scorer_sha256": spec.scorer_sha256,
            "executor_sha256": spec.executor_sha256,
            "attempted_tasks": attempted,
            "case_limit": spec.max_cases,
            "deadline_utc": spec.deadline_utc,
            "stop_conditions": list(spec.stop_conditions),
            "quality_criteria": {
                "minimum_task_count": spec.minimum_task_count,
                "minimum_pass_rate_bps": spec.minimum_pass_rate_bps,
                "require_all_tasks_pass": spec.require_all_tasks_pass,
            },
            "max_output_bytes": spec.max_output_bytes,
            "cost_status": cost_status,
            "budget_usd": _format_amount(max_budget),
            "usage_status": "unknown",
            "failure_type": type(exc).__name__,
        }
        if cost_status == "known":
            abort_report["cost_usd"] = _format_amount(spent)
        if isinstance(sealed_outputs, SealedHoldoutOutputs):
            seal_id = sealed_outputs.seal_id
            output_hash = sealed_outputs.output_sha256
            if isinstance(seal_id, str) and seal_id.strip():
                abort_report["output_seal_id"] = seal_id
            if isinstance(output_hash, str) and SHA256.fullmatch(output_hash):
                abort_report["output_sha256"] = output_hash
                abort_report["results_sha256"] = output_hash
        abort_report["report_sha256"] = _report_sha256(abort_report)
        try:
            registry.append_terminal(event_id, terminal_event_id, "aborted", abort_report)
        except BaseException as registry_error:
            raise HoldoutRunError(
                "terminal outcome is unknown; reconcile by run id before any new attempt"
            ) from registry_error
        if isinstance(exc, HoldoutRunError):
            raise
        raise HoldoutRunError("run aborted after reservation") from exc
