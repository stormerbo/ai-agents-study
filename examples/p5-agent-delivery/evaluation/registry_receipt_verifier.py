"""Offline reference verifier for Stage 5 registry receipt chains.

This verifies signatures and event integrity using caller-supplied trust
configuration. It does not fetch current key status, persist sequence floors,
or establish that an anchor service is administratively independent.
"""

from __future__ import annotations

import base64
from datetime import datetime, timedelta, timezone
import hashlib
import re
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from canonicalization import canonical_json_bytes, canonical_sha256


HASH_PROFILE = "jcs-rfc8785-v1"
RECEIPT_PROFILE = "ed25519-jcs-receipt-v1"
STATUS_PROFILE = "ed25519-jcs-key-status-v1"
ANCHOR_PROFILE = "ed25519-jcs-precompromise-anchor-v1"
GENESIS_HASH = "0" * 64
HEX_SHA256 = re.compile(r"^[a-f0-9]{64}$")
BASE64URL_32 = re.compile(r"^[A-Za-z0-9_-]{43}$")
BASE64URL_64 = re.compile(r"^[A-Za-z0-9_-]{86}$")
UTC_TIMESTAMP = re.compile(r"^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.(\d{1,6}))?Z$")

EVENT_FIELDS = {
    "schema", "hash_profile", "run_id", "sequence", "event_id", "previous_event_hash",
    "event_type", "actor_subject_id", "actor_role", "registry_recorded_at",
    "actor_asserted_at", "payload_sha256", "payload", "event_hash",
}
EVENT_PREIMAGE_FIELDS = (
    "schema", "hash_profile", "run_id", "sequence", "event_id", "previous_event_hash",
    "event_type", "actor_subject_id", "actor_role", "registry_recorded_at",
    "actor_asserted_at", "payload_sha256",
)
RECEIPT_FIELDS = {
    "schema", "hash_profile", "environment_id", "log_id", "run_id", "sequence",
    "event_id", "previous_event_hash", "event_hash", "registry_recorded_at",
    "signature_profile", "signature_algorithm", "key_id", "signature",
}
ANCHOR_FIELDS = {
    "schema", "anchor_id", "environment_id", "log_id", "run_id", "sequence",
    "event_id", "event_hash", "key_id", "receipt_sha256", "anchor_recorded_at_utc",
    "anchor_authority_id", "anchor_key_id", "signature_algorithm", "signature_profile", "signature",
}
WITNESS_PROFILE = "ed25519-jcs-witness-receipt-v1"
WITNESS_FIELDS = {
    "schema", "hash_profile", "witness_id", "authority_id", "environment_id", "log_id", "run_id",
    "authority_sequence", "authority_event_id", "authority_event_hash", "authority_entry_sha256",
    "witness_sequence", "previous_witness_receipt_sha256", "observed_at_utc", "key_id",
    "signature_algorithm", "signature_profile", "signature",
}


def _fail(message: str) -> None:
    raise ValueError(f"Registry receipt verification failed: {message}")


def _exact_fields(value: Any, expected: set[str], label: str) -> None:
    if not isinstance(value, dict) or set(value) != expected:
        _fail(f"{label} has missing or unknown fields")


def _decode_base64url(value: Any, expected_bytes: int, label: str) -> bytes:
    pattern = BASE64URL_32 if expected_bytes == 32 else BASE64URL_64
    if not isinstance(value, str) or not pattern.fullmatch(value):
        _fail(f"{label} is not canonical unpadded base64url")
    try:
        decoded = base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
    except (ValueError, base64.binascii.Error) as exc:
        raise ValueError(f"{label} is not valid base64url") from exc
    if len(decoded) != expected_bytes or base64.urlsafe_b64encode(decoded).rstrip(b"=").decode("ascii") != value:
        _fail(f"{label} has invalid encoding or length")
    return decoded


def _timestamp(value: Any, label: str) -> datetime:
    if not isinstance(value, str):
        _fail(f"{label} is not a UTC timestamp")
    match = UTC_TIMESTAMP.fullmatch(value)
    if not match:
        _fail(f"{label} is not a UTC timestamp")
    year, month, day, hour, minute, second = (int(part) for part in match.groups()[:6])
    fraction = match.group(7) or ""
    if year < 1970:
        _fail(f"{label} is outside the supported timestamp range")
    try:
        microseconds = int(fraction.ljust(6, "0")) if fraction else 0
        return datetime(year, month, day, hour, minute, second, microseconds, tzinfo=timezone.utc)
    except ValueError as exc:
        raise ValueError(f"{label} is not a real UTC calendar timestamp") from exc


def _verify_ed25519(public_key: bytes, signature: bytes, message: bytes, label: str) -> None:
    try:
        Ed25519PublicKey.from_public_bytes(public_key).verify(signature, message)
    except (InvalidSignature, ValueError) as exc:
        raise ValueError(f"{label} signature is invalid") from exc


def _verify_root_signed_payload(
    payload: dict,
    detached_signature: Any,
    trusted_root: Any,
    expected_profile: str,
    expected_digest: str | None = None,
) -> str:
    if not isinstance(trusted_root, dict) or set(trusted_root) != {"key_id", "public_key", "fingerprint_sha256"}:
        _fail("external trusted root configuration is missing or malformed")
    _exact_fields(detached_signature, {"schema", "root_key_id", "profile", "signature"}, "root signature")
    if detached_signature["schema"] != "stage5-trust-root-signature-v1":
        _fail("unsupported root signature schema")
    if detached_signature["profile"] != expected_profile:
        _fail("root signature profile does not match payload type")
    if detached_signature["root_key_id"] != trusted_root["key_id"]:
        _fail("root key id is not pinned by verifier configuration")
    public_key = _decode_base64url(trusted_root["public_key"], 32, "trusted root public key")
    fingerprint = trusted_root["fingerprint_sha256"]
    if not isinstance(fingerprint, str) or not HEX_SHA256.fullmatch(fingerprint):
        _fail("release-pinned root fingerprint is invalid")
    if hashlib.sha256(public_key).hexdigest() != fingerprint:
        _fail("trusted root key fingerprint mismatch")
    payload_bytes = canonical_json_bytes(payload)
    digest = hashlib.sha256(payload_bytes).hexdigest()
    if expected_digest is not None and digest != expected_digest:
        _fail("signed payload digest does not match frozen digest")
    signature = _decode_base64url(detached_signature["signature"], 64, "root signature")
    _verify_ed25519(public_key, signature, payload_bytes, "root")
    return digest


def _trust_bundle(bundle: Any, root_signature: Any, trusted_root: Any, expected_digest: str,
                  environment_id: str, log_id: str, signer_key_id: str) -> tuple[str, dict[str, dict]]:
    required = {"schema", "bundle_id", "hash_profile", "signature_profile", "environment_id", "log_id", "issued_at_utc", "keys"}
    _exact_fields(bundle, required, "trust bundle")
    if (bundle["schema"] != "stage5-receipt-trust-bundle-v1" or bundle["hash_profile"] != HASH_PROFILE
            or bundle["signature_profile"] != RECEIPT_PROFILE):
        _fail("unsupported trust bundle or cryptographic profile")
    if bundle["environment_id"] != environment_id or bundle["log_id"] != log_id:
        _fail("trust bundle scope does not match frozen environment/log")
    if not isinstance(bundle["bundle_id"], str) or not bundle["bundle_id"]:
        _fail("trust bundle id is missing")
    _timestamp(bundle["issued_at_utc"], "trust bundle issued_at_utc")
    digest = _verify_root_signed_payload(bundle, root_signature, trusted_root,
                                         "ed25519-jcs-trust-bundle-v1", expected_digest)
    if not isinstance(bundle["keys"], list) or not bundle["keys"]:
        _fail("trust bundle must contain signing keys")
    keys: dict[str, dict] = {}
    for key in bundle["keys"]:
        if not isinstance(key, dict):
            _fail("trust bundle key is not an object")
        state = key.get("state")
        fields = {"key_id", "algorithm", "public_key", "state", "not_before_utc", "not_after_utc"}
        if state == "retired":
            fields.add("retired_at_utc")
        elif state == "revoked":
            fields.update({"revoked_at_utc", "revocation_id"})
        _exact_fields(key, fields, "trust bundle key")
        key_id = key["key_id"]
        if not isinstance(key_id, str) or not key_id or key_id in keys:
            _fail("trust bundle has a missing or duplicate key id")
        if key["algorithm"] != "Ed25519" or state not in {"active", "retired", "revoked"}:
            _fail(f"trust bundle key {key_id} has an unsupported algorithm or state")
        _decode_base64url(key["public_key"], 32, f"key {key_id} public key")
        start = _timestamp(key["not_before_utc"], f"key {key_id} not_before_utc")
        end = _timestamp(key["not_after_utc"], f"key {key_id} not_after_utc")
        if start >= end:
            _fail(f"trust bundle key {key_id} has an invalid validity interval")
        if state == "retired":
            retired = _timestamp(key["retired_at_utc"], f"key {key_id} retired_at_utc")
            if retired < start or retired > end:
                _fail(f"trust bundle key {key_id} has invalid retirement time")
        if state == "revoked":
            revoked = _timestamp(key["revoked_at_utc"], f"key {key_id} revoked_at_utc")
            if revoked < start or not isinstance(key["revocation_id"], str) or not key["revocation_id"]:
                _fail(f"trust bundle key {key_id} has invalid revocation metadata")
        keys[key_id] = key
    if signer_key_id not in keys:
        _fail("permitted signer key is absent from frozen trust bundle")
    return digest, keys


def _verify_key_status(statement: Any, root_signature: Any, trusted_root: Any, bundle_digest: str,
                       environment_id: str, log_id: str, keys: dict[str, dict], current_time_utc: str,
                       max_freshness_seconds: int, minimum_sequence: int, clock_skew_seconds: int) -> tuple[dict, dict[str, dict], dict[str, datetime], int]:
    if not isinstance(statement, dict):
        _fail("key status statement is unavailable")
    version = statement.get("schema")
    fields = {"schema", "statement_id", "sequence", "bundle_sha256", "environment_id", "log_id", "issued_at_utc", "expires_at_utc", "revoked_keys"}
    if version not in {"stage5-key-status-statement-v1", "stage5-key-status-statement-v2"}:
        _fail("unsupported key status schema")
    _exact_fields(statement, fields, "key status statement")
    signature = "ed25519-jcs-key-status-v1"
    _verify_root_signed_payload(statement, root_signature, trusted_root, signature)
    if (statement["bundle_sha256"] != bundle_digest or statement["environment_id"] != environment_id
            or statement["log_id"] != log_id):
        _fail("key status scope or bundle digest mismatch")
    if type(max_freshness_seconds) is not int or max_freshness_seconds < 1:
        _fail("maximum key status freshness must be a positive integer")
    if type(minimum_sequence) is not int or minimum_sequence < 1:
        _fail("minimum key status sequence must be a positive integer")
    if type(clock_skew_seconds) is not int or not 0 <= clock_skew_seconds <= 300:
        _fail("clock skew must be an integer between zero and 300 seconds")
    sequence = statement["sequence"]
    if type(sequence) is not int or sequence < 1 or sequence > 9_007_199_254_740_991 or sequence < minimum_sequence:
        _fail("key status sequence rollback detected")
    now = _timestamp(current_time_utc, "verifier current time")
    issued = _timestamp(statement["issued_at_utc"], "key status issued_at_utc")
    expires = _timestamp(statement["expires_at_utc"], "key status expires_at_utc")
    freshness = timedelta(seconds=max_freshness_seconds)
    skew = timedelta(seconds=clock_skew_seconds)
    if issued > now + skew or now - issued > freshness or expires <= now or expires <= issued or expires - issued > freshness:
        _fail("key status is future dated, stale, expired, or exceeds freshness policy")
    if not isinstance(statement["revoked_keys"], list):
        _fail("revoked_keys must be an array")
    revoked: dict[str, dict] = {}
    boundaries: dict[str, datetime] = {}
    for entry in statement["revoked_keys"]:
        if not isinstance(entry, dict):
            _fail("revocation entry is not an object")
        base_fields = {"key_id", "revoked_at_utc", "revocation_id"}
        if version.endswith("v2"):
            reason = entry.get("reason")
            entry_fields = base_fields | {"reason"}
            if reason in {"compromise_suspected", "compromise_confirmed"}:
                entry_fields |= {"compromise_not_before_utc", "incident_review"}
            _exact_fields(entry, entry_fields, "v2 revocation entry")
        else:
            _exact_fields(entry, base_fields, "v1 revocation entry")
        key_id = entry["key_id"]
        if key_id not in keys or key_id in revoked:
            _fail("revocation references an unknown or duplicate key id")
        revoked_at = _timestamp(entry["revoked_at_utc"], f"key {key_id} revoked_at_utc")
        key_start = _timestamp(keys[key_id]["not_before_utc"], f"key {key_id} not_before_utc")
        if revoked_at < key_start:
            _fail("revocation predates key activation")
        if keys[key_id]["state"] == "revoked" and (
            keys[key_id]["revoked_at_utc"] != entry["revoked_at_utc"]
            or keys[key_id]["revocation_id"] != entry["revocation_id"]
        ):
            _fail("frozen trust bundle and current revocation statement conflict")
        if version.endswith("v2"):
            reason = entry["reason"]
            if reason not in {"routine", "compromise_suspected", "compromise_confirmed"}:
                _fail("unknown v2 revocation reason")
            if reason == "routine" and ("compromise_not_before_utc" in entry or "incident_review" in entry):
                _fail("routine revocation cannot provide a compromise exception")
            if reason != "routine":
                review = entry["incident_review"]
                _exact_fields(review, {"review_id", "record_sha256"}, "incident review reference")
                if not isinstance(review["review_id"], str) or not review["review_id"] or not HEX_SHA256.fullmatch(str(review["record_sha256"])):
                    _fail("incident review reference is invalid")
                boundary_value = entry["compromise_not_before_utc"]
                if boundary_value is not None:
                    boundary = _timestamp(boundary_value, f"key {key_id} compromise boundary")
                    key_end = _timestamp(keys[key_id]["not_after_utc"], f"key {key_id} not_after_utc")
                    if boundary < key_start or boundary > revoked_at or boundary > key_end:
                        _fail("compromise boundary is outside key activation and revocation interval")
                    boundaries[key_id] = boundary
        revoked[key_id] = entry
    for key_id, key in keys.items():
        if key["state"] == "revoked" and key_id not in revoked:
            _fail("revoked frozen key is absent from current key status")
    return statement, revoked, boundaries, sequence


def _verify_anchor(anchor: Any, entry: dict, trusted_anchor: Any, expected_scope: dict[str, str],
                   boundary: datetime, current_time: datetime, clock_skew_seconds: int) -> str:
    _exact_fields(anchor, ANCHOR_FIELDS, "pre-compromise anchor")
    if anchor["schema"] != "stage5-pre-compromise-anchor-v1" or anchor["signature_algorithm"] != "Ed25519" or anchor["signature_profile"] != ANCHOR_PROFILE:
        _fail("unsupported pre-compromise anchor schema or signature profile")
    if type(anchor["sequence"]) is not int or anchor["sequence"] < 1:
        _fail("anchor sequence must be a positive integer")
    if not isinstance(trusted_anchor, dict) or set(trusted_anchor) != {"authority_id", "key_id", "public_key", "fingerprint_sha256"}:
        _fail("external trusted anchor configuration is missing or malformed")
    if anchor["anchor_authority_id"] != trusted_anchor["authority_id"] or anchor["anchor_key_id"] != trusted_anchor["key_id"]:
        _fail("anchor authority/key id is not pinned by verifier configuration")
    for field, expected in expected_scope.items():
        if anchor[field] != expected:
            _fail("anchor scope does not match frozen chain")
    event, receipt = entry["event"], entry["receipt"]
    bindings = {
        "sequence": event["sequence"], "event_id": event["event_id"],
        "event_hash": event["event_hash"], "key_id": receipt["key_id"],
    }
    if any(anchor[field] != value for field, value in bindings.items()):
        _fail("anchor does not bind revoked-key event identity")
    if anchor["receipt_sha256"] != canonical_sha256({"event": event, "receipt": receipt}):
        _fail("anchor does not bind exact canonical event and receipt bytes")
    anchor_time = _timestamp(anchor["anchor_recorded_at_utc"], "anchor recorded time")
    event_time = _timestamp(event["registry_recorded_at"], "event recorded time")
    if anchor_time < event_time or anchor_time >= boundary:
        _fail("anchor time is not after event and strictly before compromise boundary")
    if anchor_time > current_time + timedelta(seconds=clock_skew_seconds):
        _fail("anchor timestamp is future dated")
    public_key = _decode_base64url(trusted_anchor["public_key"], 32, "trusted anchor public key")
    fingerprint = trusted_anchor["fingerprint_sha256"]
    if not isinstance(fingerprint, str) or not HEX_SHA256.fullmatch(fingerprint) or hashlib.sha256(public_key).hexdigest() != fingerprint:
        _fail("trusted anchor key fingerprint mismatch")
    signed = {key: value for key, value in anchor.items() if key != "signature"}
    _verify_ed25519(public_key, _decode_base64url(anchor["signature"], 64, "anchor signature"),
                    canonical_json_bytes(signed), "pre-compromise anchor")
    return anchor["anchor_id"]


def verify_dual_witness_receipt_chain(
    *, authority_entries: Any, witness_receipts: Any,
    run_id: str, environment_id: str, log_id: str,
    append_authority_domain_id: str, signing_key_custodian_domain_id: str,
    trusted_witness: Any, current_time_utc: str, clock_skew_seconds: int = 0,
) -> dict:
    """Verify a witness receipt chain against an authority chain already verified by the caller.

    This function proves local signature, exact-entry binding, and run-scoped
    predecessor consistency. It cannot prove independent service identity,
    latestness, actual log reads, retention, or organizational separation.
    """
    if not isinstance(authority_entries, list) or not authority_entries:
        _fail("dual-witness verification requires a non-empty authority chain")
    if not isinstance(witness_receipts, list) or len(witness_receipts) != len(authority_entries):
        _fail("witness receipts must cover every authority event exactly once")
    if any(not isinstance(value, str) or not value.strip() for value in (
        run_id, environment_id, log_id, append_authority_domain_id,
        signing_key_custodian_domain_id,
    )):
        _fail("frozen run identities and trust domains are required")
    expected_witness_fields = {
        "witness_id", "authority_id", "key_id", "public_key", "fingerprint_sha256",
    }
    _exact_fields(trusted_witness, expected_witness_fields, "trusted witness configuration")
    if any(not isinstance(trusted_witness.get(field), str) or not trusted_witness[field].strip()
           for field in ("witness_id", "authority_id", "key_id")):
        _fail("trusted witness identity fields are required")
    if trusted_witness["authority_id"] in {append_authority_domain_id, signing_key_custodian_domain_id}:
        _fail("witness authority must use an independent trust domain")
    if type(clock_skew_seconds) is not int or not 0 <= clock_skew_seconds <= 300:
        _fail("witness clock skew must be an integer between zero and 300 seconds")
    current_time = _timestamp(current_time_utc, "witness verifier current time")
    fingerprint = trusted_witness["fingerprint_sha256"]
    if not isinstance(fingerprint, str) or not HEX_SHA256.fullmatch(fingerprint):
        _fail("pinned witness fingerprint is invalid")
    witness_public_bytes = _decode_base64url(trusted_witness["public_key"], 32, "trusted witness public key")
    if hashlib.sha256(witness_public_bytes).hexdigest() != fingerprint:
        _fail("trusted witness key does not match pinned fingerprint")
    previous_digest = GENESIS_HASH
    previous_observed_at: datetime | None = None
    for index, (entry, witness_receipt) in enumerate(zip(authority_entries, witness_receipts, strict=True)):
        _exact_fields(entry, {"event", "receipt"}, f"authority entry {index}")
        event, authority_receipt = entry["event"], entry["receipt"]
        if not isinstance(event, dict) or not isinstance(authority_receipt, dict):
            _fail(f"authority entry {index} is malformed")
        _exact_fields(witness_receipt, WITNESS_FIELDS, f"witness receipt {index}")
        if witness_receipt["schema"] != "stage5-independent-witness-receipt-v1":
            _fail(f"witness receipt {index} has an unsupported schema")
        if witness_receipt["hash_profile"] != HASH_PROFILE:
            _fail(f"witness receipt {index} has an unsupported hash profile")
        if witness_receipt["signature_profile"] != WITNESS_PROFILE or witness_receipt["signature_algorithm"] != "Ed25519":
            _fail(f"witness receipt {index} has an unsupported signature profile")
        if (witness_receipt["witness_id"] != trusted_witness["witness_id"]
                or witness_receipt["authority_id"] != trusted_witness["authority_id"]
                or witness_receipt["key_id"] != trusted_witness["key_id"]):
            _fail(f"witness receipt {index} identity does not match pinned witness")
        if any(witness_receipt[field] != value for field, value in {
            "environment_id": environment_id, "log_id": log_id, "run_id": run_id,
        }.items()):
            _fail(f"witness receipt {index} scope does not match frozen run")
        if any(authority_receipt.get(field) != value for field, value in {
            "environment_id": environment_id, "log_id": log_id, "run_id": run_id,
        }.items()) or event.get("run_id") != run_id:
            _fail(f"authority entry {index} scope does not match frozen run")
        if (type(event.get("sequence")) is not int or event["sequence"] != index + 1
                or type(witness_receipt["authority_sequence"]) is not int
                or witness_receipt["authority_sequence"] != event["sequence"]
                or type(witness_receipt["witness_sequence"]) is not int
                or witness_receipt["witness_sequence"] != index + 1
                or witness_receipt["authority_event_id"] != event.get("event_id")
                or witness_receipt["authority_event_hash"] != event.get("event_hash")):
            _fail(f"witness receipt {index} does not bind the authority event or has a sequence gap")
        if (not isinstance(witness_receipt["authority_event_id"], str)
                or not witness_receipt["authority_event_id"]
                or not isinstance(witness_receipt["authority_event_hash"], str)
                or not HEX_SHA256.fullmatch(witness_receipt["authority_event_hash"])):
            _fail(f"witness receipt {index} event identity/hash is malformed")
        if witness_receipt["authority_entry_sha256"] != canonical_sha256(entry):
            _fail(f"witness receipt {index} does not bind the exact authority entry")
        if witness_receipt["previous_witness_receipt_sha256"] != previous_digest:
            _fail(f"witness receipt {index} predecessor breaks the witness chain")
        observed_at = _timestamp(witness_receipt["observed_at_utc"], f"witness receipt {index} observed_at_utc")
        event_at = _timestamp(event.get("registry_recorded_at"), f"authority event {index} recorded_at")
        if (observed_at < event_at or
                (previous_observed_at is not None and observed_at < previous_observed_at) or
                observed_at > current_time + timedelta(seconds=clock_skew_seconds)):
            _fail(f"witness receipt {index} observation time is invalid or out of order")
        signed = {field: witness_receipt[field] for field in WITNESS_FIELDS if field != "signature"}
        _verify_ed25519(
            witness_public_bytes,
            _decode_base64url(witness_receipt["signature"], 64, f"witness receipt {index} signature"),
            canonical_json_bytes(signed),
            f"witness receipt {index}",
        )
        previous_digest = canonical_sha256(witness_receipt)
        previous_observed_at = observed_at
    terminal = witness_receipts[-1]
    return {
        "verified": True,
        "witness_id": trusted_witness["witness_id"],
        "terminal_event_id": terminal["authority_event_id"],
        "terminal_witness_sequence": terminal["witness_sequence"],
        "terminal_witness_receipt_sha256": previous_digest,
    }


def verify_registry_status_snapshot(
    *, trust_bundle: Any, trust_bundle_root_signature: Any, trust_bundle_sha256: str,
    trusted_root: Any, environment_id: str, log_id: str, permitted_signer_key_id: str,
    key_status_statement: Any, key_status_root_signature: Any, current_time_utc: str,
    max_freshness_seconds: int, minimum_status_sequence: int, clock_skew_seconds: int = 0,
) -> dict:
    """Verify the current signed key-status checkpoint without event-chain input.

    Callers can durably record the accepted sequence immediately after this
    function succeeds, even if a later evidence artifact fails chain validation.
    The caller remains responsible for obtaining the snapshot from its
    authenticated latest-status source.
    """
    current_time = _timestamp(current_time_utc, "verifier current time")
    bundle_digest, keys = _trust_bundle(
        trust_bundle, trust_bundle_root_signature, trusted_root, trust_bundle_sha256,
        environment_id, log_id, permitted_signer_key_id,
    )
    _, revoked, boundaries, sequence = _verify_key_status(
        key_status_statement, key_status_root_signature, trusted_root, bundle_digest,
        environment_id, log_id, keys, current_time_utc, max_freshness_seconds,
        minimum_status_sequence, clock_skew_seconds,
    )
    return {
        "verified": True,
        "trust_bundle_sha256": bundle_digest,
        "key_status_sequence": sequence,
        "revoked_key_ids": sorted(revoked),
        "compromise_boundary_key_ids": sorted(boundaries),
        "verified_at_utc": current_time.isoformat().replace("+00:00", "Z"),
    }


def verify_registry_receipts(
    *, entries: Any, run_id: str, environment_id: str, log_id: str,
    trust_bundle: Any, trust_bundle_root_signature: Any, trust_bundle_sha256: str,
    trusted_root: Any, permitted_signer_key_id: str,
    key_status_statement: Any, key_status_root_signature: Any,
    current_time_utc: str, max_freshness_seconds: int, minimum_status_sequence: int,
    clock_skew_seconds: int = 0, pre_compromise_anchors: Any = None,
    pre_compromise_anchor_schema: Any = None, trusted_anchor: Any = None,
) -> dict:
    """Verify a committed chain against external trust/status inputs.

    The caller is responsible for fetching key status from an authenticated
    source and persisting the returned sequence before a future verification.
    """
    if not isinstance(entries, list) or not entries:
        _fail("a non-empty committed event chain is required")
    if any(not isinstance(value, str) or not value for value in (run_id, environment_id, log_id, permitted_signer_key_id)):
        _fail("frozen run, environment, log, and signer identities are required")
    if not isinstance(trust_bundle_sha256, str) or not HEX_SHA256.fullmatch(trust_bundle_sha256):
        _fail("frozen trust bundle digest is invalid")
    current_time = _timestamp(current_time_utc, "verifier current time")
    bundle_digest, keys = _trust_bundle(
        trust_bundle, trust_bundle_root_signature, trusted_root, trust_bundle_sha256,
        environment_id, log_id, permitted_signer_key_id,
    )
    _, revoked, boundaries, status_sequence = _verify_key_status(
        key_status_statement, key_status_root_signature, trusted_root, bundle_digest,
        environment_id, log_id, keys, current_time_utc, max_freshness_seconds,
        minimum_status_sequence, clock_skew_seconds,
    )
    anchors = pre_compromise_anchors if pre_compromise_anchors is not None else []
    if not isinstance(anchors, list):
        _fail("pre-compromise anchors must be an array")
    anchors_by_event: dict[str, dict] = {}
    anchor_ids: set[str] = set()
    for anchor in anchors:
        if not isinstance(anchor, dict) or not isinstance(anchor.get("event_id"), str):
            _fail("pre-compromise anchor event id is invalid")
        if anchor["event_id"] in anchors_by_event or not isinstance(anchor.get("anchor_id"), str) or anchor["anchor_id"] in anchor_ids:
            _fail("pre-compromise anchor ids are missing or duplicated")
        anchors_by_event[anchor["event_id"]] = anchor
        anchor_ids.add(anchor["anchor_id"])

    previous_hash = GENESIS_HASH
    previous_time: datetime | None = None
    seen_events: set[str] = set()
    used_anchors: set[str] = set()
    verified_ids: list[str] = []
    historical_ids: list[str] = []
    for index, entry in enumerate(entries):
        _exact_fields(entry, {"event", "receipt"}, f"entry {index}")
        event, receipt = entry["event"], entry["receipt"]
        _exact_fields(event, EVENT_FIELDS, f"event {index}")
        _exact_fields(receipt, RECEIPT_FIELDS, f"receipt {index}")
        if event["schema"] != "stage5-registry-event-envelope-v1" or event["hash_profile"] != HASH_PROFILE:
            _fail(f"event {index} has unsupported schema or hash profile")
        if receipt["schema"] != "stage5-append-receipt-v1" or receipt["hash_profile"] != HASH_PROFILE:
            _fail(f"receipt {index} has unsupported schema or hash profile")
        if any(not isinstance(event.get(field), str) or not event[field] for field in ("event_id", "event_type", "actor_subject_id", "actor_role")):
            _fail(f"event {index} has an invalid identity field")
        if type(event["sequence"]) is not int or event["sequence"] != index + 1:
            _fail(f"event {index} has a non-contiguous sequence")
        if event["run_id"] != run_id or receipt["run_id"] != run_id:
            _fail(f"event {index} run id does not match frozen run")
        if receipt["environment_id"] != environment_id or receipt["log_id"] != log_id:
            _fail(f"receipt {index} scope does not match frozen run")
        if event["event_id"] != receipt["event_id"] or event["event_id"] in seen_events:
            _fail(f"event {index} id is mismatched or duplicated")
        if type(receipt["sequence"]) is not int or receipt["sequence"] < 1:
            _fail(f"receipt {index} sequence must be a positive integer")
        if (event["sequence"] != receipt["sequence"] or event["previous_event_hash"] != receipt["previous_event_hash"]
                or event["event_hash"] != receipt["event_hash"] or event["registry_recorded_at"] != receipt["registry_recorded_at"]):
            _fail(f"receipt {index} does not bind committed event fields")
        if event["previous_event_hash"] != previous_hash:
            _fail(f"event {index} predecessor does not match verified chain head")
        if not isinstance(event["payload"], dict):
            _fail(f"event {index} payload must be an object")
        if event["payload_sha256"] != canonical_sha256(event["payload"]):
            _fail(f"event {index} payload hash is invalid")
        event_preimage = {field: event[field] for field in EVENT_PREIMAGE_FIELDS}
        event_hash = canonical_sha256(event_preimage)
        if event["event_hash"] != event_hash:
            _fail(f"event {index} event hash is invalid")
        recorded_at = _timestamp(event["registry_recorded_at"], f"event {index} registry_recorded_at")
        if event["actor_asserted_at"] is not None:
            _timestamp(event["actor_asserted_at"], f"event {index} actor_asserted_at")
        if previous_time is not None and recorded_at < previous_time:
            _fail(f"event {index} recorded time moves backwards")
        if receipt["signature_profile"] != RECEIPT_PROFILE or receipt["signature_algorithm"] != "Ed25519":
            _fail(f"receipt {index} has unsupported signature profile")
        if receipt["key_id"] != permitted_signer_key_id or receipt["key_id"] not in keys:
            _fail(f"receipt {index} uses an unknown or unpermitted signer")
        key = keys[receipt["key_id"]]
        public_key = _decode_base64url(key["public_key"], 32, "receipt signing key")
        receipt_signature = _decode_base64url(receipt["signature"], 64, "receipt signature")
        signed_receipt = {field: receipt[field] for field in RECEIPT_FIELDS if field != "signature"}
        if receipt["key_id"] in revoked or key["state"] == "revoked":
            boundary = boundaries.get(receipt["key_id"])
            revocation = revoked.get(receipt["key_id"])
            anchor = anchors_by_event.get(event["event_id"])
            if boundary is None or revocation is None or anchor is None:
                _fail(f"receipt {index} revoked-key history requires a known compromise boundary and anchor")
            key_start = _timestamp(key["not_before_utc"], "revoked signer activation")
            key_end = _timestamp(key["not_after_utc"], "revoked signer expiry")
            revoked_at = _timestamp(revocation["revoked_at_utc"], "signer revocation time")
            if recorded_at < key_start or recorded_at > key_end or recorded_at > revoked_at:
                _fail(f"receipt {index} recorded outside signer validity/revocation interval")
            anchor_id = _verify_anchor(
                anchor, entry, trusted_anchor,
                {"environment_id": environment_id, "log_id": log_id, "run_id": run_id},
                boundary, current_time, clock_skew_seconds,
            )
            used_anchors.add(anchor_id)
            historical_ids.append(event["event_id"])
        else:
            start = _timestamp(key["not_before_utc"], "signer activation")
            end = _timestamp(key["not_after_utc"], "signer expiry")
            if recorded_at < start or recorded_at > end:
                _fail(f"receipt {index} signing key is outside validity window")
            if key["state"] == "retired" and recorded_at > _timestamp(key["retired_at_utc"], "signer retirement"):
                _fail(f"receipt {index} was signed after key retirement")
        _verify_ed25519(public_key, receipt_signature, canonical_json_bytes(signed_receipt), f"receipt {index}")
        seen_events.add(event["event_id"])
        verified_ids.append(event["event_id"])
        previous_hash = event_hash
        previous_time = recorded_at
    if used_anchors != anchor_ids:
        _fail("unused pre-compromise anchor supplied")
    return {
        "verified": True,
        "event_count": len(entries),
        "head_hash": previous_hash,
        "event_ids": verified_ids,
        "historically_anchored_event_ids": historical_ids,
        "trust_bundle_sha256": bundle_digest,
        "key_status_sequence": status_sequence,
    }
