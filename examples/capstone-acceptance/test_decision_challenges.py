from __future__ import annotations

import unittest

import decision_challenges
from decision_challenges import (
    FreshTriggerSnapshot,
    VerifiedDecisionEvent,
    replay_verified_challenges,
)


def challenge(event_id: str, sequence: int, challenge_id: str, *, target_id="acceptance-1", target_digest="a" * 64):
    return VerifiedDecisionEvent(
        sequence=sequence,
        event_id=event_id,
        event_sha256=(event_id[0] * 64),
        payload={
            "schema": "stage5-decision-challenge-v2",
            "event": {
                "event_type": "decision-challenged",
                "challenge_id": challenge_id,
                "target_record_type": "acceptance",
                "target_record_id": target_id,
                "target_record_sha256": target_digest,
                "reason_code": "source-revoked",
                "observed_at_utc": "2026-10-23T12:00:00Z",
                "initiator": {"kind": "service", "service_id": "source-monitor"},
                "trigger": {
                    "kind": "source-state",
                    "source_id": "identity-source",
                    "source_sequence": 8,
                    "source_head_sha256": "f" * 64,
                },
                "trigger_evidence_sha256": "e" * 64,
            },
        },
    )


def resolution(event_id: str, sequence: int, resolution_id: str, challenge_event: VerifiedDecisionEvent):
    event = challenge_event.payload["event"]
    return VerifiedDecisionEvent(
        sequence=sequence,
        event_id=event_id,
        event_sha256=(event_id[0] * 64),
        payload={
            "schema": "stage5-decision-challenge-resolved-v2",
            "event": {
                "event_type": "decision-challenge-resolved",
                "resolution_id": resolution_id,
                "challenge_id": event["challenge_id"],
                "challenge_event_sha256": challenge_event.event_sha256,
                "target_record_type": event["target_record_type"],
                "target_record_id": event["target_record_id"],
                "target_record_sha256": event["target_record_sha256"],
                "fresh_decision_id": f"decision-{resolution_id}",
                "fresh_decision_receipt_sha256": "b" * 64,
                "resolution_evidence_sha256": "c" * 64,
                "initiator": {"kind": "service", "service_id": "verifier"},
            },
        },
    )


def clear_snapshot(resolution_id: str, *, trigger_active=False):
    return FreshTriggerSnapshot(
        environment_id="test-environment",
        decision_log_id="decision-log-1",
        decision_id=f"decision-{resolution_id}",
        receipt_sha256="b" * 64,
        trigger_active=trigger_active,
        trigger_binding=("source-state", "identity-source"),
    )


def reduce_with_verified_evidence(decision_log_id, prefix, *, current_trigger_state):
    # Synthetic stand-in for the upstream signature/source verifier.
    evidence_digests = {
        entry.payload["event"]["challenge_id"]: entry.payload["event"]["trigger_evidence_sha256"]
        for entry in prefix
        if entry.payload.get("schema") == "stage5-decision-challenge-v2"
        and entry.payload.get("event", {}).get("event_type") == "decision-challenged"
    }
    resolution_evidence_digests = {
        entry.payload["event"]["resolution_id"]: entry.payload["event"]["resolution_evidence_sha256"]
        for entry in prefix
        if entry.payload.get("schema") == "stage5-decision-challenge-resolved-v2"
    }
    return replay_verified_challenges(
        decision_log_id,
        prefix,
        environment_id="test-environment",
        current_trigger_state=current_trigger_state,
        verified_trigger_evidence_digests=evidence_digests,
        verified_resolution_evidence_digests=resolution_evidence_digests,
    )


class DecisionChallengeReducerTests(unittest.TestCase):
    def test_target_challenge_gate_distinguishes_blocked_unknown_and_clear(self):
        target = ("acceptance", "acceptance-1", "a" * 64)
        active = challenge("1" * 64, 1, "challenge-1")
        resolved = resolution("2" * 64, 2, "resolution-1", active)
        evaluate_gate = getattr(decision_challenges, "challenge_gate_for_target", None)
        self.assertTrue(callable(evaluate_gate), "missing challenge-specific release gate projection")

        blocked = reduce_with_verified_evidence("decision-log-1", [active], current_trigger_state={})
        unverified = reduce_with_verified_evidence(
            "decision-log-1", [active, resolved], current_trigger_state={"challenge-1": None}
        )
        clear = reduce_with_verified_evidence(
            "decision-log-1",
            [active, resolved],
            current_trigger_state={"challenge-1": clear_snapshot("resolution-1")},
        )
        no_challenges = reduce_with_verified_evidence("decision-log-1", [], current_trigger_state={})

        self.assertEqual(evaluate_gate(blocked, target), "blocked")
        self.assertEqual(evaluate_gate(unverified, target), "unverified")
        self.assertEqual(evaluate_gate(clear, target), "clear")
        self.assertEqual(evaluate_gate(no_challenges, target), "clear")

    def test_a_resolution_closes_only_its_own_challenge(self):
        first = challenge("1" * 64, 1, "challenge-1")
        second = challenge("2" * 64, 2, "challenge-2")
        close_first = resolution("3" * 64, 3, "resolution-1", first)

        result = reduce_with_verified_evidence(
            "decision-log-1",
            [first, second, close_first],
            # A source advancing does not implicitly resolve a challenge;
            # challenge-2 still needs its own resolution event.
            current_trigger_state={
                "challenge-1": clear_snapshot("resolution-1"),
                "challenge-2": clear_snapshot("no-resolution-2"),
            },
        )

        self.assertEqual(result.target_states[("acceptance", "acceptance-1", "a" * 64)], "challenged")
        self.assertEqual(result.active_challenge_ids, ("challenge-2",))

    def test_a_resolved_challenge_still_blocks_when_source_is_unavailable(self):
        challenged = challenge("1" * 64, 1, "challenge-1")
        closed = resolution("2" * 64, 2, "resolution-1", challenged)

        result = reduce_with_verified_evidence(
            "decision-log-1",
            [challenged, closed],
            current_trigger_state={"challenge-1": None},
        )

        self.assertEqual(result.target_states[("acceptance", "acceptance-1", "a" * 64)], "unverified")
        self.assertEqual(result.unverified_challenge_ids, ("challenge-1",))

    def test_resolution_must_follow_and_match_the_challenge_target(self):
        challenged = challenge("1" * 64, 1, "challenge-1")
        mismatched = resolution("2" * 64, 2, "resolution-1", challenged)
        payload = dict(mismatched.payload)
        payload["event"] = {**payload["event"], "target_record_sha256": "d" * 64}
        mismatched = VerifiedDecisionEvent(
            mismatched.sequence, mismatched.event_id, mismatched.event_sha256, payload
        )

        with self.assertRaisesRegex(ValueError, "target"):
            reduce_with_verified_evidence(
                "decision-log-1",
                [challenged, mismatched],
                current_trigger_state={"challenge-1": clear_snapshot("resolution-1")},
            )

    def test_resolution_ids_are_unique_within_the_decision_log(self):
        first = challenge("1" * 64, 1, "challenge-1")
        second = challenge("2" * 64, 2, "challenge-2", target_id="release-1")
        close_first = resolution("3" * 64, 3, "resolution-shared", first)
        close_second = resolution("4" * 64, 4, "resolution-shared", second)

        with self.assertRaisesRegex(ValueError, "resolution id"):
            reduce_with_verified_evidence(
                "decision-log-1",
                [first, second, close_first, close_second],
                current_trigger_state={
                    "challenge-1": clear_snapshot("resolution-shared"),
                    "challenge-2": clear_snapshot("resolution-shared"),
                },
            )

    def test_resolution_requires_its_exact_fresh_decision_receipt(self):
        challenged = challenge("1" * 64, 1, "challenge-1")
        closed = resolution("2" * 64, 2, "resolution-1", challenged)
        event = dict(closed.payload["event"])
        event["fresh_decision_id"] = "unrelated-decision"
        payload = {**closed.payload, "event": event}
        mismatched = VerifiedDecisionEvent(
            closed.sequence, closed.event_id, closed.event_sha256, payload
        )

        with self.assertRaisesRegex(ValueError, "fresh decision"):
            reduce_with_verified_evidence(
                "decision-log-1",
                [challenged, mismatched],
                current_trigger_state={"challenge-1": clear_snapshot("resolution-1")},
            )

    def test_one_target_record_id_cannot_change_digest_within_a_log(self):
        first = challenge("1" * 64, 1, "challenge-1")
        conflicting = challenge(
            "2" * 64, 2, "challenge-2", target_digest="e" * 64
        )

        with self.assertRaisesRegex(ValueError, "target record digest changed"):
            reduce_with_verified_evidence(
                "decision-log-1",
                [first, conflicting],
                current_trigger_state={
                    "challenge-1": clear_snapshot("no-resolution-1", trigger_active=True),
                    "challenge-2": clear_snapshot("no-resolution-2", trigger_active=True),
                },
            )

    def test_only_a_verified_receipt_prefix_can_be_reduced(self):
        first = challenge("1" * 64, 1, "challenge-1")
        gap = challenge("3" * 64, 3, "challenge-2")

        with self.assertRaisesRegex(ValueError, "sequence"):
            reduce_with_verified_evidence(
                "decision-log-1",
                [first, gap],
                current_trigger_state={
                    "challenge-1": clear_snapshot("no-resolution-1", trigger_active=True),
                    "challenge-2": clear_snapshot("no-resolution-2", trigger_active=True),
                },
            )

    def test_trigger_snapshot_accepts_only_boolean_or_unknown_values(self):
        challenged = challenge("1" * 64, 1, "challenge-1")

        with self.assertRaisesRegex(ValueError, "trigger state"):
            reduce_with_verified_evidence(
                "decision-log-1",
                [challenged],
                current_trigger_state={"challenge-1": FreshTriggerSnapshot(
                    "test-environment",
                    "decision-log-1",
                    "x",
                    "b" * 64,
                    1,
                    ("source-state", "identity-source"),
                )},
            )

    def test_reducer_rejects_legacy_v1_challenge_events(self):
        legacy = challenge("1" * 64, 1, "challenge-1")
        legacy_payload = {**legacy.payload, "schema": "stage5-decision-challenge-v1"}
        legacy = VerifiedDecisionEvent(legacy.sequence, legacy.event_id, legacy.event_sha256, legacy_payload)

        with self.assertRaisesRegex(ValueError, "unsupported challenge schema"):
            replay_verified_challenges(
                "decision-log-1",
                [legacy],
                environment_id="test-environment",
                current_trigger_state={},
                verified_trigger_evidence_digests={"challenge-1": "e" * 64},
                verified_resolution_evidence_digests={},
            )

    def test_reducer_requires_preverified_trigger_evidence_digest(self):
        challenged = challenge("1" * 64, 1, "challenge-1")

        with self.assertRaisesRegex(ValueError, "trigger evidence"):
            replay_verified_challenges(
                "decision-log-1",
                [challenged],
                environment_id="test-environment",
                current_trigger_state={},
                verified_trigger_evidence_digests={},
                verified_resolution_evidence_digests={},
            )

        with self.assertRaisesRegex(ValueError, "trigger evidence"):
            replay_verified_challenges(
                "decision-log-1",
                [challenged],
                environment_id="test-environment",
                current_trigger_state={},
                verified_trigger_evidence_digests={"challenge-1": "d" * 64},
                verified_resolution_evidence_digests={},
            )

    def test_reducer_rejects_unknown_versions_of_challenge_events(self):
        unsupported = challenge("1" * 64, 1, "challenge-1")
        payload = {**unsupported.payload, "schema": "stage5-decision-challenge-v3"}
        unsupported = VerifiedDecisionEvent(
            unsupported.sequence, unsupported.event_id, unsupported.event_sha256, payload
        )

        with self.assertRaisesRegex(ValueError, "unsupported challenge schema"):
            replay_verified_challenges(
                "decision-log-1",
                [unsupported],
                environment_id="test-environment",
                current_trigger_state={},
                verified_trigger_evidence_digests={"challenge-1": "e" * 64},
                verified_resolution_evidence_digests={},
            )

    def test_source_state_trigger_requires_a_safe_integer_sequence_and_digest(self):
        malformed = challenge("1" * 64, 1, "challenge-1")
        event = dict(malformed.payload["event"])
        event["trigger"] = {**event["trigger"], "source_sequence": True}
        payload = {**malformed.payload, "event": event}
        malformed = VerifiedDecisionEvent(
            malformed.sequence, malformed.event_id, malformed.event_sha256, payload
        )

        with self.assertRaisesRegex(ValueError, "invalid v2 challenge event"):
            reduce_with_verified_evidence(
                "decision-log-1", [malformed], current_trigger_state={}
            )

    def test_resolution_requires_preverified_resolution_evidence_digest(self):
        challenged = challenge("1" * 64, 1, "challenge-1")
        closed = resolution("2" * 64, 2, "resolution-1", challenged)
        common = {
            "environment_id": "test-environment",
            "current_trigger_state": {"challenge-1": clear_snapshot("resolution-1")},
            "verified_trigger_evidence_digests": {"challenge-1": "e" * 64},
        }

        with self.assertRaisesRegex(ValueError, "resolution evidence"):
            replay_verified_challenges(
                "decision-log-1",
                [challenged, closed],
                verified_resolution_evidence_digests={},
                **common,
            )

        with self.assertRaisesRegex(ValueError, "resolution evidence"):
            replay_verified_challenges(
                "decision-log-1",
                [challenged, closed],
                verified_resolution_evidence_digests={"resolution-1": "d" * 64},
                **common,
            )

    def test_fresh_resolution_snapshot_must_match_the_challenge_trigger_scope(self):
        challenged = challenge("1" * 64, 1, "challenge-1")
        closed = resolution("2" * 64, 2, "resolution-1", challenged)
        wrong_source = FreshTriggerSnapshot(
            environment_id="test-environment",
            decision_log_id="decision-log-1",
            decision_id="decision-resolution-1",
            receipt_sha256="b" * 64,
            trigger_active=False,
            trigger_binding=("source-state", "other-source"),
        )

        with self.assertRaisesRegex(ValueError, "trigger binding"):
            reduce_with_verified_evidence(
                "decision-log-1",
                [challenged, closed],
                current_trigger_state={"challenge-1": wrong_source},
            )

    def test_policy_trigger_resolution_binds_exact_policy_and_rule(self):
        challenged = challenge("1" * 64, 1, "challenge-policy")
        event = {
            **challenged.payload["event"],
            "trigger": {"kind": "policy", "policy_id": "release-policy", "rule_id": "source-unavailable"},
        }
        challenged = VerifiedDecisionEvent(
            challenged.sequence,
            challenged.event_id,
            challenged.event_sha256,
            {**challenged.payload, "event": event},
        )
        closed = resolution("2" * 64, 2, "resolution-policy", challenged)
        snapshot = FreshTriggerSnapshot(
            environment_id="test-environment",
            decision_log_id="decision-log-1",
            decision_id="decision-resolution-policy",
            receipt_sha256="b" * 64,
            trigger_active=False,
            trigger_binding=("policy", "release-policy", "source-unavailable"),
        )

        result = reduce_with_verified_evidence(
            "decision-log-1",
            [challenged, closed],
            current_trigger_state={"challenge-policy": snapshot},
        )

        self.assertEqual(
            result.challenge_states["challenge-policy"],
            "resolved",
        )

    def test_fresh_snapshot_must_match_environment_and_decision_log_scope(self):
        challenged = challenge("1" * 64, 1, "challenge-1")
        closed = resolution("2" * 64, 2, "resolution-1", challenged)
        wrong_scope = FreshTriggerSnapshot(
            environment_id="other-environment",
            decision_log_id="decision-log-1",
            decision_id="decision-resolution-1",
            receipt_sha256="b" * 64,
            trigger_active=False,
            trigger_binding=("source-state", "identity-source"),
        )

        with self.assertRaisesRegex(ValueError, "scope"):
            reduce_with_verified_evidence(
                "decision-log-1",
                [challenged, closed],
                current_trigger_state={"challenge-1": wrong_scope},
            )

        wrong_log = FreshTriggerSnapshot(
            environment_id="test-environment",
            decision_log_id="other-decision-log",
            decision_id="decision-resolution-1",
            receipt_sha256="b" * 64,
            trigger_active=False,
            trigger_binding=("source-state", "identity-source"),
        )
        with self.assertRaisesRegex(ValueError, "scope"):
            reduce_with_verified_evidence(
                "decision-log-1",
                [challenged, closed],
                current_trigger_state={"challenge-1": wrong_log},
            )


if __name__ == "__main__":
    unittest.main()
