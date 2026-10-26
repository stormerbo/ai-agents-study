from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from evaluation import EvaluationError, _wilson, evaluate
from canonicalization import HASH_PROFILE


PACKAGE = Path(__file__).parent
P5 = PACKAGE.parent
REPO = PACKAGE.parents[2]
if str(P5) not in sys.path:
    sys.path.insert(0, str(P5))

import release_candidate


class EvaluationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        for name in ("dev.json", "dev-results.json", "holdout.json", "holdout-results.json", "prompt.txt", "tool-schema.json", "release.json", "scorer.json", "scorer.py", "evaluation.py", "official_holdout.py", "subprocess_candidate.py", "canonicalization.py", "run_fixture.py", "lockfile.txt"):
            shutil.copy(PACKAGE / name, self.root / name)
        self.state = self.root / "state"

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_dev_fixture_is_repeatable_and_never_claims_live_evidence(self) -> None:
        first = evaluate(self.root, "dev", run_id="dev-run-a")
        second = evaluate(self.root, "dev", run_id="dev-run-b")
        self.assertEqual(first["metrics"], second["metrics"])
        self.assertEqual(first["task_results"], second["task_results"])
        self.assertEqual(first["evidence_kind"], "fixture")
        self.assertEqual(first["hash_profile"], HASH_PROFILE)
        self.assertEqual(second["evidence_kind"], "fixture")
        self.assertFalse(first["live_evidence"])
        self.assertEqual(first["provider"], "synthetic")
        self.assertEqual(first["evidence_status"], "offline_fixture")
        self.assertTrue(first["release_review_required"])
        self.assertFalse(first["publishable"])
        self.assertEqual(first["attempt_classifications"][0]["observed_state"], "completed")
        self.assertEqual(first["attempt_classifications"][0]["required_citations"], ["doc://synthetic/status-policy"])
        self.assertAlmostEqual(first["sample_size"]["task_success_95_percent_interval"]["lower"], 0.510109163545, places=11)
        self.assertEqual(first["sample_size"]["task_success_95_percent_interval"]["upper"], 1.0)

    def test_holdout_can_be_consumed_once_per_frozen_release(self) -> None:
        first = evaluate(self.root, "holdout", run_id="holdout-1", state_root=self.state, fixture_only=True)
        self.assertEqual(first["evaluation_scope"], "offline_synthetic_fixture")
        self.assertFalse(first["blind_holdout"])
        self.assertTrue(first["fixture_replay_consumed"])
        self.assertFalse(first["official_holdout_consumed"])
        self.assertNotIn("holdout_consumed", first)
        with self.assertRaisesRegex(EvaluationError, "already consumed"):
            evaluate(self.root, "holdout", run_id="holdout-2", state_root=self.state, fixture_only=True)

    def test_holdout_requires_candidate_or_explicit_fixture_scope(self) -> None:
        with self.assertRaisesRegex(EvaluationError, "requires candidate_manifest or fixture_only"):
            evaluate(self.root, "holdout", run_id="implicit-holdout", state_root=self.state)

    def test_release_rejects_unknown_hash_profile(self) -> None:
        release = json.loads((self.root / "release.json").read_text(encoding="utf-8"))
        release["hash_profile"] = "custom-json-v0"
        (self.root / "release.json").write_text(json.dumps(release), encoding="utf-8")
        with self.assertRaisesRegex(EvaluationError, "release hash profile is unsupported"):
            evaluate(self.root, "dev", run_id="unknown-hash-profile")

    def test_modified_frozen_material_invalidates_report(self) -> None:
        (self.root / "prompt.txt").write_text("changed after freeze\n", encoding="utf-8")
        with self.assertRaisesRegex(EvaluationError, "hash mismatch"):
            evaluate(self.root, "dev", run_id="changed")

    def test_modified_frozen_results_cannot_be_scored(self) -> None:
        results = json.loads((self.root / "dev-results.json").read_text(encoding="utf-8"))
        results[0]["final_state"] = "refused"
        self._write_results("dev-results.json", results)
        with self.assertRaisesRegex(EvaluationError, "hash mismatch: dev-results.json"):
            evaluate(self.root, "dev", run_id="unfrozen-results")

    def test_duplicate_and_missing_cases_are_invalid(self) -> None:
        results = json.loads((self.root / "dev-results.json").read_text(encoding="utf-8"))
        with self.assertRaisesRegex(EvaluationError, "duplicate"):
            self._write_results("dev-results.json", results + results[:1])
            self._refreeze("dev-results.json")
            evaluate(self.root, "dev", run_id="duplicate")
        self._write_results("dev-results.json", results)
        self._refreeze("dev-results.json")
        with self.assertRaisesRegex(EvaluationError, "missing required case"):
            self._write_results("dev-results.json", results[:-1])
            self._refreeze("dev-results.json")
            evaluate(self.root, "dev", run_id="missing")
        data = json.loads((self.root / "dev.json").read_text(encoding="utf-8"))
        data["cases"][1]["id"] = data["cases"][0]["id"]
        (self.root / "dev.json").write_text(json.dumps(data), encoding="utf-8")
        self._refreeze("dev.json")
        with self.assertRaisesRegex(EvaluationError, "duplicate case id"):
            evaluate(self.root, "dev", run_id="duplicate-case")

    def test_empty_dataset_or_empty_denominator_is_invalid(self) -> None:
        saved_results = json.loads((self.root / "dev-results.json").read_text(encoding="utf-8"))
        self._write_results("dev-results.json", [])
        self._refreeze("dev-results.json")
        with self.assertRaisesRegex(EvaluationError, "empty"):
            evaluate(self.root, "dev", run_id="empty")
        self._write_results("dev-results.json", saved_results)
        self._refreeze("dev-results.json")
        data = json.loads((self.root / "dev.json").read_text(encoding="utf-8"))
        data["cases"] = []
        (self.root / "dev.json").write_text(json.dumps(data), encoding="utf-8")
        self._refreeze("dev.json")
        with self.assertRaisesRegex(EvaluationError, "empty"):
            evaluate(self.root, "dev", run_id="empty-dataset")

    def test_task_metrics_are_task_level_and_undefined_metrics_are_null(self) -> None:
        results = json.loads((self.root / "dev-results.json").read_text(encoding="utf-8"))
        # A repeated attempt for one case is not another independent task sample.
        results.append(dict(results[0], attempt_id="second-attempt", quality_pass=False))
        self._write_results("dev-results.json", results)
        self._refreeze("dev-results.json")
        report = evaluate(self.root, "dev", run_id="task-level")
        self.assertEqual(report["sample_size"]["independent_tasks"], len(self._cases("dev.json")))
        self.assertEqual(report["sample_size"]["attempts"], len(results))
        self.assertEqual(report["metrics"]["task_success_rate"], 3 / 4)
        self.assertEqual(report["sample_size"]["task_success_95_percent_interval"]["method"], "Wilson score, 95%")
        self.assertEqual(report["metric_sample_sizes"]["task_success_rate"], len(self._cases("dev.json")))
        interval = report["sample_size"]["task_success_95_percent_interval"]
        self.assertAlmostEqual(interval["lower"], 0.300641842582, places=11)
        self.assertAlmostEqual(interval["upper"], 0.954412739190, places=11)
        self.assertIsNone(report["metrics"]["mean_external_tool_cost_usd"])
        self.assertIsNone(report["metrics"]["mean_latency_ms"])

    def test_empty_case_id_rejected(self) -> None:
        results = json.loads((self.root / "dev-results.json").read_text(encoding="utf-8"))
        results[0]["case_id"] = "  "
        self._write_results("dev-results.json", results)
        self._refreeze("dev-results.json")
        with self.assertRaisesRegex(EvaluationError, "empty case id"):
            evaluate(self.root, "dev", run_id="empty-id")

    def test_same_task_cannot_be_counted_as_two_independent_cases(self) -> None:
        data = json.loads((self.root / "dev.json").read_text(encoding="utf-8"))
        data["cases"][1]["task_id"] = data["cases"][0]["task_id"]
        (self.root / "dev.json").write_text(json.dumps(data), encoding="utf-8")
        self._refreeze("dev.json")
        with self.assertRaisesRegex(EvaluationError, "duplicate task id"):
            evaluate(self.root, "dev", run_id="duplicate-task")

    def test_modified_scorer_invalidates_frozen_release(self) -> None:
        (self.root / "scorer.py").write_text("# changed after freeze\n", encoding="utf-8")
        with self.assertRaisesRegex(EvaluationError, "hash mismatch"):
            evaluate(self.root, "dev", run_id="changed-scorer")

    def test_evaluator_rejects_arbitrary_in_memory_results(self) -> None:
        with self.assertRaises(TypeError):
            evaluate(self.root, "dev", self._results("dev.json"), run_id="unfrozen-input")

    def test_hard_gates_are_scored_independently_per_gate(self) -> None:
        dataset = json.loads((self.root / "dev.json").read_text(encoding="utf-8"))
        case = dataset["cases"][0]
        case["hard_gates"].append("second-independent-gate")
        (self.root / "dev.json").write_text(json.dumps(dataset), encoding="utf-8")
        self._refreeze("dev.json")
        outputs = json.loads((self.root / "dev-results.json").read_text(encoding="utf-8"))
        outputs[0]["hard_gate_passes"]["second-independent-gate"] = True
        outputs[0]["hard_gate_passes"]["grounded-answer"] = False
        (self.root / "dev-results.json").write_text(json.dumps(outputs), encoding="utf-8")
        self._refreeze("dev-results.json")
        report = evaluate(self.root, "dev", run_id="per-gate")
        self.assertEqual(report["task_results"][0]["hard_gate_results"], {
            "grounded-answer": False,
            "second-independent-gate": True,
        })

    def test_wilson_interval_fixed_references_all_failure_and_boundary_n(self) -> None:
        all_failure = _wilson(0, 4)
        self.assertAlmostEqual(all_failure["lower"], 0.0, places=12)
        self.assertAlmostEqual(all_failure["upper"], 0.489890836455, places=11)
        boundary_success = _wilson(1, 1)
        self.assertAlmostEqual(boundary_success["lower"], 0.206549314377, places=11)
        self.assertAlmostEqual(boundary_success["upper"], 1.0, places=12)
        self.assertIsNone(_wilson(0, 0))

    def _cases(self, dataset: str) -> list[dict]:
        return json.loads((self.root / dataset).read_text(encoding="utf-8"))["cases"]

    def _results(self, dataset: str) -> list[dict]:
        return [
            {
                "case_id": case["id"],
                "attempt_id": "attempt-1",
                "final_state": case["target_state"],
                "citations": list(case["required_citations"]),
                "refusal": case["expect_refusal"],
                "clarification": case["expect_clarification"],
                "hard_gate_passes": {gate: True for gate in case["hard_gates"]},
                "tool_correct": True,
                "retrieval_correct": True,
                "quality_pass": True,
                "token_usage": 10,
                "external_tool_cost_usd": None,
                "latency_ms": None,
            }
            for case in self._cases(dataset)
        ]

    def _refreeze(self, changed_name: str) -> None:
        # Tests mutate a dataset to prove empty-input validation after fixing its hash.
        from evaluation import hash_file

        manifest = json.loads((self.root / "release.json").read_text(encoding="utf-8"))
        manifest["materials"][changed_name] = hash_file(self.root / changed_name)
        (self.root / "release.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    def _write_results(self, name: str, results: list[dict]) -> None:
        (self.root / name).write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")


class CandidateBoundHoldoutTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.temp_root = Path(self.temp.name)
        self.repo = self.temp_root / "repo"
        self.repo.mkdir()
        (self.repo / ".gitignore").write_text("verify-output/\n__pycache__/\n*.py[cod]\n", encoding="utf-8")
        for relative in release_candidate._material_paths(REPO):
            source = REPO / relative
            destination = self.repo / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
        frozen = json.loads(
            (self.repo / "examples/p5-agent-delivery/evaluation/release.json").read_text(encoding="utf-8")
        )
        for name in frozen["materials"]:
            source = REPO / "examples/p5-agent-delivery/evaluation" / name
            destination = self.repo / "examples/p5-agent-delivery/evaluation" / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
        self._git("init", "-q")
        self._git("config", "user.email", "test@example.invalid")
        self._git("config", "user.name", "Test")
        self._git("add", ".")
        self._git("commit", "-qm", "candidate snapshot")
        self.eval_root = self.repo / "examples/p5-agent-delivery/evaluation"
        self.state = self.temp_root / "state"
        self.drills = [
            {"scenario_id": scenario, "run_id": f"run-{scenario}", "report_path": f"verify-output/stage5-drills/{scenario}/report.json", "report_sha256": "a" * 64}
            for scenario in release_candidate.REQUIRED_DRILLS
        ]

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _git(self, *args: str) -> str:
        result = subprocess.run(["git", *args], cwd=self.repo, capture_output=True, text=True, check=True)
        return result.stdout.strip()

    def _candidate(self, image_suffix: str) -> Path:
        with patch.object(release_candidate, "_collect_drill_evidence", return_value=self.drills):
            manifest = release_candidate.build_release_candidate(
                self.repo,
                image_digest="sha256:" + image_suffix * 64,
                evidence_root=self.repo / "verify-output/stage5-drills",
            )
        output = self.temp_root / f"candidate-{image_suffix}.json"
        release_candidate.write_new_manifest(output, manifest)
        return output

    def test_holdout_is_consumed_once_for_exact_frozen_candidate(self) -> None:
        candidate_path = self._candidate("b")
        with patch.object(release_candidate, "_collect_drill_evidence", return_value=self.drills):
            report = evaluate(
                self.eval_root,
                "holdout",
                run_id="candidate-holdout-1",
                state_root=self.state,
                candidate_manifest=candidate_path,
            )
            self.assertEqual(report["report_schema"], "p5-evaluation-report-v3")
            self.assertEqual(report["evaluation_scope"], "offline_synthetic_fixture")
            self.assertFalse(report["blind_holdout"])
            self.assertTrue(report["fixture_replay_consumed"])
            self.assertFalse(report["official_holdout_consumed"])
            self.assertTrue(report["candidate_manifest_verified"])
            self.assertTrue(report["candidate_id"].startswith("p5-rc-"))
            self.assertEqual(report["candidate_hash"], json.loads(candidate_path.read_text())["candidate_hash"])
            with self.assertRaisesRegex(EvaluationError, "already consumed"):
                evaluate(
                    self.eval_root,
                    "holdout",
                    run_id="candidate-holdout-2",
                    state_root=self.state,
                    candidate_manifest=candidate_path,
                )

    def test_tampered_candidate_manifest_is_rejected_before_holdout_consumption(self) -> None:
        candidate_path = self._candidate("c")
        candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
        candidate["publishable"] = True
        candidate_path.write_text(json.dumps(candidate), encoding="utf-8")
        with patch.object(release_candidate, "_collect_drill_evidence", return_value=self.drills):
            with self.assertRaisesRegex(EvaluationError, "candidate manifest hash"):
                evaluate(
                    self.eval_root,
                    "holdout",
                    run_id="tampered-candidate",
                    state_root=self.state,
                    candidate_manifest=candidate_path,
                )
        self.assertEqual(list(self.state.glob("fixture-consumed-*.json")) if self.state.exists() else [], [])

    def test_same_frozen_holdout_cannot_be_reused_for_a_different_candidate(self) -> None:
        first_candidate = self._candidate("e")
        second_candidate = self._candidate("f")
        with patch.object(release_candidate, "_collect_drill_evidence", return_value=self.drills):
            evaluate(
                self.eval_root,
                "holdout",
                run_id="first-candidate",
                state_root=self.state,
                candidate_manifest=first_candidate,
            )
            with self.assertRaisesRegex(EvaluationError, "already consumed"):
                evaluate(
                    self.eval_root,
                    "holdout",
                    run_id="second-candidate",
                    state_root=self.state,
                    candidate_manifest=second_candidate,
                )

    def test_ignored_untracked_candidate_material_cannot_masquerade_as_committed_source(self) -> None:
        candidate_path = self._candidate("d")
        relative = "examples/p5-agent-delivery/runner.py"
        self._git("rm", "--cached", "-q", relative)
        with (self.repo / ".gitignore").open("a", encoding="utf-8") as handle:
            handle.write(f"/{relative}\n")
        self._git("add", ".gitignore")
        self._git("commit", "-qm", "remove ignored release material from commit")
        self.assertEqual(self._git("status", "--porcelain", "--untracked-files=all"), "")
        candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
        candidate["commit_sha"] = self._git("rev-parse", "HEAD")
        candidate["candidate_hash"] = release_candidate.canonical_hash(
            release_candidate.without_candidate_hash(candidate)
        )
        candidate["candidate_id"] = f"p5-rc-{candidate['candidate_hash'][:16]}"
        candidate_path.write_text(json.dumps(candidate), encoding="utf-8")
        with patch.object(release_candidate, "_collect_drill_evidence", return_value=self.drills):
            with self.assertRaisesRegex(EvaluationError, "candidate materials are not in the commit"):
                evaluate(
                    self.eval_root,
                    "holdout",
                    run_id="untracked-material",
                    state_root=self.state,
                    candidate_manifest=candidate_path,
                )


if __name__ == "__main__":
    unittest.main()
