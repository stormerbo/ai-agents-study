import hashlib
import base64
from dataclasses import replace
import json
from pathlib import Path
import tempfile
import unittest

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from acceptance import (
    HASH_PROFILE, AcceptanceReport, Evidence, RegistryVerificationInputs, REQUIRED_GATES,
    REQUIRED_KINDS, canonical_sha256, decide,
)
from canonicalization import canonical_json_bytes
from registry_sequence_floor import SqliteSequenceFloorStore
from registry_receipt_verifier import verify_dual_witness_receipt_chain


RELEASE_ID = "release-2026-10-20.1"
RUN_ID = "run-7c44"
COMMIT_SHA = "a" * 40
EXECUTED_AT = "2026-10-20T09:00:00Z"
PROVIDER = "provider-x"
MODEL = "model-y"
CANDIDATE_SHA = "c" * 64
IMAGE_DIGEST = "sha256:" + "d" * 64
HOLDOUT_VERSION = "holdout-v3"
EXECUTOR_SHA = "9" * 64
HOLDOUT_ENVELOPE_FIELDS = {
    "gate_id", "kind", "status", "release_id", "blind", "registry", "report_sha256",
}
MATERIAL_CONTENT = {
    "lockfile": b"lockfile fixture\n",
    "prompt": b"prompt fixture\n",
    "tool_schema": b"tool schema fixture\n",
    "dataset": b"synthetic dataset fixture\n",
    "scorer": b"scorer fixture\n",
}


class StaticStatusSource:
    def __init__(self, statement, root_signature, *, source_id="status-service-test"):
        self.statement = statement
        self.root_signature = root_signature
        self.source_id = source_id
        self.requests = []
        self.unavailable = False
        self.fetched_at_utc = "2026-10-23T12:00:30Z"

    def fetch_latest_status(self, environment_id, log_id, trust_bundle_sha256):
        self.requests.append((environment_id, log_id, trust_bundle_sha256))
        if self.unavailable:
            raise OSError("test status source unavailable")
        return {
            "source_id": self.source_id,
            "environment_id": environment_id,
            "log_id": log_id,
            "trust_bundle_sha256": trust_bundle_sha256,
            "statement": self.statement,
            "root_signature": self.root_signature,
            "fetched_at_utc": self.fetched_at_utc,
        }


class StaticWitnessSource:
    def __init__(self, *, source_id="witness-service-test"):
        self.source_id = source_id
        self.receipts = []
        self.requests = []
        self.unavailable = False
        self.fetched_at_utc = "2026-10-23T12:00:30Z"

    def fetch_latest_witness_chain(self, environment_id, log_id, run_id):
        self.requests.append((environment_id, log_id, run_id))
        if self.unavailable:
            raise OSError("test witness source unavailable")
        return {
            "source_id": self.source_id,
            "environment_id": environment_id,
            "log_id": log_id,
            "run_id": run_id,
            "fetched_at_utc": self.fetched_at_utc,
            "witness_receipts": self.receipts,
        }


class StaticAnchorSource:
    def __init__(self, *, source_id="anchor-service-test"):
        self.source_id = source_id
        self.records = {}
        self.requests = []
        self.unavailable = False

    def fetch_anchor(self, environment_id, log_id, run_id, sequence, event_id, receipt_sha256):
        key = (environment_id, log_id, run_id, sequence, event_id, receipt_sha256)
        self.requests.append(key)
        if self.unavailable:
            raise OSError("test anchor source unavailable")
        anchor = self.records.get(key)
        return None if anchor is None else {"source_id": self.source_id, "anchor": anchor}


def digest(content):
    return hashlib.sha256(content).hexdigest()


def report_sha256(payload):
    body = {key: value for key, value in payload.items() if key not in HOLDOUT_ENVELOPE_FIELDS}
    return canonical_sha256(body)


FROZEN_SPEC = {
    "hash_profile": HASH_PROFILE,
    "holdout_version": HOLDOUT_VERSION,
    "run_id": RUN_ID,
    "authorization_event_id": "event-authorized",
    "owner_id": "owner-principal-7",
    "executor_id": "executor-principal-12",
    "recovery_operator_id": "recovery-principal-4",
    "candidate_sha256": CANDIDATE_SHA,
    "image_digest": IMAGE_DIGEST,
    "dataset_sha256": digest(MATERIAL_CONTENT["dataset"]),
    "scorer_sha256": digest(MATERIAL_CONTENT["scorer"]),
    "executor_sha256": EXECUTOR_SHA,
    "max_budget_usd": "5.00",
    "max_cases": 12,
    "minimum_task_count": 12,
    "minimum_pass_rate_bps": 10_000,
    "require_all_tasks_pass": True,
    "max_output_bytes": 100_000,
    "deadline_utc": "2026-10-20T10:00:00Z",
    "stop_conditions": [
        "budget", "deadline", "side-effect", "permission-boundary",
        "evidence-missing", "label-leak", "identity-mismatch",
    ],
}
FROZEN_SPEC_SHA = canonical_sha256(FROZEN_SPEC)


class EvidenceFixture:
    def __init__(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.items = []
        self.artifacts = []
        self.materials = {}
        self.material_hashes = {}
        for name, content in MATERIAL_CONTENT.items():
            locator = f"frozen/{name}.txt"
            path = self.root / locator
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
            self.material_hashes[name] = digest(content)
            self.materials[name] = {"locator": locator, "sha256": digest(content)}
        for gate in sorted(REQUIRED_GATES):
            self.add(gate, REQUIRED_KINDS.get(gate, "integration"))
        self.write_manifest()

    def payload(self, gate, kind, status="passed"):
        value = {
            "gate_id": gate, "kind": kind, "status": status,
            "release_id": RELEASE_ID, "run_id": RUN_ID,
        }
        if kind == "live":
            value.update({"provider": PROVIDER, "model": MODEL, "executed_at": EXECUTED_AT})
        elif kind == "integration":
            value.update({"command": "pytest -m integration", "run_results": [
                {"test_id": f"{gate}.case-1", "status": status},
            ]})
        elif kind == "manual":
            value.update({"reviewer_id": "reviewer-17", "reviewed_at": EXECUTED_AT,
                          "record": {"review_id": "review-218", "decision": "accepted",
                                     "rationale": "Receiver state was reconciled against delivery logs."}})
        elif kind == "holdout":
            value.update({
                "schema": "official-blind-holdout-evidence-envelope-v5",
                "hash_profile": HASH_PROFILE,
                "blind": True,
                "holdout_version": HOLDOUT_VERSION,
                "candidate_sha256": CANDIDATE_SHA,
                "image_digest": IMAGE_DIGEST,
                "scorer_sha256": self.material_hashes["scorer"],
                "executor_sha256": EXECUTOR_SHA,
                "authorization_event_id": "event-authorized",
                "reservation_event_id": "event-reserved",
                "terminal_event_id": "event-consumed",
                "frozen_spec": json.loads(json.dumps(FROZEN_SPEC)),
                "frozen_spec_sha256": FROZEN_SPEC_SHA,
                "results_sha256": "e" * 64,
                "output_sha256": "e" * 64,
                "output_seal_id": "seal-1",
                "metrics": {
                    "task_count": 12,
                    "passed_tasks": 12,
                    "pass_rate_bps": 10_000,
                    "quality_criteria": {
                        "minimum_task_count": 12,
                        "minimum_pass_rate_bps": 10_000,
                        "require_all_tasks_pass": True,
                    },
                    "token_usage": {"input_tokens": 100, "output_tokens": 10},
                    "cost_usd": "1.25",
                },
                "metrics_sha256": canonical_sha256(
                    {
                        "task_count": 12,
                        "passed_tasks": 12,
                        "pass_rate_bps": 10_000,
                        "quality_criteria": {
                            "minimum_task_count": 12,
                            "minimum_pass_rate_bps": 10_000,
                            "require_all_tasks_pass": True,
                        },
                        "token_usage": {"input_tokens": 100, "output_tokens": 10},
                        "cost_usd": "1.25",
                    }
                ),
                "independent_task_count": 12,
                "sample_size": 12,
                "passed_tasks": 12,
                "pass_rate_bps": 10_000,
                "quality_criteria": {
                    "minimum_task_count": 12,
                    "minimum_pass_rate_bps": 10_000,
                    "require_all_tasks_pass": True,
                },
                "quality_decision": "passed",
                "token_usage": {"input_tokens": 100, "output_tokens": 10},
                "case_limit": FROZEN_SPEC["max_cases"],
                "max_output_bytes": FROZEN_SPEC["max_output_bytes"],
                "deadline_utc": FROZEN_SPEC["deadline_utc"],
                "executed_at": EXECUTED_AT,
                "outcome": "passed",
                "cost_status": "known",
                "budget": {"authorized_max_usd": "5.00", "actual_usd": "1.25"},
                "stop_conditions": list(FROZEN_SPEC["stop_conditions"]),
                "registry": {
                    "registry_id": "holdout-registry-prod",
                    "append_only": True,
                    "events": [
                        {
                            "type": event_type,
                            "event_id": f"event-{event_type}",
                            "actor_id": (
                                FROZEN_SPEC["owner_id"] if event_type == "authorized"
                                else FROZEN_SPEC["executor_id"]
                            ),
                            "actor_role": "owner" if event_type == "authorized" else "executor",
                            "previous_event_id": {
                                "authorized": None,
                                "reserved": "event-authorized",
                                "consumed": "event-reserved",
                            }[event_type],
                            "holdout_version": HOLDOUT_VERSION,
                            "candidate_sha256": CANDIDATE_SHA,
                            "image_digest": IMAGE_DIGEST,
                            "dataset_sha256": self.material_hashes["dataset"],
                            "scorer_sha256": self.material_hashes["scorer"],
                            "executor_sha256": EXECUTOR_SHA,
                            "hash_profile": HASH_PROFILE,
                            "frozen_spec_sha256": FROZEN_SPEC_SHA,
                            "run_id": RUN_ID,
                            "appended_at": EXECUTED_AT,
                        }
                        for event_type in ("authorized", "reserved", "consumed")
                    ],
                },
            })
            value["report_sha256"] = report_sha256(value)
            value["registry"]["events"][-1]["report_sha256"] = value["report_sha256"]
        else:
            value["source"] = "synthetic fixture run"
        return value

    def add(self, gate, kind, locator=None, status="passed"):
        locator = locator or f"artifacts/{gate}.json"
        path = self.root / locator
        path.parent.mkdir(parents=True, exist_ok=True)
        content = json.dumps(self.payload(gate, kind, status), sort_keys=True).encode()
        path.write_bytes(content)
        sha = digest(content)
        self.items.append(Evidence(gate, status, kind, locator, sha, RELEASE_ID, RUN_ID))
        self.artifacts.append({
            "gate_id": gate, "kind": kind, "status": status, "locator": locator,
            "sha256": sha, "bytes": len(content), "release_id": RELEASE_ID, "run_id": RUN_ID,
        })
        return len(self.items) - 1

    def rewrite_artifact(self, gate, *, kind=None, status=None, mutate=None):
        idx = next(i for i, item in enumerate(self.items) if item.gate_id == gate)
        old = self.items[idx]
        new_kind = kind or old.kind
        new_status = status or old.status
        payload = self.payload(gate, new_kind, new_status)
        if mutate:
            mutate(payload)
        content = json.dumps(payload, sort_keys=True).encode()
        (self.root / old.locator).write_bytes(content)
        sha = digest(content)
        self.items[idx] = Evidence(gate, new_status, new_kind, old.locator, sha, RELEASE_ID, RUN_ID)
        artifact = next(a for a in self.artifacts if a["gate_id"] == gate)
        artifact.update({"kind": new_kind, "status": new_status, "sha256": sha,
                         "bytes": len(content)})
        self.write_manifest()

    def write_manifest(self):
        manifest = {
            "version": 2, "release_id": RELEASE_ID, "run_id": RUN_ID,
            "commit_sha": COMMIT_SHA, "provider": PROVIDER, "model": MODEL,
            "executed_at": EXECUTED_AT, "candidate_sha256": CANDIDATE_SHA,
            "image_digest": IMAGE_DIGEST, "holdout_version": HOLDOUT_VERSION,
            "materials": self.materials,
            "artifacts": self.artifacts,
        }
        manifest.update({f"{name}_sha256": sha for name, sha in self.material_hashes.items()})
        (self.root / "evidence-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    def report(self, items=None, **changes):
        values = {
            "version": 2, "release_id": RELEASE_ID, "run_id": RUN_ID,
            "commit_sha": COMMIT_SHA,
            **{f"{name}_sha256": sha for name, sha in self.material_hashes.items()},
            "provider": PROVIDER, "model": MODEL, "executed_at": EXECUTED_AT,
            "candidate_sha256": CANDIDATE_SHA, "image_digest": IMAGE_DIGEST,
            "holdout_version": HOLDOUT_VERSION,
            "executor_sha256": EXECUTOR_SHA,
            "evidence": list(self.items if items is None else items),
        }
        values.update(changes)
        return AcceptanceReport(**values)

    def close(self):
        self.temp.cleanup()


class DualWitnessVerifierTests(unittest.TestCase):
    def test_verifies_signed_run_scoped_witness_chain_and_rejects_a_resigned_fork(self):
        witness_key = Ed25519PrivateKey.from_private_bytes(bytes.fromhex(
            "1f9cbd8a376ee0214d5a7b9c0e2f31461f9cbd8a376ee0214d5a7b9c0e2f3146"
        ))
        witness_raw = witness_key.public_key().public_bytes(
            encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw,
        )
        encode = lambda value: base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")
        trusted_witness = {
            "witness_id": "witness-1", "authority_id": "witness-domain-1", "key_id": "witness-key-1",
            "public_key": encode(witness_raw), "fingerprint_sha256": hashlib.sha256(witness_raw).hexdigest(),
        }
        authority_entries = []
        for sequence in (1, 2):
            event = {
                "run_id": "run-witness-1", "sequence": sequence, "event_id": f"event-{sequence}",
                "event_hash": str(sequence) * 64, "registry_recorded_at": f"2026-10-23T12:00:0{sequence}Z",
            }
            receipt = {"environment_id": "prod-eval", "log_id": "holdout-log-1", "run_id": "run-witness-1"}
            authority_entries.append({"event": event, "receipt": receipt})
        previous_digest = "0" * 64

        def make_receipt(entry, sequence, previous):
            event = entry["event"]
            body = {
                "schema": "stage5-independent-witness-receipt-v1",
                "hash_profile": HASH_PROFILE,
                "witness_id": trusted_witness["witness_id"],
                "authority_id": trusted_witness["authority_id"],
                "environment_id": "prod-eval",
                "log_id": "holdout-log-1",
                "run_id": "run-witness-1",
                "authority_sequence": event["sequence"],
                "authority_event_id": event["event_id"],
                "authority_event_hash": event["event_hash"],
                "authority_entry_sha256": canonical_sha256(entry),
                "witness_sequence": sequence,
                "previous_witness_receipt_sha256": previous,
                "observed_at_utc": f"2026-10-23T12:00:0{sequence + 1}Z",
                "key_id": trusted_witness["key_id"],
                "signature_algorithm": "Ed25519",
                "signature_profile": "ed25519-jcs-witness-receipt-v1",
            }
            signature = encode(witness_key.sign(canonical_json_bytes(body)))
            return {**body, "signature": signature}

        witness_receipts = []
        for sequence, entry in enumerate(authority_entries, start=1):
            receipt = make_receipt(entry, sequence, previous_digest)
            witness_receipts.append(receipt)
            previous_digest = canonical_sha256(receipt)
        result = verify_dual_witness_receipt_chain(
            authority_entries=authority_entries,
            witness_receipts=witness_receipts,
            run_id="run-witness-1",
            environment_id="prod-eval",
            log_id="holdout-log-1",
            append_authority_domain_id="registry-domain-1",
            signing_key_custodian_domain_id="registry-keys-1",
            trusted_witness=trusted_witness,
            current_time_utc="2026-10-23T12:01:00Z",
        )
        self.assertEqual(result["terminal_witness_receipt_sha256"], previous_digest)
        forked = [witness_receipts[0], make_receipt(authority_entries[1], 2, "f" * 64)]
        with self.assertRaisesRegex(ValueError, "predecessor"):
            verify_dual_witness_receipt_chain(
                authority_entries=authority_entries,
                witness_receipts=forked,
                run_id="run-witness-1",
                environment_id="prod-eval",
                log_id="holdout-log-1",
                append_authority_domain_id="registry-domain-1",
                signing_key_custodian_domain_id="registry-keys-1",
                trusted_witness=trusted_witness,
                current_time_utc="2026-10-23T12:01:00Z",
            )


class AcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.fx = EvidenceFixture()

    def tearDown(self):
        self.fx.close()

    def decide(self, report=None, root=None, registry_verification=None):
        return decide(
            report or self.fx.report(), self.fx.root if root is None else root,
            registry_verification,
        )

    def _upgrade_holdout_to_v6(
        self, *, tamper_receipt_event=False, compromised=False, include_anchor=True,
        anchor_at_boundary=False, assurance_profile="single-authority-v1",
    ):
        root_key = Ed25519PrivateKey.from_private_bytes(bytes.fromhex(
            "4c3a1d8f62b0e597a1f4c891d7732a5e9f6b0c4281d3e7a9556c0bf21e84a369"
        ))
        event_key = Ed25519PrivateKey.from_private_bytes(bytes.fromhex(
            "9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60"
        ))
        anchor_key = Ed25519PrivateKey.from_private_bytes(bytes.fromhex(
            "7f4a9c12d3e5b6078a9b0c1d2e3f40517f4a9c12d3e5b6078a9b0c1d2e3f4051"
        ))
        witness_key = Ed25519PrivateKey.from_private_bytes(bytes.fromhex(
            "1f9cbd8a376ee0214d5a7b9c0e2f31461f9cbd8a376ee0214d5a7b9c0e2f3146"
        ))
        risk_owner_key = Ed25519PrivateKey.from_private_bytes(bytes.fromhex("42" * 32))
        reviewer_key = Ed25519PrivateKey.from_private_bytes(bytes.fromhex("51" * 32))
        root_raw = root_key.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        event_raw = event_key.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        anchor_raw = anchor_key.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        witness_raw = witness_key.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        risk_owner_raw = risk_owner_key.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        reviewer_raw = reviewer_key.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        encode = lambda value: base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")
        receipt_key = {
            "key_id": "audit-key-1", "algorithm": "Ed25519",
            "public_key": encode(event_raw), "state": "active",
            "not_before_utc": "2026-10-19T00:00:00Z",
            "not_after_utc": "2027-10-19T00:00:00Z",
        }
        if compromised:
            receipt_key.update({
                "state": "revoked", "revoked_at_utc": "2026-10-22T00:00:00Z",
                "revocation_id": "incident-v6-1",
            })
        bundle = {
            "schema": "stage5-receipt-trust-bundle-v1",
            "bundle_id": "acceptance-test-bundle",
            "hash_profile": HASH_PROFILE,
            "signature_profile": "ed25519-jcs-receipt-v1",
            "environment_id": "prod-eval",
            "log_id": "official-holdout-v1",
            "issued_at_utc": "2026-10-19T00:00:00Z",
            "keys": [receipt_key],
        }
        bundle_digest = canonical_sha256(bundle)
        bundle_signature = {
            "schema": "stage5-trust-root-signature-v1",
            "root_key_id": "offline-root-1",
            "profile": "ed25519-jcs-trust-bundle-v1",
            "signature": encode(root_key.sign(canonical_json_bytes(bundle))),
        }
        status = {
            "schema": "stage5-key-status-statement-v2" if compromised else "stage5-key-status-statement-v1",
            "statement_id": "acceptance-status-2" if compromised else "acceptance-status-1",
            "sequence": 2 if compromised else 1,
            "bundle_sha256": bundle_digest, "environment_id": "prod-eval",
            "log_id": "official-holdout-v1",
            "issued_at_utc": "2026-10-23T12:00:00Z",
            "expires_at_utc": "2026-10-23T12:05:00Z",
            "revoked_keys": ([{
                "key_id": "audit-key-1", "revoked_at_utc": "2026-10-22T00:00:00Z",
                "revocation_id": "incident-v6-1", "reason": "compromise_confirmed",
                "compromise_not_before_utc": "2026-10-21T00:00:00Z",
                "incident_review": {"review_id": "review-v6-1", "record_sha256": "c" * 64},
            }] if compromised else []),
        }
        status_signature = {
            "schema": "stage5-trust-root-signature-v1",
            "root_key_id": "offline-root-1",
            "profile": "ed25519-jcs-key-status-v1",
            "signature": encode(root_key.sign(canonical_json_bytes(status))),
        }
        root_pin = {
            "key_id": "offline-root-1", "public_key": encode(root_raw),
            "fingerprint_sha256": hashlib.sha256(root_raw).hexdigest(),
        }
        status_source = StaticStatusSource(status, status_signature)
        anchor_source = StaticAnchorSource()
        witness_source = StaticWitnessSource() if assurance_profile == "dual-witness-v1" else None
        trusted_witness = {
            "witness_id": "independent-witness-v6",
            "authority_id": "witness-domain-v6",
            "key_id": "witness-key-v6",
            "public_key": encode(witness_raw),
            "fingerprint_sha256": hashlib.sha256(witness_raw).hexdigest(),
        }
        governance_signer_pin = lambda subject_id, role, key_id, raw: {
            "subject_id": subject_id, "role": role, "key_id": key_id,
            "public_key": encode(raw), "fingerprint_sha256": hashlib.sha256(raw).hexdigest(),
            "policy_version": "risk-policy-v1", "status": "active",
            "not_before_utc": "2026-01-01T00:00:00Z",
            "not_after_utc": "2027-01-01T00:00:00Z",
        }
        trusted_risk_owner = governance_signer_pin(
            "risk-owner-1", "risk_owner", "risk-owner-key-1", risk_owner_raw,
        )
        trusted_reviewer = governance_signer_pin(
            "independent-reviewer-1", "independent_reviewer", "reviewer-key-1", reviewer_raw,
        )
        handoff_sha256 = "e" * 64
        trusted_anchor = None
        if compromised:
            trusted_anchor = {
                "authority_id": "independent-anchor-v6",
                "key_id": "anchor-key-v6",
                "public_key": encode(anchor_raw),
                "fingerprint_sha256": hashlib.sha256(anchor_raw).hexdigest(),
            }
        verification = RegistryVerificationInputs(
            environment_id="prod-eval", log_id="official-holdout-v1",
            permitted_signer_key_id="audit-key-1", trusted_root=root_pin,
            status_source=status_source, key_status_source_id=status_source.source_id,
            current_time_utc="2026-10-23T12:01:00Z", assurance_profile=assurance_profile,
            max_freshness_seconds=600,
            clock_skew_seconds=0,
            sequence_floor_store=SqliteSequenceFloorStore(self.fx.root / "sequence-floor.sqlite3"),
            append_authority_domain_id="registry-domain-v6",
            signing_key_custodian_domain_id="registry-keys-v6",
            witness_source=witness_source,
            witness_source_id=witness_source.source_id if witness_source else None,
            trusted_witness=trusted_witness if witness_source else None,
            trusted_anchor=trusted_anchor,
            anchor_source=anchor_source, anchor_source_id=anchor_source.source_id,
            trusted_risk_owner=trusted_risk_owner,
            trusted_independent_reviewer=trusted_reviewer,
            handoff_record_sha256=handoff_sha256,
        )
        attestation_context = {}

        def upgrade(payload):
            frozen = payload["frozen_spec"]
            frozen.update({
                "registry_environment_id": verification.environment_id,
                "registry_log_id": verification.log_id,
                "permitted_signer_key_id": verification.permitted_signer_key_id,
                "trust_bundle_sha256": bundle_digest,
                "receipt_hash_profile": "jcs-rfc8785-v1",
                "receipt_signature_profile": "ed25519-jcs-receipt-v1",
                "max_status_age_seconds": 600,
                "clock_skew_seconds": 0,
                "assurance_profile": assurance_profile,
                "append_authority_domain_id": verification.append_authority_domain_id,
                "signing_key_custodian_domain_id": verification.signing_key_custodian_domain_id,
                "witness_authority_domain_id": trusted_witness["authority_id"] if witness_source else None,
                "witness_root_fingerprint_sha256": trusted_witness["fingerprint_sha256"] if witness_source else None,
            })
            frozen_digest = canonical_sha256(frozen)
            payload["frozen_spec_sha256"] = frozen_digest
            for event in payload["registry"]["events"]:
                event["frozen_spec_sha256"] = frozen_digest
            payload["schema"] = "official-blind-holdout-evidence-envelope-v5"
            payload["report_sha256"] = report_sha256(payload)
            payload["registry"]["events"][-1]["report_sha256"] = payload["report_sha256"]

            receipt_chain = []
            pre_compromise_anchors = []
            previous_hash = "0" * 64
            preimage_fields = (
                "schema", "hash_profile", "run_id", "sequence", "event_id",
                "previous_event_hash", "event_type", "actor_subject_id", "actor_role",
                "registry_recorded_at", "actor_asserted_at", "payload_sha256",
            )
            for sequence, summary in enumerate(payload["registry"]["events"], start=1):
                event_payload = json.loads(json.dumps(summary))
                if tamper_receipt_event and sequence == 1:
                    event_payload["candidate_sha256"] = "f" * 64
                event = {
                    "schema": "stage5-registry-event-envelope-v1",
                    "hash_profile": HASH_PROFILE,
                    "run_id": RUN_ID,
                    "sequence": sequence,
                    "event_id": summary["event_id"],
                    "previous_event_hash": previous_hash,
                    "event_type": summary["type"],
                    "actor_subject_id": summary["actor_id"],
                    "actor_role": summary["actor_role"],
                    "registry_recorded_at": summary["appended_at"],
                    "actor_asserted_at": None,
                    "payload_sha256": canonical_sha256(event_payload),
                    "payload": event_payload,
                }
                event["event_hash"] = canonical_sha256({key: event[key] for key in preimage_fields})
                receipt = {
                    "schema": "stage5-append-receipt-v1", "hash_profile": HASH_PROFILE,
                    "environment_id": verification.environment_id, "log_id": verification.log_id,
                    "run_id": RUN_ID, "sequence": sequence, "event_id": event["event_id"],
                    "previous_event_hash": previous_hash, "event_hash": event["event_hash"],
                    "registry_recorded_at": event["registry_recorded_at"],
                    "signature_profile": "ed25519-jcs-receipt-v1",
                    "signature_algorithm": "Ed25519", "key_id": verification.permitted_signer_key_id,
                }
                receipt["signature"] = encode(event_key.sign(canonical_json_bytes(receipt)))
                entry = {"event": event, "receipt": receipt}
                receipt_chain.append(entry)
                if compromised and include_anchor:
                    anchor = {
                        "schema": "stage5-pre-compromise-anchor-v1",
                        "anchor_id": f"anchor-v6-{sequence}",
                        "environment_id": verification.environment_id,
                        "log_id": verification.log_id,
                        "run_id": RUN_ID,
                        "sequence": sequence,
                        "event_id": event["event_id"],
                        "event_hash": event["event_hash"],
                        "key_id": receipt["key_id"],
                        "receipt_sha256": canonical_sha256(entry),
                        "anchor_recorded_at_utc": (
                            "2026-10-21T00:00:00Z" if anchor_at_boundary
                            else "2026-10-20T09:01:00Z"
                        ),
                        "anchor_authority_id": trusted_anchor["authority_id"],
                        "anchor_key_id": trusted_anchor["key_id"],
                        "signature_algorithm": "Ed25519",
                        "signature_profile": "ed25519-jcs-precompromise-anchor-v1",
                    }
                    anchor["signature"] = encode(anchor_key.sign(canonical_json_bytes(anchor)))
                    pre_compromise_anchors.append(anchor)
                    anchor_source.records[(
                        verification.environment_id, verification.log_id, RUN_ID,
                        sequence, event["event_id"], canonical_sha256(entry),
                    )] = anchor
                previous_hash = event["event_hash"]
            if witness_source is not None:
                previous_witness_digest = "0" * 64
                for witness_sequence, entry in enumerate(receipt_chain, start=1):
                    body = {
                        "schema": "stage5-independent-witness-receipt-v1",
                        "hash_profile": HASH_PROFILE,
                        "witness_id": trusted_witness["witness_id"],
                        "authority_id": trusted_witness["authority_id"],
                        "environment_id": verification.environment_id,
                        "log_id": verification.log_id,
                        "run_id": RUN_ID,
                        "authority_sequence": entry["event"]["sequence"],
                        "authority_event_id": entry["event"]["event_id"],
                        "authority_event_hash": entry["event"]["event_hash"],
                        "authority_entry_sha256": canonical_sha256(entry),
                        "witness_sequence": witness_sequence,
                        "previous_witness_receipt_sha256": previous_witness_digest,
                        "observed_at_utc": f"2026-10-23T12:00:{30 + witness_sequence:02d}Z",
                        "key_id": trusted_witness["key_id"],
                        "signature_algorithm": "Ed25519",
                        "signature_profile": "ed25519-jcs-witness-receipt-v1",
                    }
                    signed_witness_receipt = {
                        **body,
                        "signature": encode(witness_key.sign(canonical_json_bytes(body))),
                    }
                    witness_source.receipts.append(signed_witness_receipt)
                    previous_witness_digest = canonical_sha256(signed_witness_receipt)
            payload["registry"]["receipt_chain"] = receipt_chain
            if compromised:
                payload["registry"]["pre_compromise_anchors"] = pre_compromise_anchors
            payload["trust_bundle"] = bundle
            payload["trust_bundle_root_signature"] = bundle_signature
            payload["trust_bundle_sha256"] = bundle_digest
            payload["schema"] = "official-blind-holdout-evidence-envelope-v6"
            attestation_context.update({
                "frozen_digest": frozen_digest,
                "authorization_at": payload["registry"]["events"][0]["appended_at"],
                "terminal_at": payload["registry"]["events"][-1]["appended_at"],
            })

        self.fx.rewrite_artifact("official_blind_holdout", mutate=upgrade)
        risk_approval = {
            "schema": "stage5-assurance-approval-v1",
            "approval_id": "risk-approval-v6-1",
            "subject_id": trusted_risk_owner["subject_id"],
            "role": "risk_owner", "decision": "approved",
            "frozen_spec_sha256": attestation_context["frozen_digest"],
            "assurance_profile": assurance_profile,
            "append_authority_domain_id": verification.append_authority_domain_id,
            "signing_key_custodian_domain_id": verification.signing_key_custodian_domain_id,
            "append_authority_compromise_in_scope": assurance_profile == "dual-witness-v1",
            "witness_authority_domain_id": trusted_witness["authority_id"] if witness_source else None,
            "witness_root_fingerprint_sha256": trusted_witness["fingerprint_sha256"] if witness_source else None,
            "policy_version": "risk-policy-v1",
            "approved_at_utc": "2026-10-20T08:59:00Z",
            "expires_at_utc": "2026-10-24T00:00:00Z",
            "signature_profile": "ed25519-jcs-assurance-attestation-v1",
            "key_id": trusted_risk_owner["key_id"],
        }
        risk_approval["signature"] = encode(risk_owner_key.sign(canonical_json_bytes(risk_approval)))
        handoff_review = {
            "schema": "stage5-handoff-review-attestation-v1",
            "review_id": "handoff-review-v6-1",
            "subject_id": trusted_reviewer["subject_id"],
            "role": "independent_reviewer", "decision": "accepted",
            "frozen_spec_sha256": attestation_context["frozen_digest"],
            "handoff_sha256": handoff_sha256,
            "policy_version": "risk-policy-v1",
            "reviewed_at_utc": "2026-10-23T12:00:45Z",
            "expires_at_utc": "2026-10-24T00:00:00Z",
            "signature_profile": "ed25519-jcs-assurance-attestation-v1",
            "key_id": trusted_reviewer["key_id"],
        }
        handoff_review["signature"] = encode(reviewer_key.sign(canonical_json_bytes(handoff_review)))
        verification = replace(
            verification,
            risk_approval_attestation=risk_approval,
            handoff_review_attestation=handoff_review,
        )
        if witness_source is not None:
            verification = replace(
                verification,
                terminal_witness_receipt_sha256=canonical_sha256(witness_source.receipts[-1]),
            )
        return verification

    def test_acceptance_matrix_reports_each_gate_and_missing_holdout(self):
        from acceptance import build_acceptance_matrix

        items = [item for item in self.fx.items if item.gate_id != "official_blind_holdout"]
        matrix = build_acceptance_matrix(self.fx.report(items), self.fx.root)
        self.assertEqual(matrix["decision"], "incomplete")
        by_gate = {gate["gate_id"]: gate for gate in matrix["gates"]}
        self.assertEqual(by_gate["live_model_normal"]["state"], "passed")
        self.assertEqual(by_gate["official_blind_holdout"]["state"], "missing")
        self.assertFalse(matrix["authenticated"])

    def test_acceptance_matrix_keeps_missing_gate_visible_when_another_gate_fails(self):
        from acceptance import build_acceptance_matrix

        self.fx.rewrite_artifact("live_model_normal", status="failed")
        items = [item for item in self.fx.items if item.gate_id != "official_blind_holdout"]
        matrix = build_acceptance_matrix(self.fx.report(items), self.fx.root)
        by_gate = {gate["gate_id"]: gate for gate in matrix["gates"]}
        self.assertEqual(matrix["decision"], "blocked")
        self.assertEqual(by_gate["live_model_normal"]["state"], "failed")
        self.assertEqual(by_gate["official_blind_holdout"]["state"], "missing")

    def test_acceptance_matrix_marks_fixture_holdout_unverified(self):
        from acceptance import build_acceptance_matrix

        self.fx.rewrite_artifact("official_blind_holdout", kind="fixture")
        matrix = build_acceptance_matrix(self.fx.report(), self.fx.root)
        by_gate = {gate["gate_id"]: gate for gate in matrix["gates"]}
        self.assertEqual(matrix["decision"], "insufficient-evidence")
        self.assertEqual(by_gate["official_blind_holdout"]["state"], "unverified")

    def test_acceptance_matrix_marks_structural_v5_receipts_unverified(self):
        from acceptance import build_acceptance_matrix

        matrix = build_acceptance_matrix(self.fx.report(), self.fx.root)
        by_gate = {gate["gate_id"]: gate for gate in matrix["gates"]}
        self.assertEqual(matrix["decision"], "insufficient-evidence")
        self.assertEqual(by_gate["official_blind_holdout"]["state"], "unverified")

    def test_structural_v5_holdout_does_not_satisfy_the_signed_receipt_gate(self):
        result = self.decide()
        self.assertEqual(result["decision"], "insufficient-evidence")
        self.assertIn("official_blind_holdout", result["unverified"])

    def test_v6_holdout_without_external_verifier_inputs_stays_unverified(self):
        self._upgrade_holdout_to_v6()
        result = self.decide()
        self.assertEqual(result["decision"], "insufficient-evidence")
        self.assertIn("official_blind_holdout", result["unverified"])

    def test_v6_holdout_without_signed_governance_attestations_stays_unverified(self):
        verification = self._upgrade_holdout_to_v6()
        verification = replace(
            verification, risk_approval_attestation=None, handoff_review_attestation=None,
        )
        result = self.decide(registry_verification=verification)
        self.assertEqual(result["decision"], "insufficient-evidence")
        self.assertIn("official_blind_holdout", result["unverified"])

    def test_v6_invalid_governance_signature_or_handoff_binding_is_invalid(self):
        tampered = self._upgrade_holdout_to_v6()
        changed_approval = dict(tampered.risk_approval_attestation)
        changed_approval["approval_id"] = "different-approval"
        tampered = replace(tampered, risk_approval_attestation=changed_approval)
        self.assertEqual(self.decide(registry_verification=tampered)["decision"], "invalid-report")

        mismatched_handoff = self._upgrade_holdout_to_v6()
        mismatched_handoff = replace(mismatched_handoff, handoff_record_sha256="f" * 64)
        self.assertEqual(self.decide(registry_verification=mismatched_handoff)["decision"], "invalid-report")

    def test_v6_inactive_pinned_risk_owner_stays_unverified(self):
        verification = self._upgrade_holdout_to_v6()
        inactive = dict(verification.trusted_risk_owner)
        inactive["status"] = "revoked"
        verification = replace(verification, trusted_risk_owner=inactive)
        result = self.decide(registry_verification=verification)
        self.assertEqual(result["decision"], "insufficient-evidence")
        self.assertIn("official_blind_holdout", result["unverified"])

    def test_valid_signed_v6_holdout_uses_full_acceptance_path_and_advances_floor(self):
        verification = self._upgrade_holdout_to_v6()
        result = self.decide(registry_verification=verification)
        self.assertEqual(result["decision"], "ready-for-human-acceptance")
        scope = {
            "environment_id": verification.environment_id,
            "log_id": verification.log_id,
            "trust_bundle_sha256": verification.status_source.statement["bundle_sha256"],
        }
        self.assertEqual(verification.sequence_floor_store.read(scope), 1)
        self.assertEqual(self.decide(registry_verification=verification)["decision"],
                         "ready-for-human-acceptance")
        self.assertEqual(len(verification.status_source.requests), 2)

    def test_v6_dual_witness_profile_requires_and_verifies_latest_witness_chain(self):
        verification = self._upgrade_holdout_to_v6(assurance_profile="dual-witness-v1")
        result = self.decide(registry_verification=verification)
        self.assertEqual(result["decision"], "ready-for-human-acceptance")
        self.assertEqual(len(verification.witness_source.requests), 1)
        self.assertEqual(len(verification.witness_source.receipts), 3)
        self.assertEqual(
            canonical_sha256(verification.witness_source.receipts[-1]),
            verification.terminal_witness_receipt_sha256,
        )

    def test_v6_dual_witness_source_unavailable_or_stale_stays_unverified(self):
        unavailable = self._upgrade_holdout_to_v6(assurance_profile="dual-witness-v1")
        unavailable.witness_source.unavailable = True
        result = self.decide(registry_verification=unavailable)
        self.assertEqual(result["decision"], "insufficient-evidence")
        self.assertIn("official_blind_holdout", result["unverified"])

        stale = self._upgrade_holdout_to_v6(assurance_profile="dual-witness-v1")
        stale.witness_source.fetched_at_utc = "2026-10-23T11:00:00Z"
        result = self.decide(registry_verification=stale)
        self.assertEqual(result["decision"], "insufficient-evidence")
        self.assertIn("official_blind_holdout", result["unverified"])

    def test_v6_dual_witness_receipt_tampering_and_handoff_digest_mismatch_are_invalid(self):
        tampered = self._upgrade_holdout_to_v6(assurance_profile="dual-witness-v1")
        tampered.witness_source.receipts[0]["authority_event_hash"] = "f" * 64
        result = self.decide(registry_verification=tampered)
        self.assertEqual(result["decision"], "invalid-report")

        original = self._upgrade_holdout_to_v6(assurance_profile="dual-witness-v1")
        mismatched = replace(original, terminal_witness_receipt_sha256="f" * 64)
        result = self.decide(registry_verification=mismatched)
        self.assertEqual(result["decision"], "invalid-report")

    def test_v6_verifier_profile_must_match_the_frozen_profile(self):
        verification = self._upgrade_holdout_to_v6(assurance_profile="dual-witness-v1")
        mismatched = replace(verification, assurance_profile="single-authority-v1")
        result = self.decide(registry_verification=mismatched)
        self.assertEqual(result["decision"], "invalid-report")
        self.assertIn("official_blind_holdout", result.get("gates", []))

    def test_v6_status_source_unavailable_keeps_gate_unverified_without_advancing_floor(self):
        verification = self._upgrade_holdout_to_v6()
        verification.status_source.unavailable = True
        result = self.decide(registry_verification=verification)
        self.assertEqual(result["decision"], "insufficient-evidence")
        self.assertIn("official_blind_holdout", result["unverified"])
        scope = {
            "environment_id": verification.environment_id,
            "log_id": verification.log_id,
            "trust_bundle_sha256": verification.status_source.statement["bundle_sha256"],
        }
        self.assertEqual(verification.sequence_floor_store.read(scope), 0)

    def test_v6_status_source_stale_cache_keeps_gate_unverified_without_advancing_floor(self):
        verification = self._upgrade_holdout_to_v6()
        verification.status_source.fetched_at_utc = "2026-10-23T11:00:00Z"
        result = self.decide(registry_verification=verification)
        self.assertEqual(result["decision"], "insufficient-evidence")
        self.assertIn("official_blind_holdout", result["unverified"])
        scope = {
            "environment_id": verification.environment_id,
            "log_id": verification.log_id,
            "trust_bundle_sha256": verification.status_source.statement["bundle_sha256"],
        }
        self.assertEqual(verification.sequence_floor_store.read(scope), 0)

    def test_v6_status_source_must_match_pinned_identity_and_scope(self):
        verification = self._upgrade_holdout_to_v6()
        verification.status_source.source_id = "other-status-service"
        result = self.decide(registry_verification=verification)
        self.assertEqual(result["decision"], "insufficient-evidence")
        self.assertIn("official_blind_holdout", result["unverified"])

    def test_v6_stale_status_keeps_gate_unverified_without_advancing_floor(self):
        verification = self._upgrade_holdout_to_v6()
        stale_inputs = replace(verification, current_time_utc="2026-10-23T12:10:00Z")
        result = self.decide(registry_verification=stale_inputs)
        self.assertEqual(result["decision"], "insufficient-evidence")
        self.assertIn("official_blind_holdout", result["unverified"])
        scope = {
            "environment_id": verification.environment_id,
            "log_id": verification.log_id,
            "trust_bundle_sha256": verification.status_source.statement["bundle_sha256"],
        }
        self.assertEqual(verification.sequence_floor_store.read(scope), 0)

    def test_v6_compromised_signer_is_accepted_only_with_exact_pre_compromise_anchor(self):
        verification = self._upgrade_holdout_to_v6(compromised=True)
        result = self.decide(registry_verification=verification)
        self.assertEqual(result["decision"], "ready-for-human-acceptance")
        self.assertEqual(len(verification.anchor_source.requests), 3)
        self.assertEqual(self.decide(registry_verification=verification)["decision"],
                         "ready-for-human-acceptance")
        self.assertEqual(len(verification.anchor_source.requests), 6)

    def test_v6_compromised_signer_without_anchor_stays_unverified(self):
        verification = self._upgrade_holdout_to_v6(compromised=True, include_anchor=False)
        result = self.decide(registry_verification=verification)
        self.assertEqual(result["decision"], "insufficient-evidence")
        self.assertIn("official_blind_holdout", result["unverified"])

    def test_v6_compromised_signer_fails_closed_when_anchor_source_is_unavailable(self):
        verification = self._upgrade_holdout_to_v6(compromised=True)
        verification.anchor_source.unavailable = True
        result = self.decide(registry_verification=verification)
        self.assertEqual(result["decision"], "insufficient-evidence")
        self.assertIn("official_blind_holdout", result["unverified"])

    def test_v6_compromised_signer_fails_closed_when_anchor_source_identity_changes(self):
        verification = self._upgrade_holdout_to_v6(compromised=True)
        verification.anchor_source.source_id = "unexpected-anchor-service"
        result = self.decide(registry_verification=verification)
        self.assertEqual(result["decision"], "insufficient-evidence")
        self.assertIn("official_blind_holdout", result["unverified"])

    def test_v6_anchor_embedded_in_artifact_is_not_used_when_source_has_no_record(self):
        verification = self._upgrade_holdout_to_v6(compromised=True)
        verification.anchor_source.records.clear()
        result = self.decide(registry_verification=verification)
        self.assertEqual(result["decision"], "insufficient-evidence")
        self.assertIn("official_blind_holdout", result["unverified"])

    def test_v6_compromise_anchor_at_boundary_stays_unverified(self):
        verification = self._upgrade_holdout_to_v6(
            compromised=True, anchor_at_boundary=True
        )
        result = self.decide(registry_verification=verification)
        self.assertEqual(result["decision"], "insufficient-evidence")
        self.assertIn("official_blind_holdout", result["unverified"])

    def test_v6_receipt_mutation_is_invalid_even_when_domain_report_remains_unchanged(self):
        verification = self._upgrade_holdout_to_v6(tamper_receipt_event=True)
        result = self.decide(registry_verification=verification)
        self.assertEqual(result["decision"], "invalid-report")
        self.assertIn("official_blind_holdout", result["gates"])
        scope = {
            "environment_id": verification.environment_id,
            "log_id": verification.log_id,
            "trust_bundle_sha256": verification.status_source.statement["bundle_sha256"],
        }
        self.assertEqual(verification.sequence_floor_store.read(scope), 1)

    def test_missing_gate_makes_report_incomplete(self):
        self.assertEqual(self.decide(self.fx.report(self.fx.items[:-1]))["decision"], "incomplete")

    def test_official_blind_holdout_gate_is_required_for_acceptance(self):
        evidence = [item for item in self.fx.items if item.gate_id != "official_blind_holdout"]
        result = self.decide(self.fx.report(evidence))
        self.assertEqual(result["decision"], "incomplete")
        self.assertIn("official_blind_holdout", result["missing"])

    def test_official_holdout_requires_the_frozen_result_schema_version(self):
        self.fx.rewrite_artifact(
            "official_blind_holdout",
            mutate=lambda payload: payload.update({"schema": "official-blind-holdout-evidence-envelope-v4"}),
        )
        self.assertEqual(self.decide()["decision"], "invalid-report")

    def test_official_holdout_requires_the_declared_hash_profile(self):
        def mutate(payload):
            payload["hash_profile"] = "custom-json-v0"
            payload["report_sha256"] = report_sha256(payload)

        self.fx.rewrite_artifact("official_blind_holdout", mutate=mutate)
        self.assertEqual(self.decide()["decision"], "invalid-report")

    def test_synthetic_fixture_cannot_satisfy_official_blind_holdout_gate(self):
        self.fx.rewrite_artifact("official_blind_holdout", kind="fixture")
        result = self.decide()
        self.assertEqual(result["decision"], "insufficient-evidence")
        self.assertIn("official_blind_holdout", result["unverified"])

    def test_official_holdout_must_bind_to_frozen_candidate_and_registry(self):
        self.fx.rewrite_artifact(
            "official_blind_holdout",
            mutate=lambda payload: payload.update({"candidate_sha256": "b" * 64}),
        )
        self.assertEqual(self.decide()["decision"], "invalid-report")

    def test_official_holdout_must_bind_to_frozen_executor(self):
        self.fx.rewrite_artifact(
            "official_blind_holdout",
            mutate=lambda payload: payload.update({"executor_sha256": "b" * 64}),
        )
        self.assertEqual(self.decide()["decision"], "invalid-report")

    def test_official_holdout_report_must_bind_all_registry_event_ids(self):
        self.fx.rewrite_artifact(
            "official_blind_holdout",
            mutate=lambda payload: payload.update({"terminal_event_id": "unrelated-event"}),
        )
        self.assertEqual(self.decide()["decision"], "invalid-report")

    def test_official_holdout_requires_one_frozen_spec_hash_across_report_and_registry(self):
        def change_reserved_spec(payload):
            payload["registry"]["events"][1]["frozen_spec_sha256"] = "7" * 64

        self.fx.rewrite_artifact("official_blind_holdout", mutate=change_reserved_spec)
        self.assertEqual(self.decide()["decision"], "invalid-report")

    def test_official_holdout_rejects_quality_criteria_detached_from_frozen_spec(self):
        def loosen_reported_threshold(payload):
            payload["quality_criteria"]["minimum_pass_rate_bps"] = 0

        self.fx.rewrite_artifact("official_blind_holdout", mutate=loosen_reported_threshold)
        self.assertEqual(self.decide()["decision"], "invalid-report")

    def test_official_holdout_rejects_metrics_body_without_matching_hash(self):
        self.fx.rewrite_artifact(
            "official_blind_holdout",
            mutate=lambda payload: payload["metrics"].update({"pass_rate_bps": 9_999}),
        )
        self.assertEqual(self.decide()["decision"], "invalid-report")

    def test_official_holdout_rejects_stop_conditions_detached_from_frozen_spec(self):
        self.fx.rewrite_artifact(
            "official_blind_holdout",
            mutate=lambda payload: payload["stop_conditions"].append("new-unfrozen-stop"),
        )
        self.assertEqual(self.decide()["decision"], "invalid-report")

    def test_official_holdout_requires_all_mandatory_stop_conditions(self):
        def remove_required_stop(payload):
            payload["stop_conditions"].remove("label-leak")
            payload["frozen_spec"]["stop_conditions"].remove("label-leak")
            digest_value = hashlib.sha256(json.dumps(
                payload["frozen_spec"],
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
                allow_nan=False,
            ).encode("utf-8")).hexdigest()
            payload["frozen_spec_sha256"] = digest_value
            for event in payload["registry"]["events"]:
                event["frozen_spec_sha256"] = digest_value
            payload["report_sha256"] = report_sha256(payload)
            payload["registry"]["events"][-1]["report_sha256"] = payload["report_sha256"]

        self.fx.rewrite_artifact("official_blind_holdout", mutate=remove_required_stop)
        self.assertEqual(self.decide()["decision"], "invalid-report")

    def test_aborted_holdout_requires_runtime_stop_and_capability_revocation_evidence(self):
        def abort_without_capability_revocation(payload):
            payload.update({
                "outcome": "aborted",
                "decision": "aborted",
                "attempted_tasks": 1,
                "failure_type": "ExecutorInterrupted",
                "cost_status": "unknown",
            })
            payload["budget"]["actual_usd"] = None
            for field in (
                "output_seal_id", "output_sha256", "results_sha256", "metrics_sha256",
                "metrics", "independent_task_count", "sample_size", "passed_tasks",
                "pass_rate_bps", "quality_decision", "executed_at",
            ):
                payload.pop(field, None)
            payload["registry"]["events"][-1].update({
                "type": "aborted",
                "event_id": "event-aborted",
            })
            payload["termination_evidence"] = {
                "runtime_audit_ref": "runtime-audit://holdout/run-7c44",
                "runtime_audit_sha256": "f" * 64,
            }
            payload["terminal_event_id"] = "event-aborted"
            payload["report_sha256"] = report_sha256(payload)
            payload["registry"]["events"][-1]["report_sha256"] = payload["report_sha256"]

        self.fx.rewrite_artifact(
            "official_blind_holdout", status="unverified", mutate=abort_without_capability_revocation
        )
        self.assertEqual(self.decide()["decision"], "invalid-report")

    def test_aborted_holdout_uses_aborted_terminal_event_and_stays_unverified(self):
        def abort_run(payload):
            payload["outcome"] = "aborted"
            payload["decision"] = "aborted"
            payload["attempted_tasks"] = 1
            payload["failure_type"] = "BudgetExceeded"
            payload["termination_evidence"] = {
                "runtime_audit_ref": "runtime-audit://holdout/run-7c44",
                "runtime_audit_sha256": "f" * 64,
                "capability_revocation_ref": "custodian-revoke://holdout/run-7c44",
                "capability_revocation_sha256": "a" * 64,
            }
            payload["cost_status"] = "unknown"
            payload["budget"]["actual_usd"] = None
            payload["terminal_event_id"] = "event-aborted"
            payload["registry"]["events"][-1].update({
                "type": "aborted",
                "event_id": "event-aborted",
            })
            for field in (
                "output_seal_id", "output_sha256", "results_sha256", "metrics_sha256",
                "independent_task_count", "sample_size", "passed_tasks", "pass_rate_bps", "quality_decision",
                "executed_at",
            ):
                payload.pop(field, None)
            payload["report_sha256"] = report_sha256(payload)
            payload["registry"]["events"][-1]["report_sha256"] = payload["report_sha256"]

        self.fx.rewrite_artifact(
            "official_blind_holdout",
            status="unverified",
            mutate=abort_run,
        )
        result = self.decide()
        self.assertEqual(result["decision"], "insufficient-evidence")
        self.assertIn("official_blind_holdout", result["unverified"])

        def add_incomplete_seal_reference(payload):
            payload["output_seal_id"] = "seal-1"
            payload["report_sha256"] = report_sha256(payload)
            payload["registry"]["events"][-1]["report_sha256"] = payload["report_sha256"]

        self.fx.rewrite_artifact("official_blind_holdout", mutate=lambda payload: (
            abort_run(payload), add_incomplete_seal_reference(payload)
        ))
        self.assertEqual(self.decide()["decision"], "invalid-report")

        def add_complete_seal_reference(payload):
            payload["output_seal_id"] = "seal-1"
            payload["output_sha256"] = "e" * 64
            payload["results_sha256"] = "e" * 64
            payload["report_sha256"] = report_sha256(payload)
            payload["registry"]["events"][-1]["report_sha256"] = payload["report_sha256"]

        self.fx.rewrite_artifact("official_blind_holdout", mutate=lambda payload: (
            abort_run(payload), add_complete_seal_reference(payload)
        ))
        self.assertEqual(self.decide()["decision"], "insufficient-evidence")

    def test_official_holdout_registry_events_must_bind_image_scorer_and_executor(self):
        def mutate(payload):
            payload["registry"]["events"][0]["executor_sha256"] = "b" * 64

        self.fx.rewrite_artifact("official_blind_holdout", mutate=mutate)
        self.assertEqual(self.decide()["decision"], "invalid-report")

    def test_registry_actor_roles_and_ids_must_match_frozen_principals(self):
        def mutate(payload):
            payload["registry"]["events"][0]["actor_id"] = "unlisted-owner"

        self.fx.rewrite_artifact("official_blind_holdout", mutate=mutate)
        self.assertEqual(self.decide()["decision"], "invalid-report")

    def test_recovery_operator_cannot_mark_completed_without_usage_ledger(self):
        def recover_without_ledger(payload):
            payload["registry"]["events"][-1].update({
                "actor_id": payload["frozen_spec"]["recovery_operator_id"],
                "actor_role": "recovery_operator",
            })
            payload["termination_evidence"] = {
                "runtime_audit_ref": "runtime-audit://holdout/run-7c44",
                "runtime_audit_sha256": "f" * 64,
                "capability_revocation_ref": "custodian-revoke://holdout/run-7c44",
                "capability_revocation_sha256": "a" * 64,
            }
            payload["report_sha256"] = report_sha256(payload)
            payload["registry"]["events"][-1]["report_sha256"] = payload["report_sha256"]

        self.fx.rewrite_artifact("official_blind_holdout", mutate=recover_without_ledger)
        self.assertEqual(self.decide()["decision"], "invalid-report")

    def test_recovered_aborted_holdout_can_record_unknown_usage(self):
        def recover_aborted(payload):
            payload.update({
                "outcome": "aborted",
                "decision": "aborted",
                "attempted_tasks": 1,
                "failure_type": "ExecutorInterrupted",
                "cost_status": "unknown",
            })
            payload["budget"]["actual_usd"] = None
            for field in (
                "output_seal_id", "output_sha256", "results_sha256", "metrics_sha256",
                "metrics", "independent_task_count", "sample_size", "passed_tasks",
                "pass_rate_bps", "quality_decision", "executed_at",
            ):
                payload.pop(field, None)
            payload["registry"]["events"][-1].update({
                "type": "aborted",
                "event_id": "event-aborted",
                "actor_id": payload["frozen_spec"]["recovery_operator_id"],
                "actor_role": "recovery_operator",
            })
            payload["termination_evidence"] = {
                "runtime_audit_ref": "runtime-audit://holdout/run-7c44",
                "runtime_audit_sha256": "f" * 64,
                "capability_revocation_ref": "custodian-revoke://holdout/run-7c44",
                "capability_revocation_sha256": "a" * 64,
            }
            payload["terminal_event_id"] = "event-aborted"
            payload["report_sha256"] = report_sha256(payload)
            payload["registry"]["events"][-1]["report_sha256"] = payload["report_sha256"]

        self.fx.rewrite_artifact(
            "official_blind_holdout", status="unverified", mutate=recover_aborted
        )
        result = self.decide()
        self.assertEqual(result["decision"], "insufficient-evidence")
        self.assertIn("official_blind_holdout", result["unverified"])

    def test_recovery_operator_can_finalize_completed_holdout_with_bound_evidence(self):
        def recover_run(payload):
            payload["registry"]["events"][-1].update({
                "actor_id": payload["frozen_spec"]["recovery_operator_id"],
                "actor_role": "recovery_operator",
            })
            payload["termination_evidence"] = {
                "runtime_audit_ref": "runtime-audit://holdout/run-7c44",
                "runtime_audit_sha256": "f" * 64,
                "capability_revocation_ref": "custodian-revoke://holdout/run-7c44",
                "capability_revocation_sha256": "b" * 64,
            }
            payload["recovery_evidence"] = {
                "usage_ledger_ref": "usage-ledger://holdout/run-7c44",
                "usage_ledger_sha256": "a" * 64,
            }
            payload["report_sha256"] = report_sha256(payload)
            payload["registry"]["events"][-1]["report_sha256"] = payload["report_sha256"]

        self.fx.rewrite_artifact("official_blind_holdout", mutate=recover_run)
        result = self.decide()
        self.assertEqual(result["decision"], "insufficient-evidence")
        self.assertIn("official_blind_holdout", result["unverified"])

    def test_recovery_operator_cannot_finalize_without_runtime_evidence(self):
        def recover_without_evidence(payload):
            payload["registry"]["events"][-1].update({
                "actor_id": payload["frozen_spec"]["recovery_operator_id"],
                "actor_role": "recovery_operator",
            })
            payload["report_sha256"] = report_sha256(payload)
            payload["registry"]["events"][-1]["report_sha256"] = payload["report_sha256"]

        self.fx.rewrite_artifact("official_blind_holdout", mutate=recover_without_evidence)
        self.assertEqual(self.decide()["decision"], "invalid-report")

    def test_recovery_actor_must_match_the_frozen_recovery_principal(self):
        def mutate(payload):
            payload["outcome"] = "aborted"
            payload["registry"]["events"][2].update({
                "type": "aborted",
                "actor_id": "unlisted-recovery-operator",
                "actor_role": "recovery_operator",
            })
            payload["report_sha256"] = report_sha256(payload)
            payload["registry"]["events"][-1]["report_sha256"] = payload["report_sha256"]

        self.fx.rewrite_artifact("official_blind_holdout", mutate=mutate)
        self.assertEqual(self.decide()["decision"], "invalid-report")

    def test_official_holdout_rejects_binary_numeric_costs(self):
        self.fx.rewrite_artifact(
            "official_blind_holdout",
            mutate=lambda payload: payload["budget"].update({"actual_usd": 1.25}),
        )
        self.assertEqual(self.decide()["decision"], "invalid-report")

    def test_official_holdout_rejects_numeric_budget_limit(self):
        self.fx.rewrite_artifact(
            "official_blind_holdout",
            mutate=lambda payload: payload["budget"].update({"authorized_max_usd": 5}),
        )
        self.assertEqual(self.decide()["decision"], "invalid-report")

    def test_official_holdout_rejects_inconsistent_quality_rate(self):
        self.fx.rewrite_artifact(
            "official_blind_holdout",
            mutate=lambda payload: payload.update({"passed_tasks": 11}),
        )
        self.assertEqual(self.decide()["decision"], "invalid-report")

    def test_official_holdout_cannot_claim_pass_below_frozen_threshold(self):
        def lower_score(payload):
            payload.update({"passed_tasks": 11, "pass_rate_bps": 9_166})

        self.fx.rewrite_artifact("official_blind_holdout", mutate=lower_score)
        self.assertEqual(self.decide()["decision"], "invalid-report")

    def test_official_holdout_registry_timestamps_must_follow_event_order(self):
        def reverse_event_time(payload):
            events = payload["registry"]["events"]
            events[0]["appended_at"] = "2026-10-20T09:00:02Z"
            events[1]["appended_at"] = "2026-10-20T09:00:01Z"

        self.fx.rewrite_artifact("official_blind_holdout", mutate=reverse_event_time)
        self.assertEqual(self.decide()["decision"], "invalid-report")

    def test_official_holdout_registry_event_ids_must_be_unique(self):
        def duplicate_event(payload):
            payload["registry"]["events"][1]["event_id"] = payload["registry"]["events"][0]["event_id"]

        self.fx.rewrite_artifact("official_blind_holdout", mutate=duplicate_event)
        self.assertEqual(self.decide()["decision"], "invalid-report")

    def test_official_holdout_registry_events_must_form_a_previous_event_chain(self):
        def break_terminal_link(payload):
            payload["registry"]["events"][2]["previous_event_id"] = "event-authorized"

        self.fx.rewrite_artifact("official_blind_holdout", mutate=break_terminal_link)
        self.assertEqual(self.decide()["decision"], "invalid-report")

    def test_completed_holdout_requires_custodian_output_seal_id(self):
        def remove_seal_reference(payload):
            payload.pop("output_seal_id")
            payload["report_sha256"] = report_sha256(payload)
            payload["registry"]["events"][-1]["report_sha256"] = payload["report_sha256"]

        self.fx.rewrite_artifact("official_blind_holdout", mutate=remove_seal_reference)
        self.assertEqual(self.decide()["decision"], "invalid-report")

    def test_official_holdout_digests_must_be_strings(self):
        self.fx.rewrite_artifact(
            "official_blind_holdout",
            mutate=lambda payload: payload.update({"results_sha256": 10**63}),
        )
        self.assertEqual(self.decide()["decision"], "invalid-report")

    def test_official_holdout_result_body_must_match_terminal_registry_hash(self):
        self.fx.rewrite_artifact(
            "official_blind_holdout",
            mutate=lambda payload: payload.update({"results_sha256": "f" * 64}),
        )
        self.assertEqual(self.decide()["decision"], "invalid-report")

    def test_official_holdout_terminal_hash_must_match_the_report_body_hash(self):
        def update_result_without_reappending_registry_event(payload):
            payload["results_sha256"] = "f" * 64
            payload["report_sha256"] = report_sha256(payload)

        self.fx.rewrite_artifact(
            "official_blind_holdout",
            mutate=update_result_without_reappending_registry_event,
        )
        self.assertEqual(self.decide()["decision"], "invalid-report")

    def test_official_holdout_sample_size_must_be_an_integer_not_a_boolean(self):
        self.fx.rewrite_artifact(
            "official_blind_holdout",
            mutate=lambda payload: payload.update({"independent_task_count": 1, "sample_size": True}),
        )
        self.assertEqual(self.decide()["decision"], "invalid-report")

    def test_failed_invariant_blocks_when_artifact_also_reports_failure(self):
        gate = self.fx.items[0].gate_id
        self.fx.rewrite_artifact(gate, status="failed")
        self.assertEqual(self.decide()["decision"], "blocked")

    def test_report_status_must_match_artifact_status(self):
        items = list(self.fx.items)
        items[0] = Evidence(**{**items[0].__dict__, "status": "failed"})
        self.assertEqual(self.decide(self.fx.report(items))["decision"], "invalid-report")

    def test_fixture_cannot_satisfy_live_gate_even_if_report_claims_live(self):
        self.fx.rewrite_artifact("live_model_normal", kind="fixture")
        items = list(self.fx.items)
        idx = next(i for i, item in enumerate(items) if item.gate_id == "live_model_normal")
        items[idx] = Evidence(**{**items[idx].__dict__, "kind": "live"})
        self.assertEqual(self.decide(self.fx.report(items))["decision"], "invalid-report")

    def test_fixture_cannot_satisfy_integration_or_manual_gates(self):
        self.fx.rewrite_artifact("midflow_approval", kind="fixture")
        self.fx.rewrite_artifact("receiver_without_idempotency", kind="fixture")
        result = self.decide()
        self.assertEqual(result["decision"], "insufficient-evidence")
        self.assertIn("midflow_approval", result["unverified"])
        self.assertIn("receiver_without_idempotency", result["unverified"])

    def test_missing_file_is_invalid(self):
        (self.fx.root / self.fx.items[0].locator).unlink()
        self.assertEqual(self.decide()["decision"], "invalid-report")

    def test_path_traversal_uri_and_absolute_locators_are_invalid(self):
        for locator in ("../outside.json", "artifact://anything", "/tmp/outside.json"):
            with self.subTest(locator=locator):
                items = list(self.fx.items)
                items[0] = Evidence(**{**items[0].__dict__, "locator": locator})
                self.assertEqual(self.decide(self.fx.report(items))["decision"], "invalid-report")

    def test_symlink_escape_is_invalid(self):
        outside = self.fx.root.parent / f"{self.fx.root.name}-outside.json"
        outside.write_text("{}", encoding="utf-8")
        link = self.fx.root / "artifacts" / "escape.json"
        link.symlink_to(outside)
        items = list(self.fx.items)
        items[0] = Evidence(**{**items[0].__dict__, "locator": "artifacts/escape.json"})
        try:
            self.assertEqual(self.decide(self.fx.report(items))["decision"], "invalid-report")
        finally:
            outside.unlink()

    def test_wrong_hash_or_byte_count_is_invalid(self):
        items = list(self.fx.items)
        items[0] = Evidence(**{**items[0].__dict__, "sha256": "0" * 64})
        self.assertEqual(self.decide(self.fx.report(items))["decision"], "invalid-report")
        self.fx.artifacts[0]["bytes"] += 1
        self.fx.write_manifest()
        self.assertEqual(self.decide()["decision"], "invalid-report")

    def test_frozen_material_hash_mismatch_is_invalid(self):
        report = self.fx.report(prompt_sha256="0" * 64)
        self.assertEqual(self.decide(report)["decision"], "invalid-report")
        material = self.fx.root / self.fx.materials["dataset"]["locator"]
        material.write_text("mutated dataset", encoding="utf-8")
        self.assertEqual(self.decide()["decision"], "invalid-report")

    def test_missing_or_malformed_frozen_provenance_is_invalid(self):
        self.assertEqual(self.decide(self.fx.report(commit_sha=""))["decision"], "invalid-report")
        self.assertEqual(self.decide(self.fx.report(provider=""))["decision"], "invalid-report")
        self.assertEqual(self.decide(self.fx.report(executed_at="yesterday"))["decision"], "invalid-report")

    def test_wrong_kind_against_manifest_is_invalid(self):
        items = list(self.fx.items)
        idx = next(i for i, item in enumerate(items) if item.gate_id == "live_model_normal")
        items[idx] = Evidence(**{**items[idx].__dict__, "kind": "integration"})
        self.assertEqual(self.decide(self.fx.report(items))["decision"], "invalid-report")

    def test_live_and_manual_payloads_require_complete_source_fields(self):
        self.fx.rewrite_artifact("live_model_normal", mutate=lambda p: p.pop("provider"))
        self.assertEqual(self.decide()["decision"], "invalid-report")
        self.fx.rewrite_artifact("live_model_normal")
        self.fx.rewrite_artifact("receiver_without_idempotency", mutate=lambda p: p.pop("reviewer_id"))
        self.assertEqual(self.decide()["decision"], "invalid-report")

    def test_integration_payload_requires_command_and_nonempty_results(self):
        self.fx.rewrite_artifact("midflow_approval", mutate=lambda p: p.update(run_results=[]))
        self.assertEqual(self.decide()["decision"], "invalid-report")

    def test_integration_aggregate_cannot_claim_passed_with_failed_case(self):
        self.fx.rewrite_artifact(
            "midflow_approval",
            mutate=lambda p: p["run_results"].__setitem__(0, {"test_id": "case-1", "status": "failed"}),
        )
        self.assertEqual(self.decide()["decision"], "invalid-report")

    def test_integration_aggregate_cannot_claim_passed_with_unverified_case(self):
        self.fx.rewrite_artifact(
            "midflow_approval",
            mutate=lambda p: p["run_results"].__setitem__(0, {"test_id": "case-1", "status": "unverified"}),
        )
        self.assertEqual(self.decide()["decision"], "invalid-report")

    def test_manual_review_record_must_be_structured_and_complete(self):
        self.fx.rewrite_artifact("receiver_without_idempotency", mutate=lambda p: p.update(record=None))
        self.assertEqual(self.decide()["decision"], "invalid-report")
        self.fx.rewrite_artifact("receiver_without_idempotency",
                                 mutate=lambda p: p["record"].pop("rationale"))
        self.assertEqual(self.decide()["decision"], "invalid-report")

    def test_rejected_manual_record_cannot_claim_passed_gate(self):
        self.fx.rewrite_artifact(
            "receiver_without_idempotency",
            mutate=lambda p: p["record"].update(decision="rejected"),
        )
        self.assertEqual(self.decide()["decision"], "invalid-report")

    def test_rejected_manual_record_with_failed_status_blocks_release(self):
        self.fx.rewrite_artifact(
            "receiver_without_idempotency", status="failed",
            mutate=lambda p: p["record"].update(decision="rejected"),
        )
        result = self.decide()
        self.assertEqual(result["decision"], "blocked")
        self.assertIn("receiver_without_idempotency", result["failed"])

    def test_malformed_report_and_evidence_types_never_raise(self):
        self.assertEqual(decide(None, self.fx.root)["decision"], "invalid-report")
        self.assertEqual(self.decide(self.fx.report(evidence=None))["decision"], "invalid-report")
        self.assertEqual(self.decide(self.fx.report(evidence=[object()]))["decision"], "invalid-report")
        items = list(self.fx.items)
        items[0] = Evidence(**{**items[0].__dict__, "sha256": None})
        self.assertEqual(self.decide(self.fx.report(items))["decision"], "invalid-report")
        items[0] = Evidence(**{**items[0].__dict__, "locator": None})
        self.assertEqual(self.decide(self.fx.report(items))["decision"], "invalid-report")
        items[0] = Evidence(**{**items[0].__dict__, "status": []})
        self.assertEqual(self.decide(self.fx.report(items))["decision"], "invalid-report")
        items[0] = Evidence(**{**items[0].__dict__, "kind": []})
        self.assertEqual(self.decide(self.fx.report(items))["decision"], "invalid-report")

    def test_invalid_utf8_evidence_and_manifest_are_invalid(self):
        path = self.fx.root / self.fx.items[0].locator
        path.write_bytes(b"\xff\xfe")
        self.assertEqual(self.decide()["decision"], "invalid-report")
        (self.fx.root / "evidence-manifest.json").write_bytes(b"\xff\xfe")
        self.assertEqual(self.decide()["decision"], "invalid-report")

    def test_unsupported_version_duplicate_gate_and_missing_provenance(self):
        self.assertEqual(self.decide(self.fx.report(version=99))["decision"], "invalid-report")
        items = list(self.fx.items) + [self.fx.items[0]]
        self.assertEqual(self.decide(self.fx.report(items))["decision"], "invalid-report")
        self.assertEqual(self.decide(self.fx.report(release_id=""))["decision"], "invalid-report")


if __name__ == "__main__":
    unittest.main()
