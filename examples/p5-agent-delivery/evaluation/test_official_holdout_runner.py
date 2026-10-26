from __future__ import annotations

import unittest
from dataclasses import asdict, dataclass, field
import hashlib
import json
import pickle
from datetime import datetime, timezone
from pathlib import Path
import sys
import traceback
from typing import Callable

from canonicalization import HASH_PROFILE, canonical_sha256

from official_holdout import (
    CandidateOutput,
    HoldoutReservation,
    HoldoutSessionCapability,
    HoldoutRunError,
    HoldoutRuntimeIdentity,
    HoldoutRunSpec,
    PublicHoldoutAttempt,
    RegistryEventSnapshot,
    RegistrySnapshot,
    ScoredAttempt,
    SealedHoldoutOutputs,
    canonical_run_spec_sha256,
    execute_official_holdout,
    _validate_spec,
    executor_bundle_sha256,
)
from subprocess_candidate import SubprocessCandidateRuntime


@dataclass(frozen=True)
class Case:
    case_id: str
    public_input: dict
    private_label: dict


@dataclass(frozen=True)
class Reservation:
    event_id: str
    spec_sha256: str
    session_capability: HoldoutSessionCapability | None = field(default=None, repr=False)
    registry_snapshot: RegistrySnapshot | None = None


class DataSession:
    def __init__(self, cases: tuple[Case, ...]) -> None:
        self._cases = cases
        self._index = 0
        self._outputs: list[CandidateOutput] = []
        self._reservation_event_id = ""
        self._spec: HoldoutRunSpec | None = None
        self.closed = False
        self.sealed = False
        self.aborted = False
        self.sealed_outputs: SealedHoldoutOutputs | None = None

    def next_attempt(self) -> PublicHoldoutAttempt | None:
        if self.closed or self._index == len(self._cases):
            return None
        index = self._index
        self._index += 1
        return PublicHoldoutAttempt(f"task-{index + 1:04d}", self._cases[index].public_input)

    def record_output(self, attempt_id: str, output: dict) -> None:
        self._outputs.append(CandidateOutput(attempt_id, output))

    def close_and_seal(self) -> SealedHoldoutOutputs:
        self.closed = True
        self.sealed = True
        attempt_ids = tuple(output.attempt_id for output in self._outputs)
        assert self._spec is not None
        digest = canonical_sha256([
            {"attempt_id": output.attempt_id, "output": output.output}
            for output in self._outputs
        ])
        self.sealed_outputs = SealedHoldoutOutputs(
            seal_id="seal-1",
            run_id=self._spec.run_id,
            reservation_event_id=self._reservation_event_id,
            frozen_spec_sha256=canonical_run_spec_sha256(self._spec),
            candidate_sha256=self._spec.candidate_sha256,
            image_digest=self._spec.image_digest,
            dataset_sha256=self._spec.dataset_sha256,
            scorer_sha256=self._spec.scorer_sha256,
            output_sha256=digest,
            attempt_ids=attempt_ids,
            outputs=tuple(self._outputs),
        )
        return self.sealed_outputs

    def abort(self) -> None:
        self.closed = True
        self.aborted = True


class DataPlane:
    def __init__(self, cases: tuple[Case, ...]) -> None:
        self.cases = cases
        self.session: DataSession | None = DataSession(cases)
        self.opened_capabilities: list[str] = []
        self.opened_runtime_identities: list[HoldoutRuntimeIdentity] = []

    def open_session(
        self,
        capability: str,
        runtime_identity: HoldoutRuntimeIdentity,
        run_spec: HoldoutRunSpec,
    ) -> DataSession:
        assert self.session is not None
        self.opened_capabilities.append(capability)
        self.opened_runtime_identities.append(runtime_identity)
        self.session._reservation_event_id = runtime_identity.reservation_event_id
        self.session._spec = run_spec
        return self.session

    def reconcile_seal(
        self,
        reservation_event_id: str,
        runtime_identity: HoldoutRuntimeIdentity,
        run_spec: HoldoutRunSpec,
    ) -> SealedHoldoutOutputs | None:
        assert self.session is not None
        sealed = self.session.sealed_outputs
        if not self.session.sealed or sealed is None:
            return None
        if (
            sealed.reservation_event_id != reservation_event_id
            or runtime_identity.reservation_event_id != reservation_event_id
            or sealed.run_id != run_spec.run_id
            or runtime_identity.run_id != run_spec.run_id
        ):
            raise ValueError("seal reconciliation identity mismatch")
        return sealed

    def abort_session(self, reservation_event_id: str) -> None:
        assert self.session is not None
        self.session.abort()


class Registry:
    def __init__(self, cases: tuple[Case, ...]) -> None:
        self.cases = cases
        self.events: list[tuple[str, dict]] = []
        self.data_plane = DataPlane(cases)
        self.reservation: Reservation | None = None

    def reconcile(self, run_id: str) -> RegistrySnapshot:
        snapshots = tuple(
            RegistryEventSnapshot(
                event_id=payload.get("event_id", f"event-{index}"),
                state=state,
                payload_sha256=canonical_sha256(payload),
                payload=payload,
            )
            for index, (state, payload) in enumerate(self.events, start=1)
        )
        state = snapshots[-1].state if snapshots else "not_found"
        return RegistrySnapshot(run_id=run_id, state=state, events=snapshots)

    @staticmethod
    def _event_payload(spec: HoldoutRunSpec, event_id: str, role: str, previous_event_id: str | None) -> dict:
        actor_id = {
            "owner": spec.owner_id,
            "executor": spec.executor_id,
            "recovery_operator": spec.recovery_operator_id,
        }[role]
        return {
            "event_id": event_id,
            "actor_id": actor_id,
            "actor_role": role,
            "recorded_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
            "previous_event_id": previous_event_id,
            "run_id": spec.run_id,
            "holdout_version": spec.holdout_version,
            "frozen_spec_sha256": canonical_run_spec_sha256(spec),
            "candidate_sha256": spec.candidate_sha256,
            "image_digest": spec.image_digest,
            "dataset_sha256": spec.dataset_sha256,
            "scorer_sha256": spec.scorer_sha256,
            "executor_sha256": spec.executor_sha256,
            "hash_profile": spec.hash_profile,
        }

    def recover_abort(
        self,
        run_id: str,
        reservation_event_id: str,
        terminal_event_id: str,
        reason: str,
        no_execution_evidence_ref: str,
        no_execution_evidence_sha256: str,
    ) -> RegistryEventSnapshot:
        if self.reconcile(run_id).state != "reserved":
            raise ValueError("only a reserved run can be recovery-aborted")
        if (
            not no_execution_evidence_ref.startswith("runtime-audit:")
            or len(no_execution_evidence_sha256) != 64
            or any(char not in "0123456789abcdef" for char in no_execution_evidence_sha256)
        ):
            raise ValueError("recovery requires a trusted immutable no-execution evidence reference and hash")
        payload = {
            "run_id": run_id,
            "reservation_event_id": reservation_event_id,
            "terminal_event_id": terminal_event_id,
            "reason": reason,
            "no_execution_evidence_ref": no_execution_evidence_ref,
            "no_execution_evidence_sha256": no_execution_evidence_sha256,
        }
        self.events.append(("aborted", payload))
        return self.reconcile(run_id).events[-1]

    def reserve(self, spec: HoldoutRunSpec) -> Reservation:
        authorization_event_id = spec.authorization_event_id
        reservation_event_id = "reservation-1"
        self.events.append(("authorized", self._event_payload(spec, authorization_event_id, "owner", None)))
        self.events.append(("reserved", self._event_payload(spec, reservation_event_id, "executor", authorization_event_id)))
        spec_hash = canonical_run_spec_sha256(spec)
        self.reservation = Reservation(
            reservation_event_id,
            spec_hash,
            HoldoutSessionCapability("fixture-one-time-capability"),
            self.reconcile(spec.run_id),
        )
        return self.reservation

    def append_terminal(
        self, reservation_event_id: str, terminal_event_id: str, state: str, report: dict
    ) -> None:
        self.events.append((state, {
            "reservation_event_id": reservation_event_id,
            "terminal_event_id": terminal_event_id,
            "report_sha256": report.get("report_sha256"),
            "report": report,
        }))


class Candidate:
    candidate_sha256 = "a" * 64
    image_digest = "sha256:" + "b" * 64
    max_output_bytes = 1024

    def __init__(self) -> None:
        self.seen: list[tuple[str, dict]] = []

    def execute(self, case_id: str, public_input: dict, deadline_utc: str, remaining_budget_usd: str) -> dict:
        self.seen.append((case_id, public_input))
        return {
            "output": {"answer": "A"},
            "cost_usd": "0.10",
            "input_tokens": 12,
            "output_tokens": 2,
            "latency_ms": 12,
        }


@dataclass
class FrozenScorer:
    scorer_sha256: str
    score_case: Callable[[Case, dict], bool]
    data_plane: DataPlane | None = None
    stored_scores: dict[tuple[str, str, str], tuple[ScoredAttempt, ...]] = field(default_factory=dict)

    @staticmethod
    def _score_key(seal_id: str, scorer_sha256: str, output_sha256: str) -> tuple[str, str, str]:
        return seal_id, scorer_sha256, output_sha256

    def score_sealed(self, outputs: SealedHoldoutOutputs) -> tuple[ScoredAttempt, ...]:
        key = self._score_key(outputs.seal_id, self.scorer_sha256, outputs.output_sha256)
        if key in self.stored_scores:
            return self.stored_scores[key]
        assert self.data_plane is not None
        scores = tuple(
            ScoredAttempt(attempt_id, self.score_case(case, output.output))
            for attempt_id, case, output in zip(
                outputs.attempt_ids,
                self.data_plane.cases,
                outputs.outputs,
                strict=True,
            )
        )
        self.stored_scores[key] = scores
        return scores

    def reconcile_sealed(
        self, seal_id: str, scorer_sha256: str, output_sha256: str
    ) -> tuple[ScoredAttempt, ...] | None:
        return self.stored_scores.get(self._score_key(seal_id, scorer_sha256, output_sha256))


def scorer(function: Callable[[Case, dict], bool]) -> FrozenScorer:
    return FrozenScorer("d" * 64, function)


def run_holdout(*, spec: HoldoutRunSpec, registry: Registry, candidate, scorer, data_plane=None):
    selected_data_plane = data_plane or registry.data_plane
    if isinstance(scorer, FrozenScorer):
        scorer.data_plane = selected_data_plane
    return execute_official_holdout(
        spec=spec,
        registry=registry,
        data_plane=selected_data_plane,
        candidate=candidate,
        scorer=scorer,
    )


def spec(
    *, assurance_profile="single-authority-v1", append_authority_domain_id="registry-domain-1",
    signing_key_custodian_domain_id="registry-keys-1", witness_authority_domain_id=None,
    witness_root_fingerprint_sha256=None,
) -> HoldoutRunSpec:
    return HoldoutRunSpec(
        holdout_version="holdout-v7",
        run_id="run-2026-01",
        authorization_event_id="authorization-2026-01",
        owner_id="owner-2026-01",
        executor_id="executor-2026-01",
        recovery_operator_id="recovery-2026-01",
        assurance_profile=assurance_profile,
        append_authority_domain_id=append_authority_domain_id,
        signing_key_custodian_domain_id=signing_key_custodian_domain_id,
        witness_authority_domain_id=witness_authority_domain_id,
        witness_root_fingerprint_sha256=witness_root_fingerprint_sha256,
        candidate_sha256="a" * 64,
        image_digest="sha256:" + "b" * 64,
        dataset_sha256="c" * 64,
        scorer_sha256="d" * 64,
        executor_sha256=executor_bundle_sha256(),
        max_budget_usd="1.00",
        max_cases=1,
        minimum_task_count=1,
        minimum_pass_rate_bps=10_000,
        require_all_tasks_pass=True,
        max_output_bytes=1024,
        deadline_utc="2099-10-22T00:00:00Z",
        stop_conditions=(
            "budget", "deadline", "side-effect", "permission-boundary",
            "evidence-missing", "label-leak", "identity-mismatch",
        ),
    )


class OfficialHoldoutRunnerTests(unittest.TestCase):
    def test_freezes_assurance_profile_and_rejects_non_independent_witness_domain(self) -> None:
        single_authority = spec()
        dual_witness = spec(
            assurance_profile="dual-witness-v1",
            witness_authority_domain_id="witness-domain-1",
            witness_root_fingerprint_sha256="e" * 64,
        )
        _validate_spec(dual_witness)
        self.assertNotEqual(
            canonical_run_spec_sha256(single_authority),
            canonical_run_spec_sha256(dual_witness),
        )
        with self.assertRaisesRegex(HoldoutRunError, "independent trust domain"):
            _validate_spec(spec(
                assurance_profile="dual-witness-v1",
                witness_authority_domain_id="registry-domain-1",
                witness_root_fingerprint_sha256="e" * 64,
            ))

    def test_capability_wrapper_rejects_empty_values_and_is_immutable(self) -> None:
        with self.assertRaisesRegex(ValueError, "must be a non-empty string"):
            HoldoutSessionCapability("")
        capability = HoldoutSessionCapability("fixture-one-time-capability")
        with self.assertRaisesRegex(AttributeError, "immutable"):
            capability._HoldoutSessionCapability__value = "replaced"
        self.assertEqual(capability.reveal_for_custodian(), "fixture-one-time-capability")
        with self.assertRaisesRegex(RuntimeError, "already been presented"):
            capability.reveal_for_custodian()

    def test_independent_scorer_runs_only_after_data_session_is_sealed(self) -> None:
        registry = Registry((Case("case-1", {"question": "Q"}, {"answer": "A"}),))
        session = registry.data_plane.session
        candidate = Candidate()
        scoring_observations: list[tuple[bool, bool]] = []

        class OrderedScorer(FrozenScorer):
            def score_sealed(self, sealed: SealedHoldoutOutputs) -> tuple[ScoredAttempt, ...]:
                scoring_observations.append((session.closed, session.sealed))
                self.assert_manifest(sealed)
                return (ScoredAttempt("task-0001", True),)

            @staticmethod
            def assert_manifest(sealed: SealedHoldoutOutputs) -> None:
                assert sealed.attempt_ids == ("task-0001",)
                assert sealed.run_id == spec().run_id
                assert sealed.reservation_event_id == "reservation-1"
                assert sealed.frozen_spec_sha256 == canonical_run_spec_sha256(spec())
                assert sealed.candidate_sha256 == spec().candidate_sha256
                assert sealed.image_digest == spec().image_digest
                assert sealed.dataset_sha256 == spec().dataset_sha256
                assert sealed.scorer_sha256 == spec().scorer_sha256

        report = run_holdout(
            spec=spec(),
            registry=registry,
            candidate=candidate,
            scorer=OrderedScorer("d" * 64, lambda _case, _output: True),
        )

        self.assertFalse(hasattr(registry.reservation, "cases"))
        self.assertIsInstance(registry.reservation.session_capability, HoldoutSessionCapability)
        self.assertNotIn("fixture-one-time-capability", repr(registry.reservation.session_capability))
        self.assertEqual(registry.data_plane.opened_capabilities, ["fixture-one-time-capability"])
        self.assertNotIn("fixture-one-time-capability", repr(registry.reservation))
        serialized = asdict(registry.reservation)
        self.assertNotIn("fixture-one-time-capability", repr(serialized))
        self.assertEqual(serialized["session_capability"], "<redacted>")
        self.assertNotIn("fixture-one-time-capability", json.dumps(serialized))
        with self.assertRaisesRegex(TypeError, "cannot be pickled"):
            pickle.dumps(registry.reservation.session_capability)
        self.assertNotIn(
            "fixture-one-time-capability",
            repr(HoldoutReservation(
                "reservation-1", "f" * 64, HoldoutSessionCapability("fixture-one-time-capability")
            )),
        )
        self.assertEqual(registry.data_plane.opened_runtime_identities, [HoldoutRuntimeIdentity(
            run_id=spec().run_id,
            reservation_event_id="reservation-1",
            candidate_sha256=spec().candidate_sha256,
            image_digest=spec().image_digest,
            dataset_sha256=spec().dataset_sha256,
            scorer_sha256=spec().scorer_sha256,
            executor_sha256=spec().executor_sha256,
        )])
        self.assertEqual(scoring_observations, [(True, True)])
        self.assertEqual(report["quality_decision"], "passed")
        self.assertEqual(candidate.seen, [("task-0001", {"question": "Q"})])
        self.assertNotIn("fixture-one-time-capability", str(report))
        self.assertNotIn("fixture-one-time-capability", str(registry.events))

    def test_scorer_is_not_called_when_seal_identity_does_not_match_frozen_run(self) -> None:
        registry = Registry((Case("case-1", {"question": "Q"}, {"answer": "A"}),))
        data_plane = registry.data_plane
        session = data_plane.session
        original_close = session.close_and_seal

        def forged_seal() -> SealedHoldoutOutputs:
            sealed = original_close()
            return SealedHoldoutOutputs(**{**sealed.__dict__, "dataset_sha256": "f" * 64})

        session.close_and_seal = forged_seal
        scores: list[bool] = []
        with self.assertRaisesRegex(HoldoutRunError, "sealed outputs do not match"):
            run_holdout(
                spec=spec(), registry=registry, candidate=Candidate(),
                scorer=scorer(lambda _case, _output: scores.append(True) or True),
            )

        self.assertEqual(scores, [])
        self.assertEqual(registry.events[-1][0], "aborted")

    def test_lost_seal_response_reconciles_and_scores_without_rerunning_candidate(self) -> None:
        registry = Registry((Case("case-1", {"question": "Q"}, {"answer": "A"}),))
        session = registry.data_plane.session
        original_close = session.close_and_seal
        original_reconcile = registry.data_plane.reconcile_seal
        reconcile_calls = []

        def close_then_lose_response():
            original_close()
            raise TimeoutError("seal response was lost")

        def reconcile_seal(reservation_event_id, runtime_identity, run_spec):
            reconcile_calls.append(reservation_event_id)
            self.assertEqual(reservation_event_id, "reservation-1")
            self.assertEqual(runtime_identity.run_id, spec().run_id)
            self.assertEqual(run_spec.run_id, spec().run_id)
            return original_reconcile(reservation_event_id, runtime_identity, run_spec)

        session.close_and_seal = close_then_lose_response
        registry.data_plane.reconcile_seal = reconcile_seal
        candidate = Candidate()
        report = run_holdout(
            spec=spec(), registry=registry, candidate=candidate,
            scorer=scorer(lambda _case, _output: True),
        )

        self.assertEqual(report["decision"], "completed")
        self.assertEqual(report["output_seal_id"], "seal-1")
        self.assertEqual(reconcile_calls, ["reservation-1"])
        self.assertEqual(len(candidate.seen), 1)
        self.assertEqual(registry.events[-1][0], "consumed")

    def test_confirmed_absent_seal_allows_revoke_then_abort(self) -> None:
        registry = Registry((Case("case-1", {"question": "Q"}, {"answer": "A"}),))
        session = registry.data_plane.session

        def close_without_commit():
            raise TimeoutError("seal was not committed")

        session.close_and_seal = close_without_commit
        candidate = Candidate()
        with self.assertRaisesRegex(HoldoutRunError, "run aborted after reservation"):
            run_holdout(
                spec=spec(), registry=registry, candidate=candidate,
                scorer=scorer(lambda _case, _output: True),
            )

        self.assertIsNone(registry.data_plane.reconcile_seal(
            "reservation-1", registry.data_plane.opened_runtime_identities[0], spec()
        ))
        self.assertTrue(session.aborted)
        self.assertEqual(registry.events[-1][0], "aborted")
        self.assertEqual(len(candidate.seen), 1)

    def test_unknown_seal_reconciliation_leaves_registry_reserved(self) -> None:
        registry = Registry((Case("case-1", {"question": "Q"}, {"answer": "A"}),))
        session = registry.data_plane.session
        original_close = session.close_and_seal

        def close_then_lose_response():
            original_close()
            raise TimeoutError("seal response was lost")

        def unknown_reconciliation(reservation_event_id, runtime_identity, run_spec):
            raise TimeoutError("custodian seal state is unavailable")

        session.close_and_seal = close_then_lose_response
        registry.data_plane.reconcile_seal = unknown_reconciliation
        with self.assertRaisesRegex(HoldoutRunError, "seal outcome is unknown"):
            run_holdout(
                spec=spec(), registry=registry, candidate=Candidate(),
                scorer=scorer(lambda _case, _output: True),
            )

        self.assertEqual([event[0] for event in registry.events], ["authorized", "reserved"])
        self.assertEqual(registry.reconcile(spec().run_id).state, "reserved")
        self.assertFalse(session.aborted)

    def test_unknown_data_session_revocation_leaves_registry_reservation_open(self) -> None:
        registry = Registry((Case("case-1", {"question": "Q"}, {"answer": "A"}),))
        data_plane = registry.data_plane

        class FailingCandidate(Candidate):
            def execute(self, attempt_id, public_input, deadline_utc, remaining_budget_usd):
                raise TimeoutError("candidate timed out")

        def unknown_abort(reservation_event_id: str) -> None:
            raise TimeoutError("custodian did not confirm capability revocation")

        data_plane.abort_session = unknown_abort
        with self.assertRaisesRegex(HoldoutRunError, "revocation outcome is unknown"):
            run_holdout(
                spec=spec(), registry=registry, candidate=FailingCandidate(),
                scorer=scorer(lambda _case, _output: True),
            )

        self.assertEqual([event[0] for event in registry.events], ["authorized", "reserved"])
        self.assertEqual(registry.reconcile(spec().run_id).state, "reserved")

    def test_lost_session_open_response_revokes_by_reservation_id_before_abort(self) -> None:
        registry = Registry((Case("case-1", {"question": "Q"}, {"answer": "A"}),))
        data_plane = registry.data_plane

        def open_then_lose_response(
            capability: str,
            runtime_identity: HoldoutRuntimeIdentity,
            run_spec: HoldoutRunSpec,
        ):
            data_plane.session = DataSession(data_plane.cases)
            raise TimeoutError("session opened but response was lost")

        data_plane.open_session = open_then_lose_response
        with self.assertRaisesRegex(HoldoutRunError, "run aborted after reservation"):
            run_holdout(
                spec=spec(), registry=registry, data_plane=data_plane, candidate=Candidate(),
                scorer=scorer(lambda _case, _output: True),
            )

        self.assertTrue(data_plane.session.aborted)
        self.assertEqual([event[0] for event in registry.events], ["authorized", "reserved", "aborted"])

    def test_bounded_subprocess_runtime_completes_the_holdout_adapter_contract(self) -> None:
        candidate = SubprocessCandidateRuntime(
            argv=(
                sys.executable,
                "-c",
                "import json,sys; request=json.load(sys.stdin); print(json.dumps({'output': {'answer': request['public_input']['question']}, 'cost_usd': '0.10', 'input_tokens': 12, 'output_tokens': 2, 'latency_ms': 12}))",
            ),
            candidate_sha256="a" * 64,
            image_digest="sha256:" + "b" * 64,
            max_output_bytes=1024,
        )
        registry = Registry((Case("case-1", {"question": "A"}, {"answer": "A"}),))

        report = run_holdout(
            spec=spec(),
            registry=registry,
            candidate=candidate,
            scorer=scorer(lambda case, output: output == case.private_label),
        )

        self.assertEqual(report["decision"], "completed")
        self.assertEqual(report["quality_decision"], "passed")
        self.assertEqual(registry.events[-1][0], "consumed")

    def test_registry_contract_exposes_read_only_reconciliation(self) -> None:
        registry = Registry((Case("case-1", {"question": "Q"}, {"answer": "A"}),))
        empty = registry.reconcile("run-2026-01")
        self.assertEqual((empty.run_id, empty.state, empty.events), ("run-2026-01", "not_found", ()))

        registry.events.append(("authorized", {"run_id": "run-2026-01"}))
        authorized = registry.reconcile("run-2026-01")
        self.assertEqual(authorized.state, "authorized")
        self.assertEqual([event.state for event in authorized.events], ["authorized"])

        registry.events.append(("reserved", {"run_id": "run-2026-01"}))
        reconciled = registry.reconcile("run-2026-01")
        self.assertEqual(reconciled.state, "reserved")
        self.assertEqual([event.state for event in reconciled.events], ["authorized", "reserved"])
        self.assertRegex(reconciled.events[-1].payload_sha256, r"^[0-9a-f]{64}$")
        self.assertEqual(reconciled.events[-1].payload["run_id"], "run-2026-01")

    def test_stranded_reservation_can_only_be_closed_with_no_execution_evidence(self) -> None:
        registry = Registry((Case("case-1", {"question": "Q"}, {"answer": "A"}),))
        registry.events.extend([
            ("authorized", {"run_id": "run-2026-01"}),
            ("reserved", {"run_id": "run-2026-01"}),
        ])
        with self.assertRaisesRegex(ValueError, "trusted immutable no-execution evidence"):
            registry.recover_abort("run-2026-01", "reservation-1", "terminal-1", "lost_reply", "runtime-audit:run-1", "bad")
        self.assertEqual(registry.reconcile("run-2026-01").state, "reserved")

        terminal = registry.recover_abort(
            "run-2026-01", "reservation-1", "terminal-1", "lost_reply", "runtime-audit:run-1", "f" * 64
        )
        self.assertEqual(terminal.state, "aborted")
        self.assertEqual(registry.reconcile("run-2026-01").state, "aborted")
        self.assertEqual(terminal.payload["no_execution_evidence_ref"], "runtime-audit:run-1")

    def test_runner_implementation_is_part_of_both_frozen_material_sets(self) -> None:
        evaluation_root = Path(__file__).resolve().parent
        runner_path = evaluation_root / "official_holdout.py"
        runtime_path = evaluation_root / "subprocess_candidate.py"
        canonicalization_path = evaluation_root / "canonicalization.py"
        expected_materials = {
            runner_path.name: hashlib.sha256(runner_path.read_bytes()).hexdigest(),
            runtime_path.name: hashlib.sha256(runtime_path.read_bytes()).hexdigest(),
            canonicalization_path.name: hashlib.sha256(canonicalization_path.read_bytes()).hexdigest(),
        }
        expected_executor = hashlib.sha256()
        for path in (runner_path, runtime_path, canonicalization_path):
            name = path.name.encode("utf-8")
            content = path.read_bytes()
            expected_executor.update(len(name).to_bytes(4, "big"))
            expected_executor.update(name)
            expected_executor.update(len(content).to_bytes(8, "big"))
            expected_executor.update(content)
        self.assertEqual(spec().executor_sha256, expected_executor.hexdigest())
        frozen = json.loads((evaluation_root / "release.json").read_text(encoding="utf-8"))
        for name, digest in expected_materials.items():
            self.assertEqual(frozen["materials"].get(name), digest)

        project_root = evaluation_root.parents[2]
        sys.path.insert(0, str(project_root / "examples/p5-agent-delivery"))
        import release_candidate

        self.assertIn("examples/p5-agent-delivery/evaluation/official_holdout.py", release_candidate.REQUIRED_FILES)
        self.assertIn("examples/p5-agent-delivery/evaluation/subprocess_candidate.py", release_candidate.REQUIRED_FILES)
        self.assertIn("examples/p5-agent-delivery/evaluation/canonicalization.py", release_candidate.REQUIRED_FILES)

    def test_candidate_runtime_identity_must_match_before_registry_reservation(self) -> None:
        registry = Registry((Case("case-1", {"question": "Q"}, {"answer": "A"}),))
        candidate = Candidate()
        candidate.image_digest = "sha256:" + "e" * 64

        with self.assertRaisesRegex(HoldoutRunError, "candidate runtime identity"):
            run_holdout(
                spec=spec(), registry=registry, candidate=candidate, scorer=scorer(lambda case, output: True)
            )

        self.assertEqual(registry.events, [])

    def test_candidate_stream_limit_must_match_frozen_spec_before_reservation(self) -> None:
        registry = Registry((Case("case-1", {"question": "Q"}, {"answer": "A"}),))
        candidate = Candidate()
        candidate.max_output_bytes = 1024
        run_spec = HoldoutRunSpec(**{**spec().__dict__, "max_output_bytes": 4})

        with self.assertRaisesRegex(HoldoutRunError, "output limit"):
            run_holdout(
                spec=run_spec,
                registry=registry,
                candidate=candidate,
                scorer=scorer(lambda case, output: True),
            )

        self.assertEqual(registry.events, [])
        self.assertEqual(candidate.seen, [])

    def test_scorer_hash_must_match_before_registry_reservation(self) -> None:
        registry = Registry((Case("case-1", {"question": "Q"}, {"answer": "A"}),))
        wrong_scorer = FrozenScorer("e" * 64, lambda case, output: True)

        with self.assertRaisesRegex(HoldoutRunError, "scorer hash"):
            run_holdout(spec=spec(), registry=registry, candidate=Candidate(), scorer=wrong_scorer)

        self.assertEqual(registry.events, [])

    def test_executor_source_hash_must_match_before_registry_reservation(self) -> None:
        registry = Registry((Case("case-1", {"question": "Q"}, {"answer": "A"}),))
        run_spec = HoldoutRunSpec(**{**spec().__dict__, "executor_sha256": "f" * 64})

        with self.assertRaisesRegex(HoldoutRunError, "executor hash"):
            run_holdout(
                spec=run_spec,
                registry=registry,
                candidate=Candidate(),
                scorer=scorer(lambda case, output: True),
            )

        self.assertEqual(registry.events, [])

    def test_reservation_must_bind_the_exact_frozen_run_spec_before_candidate_execution(self) -> None:
        class WrongBindingRegistry(Registry):
            def reserve(self, run_spec: HoldoutRunSpec) -> Reservation:
                self.events.append(("reserved", {"run_id": run_spec.run_id}))
                return Reservation("reservation-1", "f" * 64)

        registry = WrongBindingRegistry((Case("case-1", {"question": "Q"}, {"answer": "A"}),))
        candidate = Candidate()
        with self.assertRaisesRegex(HoldoutRunError, "reservation does not bind"):
            run_holdout(
                spec=spec(), registry=registry, candidate=candidate, scorer=scorer(lambda case, output: True)
            )

        self.assertEqual(candidate.seen, [])
        self.assertEqual(registry.events[-1][0], "aborted")

    def test_candidate_does_not_start_when_reserved_event_identity_is_forged(self) -> None:
        class ForgedSnapshotRegistry(Registry):
            def reserve(self, run_spec: HoldoutRunSpec) -> Reservation:
                reservation = super().reserve(run_spec)
                assert reservation.registry_snapshot is not None
                auth_event, reserved_event = reservation.registry_snapshot.events
                payload = {**reserved_event.payload, "candidate_sha256": "e" * 64}
                digest = canonical_sha256(payload)
                forged = RegistryEventSnapshot(
                    event_id=reserved_event.event_id,
                    state=reserved_event.state,
                    payload_sha256=digest,
                    payload=payload,
                )
                snapshot = RegistrySnapshot(
                    run_id=run_spec.run_id,
                    state="reserved",
                    events=(auth_event, forged),
                )
                return Reservation(
                    reservation.event_id,
                    reservation.spec_sha256,
                    reservation.session_capability,
                    snapshot,
                )

        registry = ForgedSnapshotRegistry((Case("case-1", {"question": "Q"}, {"answer": "A"}),))
        candidate = Candidate()
        with self.assertRaisesRegex(HoldoutRunError, "complete frozen run identity"):
            run_holdout(
                spec=spec(), registry=registry, candidate=candidate, scorer=scorer(lambda case, output: True)
            )

        self.assertEqual(candidate.seen, [])
        self.assertEqual(registry.events[-1][0], "aborted")

    def test_candidate_does_not_start_when_authorized_actor_id_is_forged(self) -> None:
        class ForgedActorRegistry(Registry):
            def reserve(self, run_spec: HoldoutRunSpec) -> Reservation:
                reservation = super().reserve(run_spec)
                assert reservation.registry_snapshot is not None
                auth_event, reserved_event = reservation.registry_snapshot.events
                payload = {**auth_event.payload, "actor_id": "attacker-principal"}
                digest = canonical_sha256(payload)
                forged = RegistryEventSnapshot(auth_event.event_id, auth_event.state, digest, payload)
                snapshot = RegistrySnapshot(run_spec.run_id, "reserved", (forged, reserved_event))
                return Reservation(
                    reservation.event_id,
                    reservation.spec_sha256,
                    reservation.session_capability,
                    snapshot,
                )

        registry = ForgedActorRegistry((Case("case-1", {"question": "Q"}, {"answer": "A"}),))
        candidate = Candidate()
        with self.assertRaisesRegex(HoldoutRunError, "actor identity"):
            run_holdout(
                spec=spec(), registry=registry, candidate=candidate, scorer=scorer(lambda case, output: True)
            )
        self.assertEqual(candidate.seen, [])


    def test_ambiguous_reservation_response_stops_without_candidate_execution_or_retry(self) -> None:
        class AmbiguousReservationRegistry(Registry):
            def reserve(self, run_spec: HoldoutRunSpec) -> Reservation:
                self.events.append(("reserved", {"run_id": run_spec.run_id}))
                raise TimeoutError("reservation response lost")

        registry = AmbiguousReservationRegistry((Case("case-1", {"question": "Q"}, {"answer": "A"}),))
        candidate = Candidate()
        with self.assertRaisesRegex(HoldoutRunError, "reservation outcome is unknown"):
            run_holdout(
                spec=spec(), registry=registry, candidate=candidate, scorer=scorer(lambda case, output: True)
            )

        self.assertEqual(candidate.seen, [])
        self.assertEqual([event[0] for event in registry.events], ["reserved"])

    def test_malformed_reservation_response_is_treated_as_unknown(self) -> None:
        class MalformedRegistry(Registry):
            def reserve(self, run_spec: HoldoutRunSpec):
                self.events.append(("reserved", {"run_id": run_spec.run_id}))
                return None

        registry = MalformedRegistry((Case("case-1", {"question": "Q"}, {"answer": "A"}),))
        with self.assertRaisesRegex(HoldoutRunError, "reservation outcome is unknown"):
            run_holdout(
                spec=spec(), registry=registry, candidate=Candidate(), scorer=scorer(lambda case, output: True)
            )

        self.assertEqual([event[0] for event in registry.events], ["reserved"])

    def test_custodian_error_does_not_expose_capability_in_traceback(self) -> None:
        registry = Registry((Case("case-1", {"question": "Q"}, {"answer": "A"}),))
        capability = "fixture-one-time-capability"

        def failed_open(received_capability, runtime_identity, run_spec):
            raise TimeoutError(f"transport rejected credential {received_capability}")

        registry.data_plane.open_session = failed_open
        with self.assertRaises(HoldoutRunError) as caught:
            try:
                run_holdout(
                    spec=spec(), registry=registry, candidate=Candidate(),
                    scorer=scorer(lambda _case, _output: True),
                )
            except HoldoutRunError:
                self.assertNotIn(capability, traceback.format_exc())
                raise

        pending = [caught.exception]
        visited = set()
        while pending:
            error = pending.pop()
            if id(error) in visited:
                continue
            visited.add(id(error))
            self.assertNotIn(capability, str(error))
            pending.extend(item for item in (error.__cause__, error.__context__) if item is not None)
        self.assertNotIn(capability, repr(registry.events))
        self.assertEqual(registry.events[-1][0], "aborted")

    def test_missing_session_capability_aborts_without_starting_candidate(self) -> None:
        class MissingCapabilityRegistry(Registry):
            def reserve(self, run_spec: HoldoutRunSpec) -> Reservation:
                reservation = super().reserve(run_spec)
                return Reservation(
                    reservation.event_id,
                    reservation.spec_sha256,
                    None,
                    reservation.registry_snapshot,
                )

        registry = MissingCapabilityRegistry((Case("case-1", {"question": "Q"}, {"answer": "A"}),))
        candidate = Candidate()
        with self.assertRaisesRegex(HoldoutRunError, "omitted its one-time data capability"):
            run_holdout(
                spec=spec(), registry=registry, candidate=candidate,
                scorer=scorer(lambda _case, _output: True),
            )

        self.assertEqual(candidate.seen, [])
        self.assertEqual(registry.data_plane.opened_capabilities, [])
        self.assertTrue(registry.data_plane.session.aborted)
        self.assertEqual(registry.events[-1][0], "aborted")

    def test_data_plane_limit_stops_before_executing_an_extra_attempt(self) -> None:
        registry = Registry((
            Case("case-1", {"question": "Q1"}, {"answer": "A1"}),
            Case("case-2", {"question": "Q2"}, {"answer": "A2"}),
        ))
        candidate = Candidate()
        with self.assertRaisesRegex(HoldoutRunError, "case limit"):
            run_holdout(
                spec=spec(), registry=registry, candidate=candidate,
                scorer=scorer(lambda case, output: True),
            )
        self.assertEqual(candidate.seen, [("task-0001", {"question": "Q1"})])
        self.assertTrue(registry.data_plane.session.aborted)

    def test_non_utc_deadline_is_rejected_before_registry_reservation(self) -> None:
        registry = Registry((Case("case-1", {"question": "Q"}, {"answer": "A"}),))
        run_spec = HoldoutRunSpec(**{**spec().__dict__, "deadline_utc": "2026-10-22T08:00:00+08:00"})

        with self.assertRaisesRegex(HoldoutRunError, "UTC"):
            run_holdout(
                spec=run_spec, registry=registry, candidate=Candidate(), scorer=scorer(lambda case, output: True)
            )

        self.assertEqual(registry.events, [])

    def test_expired_deadline_is_rejected_before_registry_reservation(self) -> None:
        registry = Registry((Case("case-1", {"question": "Q"}, {"answer": "A"}),))
        run_spec = HoldoutRunSpec(**{**spec().__dict__, "deadline_utc": "2000-01-01T00:00:00Z"})

        with self.assertRaisesRegex(HoldoutRunError, "expired"):
            run_holdout(
                spec=run_spec, registry=registry, candidate=Candidate(), scorer=scorer(lambda case, output: True)
            )

        self.assertEqual(registry.events, [])

    def test_boolean_budget_is_rejected_before_registry_reservation(self) -> None:
        registry = Registry((Case("case-1", {"question": "Q"}, {"answer": "A"}),))
        run_spec = HoldoutRunSpec(**{**spec().__dict__, "max_budget_usd": True})

        with self.assertRaisesRegex(HoldoutRunError, "budget"):
            run_holdout(
                spec=run_spec, registry=registry, candidate=Candidate(), scorer=scorer(lambda case, output: True)
            )

        self.assertEqual(registry.events, [])

    def test_reserves_before_execution_hides_labels_and_appends_only_redacted_terminal_report(self) -> None:
        registry = Registry((Case("case-1", {"question": "Q"}, {"answer": "A"}),))
        candidate = Candidate()
        report = run_holdout(
            spec=spec(),
            registry=registry,
            candidate=candidate,
            scorer=scorer(lambda case, output: output == case.private_label),
        )

        self.assertEqual([event[0] for event in registry.events], ["authorized", "reserved", "consumed"])
        self.assertEqual(candidate.seen, [("task-0001", {"question": "Q"})])
        self.assertEqual(report["decision"], "completed")
        self.assertEqual(report["schema"], "official-blind-holdout-run-result-v4")
        self.assertEqual(report["executor_sha256"], spec().executor_sha256)
        self.assertEqual(report["authorization_event_id"], spec().authorization_event_id)
        self.assertEqual(report["frozen_spec_sha256"], canonical_run_spec_sha256(spec()))
        self.assertEqual(report["reservation_event_id"], "reservation-1")
        self.assertEqual(report["output_seal_id"], "seal-1")
        self.assertEqual(report["terminal_event_id"], registry.events[-1][1]["terminal_event_id"])
        self.assertEqual(report["task_count"], 1)
        self.assertEqual(report["passed_tasks"], 1)
        self.assertEqual(report["metrics"]["task_count"], report["task_count"])
        self.assertEqual(report["metrics"]["quality_criteria"], report["quality_criteria"])
        expected_metrics_hash = canonical_sha256(report["metrics"])
        self.assertEqual(report["metrics_sha256"], expected_metrics_hash)
        self.assertEqual(report["results_sha256"], report["output_sha256"])
        self.assertTrue(report["executed_at"].endswith("Z"))
        self.assertEqual(report["token_usage"], {"input_tokens": 12, "output_tokens": 2})
        self.assertEqual(report["task_results"][0]["token_usage"], {"input_tokens": 12, "output_tokens": 2})
        self.assertEqual(report["task_results"][0]["cost_usd"], "0.10")
        serialized = str(registry.events[-1][1]["report"])
        self.assertNotIn("private_label", serialized)
        self.assertNotIn('"answer": "A"', serialized)

    def test_lost_scorer_response_reconciles_same_seal_without_rerunning_candidate(self) -> None:
        registry = Registry((Case("case-1", {"question": "Q"}, {"answer": "A"}),))
        candidate = Candidate()
        score_calls = []
        stored_scores = []
        test_case = self

        class CommitThenLoseScorer(FrozenScorer):
            def score_sealed(self, outputs):
                score_calls.append((outputs.seal_id, outputs.output_sha256))
                stored_scores.extend(super().score_sealed(outputs))
                raise TimeoutError("scorer response lost after commit")

            def reconcile_sealed(self, seal_id, scorer_sha256, output_sha256):
                test_case.assertEqual(seal_id, "seal-1")
                test_case.assertEqual(scorer_sha256, spec().scorer_sha256)
                test_case.assertEqual(output_sha256, score_calls[0][1])
                return tuple(stored_scores)


        report = run_holdout(
            spec=spec(), registry=registry, candidate=candidate,
            scorer=CommitThenLoseScorer("d" * 64, lambda _case, _output: True, registry.data_plane),
        )
        self.assertEqual(report["decision"], "completed")
        self.assertEqual(score_calls, [("seal-1", report["output_sha256"])])
        self.assertEqual(len(candidate.seen), 1)
        self.assertEqual(registry.events[-1][0], "consumed")

    def test_confirmed_absent_score_retries_same_seal_once(self) -> None:
        registry = Registry((Case("case-1", {"question": "Q"}, {"answer": "A"}),))
        candidate = Candidate()

        class NoCommitThenSuccessScorer(FrozenScorer):
            calls = 0

            def score_sealed(self, outputs):
                self.calls += 1
                if self.calls == 1:
                    raise TimeoutError("score request was not committed")
                return super().score_sealed(outputs)

            def reconcile_sealed(self, seal_id, scorer_sha256, output_sha256):
                return None

        scoring = NoCommitThenSuccessScorer("d" * 64, lambda _case, _output: True, registry.data_plane)
        report = run_holdout(spec=spec(), registry=registry, candidate=candidate, scorer=scoring)

        self.assertEqual(scoring.calls, 2)
        self.assertEqual(report["decision"], "completed")
        self.assertEqual(report["output_seal_id"], "seal-1")
        self.assertEqual(len(candidate.seen), 1)
        self.assertEqual(registry.events[-1][0], "consumed")

    def test_unknown_scorer_reconciliation_leaves_registry_reserved(self) -> None:
        registry = Registry((Case("case-1", {"question": "Q"}, {"answer": "A"}),))
        candidate = Candidate()

        class UnknownScorer(FrozenScorer):
            def score_sealed(self, outputs):
                raise TimeoutError("scorer response is unknown")

            def reconcile_sealed(self, seal_id, scorer_sha256, output_sha256):
                raise TimeoutError("scorer state is unavailable")

        with self.assertRaisesRegex(HoldoutRunError, "score outcome is unknown"):
            run_holdout(
                spec=spec(), registry=registry, candidate=candidate,
                scorer=UnknownScorer("d" * 64, lambda _case, _output: True, registry.data_plane),
            )

        self.assertEqual([event[0] for event in registry.events], ["authorized", "reserved"])
        self.assertEqual(registry.reconcile(spec().run_id).state, "reserved")
        self.assertEqual(len(candidate.seen), 1)

    def test_invalid_scorer_result_report_retains_the_sealed_output_reference(self) -> None:
        registry = Registry((Case("case-1", {"question": "Q"}, {"answer": "A"}),))

        class InvalidScorer(FrozenScorer):
            def score_sealed(self, outputs):
                return ()

        with self.assertRaisesRegex(HoldoutRunError, "incomplete result set"):
            run_holdout(
                spec=spec(), registry=registry, candidate=Candidate(),
                scorer=InvalidScorer("d" * 64, lambda _case, _output: True, registry.data_plane),
            )

        abort_report = registry.events[-1][1]["report"]
        self.assertEqual(registry.events[-1][0], "aborted")
        self.assertEqual(abort_report["output_seal_id"], "seal-1")
        self.assertEqual(abort_report["output_sha256"], abort_report["results_sha256"])
        self.assertEqual(len(abort_report["output_sha256"]), 64)

    def test_completed_run_can_fail_predeclared_quality_criteria(self) -> None:
        registry = Registry((Case("case-1", {"question": "Q"}, {"answer": "A"}),))
        report = run_holdout(
            spec=spec(),
            registry=registry,
            candidate=Candidate(),
            scorer=scorer(lambda case, output: False),
        )

        self.assertEqual(report["decision"], "completed")
        self.assertEqual(report["quality_decision"], "failed")
        self.assertEqual(report["passed_tasks"], 0)
        self.assertEqual(registry.events[-1][0], "consumed")

    def test_run_spec_freezes_quality_thresholds_before_reservation(self) -> None:
        run_spec = HoldoutRunSpec(**{
            **spec().__dict__,
            "minimum_pass_rate_bps": True,
        })
        registry = Registry((Case("case-1", {"question": "Q"}, {"answer": "A"}),))

        with self.assertRaisesRegex(HoldoutRunError, "pass-rate threshold"):
            run_holdout(
                spec=run_spec,
                registry=registry,
                candidate=Candidate(),
                scorer=scorer(lambda case, output: True),
            )

        self.assertEqual(registry.events, [])

    def test_owner_executor_and_recovery_principals_must_be_distinct(self) -> None:
        run_spec = HoldoutRunSpec(**{**spec().__dict__, "recovery_operator_id": "owner-2026-01"})
        registry = Registry((Case("case-1", {"question": "Q"}, {"answer": "A"}),))
        with self.assertRaisesRegex(HoldoutRunError, "must be distinct frozen principals"):
            run_holdout(
                spec=run_spec, registry=registry, candidate=Candidate(), scorer=scorer(lambda case, output: True)
            )
        self.assertEqual(registry.events, [])

    def test_run_spec_requires_frozen_stop_conditions_before_reservation(self) -> None:
        run_spec = HoldoutRunSpec(**{**spec().__dict__, "stop_conditions": ()})
        registry = Registry((Case("case-1", {"question": "Q"}, {"answer": "A"}),))

        with self.assertRaisesRegex(HoldoutRunError, "stop conditions"):
            run_holdout(
                spec=run_spec,
                registry=registry,
                candidate=Candidate(),
                scorer=scorer(lambda case, output: True),
            )

        self.assertEqual(registry.events, [])

    def test_run_spec_rejects_unknown_hash_profile_before_reservation(self) -> None:
        run_spec = HoldoutRunSpec(**{**spec().__dict__, "hash_profile": "custom-json-v0"})
        registry = Registry((Case("case-1", {"question": "Q"}, {"answer": "A"}),))
        with self.assertRaisesRegex(HoldoutRunError, "unsupported frozen hash profile"):
            run_holdout(
                spec=run_spec, registry=registry, candidate=Candidate(), scorer=scorer(lambda case, output: True)
            )
        self.assertEqual(registry.events, [])

    def test_run_spec_cannot_omit_a_required_stop_condition(self) -> None:
        missing_label_leak = tuple(item for item in spec().stop_conditions if item != "label-leak")
        run_spec = HoldoutRunSpec(**{**spec().__dict__, "stop_conditions": missing_label_leak})
        registry = Registry((Case("case-1", {"question": "Q"}, {"answer": "A"}),))

        with self.assertRaisesRegex(HoldoutRunError, "required stop conditions"):
            run_holdout(
                spec=run_spec,
                registry=registry,
                candidate=Candidate(),
                scorer=scorer(lambda case, output: True),
            )

        self.assertEqual(registry.events, [])

    def test_candidate_failure_consumes_reservation_as_aborted_without_retry(self) -> None:
        registry = Registry((Case("case-1", {"question": "Q"}, {"answer": "A"}),))

        class FailsOnce:
            candidate_sha256 = "a" * 64
            image_digest = "sha256:" + "b" * 64
            max_output_bytes = 1024
            calls = 0

            def execute(self, case_id: str, public_input: dict, deadline_utc: str, remaining_budget_usd: str) -> dict:
                self.calls += 1
                raise TimeoutError("private provider detail")

        candidate = FailsOnce()
        with self.assertRaises(HoldoutRunError):
            run_holdout(
                spec=spec(), registry=registry, candidate=candidate, scorer=scorer(lambda case, output: True)
            )

        self.assertEqual(candidate.calls, 1)
        self.assertEqual([event[0] for event in registry.events], ["authorized", "reserved", "aborted"])
        self.assertTrue(registry.data_plane.session.aborted)
        self.assertNotIn("private provider detail", str(registry.events[-1][1]))
        abort = registry.events[-1][1]["report"]
        self.assertEqual(abort["cost_status"], "unknown")
        self.assertNotIn("cost_usd", abort)
        abort_hash = abort.pop("report_sha256")
        self.assertEqual(abort_hash, canonical_sha256(abort))
        self.assertEqual(registry.events[-1][1]["report_sha256"], abort_hash)

    def test_budget_overrun_aborts_and_never_scores_or_runs_another_case(self) -> None:
        registry = Registry((
            Case("case-1", {"question": "Q1"}, {"answer": "A1"}),
            Case("case-2", {"question": "Q2"}, {"answer": "A2"}),
        ))
        candidate = Candidate()
        scored: list[str] = []
        run_spec = HoldoutRunSpec(**{**spec().__dict__, "max_budget_usd": "0.05", "max_cases": 2})

        with self.assertRaises(HoldoutRunError):
            run_holdout(
                spec=run_spec,
                registry=registry,
                candidate=candidate,
                scorer=scorer(lambda case, output: scored.append(case.case_id) or True),
            )

        self.assertEqual(len(candidate.seen), 1)
        self.assertEqual(scored, [])
        self.assertEqual(registry.events[-1][0], "aborted")

    def test_candidate_receives_exact_remaining_budget_before_each_task(self) -> None:
        registry = Registry((
            Case("case-1", {"question": "Q1"}, {"answer": "A1"}),
            Case("case-2", {"question": "Q2"}, {"answer": "A2"}),
        ))

        class BudgetAwareCandidate:
            candidate_sha256 = "a" * 64
            image_digest = "sha256:" + "b" * 64
            max_output_bytes = 1024

            def __init__(self) -> None:
                self.remaining: list[str] = []

            def execute(self, attempt_id: str, public_input: dict, deadline_utc: str, remaining_budget_usd: str) -> dict:
                self.remaining.append(remaining_budget_usd)
                cost = "0.03" if len(self.remaining) == 1 else "0.02"
                return {
                    "output": {"answer": "A"},
                    "cost_usd": cost,
                    "input_tokens": 1,
                    "output_tokens": 1,
                    "latency_ms": 1,
                }

        candidate = BudgetAwareCandidate()
        run_holdout(
            spec=HoldoutRunSpec(**{**spec().__dict__, "max_cases": 2}),
            registry=registry,
            candidate=candidate,
            scorer=scorer(lambda case, output: True),
        )

        self.assertEqual(candidate.remaining, ["1.00", "0.97"])

    def test_budget_report_does_not_round_spend_down_to_zero(self) -> None:
        registry = Registry((Case("case-1", {"question": "Q"}, {"answer": "A"}),))

        class TinyCostCandidate:
            candidate_sha256 = "a" * 64
            image_digest = "sha256:" + "b" * 64
            max_output_bytes = 1024

            def execute(self, attempt_id: str, public_input: dict, deadline_utc: str, remaining_budget_usd: str) -> dict:
                return {
                    "output": {"answer": "A"},
                    "cost_usd": "0.000000009",
                    "input_tokens": 1,
                    "output_tokens": 1,
                    "latency_ms": 1,
                }

        run_spec = HoldoutRunSpec(**{**spec().__dict__, "max_budget_usd": "0.000000005"})
        with self.assertRaises(HoldoutRunError):
            run_holdout(
                spec=run_spec,
                registry=registry,
                candidate=TinyCostCandidate(),
                scorer=scorer(lambda case, output: True),
            )

        report = registry.events[-1][1]["report"]
        self.assertEqual(report["cost_usd"], "0.000000009")
        self.assertEqual(report["budget_usd"], "0.000000005")

    def test_binary_float_cost_is_rejected_instead_of_claimed_as_exact(self) -> None:
        registry = Registry((Case("case-1", {"question": "Q"}, {"answer": "A"}),))

        class FloatCostCandidate:
            candidate_sha256 = "a" * 64
            image_digest = "sha256:" + "b" * 64
            max_output_bytes = 1024

            def execute(self, attempt_id: str, public_input: dict, deadline_utc: str, remaining_budget_usd: str) -> dict:
                return {
                    "output": {"answer": "A"},
                    "cost_usd": 0.1,
                    "input_tokens": 1,
                    "output_tokens": 1,
                    "latency_ms": 1,
                }

        with self.assertRaisesRegex(HoldoutRunError, "invalid cost"):
            run_holdout(
                spec=spec(),
                registry=registry,
                candidate=FloatCostCandidate(),
                scorer=scorer(lambda case, output: True),
            )

        self.assertEqual(registry.events[-1][0], "aborted")

    def test_numeric_integer_cost_is_rejected_instead_of_claimed_as_decimal_string(self) -> None:
        registry = Registry((Case("case-1", {"question": "Q"}, {"answer": "A"}),))

        class IntegerCostCandidate:
            candidate_sha256 = "a" * 64
            image_digest = "sha256:" + "b" * 64
            max_output_bytes = 1024

            def execute(self, attempt_id: str, public_input: dict, deadline_utc: str, remaining_budget_usd: str) -> dict:
                return {
                    "output": {"answer": "A"},
                    "cost_usd": 1,
                    "input_tokens": 1,
                    "output_tokens": 1,
                    "latency_ms": 1,
                }

        with self.assertRaisesRegex(HoldoutRunError, "invalid cost"):
            run_holdout(
                spec=spec(),
                registry=registry,
                candidate=IntegerCostCandidate(),
                scorer=scorer(lambda case, output: True),
            )

        self.assertEqual(registry.events[-1][0], "aborted")

    def test_reserved_case_count_cannot_exceed_predeclared_limit(self) -> None:
        registry = Registry((
            Case("case-1", {"question": "Q1"}, {"answer": "A1"}),
            Case("case-2", {"question": "Q2"}, {"answer": "A2"}),
        ))
        candidate = Candidate()
        with self.assertRaisesRegex(HoldoutRunError, "case limit"):
            run_holdout(
                spec=spec(), registry=registry, candidate=candidate, scorer=scorer(lambda case, output: True)
            )

        self.assertEqual(candidate.seen, [("task-0001", {"question": "Q1"})])
        self.assertEqual(registry.events[-1][0], "aborted")

    def test_missing_token_usage_aborts_and_is_not_reported_as_zero(self) -> None:
        registry = Registry((Case("case-1", {"question": "Q"}, {"answer": "A"}),))
        scored: list[bool] = []

        class MissingUsage:
            candidate_sha256 = "a" * 64
            image_digest = "sha256:" + "b" * 64
            max_output_bytes = 1024

            def execute(self, attempt_id: str, public_input: dict, deadline_utc: str, remaining_budget_usd: str) -> dict:
                return {"output": {"answer": "A"}, "cost_usd": 0.1, "latency_ms": 12}

        with self.assertRaises(HoldoutRunError):
            run_holdout(
                spec=spec(),
                registry=registry,
                candidate=MissingUsage(),
                scorer=scorer(lambda case, output: scored.append(True) or True),
            )

        abort = registry.events[-1][1]["report"]
        self.assertEqual(registry.events[-1][0], "aborted")
        self.assertEqual(abort["usage_status"], "unknown")
        self.assertNotIn("token_usage", abort)
        self.assertEqual(scored, [])

    def test_oversized_output_aborts_before_scoring(self) -> None:
        registry = Registry((Case("case-1", {"question": "Q"}, {"answer": "A"}),))
        run_spec = HoldoutRunSpec(**{**spec().__dict__, "max_output_bytes": 4})
        scored: list[bool] = []
        candidate = Candidate()
        candidate.max_output_bytes = 4

        with self.assertRaisesRegex(HoldoutRunError, "output size"):
            run_holdout(
                spec=run_spec,
                registry=registry,
                candidate=candidate,
                scorer=scorer(lambda case, output: scored.append(True) or True),
            )

        self.assertEqual(scored, [])
        self.assertEqual(registry.events[-1][0], "aborted")

    def test_ambiguous_terminal_append_is_not_followed_by_a_second_terminal_event(self) -> None:
        class AmbiguousRegistry(Registry):
            terminal_attempts = 0

            def append_terminal(
                self, reservation_event_id: str, terminal_event_id: str, state: str, report: dict
            ) -> None:
                self.terminal_attempts += 1
                raise TimeoutError("registry response was lost")

        registry = AmbiguousRegistry((Case("case-1", {"question": "Q"}, {"answer": "A"}),))
        with self.assertRaisesRegex(HoldoutRunError, "terminal outcome is unknown"):
            run_holdout(
                spec=spec(),
                registry=registry,
                candidate=Candidate(),
                scorer=scorer(lambda case, output: True),
            )

        self.assertEqual(registry.terminal_attempts, 1)

    def test_ambiguous_abort_append_is_reported_unknown_without_retry(self) -> None:
        class LostAbortRegistry(Registry):
            terminal_attempts = 0

            def append_terminal(
                self, reservation_event_id: str, terminal_event_id: str, state: str, report: dict
            ) -> None:
                self.terminal_attempts += 1
                raise TimeoutError("append result lost")

        class FailsOnce:
            candidate_sha256 = "a" * 64
            image_digest = "sha256:" + "b" * 64
            max_output_bytes = 1024

            def execute(self, attempt_id: str, public_input: dict, deadline_utc: str, remaining_budget_usd: str) -> dict:
                raise TimeoutError("provider outcome unknown")

        registry = LostAbortRegistry((Case("case-1", {"question": "Q"}, {"answer": "A"}),))
        with self.assertRaisesRegex(HoldoutRunError, "terminal outcome is unknown"):
            run_holdout(
                spec=spec(), registry=registry, candidate=FailsOnce(), scorer=scorer(lambda case, output: True)
            )

        self.assertEqual(registry.terminal_attempts, 1)

    def test_terminal_registry_record_binds_the_canonical_report_body_hash(self) -> None:
        registry = Registry((Case("case-1", {"question": "Q"}, {"answer": "A"}),))
        report = run_holdout(
            spec=spec(), registry=registry, candidate=Candidate(),
            scorer=scorer(lambda case, output: True),
        )
        report_hash = report.pop("report_sha256")
        expected_hash = canonical_sha256(report)
        self.assertEqual(report_hash, expected_hash)
        terminal = registry.events[-1][1]
        self.assertEqual(terminal["report_sha256"], report_hash)


if __name__ == "__main__":
    unittest.main()
