import base64
import hashlib
import json
import math
import unittest

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from pathlib import Path

from canonicalization import canonical_json_bytes, canonical_sha256, parse_json_strict


class CanonicalizationTests(unittest.TestCase):
    def test_rfc8785_section_3_2_vector_produces_the_canonical_utf8_bytes(self) -> None:
        value = {
            "numbers": [333333333.33333329, 1e30, 4.50, 2e-3, 1e-27],
            "string": "€$\u000f\nA'B\"\\\\\"/",
            "literals": [None, True, False],
        }

        expected = r'''{"literals":[null,true,false],"numbers":[333333333.3333333,1e+30,4.5,0.002,1e-27],"string":"€$\u000f\nA'B\"\\\\\"/"}'''
        self.assertEqual(canonical_json_bytes(value), expected.encode("utf-8"))

    def test_hash_is_sha256_of_canonical_utf8_bytes(self) -> None:
        value = {"z": 1, "a": "中文"}
        self.assertEqual(canonical_sha256(value), hashlib.sha256(canonical_json_bytes(value)).hexdigest())

    def test_shared_vectors_match_canonical_bytes_and_sha256(self) -> None:
        vectors_path = Path(__file__).with_name("jcs-vectors.json")
        vectors = json.loads(vectors_path.read_text(encoding="utf-8"))
        self.assertEqual(
            {vector["id"] for vector in vectors},
            {
                "rfc-8785-section-3-2",
                "stage5-registry-payload",
                "stage5-report-payload",
                "stage5-registry-event-payload",
                "stage5-registry-event-envelope",
                "stage5-append-receipt",
                "stage5-source-probe-journal-page",
            },
        )
        for vector in vectors:
            with self.subTest(vector=vector["id"]):
                self.assertEqual(
                    canonical_json_bytes(vector["value"]),
                    vector["canonical_utf8"].encode("utf-8"),
                )
                self.assertEqual(canonical_sha256(vector["value"]), vector["sha256"])

    def test_source_probe_page_signature_matches_the_shared_vector(self) -> None:
        vectors_path = Path(__file__).with_name("jcs-vectors.json")
        vectors = json.loads(vectors_path.read_text(encoding="utf-8"))
        vector = next(item for item in vectors if item["id"] == "stage5-source-probe-journal-page")
        public_key = Ed25519PublicKey.from_public_bytes(
            base64.urlsafe_b64decode(vector["ed25519_public_key_base64url"] + "==")
        )
        signature = base64.urlsafe_b64decode(vector["ed25519_signature_base64url"] + "==")
        public_key.verify(signature, canonical_json_bytes(vector["value"]))
        from cryptography.exceptions import InvalidSignature

        with self.assertRaises(InvalidSignature):
            public_key.verify(
                signature,
                canonical_json_bytes({**vector["value"], "query_nonce": "B" * 43}),
            )

    def test_rejects_non_finite_numbers(self) -> None:
        for value in (math.nan, math.inf, -math.inf):
            with self.subTest(value=value), self.assertRaises(ValueError):
                canonical_json_bytes({"value": value})

    def test_rejects_non_string_object_keys(self) -> None:
        with self.assertRaises(ValueError):
            canonical_json_bytes({1: "not a JSON object key"})

    def test_integer_fields_must_stay_within_the_javascript_safe_integer_range(self) -> None:
        self.assertEqual(
            canonical_json_bytes({"count": 9007199254740991}),
            b'{"count":9007199254740991}',
        )
        for raw in ('{"count":9007199254740992}', '{"count":9007199254740993}'):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                parse_json_strict(raw)

    def test_strict_parser_rejects_duplicate_object_keys(self) -> None:
        with self.assertRaisesRegex(ValueError, "duplicate JSON object key"):
            parse_json_strict('{"state":"authorized","state":"consumed"}')

    def test_strict_parser_rejects_non_json_numeric_constants(self) -> None:
        for raw in ('{"value":NaN}', '{"value":Infinity}', '{"value":-Infinity}'):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                parse_json_strict(raw)

    def test_strict_parser_rejects_surrogate_code_points(self) -> None:
        with self.assertRaises(ValueError):
            parse_json_strict('{"value":"\\ud800"}')


    def test_identity_signature_vectors_match_python_jcs_and_ed25519(self) -> None:
        from cryptography.exceptions import InvalidSignature

        repo_root = Path(__file__).resolve().parents[3]
        vector_path = repo_root / "docs/superpowers/specs/stage5-identity-signature-vectors-v1.json"
        document = json.loads(vector_path.read_text(encoding="utf-8"))
        self.assertEqual(document["schema"], "stage5-identity-signature-vectors-v1")
        self.assertIs(document["test_only"], True)

        def decode_base64url(value: str) -> bytes:
            return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))

        profiles = [vector["profile"] for vector in document["vectors"]]
        self.assertEqual(len(profiles), len(set(profiles)))
        for vector in document["vectors"]:
            with self.subTest(profile=vector["profile"]):
                canonical = canonical_json_bytes(vector["message"])
                self.assertEqual(canonical.decode("utf-8"), vector["canonical_utf8"])
                self.assertEqual(hashlib.sha256(canonical).hexdigest(), vector["sha256"])
                public_key = Ed25519PublicKey.from_public_bytes(
                    decode_base64url(vector["public_key_base64url"])
                )
                signature = decode_base64url(vector["signature_base64url"])
                public_key.verify(signature, canonical)

                if "record_content" in vector:
                    record_bytes = canonical_json_bytes(vector["record_content"])
                    self.assertEqual(
                        hashlib.sha256(record_bytes).hexdigest(), vector["record_sha256"]
                    )

                tampered = {
                    **vector["message"],
                    vector["tamper_field"]: "tampered",
                }
                with self.assertRaises(InvalidSignature):
                    public_key.verify(signature, canonical_json_bytes(tampered))

        for vector in document["digest_vectors"]:
            with self.subTest(digest_vector=vector["id"]):
                canonical = canonical_json_bytes(vector["value"])
                self.assertEqual(canonical.decode("utf-8"), vector["canonical_utf8"])
                self.assertEqual(hashlib.sha256(canonical).hexdigest(), vector["sha256"])

    def test_decision_signature_vector_matches_python_jcs_and_ed25519(self) -> None:
        from cryptography.exceptions import InvalidSignature

        repo_root = Path(__file__).resolve().parents[3]
        vector_path = repo_root / "docs/superpowers/specs/stage5-decision-signature-vectors-v1.json"
        document = json.loads(vector_path.read_text(encoding="utf-8"))
        self.assertEqual(document["schema"], "stage5-decision-signature-vectors-v1")
        self.assertIs(document["test_only"], True)
        vector = document["vector"]
        canonical = canonical_json_bytes(vector["message"])
        self.assertEqual(canonical.decode("utf-8"), vector["canonical_utf8"])
        self.assertEqual(hashlib.sha256(canonical).hexdigest(), vector["sha256"])

        def decode_base64url(value: str) -> bytes:
            return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))

        public_key = Ed25519PublicKey.from_public_bytes(
            decode_base64url(vector["public_key_base64url"])
        )
        signature = decode_base64url(vector["signature_base64url"])
        public_key.verify(signature, canonical)
        with self.assertRaises(InvalidSignature):
            public_key.verify(
                signature,
                canonical_json_bytes({**vector["message"], "holdout_outcome": "failed"}),
            )

    def test_stage5_v7_digest_vectors_match_report_and_handoff_boundaries(self) -> None:
        repo_root = Path(__file__).resolve().parents[3]
        vector_path = repo_root / "docs/superpowers/specs/stage5-v7-digest-vectors-v1.json"
        document = json.loads(vector_path.read_text(encoding="utf-8"))
        self.assertEqual(document["schema"], "stage5-v7-digest-vectors-v1")
        self.assertIs(document["test_only"], True)

        def report_preimage(envelope: dict) -> dict:
            report = dict(envelope)
            report["schema"] = "official-blind-holdout-evidence-envelope-v5"
            for field in (
                "gate_id",
                "kind",
                "status",
                "release_id",
                "blind",
                "registry",
                "report_sha256",
                "trust_bundle",
                "trust_bundle_root_signature",
                "trust_bundle_sha256",
                "governance",
            ):
                report.pop(field, None)
            return report

        envelope = document["envelope"]
        preimages = {
            "report_sha256": report_preimage(envelope),
            "handoff_core_sha256": envelope["governance"]["handoff_core"],
            "handoff_evidence_sha256": envelope["governance"],
            "evidence_envelope_sha256": envelope,
        }
        for name, preimage in preimages.items():
            with self.subTest(preimage=name):
                canonical = canonical_json_bytes(preimage)
                self.assertEqual(
                    canonical.decode("utf-8"), document["canonical_preimages"][name]
                )
                self.assertEqual(hashlib.sha256(canonical).hexdigest(), document["expected"][name])

        baseline = {
            "report": canonical_sha256(report_preimage(envelope)),
            "core": canonical_sha256(envelope["governance"]["handoff_core"]),
            "evidence": canonical_sha256(envelope["governance"]),
            "outer": canonical_sha256(envelope),
        }
        receipt_changed = json.loads(json.dumps(envelope))
        receipt_changed["registry"]["receipt_chain"].append(
            {"event_id": "evt-next", "signature": "test-signature"}
        )
        self.assertEqual(canonical_sha256(report_preimage(receipt_changed)), baseline["report"])
        self.assertEqual(canonical_sha256(receipt_changed["governance"]), baseline["evidence"])
        self.assertNotEqual(canonical_sha256(receipt_changed), baseline["outer"])

        identity_changed = json.loads(json.dumps(envelope))
        identity_changed["governance"]["identity_decisions"].append(
            {"event_id": "evt-next", "phase": "preflight"}
        )
        self.assertEqual(canonical_sha256(report_preimage(identity_changed)), baseline["report"])
        self.assertEqual(
            canonical_sha256(identity_changed["governance"]["handoff_core"]), baseline["core"]
        )
        self.assertNotEqual(canonical_sha256(identity_changed["governance"]), baseline["evidence"])
        self.assertNotEqual(canonical_sha256(identity_changed), baseline["outer"])

        core_changed = json.loads(json.dumps(envelope))
        core_changed["governance"]["handoff_core"]["incident_contact"] = "updated"
        self.assertEqual(canonical_sha256(report_preimage(core_changed)), baseline["report"])
        self.assertNotEqual(
            canonical_sha256(core_changed["governance"]["handoff_core"]), baseline["core"]
        )
        self.assertNotEqual(canonical_sha256(core_changed["governance"]), baseline["evidence"])
        self.assertNotEqual(canonical_sha256(core_changed), baseline["outer"])

        report_changed = json.loads(json.dumps(envelope))
        report_changed["run_id"] = "run-other"
        self.assertNotEqual(canonical_sha256(report_preimage(report_changed)), baseline["report"])
        self.assertNotEqual(canonical_sha256(report_changed), baseline["outer"])


if __name__ == "__main__":
    unittest.main()
