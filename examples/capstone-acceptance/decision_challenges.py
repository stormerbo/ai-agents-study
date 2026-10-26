"""Pure reducer for an already verified Stage 5 decision-log prefix.

This module does not authenticate people, verify append receipts, or fetch
identity/policy sources. The caller must provide a contiguous receipt prefix
whose signatures, authority, freshness, and frozen policy have already been
verified. `current_trigger_state` must likewise come from a separately
authenticated, policy-bounded source snapshot.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Literal


SHA256 = re.compile(r"[0-9a-f]{64}\Z")
Target = tuple[str, str, str]
ChallengeState = Literal["active", "resolved", "unverified"]
TargetState = Literal["challenged", "clear", "unverified"]
ChallengeGateState = Literal["blocked", "clear", "unverified"]


@dataclass(frozen=True)
class VerifiedDecisionEvent:
    sequence: int
    event_id: str
    event_sha256: str
    payload: dict[str, Any]


@dataclass(frozen=True)
class FreshTriggerSnapshot:
    """Authenticated current-state result, already checked against policy freshness."""

    environment_id: str
    decision_log_id: str
    decision_id: str
    receipt_sha256: str
    trigger_active: bool | None
    trigger_binding: tuple[str, ...]


@dataclass(frozen=True)
class ChallengeReduction:
    challenge_states: dict[str, ChallengeState]
    target_states: dict[Target, TargetState]
    active_challenge_ids: tuple[str, ...]
    unverified_challenge_ids: tuple[str, ...]


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _trigger_binding(trigger: dict[str, Any]) -> tuple[str, ...]:
    if trigger.get("kind") == "source-state":
        return ("source-state", trigger["source_id"])
    if trigger.get("kind") == "policy":
        return ("policy", trigger["policy_id"], trigger["rule_id"])
    raise ValueError("invalid challenge trigger binding")


def _target(event: dict[str, Any]) -> Target:
    record_type = event.get("target_record_type")
    record_id = event.get("target_record_id")
    digest = event.get("target_record_sha256")
    if not isinstance(record_type, str) or record_type not in {"acceptance", "release"} or not _nonempty(record_id):
        raise ValueError("invalid challenge target")
    if not isinstance(digest, str) or not SHA256.fullmatch(digest):
        raise ValueError("invalid challenge target digest")
    return (record_type, record_id, digest)


def replay_verified_challenges(
    decision_log_id: str,
    verified_receipt_prefix: list[VerifiedDecisionEvent] | tuple[VerifiedDecisionEvent, ...],
    *,
    environment_id: str,
    current_trigger_state: dict[str, FreshTriggerSnapshot | None],
    verified_trigger_evidence_digests: dict[str, str],
    verified_resolution_evidence_digests: dict[str, str],
) -> ChallengeReduction:
    """Derive per-challenge/per-target state deterministically from a log prefix.

    Each snapshot and each trigger evidence digest are already authenticated,
    semantically verified, and freshness-checked by the caller. The evidence
    maps must contain exactly one verified digest for every v2 challenge and
    resolution. This reducer rejects v1 challenge records and does not itself authenticate
    monitor keys, validate probe journals, or fetch sources. A resolved
    challenge additionally requires the snapshot's decision id and receipt
    digest to match those referenced by its resolution event. A challenge is
    never cleared merely because its source advanced; it also needs its own
    valid resolution event.
    """
    if not _nonempty(decision_log_id):
        raise ValueError("invalid decision log id")
    if not _nonempty(environment_id):
        raise ValueError("invalid environment id")
    if not isinstance(verified_receipt_prefix, (list, tuple)):
        raise ValueError("invalid verified receipt prefix")
    if not isinstance(current_trigger_state, dict):
        raise ValueError("invalid current trigger state")
    if not isinstance(verified_trigger_evidence_digests, dict):
        raise ValueError("invalid verified trigger evidence digests")
    if not isinstance(verified_resolution_evidence_digests, dict):
        raise ValueError("invalid verified resolution evidence digests")

    challenges: dict[str, tuple[Target, str, str, tuple[str, ...]]] = {}
    resolutions: dict[str, VerifiedDecisionEvent] = {}
    event_ids: set[str] = set()
    resolution_ids: set[str] = set()
    expected_resolution_evidence_digests: dict[str, str] = {}
    target_record_digests: dict[tuple[str, str], str] = {}

    for expected_sequence, entry in enumerate(verified_receipt_prefix, start=1):
        if not isinstance(entry, VerifiedDecisionEvent):
            raise ValueError("receipt prefix contains an unverified event")
        if type(entry.sequence) is not int or entry.sequence != expected_sequence:
            raise ValueError("verified receipt prefix sequence is not contiguous")
        if not _nonempty(entry.event_id) or entry.event_id in event_ids:
            raise ValueError("duplicate or missing event id")
        event_ids.add(entry.event_id)
        if not isinstance(entry.event_sha256, str) or not SHA256.fullmatch(entry.event_sha256):
            raise ValueError("invalid verified event digest")
        if not isinstance(entry.payload, dict) or not isinstance(entry.payload.get("event"), dict):
            raise ValueError("invalid decision event payload")

        payload = entry.payload
        event = payload["event"]
        schema = payload.get("schema")
        if schema == "stage5-decision-challenge-v2":
            challenge_id = event.get("challenge_id")
            trigger = event.get("trigger")
            evidence_digest = event.get("trigger_evidence_sha256")
            valid_source_trigger = (
                isinstance(trigger, dict)
                and trigger.get("kind") == "source-state"
                and _nonempty(trigger.get("source_id"))
                and type(trigger.get("source_sequence")) is int
                and 0 <= trigger["source_sequence"] <= 9_007_199_254_740_991
                and isinstance(trigger.get("source_head_sha256"), str)
                and SHA256.fullmatch(trigger["source_head_sha256"])
            )
            valid_policy_trigger = (
                isinstance(trigger, dict)
                and trigger.get("kind") == "policy"
                and _nonempty(trigger.get("policy_id"))
                and _nonempty(trigger.get("rule_id"))
            )
            if (
                event.get("event_type") != "decision-challenged"
                or not _nonempty(challenge_id)
                or not isinstance(evidence_digest, str)
                or not SHA256.fullmatch(evidence_digest)
                or not (valid_source_trigger or valid_policy_trigger)
            ):
                raise ValueError("invalid v2 challenge event")
            if challenge_id in challenges:
                raise ValueError("duplicate challenge id")
            target = _target(event)
            record_identity = (target[0], target[1])
            known_digest = target_record_digests.get(record_identity)
            if known_digest is not None and known_digest != target[2]:
                raise ValueError("target record digest changed within decision log")
            target_record_digests[record_identity] = target[2]
            challenges[challenge_id] = (
                target,
                entry.event_sha256,
                evidence_digest,
                _trigger_binding(trigger),
            )
        elif schema in {
            "stage5-decision-challenge-v1",
            "stage5-decision-challenge-resolved-v1",
        }:
            raise ValueError("unsupported challenge schema: official reducer requires v2")
        elif schema == "stage5-decision-challenge-resolved-v2":
            challenge_id = event.get("challenge_id")
            if event.get("event_type") != "decision-challenge-resolved" or not _nonempty(challenge_id):
                raise ValueError("invalid resolution event")
            if challenge_id not in challenges:
                raise ValueError("resolution precedes or references unknown challenge")
            if challenge_id in resolutions:
                raise ValueError("duplicate challenge resolution")
            resolution_id = event.get("resolution_id")
            if not _nonempty(resolution_id) or resolution_id in resolution_ids:
                raise ValueError("duplicate or missing resolution id")
            target, challenge_digest, _, _ = challenges[challenge_id]
            if (
                _target(event) != target
                or event.get("challenge_event_sha256") != challenge_digest
                or not _nonempty(event.get("fresh_decision_id"))
                or not isinstance(event.get("fresh_decision_receipt_sha256"), str)
                or not SHA256.fullmatch(event["fresh_decision_receipt_sha256"])
                or not isinstance(event.get("resolution_evidence_sha256"), str)
                or not SHA256.fullmatch(event["resolution_evidence_sha256"])
            ):
                raise ValueError("resolution does not match challenge target or evidence")
            resolution_ids.add(resolution_id)
            expected_resolution_evidence_digests[resolution_id] = event[
                "resolution_evidence_sha256"
            ]
            resolutions[challenge_id] = entry
        else:
            if event.get("event_type") in {
                "decision-challenged",
                "decision-challenge-resolved",
            }:
                raise ValueError("unsupported challenge schema for challenge event")
            # The decision log may contain unrelated event types. They remain
            # in the verified prefix but do not affect the challenge reducer.
            continue

    if set(current_trigger_state) - set(challenges):
        raise ValueError("trigger state references an unknown challenge")
    if set(verified_trigger_evidence_digests) != set(challenges):
        raise ValueError("verified trigger evidence is missing or contains unknown challenges")
    for challenge_id, (_, _, evidence_digest, _) in challenges.items():
        verified_digest = verified_trigger_evidence_digests.get(challenge_id)
        if (
            not isinstance(verified_digest, str)
            or not SHA256.fullmatch(verified_digest)
            or verified_digest != evidence_digest
        ):
            raise ValueError("verified trigger evidence digest does not match challenge")
    if set(verified_resolution_evidence_digests) != set(expected_resolution_evidence_digests):
        raise ValueError("verified resolution evidence is missing or contains unknown resolutions")
    for resolution_id, evidence_digest in expected_resolution_evidence_digests.items():
        verified_digest = verified_resolution_evidence_digests.get(resolution_id)
        if (
            not isinstance(verified_digest, str)
            or not SHA256.fullmatch(verified_digest)
            or verified_digest != evidence_digest
        ):
            raise ValueError("verified resolution evidence digest does not match resolution")
    if any(
        value is not None and not isinstance(value, FreshTriggerSnapshot)
        for value in current_trigger_state.values()
    ):
        raise ValueError("invalid trigger state value")
    for snapshot in current_trigger_state.values():
        if snapshot is not None and (
            not _nonempty(snapshot.environment_id)
            or not _nonempty(snapshot.decision_log_id)
            or not _nonempty(snapshot.decision_id)
            or not isinstance(snapshot.receipt_sha256, str)
            or not SHA256.fullmatch(snapshot.receipt_sha256)
            or (snapshot.trigger_active is not None and type(snapshot.trigger_active) is not bool)
            or not isinstance(snapshot.trigger_binding, tuple)
            or len(snapshot.trigger_binding) not in {2, 3}
            or any(not _nonempty(part) for part in snapshot.trigger_binding)
            or snapshot.trigger_binding[0] not in {"source-state", "policy"}
            or (snapshot.trigger_binding[0] == "source-state" and len(snapshot.trigger_binding) != 2)
            or (snapshot.trigger_binding[0] == "policy" and len(snapshot.trigger_binding) != 3)
        ):
            raise ValueError("invalid trigger state value")

    states: dict[str, ChallengeState] = {}
    target_challenges: dict[Target, list[ChallengeState]] = {}
    for challenge_id, (target, _, _, expected_trigger_binding) in challenges.items():
        snapshot = current_trigger_state.get(challenge_id)
        if snapshot is not None and (
            snapshot.environment_id != environment_id
            or snapshot.decision_log_id != decision_log_id
        ):
            raise ValueError("fresh trigger snapshot scope does not match decision log")
        if snapshot is not None and snapshot.trigger_binding != expected_trigger_binding:
            raise ValueError("fresh trigger snapshot does not match challenge trigger binding")
        if challenge_id not in resolutions:
            state: ChallengeState = "active"
        elif snapshot is None:
            state = "unverified"
        else:
            resolution_event = resolutions[challenge_id].payload["event"]
            if (
                snapshot.decision_id != resolution_event["fresh_decision_id"]
                or snapshot.receipt_sha256 != resolution_event["fresh_decision_receipt_sha256"]
            ):
                raise ValueError("resolution does not bind the fresh decision receipt")
        if challenge_id in resolutions and snapshot is not None and snapshot.trigger_active is None:
            state = "unverified"
        elif challenge_id in resolutions and snapshot is not None and snapshot.trigger_active is True:
            raise ValueError("resolution claims a trigger that remains active")
        elif challenge_id in resolutions and snapshot is not None:
            state = "resolved"
        states[challenge_id] = state
        target_challenges.setdefault(target, []).append(state)

    target_states: dict[Target, TargetState] = {}
    for target, challenge_states in target_challenges.items():
        if "active" in challenge_states:
            target_states[target] = "challenged"
        elif "unverified" in challenge_states:
            target_states[target] = "unverified"
        else:
            target_states[target] = "clear"

    active = tuple(sorted(key for key, value in states.items() if value == "active"))
    unverified = tuple(sorted(key for key, value in states.items() if value == "unverified"))
    return ChallengeReduction(states, target_states, active, unverified)


def challenge_gate_for_target(
    reduction: ChallengeReduction,
    target: Target,
) -> ChallengeGateState:
    """Return only the challenge dimension of a release decision.

    `clear` means no active or unverifiable challenge exists for this exact
    target in the complete verified log prefix. It does not authorize release;
    every other governance, integrity, freshness, and deployment gate remains
    the responsibility of its own verifier.
    """
    if not isinstance(reduction, ChallengeReduction):
        raise ValueError("invalid challenge reduction")
    if (
        not isinstance(target, tuple)
        or len(target) != 3
        or not isinstance(target[0], str)
        or target[0] not in {"acceptance", "release"}
        or not _nonempty(target[1])
        or not isinstance(target[2], str)
        or not SHA256.fullmatch(target[2])
    ):
        raise ValueError("invalid challenge gate target")

    state = reduction.target_states.get(target)
    if state is None or state == "clear":
        return "clear"
    if state == "challenged":
        return "blocked"
    if state == "unverified":
        return "unverified"
    raise ValueError("invalid derived challenge state")
