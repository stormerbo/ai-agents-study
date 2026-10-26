import hashlib
from pathlib import Path
import sys
import unittest

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

EVALUATION_DIR = Path(__file__).resolve().parents[1] / "p5-agent-delivery" / "evaluation"
sys.path.insert(0, str(EVALUATION_DIR))
from canonicalization import canonical_json_bytes, canonical_sha256
from registry_receipt_verifier import verify_registry_receipts


def private_key(seed):
    return Ed25519PrivateKey.from_private_bytes(bytes.fromhex(seed))


def public_b64(key):
    import base64

    raw = key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii"), raw


def signed(payload, key):
    return key.sign(canonical_json_bytes(payload))


def b64(value):
    import base64

    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


class RegistryReceiptVerifierTests(unittest.TestCase):
    def setUp(self):
        self.root_key = private_key("4c3a1d8f62b0e597a1f4c891d7732a5e9f6b0c4281d3e7a9556c0bf21e84a369")
        self.event_key = private_key("9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60")
        self.anchor_key = private_key("7f4a9c12d3e5b6078a9b0c1d2e3f40517f4a9c12d3e5b6078a9b0c1d2e3f4051")
        root_public, root_raw = public_b64(self.root_key)
        event_public, _ = public_b64(self.event_key)
        anchor_public, anchor_raw = public_b64(self.anchor_key)
        self.trusted_root = {
            "key_id": "offline-root-1",
            "public_key": root_public,
            "fingerprint_sha256": hashlib.sha256(root_raw).hexdigest(),
        }
        self.trusted_anchor = {
            "authority_id": "independent-anchor-1",
            "key_id": "anchor-key-1",
            "public_key": anchor_public,
            "fingerprint_sha256": hashlib.sha256(anchor_raw).hexdigest(),
        }
        self.bundle = {
            "schema": "stage5-receipt-trust-bundle-v1",
            "bundle_id": "bundle-1",
            "hash_profile": "jcs-rfc8785-v1",
            "signature_profile": "ed25519-jcs-receipt-v1",
            "environment_id": "prod-eval",
            "log_id": "official-holdout-v1",
            "issued_at_utc": "2026-10-23T11:00:00Z",
            "keys": [{
                "key_id": "audit-key-1",
                "algorithm": "Ed25519",
                "public_key": event_public,
                "state": "active",
                "not_before_utc": "2026-10-23T11:00:00Z",
                "not_after_utc": "2027-10-23T11:00:00Z",
            }],
        }
        self.bundle_digest = canonical_sha256(self.bundle)
        self.bundle_signature = self.root_key.sign(canonical_json_bytes(self.bundle))
        self.status = {
            "schema": "stage5-key-status-statement-v1",
            "statement_id": "status-1",
            "sequence": 1,
            "bundle_sha256": self.bundle_digest,
            "environment_id": "prod-eval",
            "log_id": "official-holdout-v1",
            "issued_at_utc": "2026-10-23T12:00:00Z",
            "expires_at_utc": "2026-10-23T12:05:00Z",
            "revoked_keys": [],
        }
        self.status_signature = self.root_key.sign(canonical_json_bytes(self.status))
        payload = {"frozen_spec_sha256": "a" * 64}
        event = {
            "schema": "stage5-registry-event-envelope-v1",
            "hash_profile": "jcs-rfc8785-v1",
            "run_id": "run-1",
            "sequence": 1,
            "event_id": "evt-1",
            "previous_event_hash": "0" * 64,
            "event_type": "authorized",
            "actor_subject_id": "owner-1",
            "actor_role": "owner",
            "registry_recorded_at": "2026-10-23T12:00:00Z",
            "actor_asserted_at": None,
            "payload_sha256": canonical_sha256(payload),
            "payload": payload,
        }
        preimage_fields = (
            "schema", "hash_profile", "run_id", "sequence", "event_id", "previous_event_hash",
            "event_type", "actor_subject_id", "actor_role", "registry_recorded_at", "actor_asserted_at", "payload_sha256",
        )
        event["event_hash"] = canonical_sha256({key: event[key] for key in preimage_fields})
        receipt = {
            "schema": "stage5-append-receipt-v1",
            "hash_profile": "jcs-rfc8785-v1",
            "environment_id": "prod-eval",
            "log_id": "official-holdout-v1",
            "run_id": "run-1",
            "sequence": 1,
            "event_id": "evt-1",
            "previous_event_hash": "0" * 64,
            "event_hash": event["event_hash"],
            "registry_recorded_at": event["registry_recorded_at"],
            "signature_profile": "ed25519-jcs-receipt-v1",
            "signature_algorithm": "Ed25519",
            "key_id": "audit-key-1",
        }
        receipt["signature"] = b64(self.event_key.sign(canonical_json_bytes(receipt)))
        self.entries = [{"event": event, "receipt": receipt}]
        self.trust_bundle_root_signature = {
            "schema": "stage5-trust-root-signature-v1",
            "root_key_id": "offline-root-1",
            "profile": "ed25519-jcs-trust-bundle-v1",
            "signature": b64(self.bundle_signature),
        }
        self.key_status_root_signature = {
            "schema": "stage5-trust-root-signature-v1",
            "root_key_id": "offline-root-1",
            "profile": "ed25519-jcs-key-status-v1",
            "signature": b64(self.status_signature),
        }

    def verify(self, **overrides):
        options = {
            "entries": self.entries,
            "run_id": "run-1",
            "environment_id": "prod-eval",
            "log_id": "official-holdout-v1",
            "trust_bundle": self.bundle,
            "trust_bundle_root_signature": self.trust_bundle_root_signature,
            "trust_bundle_sha256": self.bundle_digest,
            "trusted_root": self.trusted_root,
            "permitted_signer_key_id": "audit-key-1",
            "key_status_statement": self.status,
            "key_status_root_signature": self.key_status_root_signature,
            "current_time_utc": "2026-10-23T12:01:00Z",
            "max_freshness_seconds": 600,
            "minimum_status_sequence": 1,
            "clock_skew_seconds": 0,
        }
        options.update(overrides)
        return verify_registry_receipts(**options)

    def prepare_v2_revocation(self, boundary="2026-10-23T12:01:00Z"):
        self.bundle = {
            **self.bundle,
            "keys": [{
                **self.bundle["keys"][0],
                "state": "revoked",
                "revoked_at_utc": "2026-10-23T12:02:00Z",
                "revocation_id": "incident-10",
            }],
        }
        self.bundle_digest = canonical_sha256(self.bundle)
        self.bundle_signature = self.root_key.sign(canonical_json_bytes(self.bundle))
        self.trust_bundle_root_signature["signature"] = b64(self.bundle_signature)
        self.status = {
            "schema": "stage5-key-status-statement-v2",
            "statement_id": "status-2",
            "sequence": 2,
            "bundle_sha256": self.bundle_digest,
            "environment_id": "prod-eval",
            "log_id": "official-holdout-v1",
            "issued_at_utc": "2026-10-23T12:59:00Z",
            "expires_at_utc": "2026-10-23T13:04:00Z",
            "revoked_keys": [{
                "key_id": "audit-key-1",
                "revoked_at_utc": "2026-10-23T12:02:00Z",
                "revocation_id": "incident-10",
                "reason": "compromise_confirmed",
                "compromise_not_before_utc": boundary,
                "incident_review": {"review_id": "review-10", "record_sha256": "c" * 64},
            }],
        }
        self.status_signature = self.root_key.sign(canonical_json_bytes(self.status))
        self.key_status_root_signature["signature"] = b64(self.status_signature)

    def anchor(self, recorded_at="2026-10-23T12:00:30Z"):
        entry = self.entries[0]
        anchor = {
            "schema": "stage5-pre-compromise-anchor-v1",
            "anchor_id": "anchor-1",
            "environment_id": "prod-eval",
            "log_id": "official-holdout-v1",
            "run_id": "run-1",
            "sequence": 1,
            "event_id": entry["event"]["event_id"],
            "event_hash": entry["event"]["event_hash"],
            "key_id": entry["receipt"]["key_id"],
            "receipt_sha256": canonical_sha256(entry),
            "anchor_recorded_at_utc": recorded_at,
            "anchor_authority_id": self.trusted_anchor["authority_id"],
            "anchor_key_id": self.trusted_anchor["key_id"],
            "signature_algorithm": "Ed25519",
            "signature_profile": "ed25519-jcs-precompromise-anchor-v1",
        }
        anchor["signature"] = b64(self.anchor_key.sign(canonical_json_bytes(anchor)))
        return anchor

    def test_accepts_a_valid_root_signed_bundle_status_and_receipt_chain(self):
        result = self.verify()
        self.assertEqual(result["event_count"], 1)
        self.assertEqual(result["head_hash"], self.entries[0]["event"]["event_hash"])

    def test_rejects_payload_tampering_and_missing_external_trust_inputs(self):
        self.entries[0]["event"]["payload"]["frozen_spec_sha256"] = "b" * 64
        with self.assertRaisesRegex(ValueError, "payload|event hash"):
            self.verify()
        self.entries[0]["event"]["payload"]["frozen_spec_sha256"] = "a" * 64
        with self.assertRaisesRegex(ValueError, "root|trust"):
            self.verify(trusted_root=None)

    def test_accepts_revoked_key_only_with_exact_anchor_before_signed_compromise_boundary(self):
        self.prepare_v2_revocation()
        result = self.verify(
            current_time_utc="2026-10-23T13:00:00Z",
            minimum_status_sequence=2,
            pre_compromise_anchors=[self.anchor()],
            trusted_anchor=self.trusted_anchor,
        )
        self.assertEqual(result["historically_anchored_event_ids"], ["evt-1"])

    def test_rejects_v1_or_unknown_boundary_and_anchor_at_or_after_compromise(self):
        self.prepare_v2_revocation(boundary=None)
        with self.assertRaisesRegex(ValueError, "compromise boundary|anchor"):
            self.verify(current_time_utc="2026-10-23T13:00:00Z", minimum_status_sequence=2,
                        pre_compromise_anchors=[self.anchor()], trusted_anchor=self.trusted_anchor)
        self.prepare_v2_revocation()
        with self.assertRaisesRegex(ValueError, "strictly before compromise|anchor time"):
            self.verify(current_time_utc="2026-10-23T13:00:00Z", minimum_status_sequence=2,
                        pre_compromise_anchors=[self.anchor("2026-10-23T12:01:00Z")],
                        trusted_anchor=self.trusted_anchor)
        with self.assertRaisesRegex(ValueError, "sequence rollback"):
            self.verify(current_time_utc="2026-10-23T13:00:00Z", minimum_status_sequence=3)

    def test_rejects_stale_status_and_untrusted_anchor_fingerprint(self):
        with self.assertRaisesRegex(ValueError, "stale|freshness"):
            self.verify(current_time_utc="2026-10-23T12:20:00Z")
        self.prepare_v2_revocation()
        untrusted_anchor = {**self.trusted_anchor, "fingerprint_sha256": "f" * 64}
        with self.assertRaisesRegex(ValueError, "fingerprint"):
            self.verify(
                current_time_utc="2026-10-23T13:00:00Z",
                minimum_status_sequence=2,
                pre_compromise_anchors=[self.anchor()],
                trusted_anchor=untrusted_anchor,
            )

    def test_rejects_boolean_sequence_even_when_receipt_signature_matches(self):
        entry = {"event": dict(self.entries[0]["event"]), "receipt": dict(self.entries[0]["receipt"])}
        entry["receipt"]["sequence"] = True
        entry["receipt"].pop("signature")
        entry["receipt"]["signature"] = b64(self.event_key.sign(canonical_json_bytes(entry["receipt"])))
        self.entries = [entry]
        with self.assertRaisesRegex(ValueError, "sequence"):
            self.verify()


if __name__ == "__main__":
    unittest.main()
