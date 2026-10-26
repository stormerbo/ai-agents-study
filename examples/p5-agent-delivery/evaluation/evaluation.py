"""Offline-only frozen evaluation harness for synthetic P5 cases."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from canonicalization import HASH_PROFILE, canonical_sha256, parse_json_strict


class EvaluationError(ValueError):
    pass


IMAGE_DIGEST = re.compile(r"sha256:[0-9a-f]{64}\Z")


def hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_hash(value: Any) -> str:
    return canonical_sha256(value)


def _read_json(path: Path) -> dict:
    try:
        return parse_json_strict(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError) as exc:
        raise EvaluationError(f"cannot read valid JSON: {path.name}") from exc


def _load_frozen(root: Path) -> tuple[dict, dict[str, str]]:
    manifest = _read_json(root / "release.json")
    expected_names = {
        "dev.json", "dev-results.json", "holdout.json", "holdout-results.json", "prompt.txt",
        "tool-schema.json", "scorer.json", "scorer.py", "evaluation.py", "official_holdout.py", "subprocess_candidate.py", "canonicalization.py",
        "run_fixture.py", "lockfile.txt"
    }
    materials = manifest.get("materials")
    if not isinstance(materials, dict) or set(materials) != expected_names:
        raise EvaluationError("frozen material manifest is incomplete")
    if any(not isinstance(value, str) or len(value) != 64 for value in materials.values()):
        raise EvaluationError("frozen material hash is malformed")
    for role, expected_name in (("lockfile", "lockfile.txt"), ("prompt", "prompt.txt"), ("tool_schema", "tool-schema.json"), ("scorer", "scorer.json")):
        if manifest.get(role) != expected_name:
            raise EvaluationError(f"frozen release {role} reference is invalid")
    if not all(isinstance(manifest.get(field), str) and manifest[field].strip() for field in ("provider", "model")):
        raise EvaluationError("provider/model identity is incomplete")
    actual = {}
    for name, expected_hash in materials.items():
        path = (root / name).resolve()
        if path.parent != root.resolve() or not path.is_file():
            raise EvaluationError(f"frozen material missing or outside root: {name}")
        actual[name] = hash_file(path)
        if actual[name] != expected_hash:
            raise EvaluationError(f"frozen material hash mismatch: {name}")
    if not manifest.get("release_id") or not manifest.get("commit"):
        raise EvaluationError("release identity is incomplete")
    if manifest.get("hash_profile") != HASH_PROFILE:
        raise EvaluationError("release hash profile is unsupported")
    return manifest, actual


def _load_candidate(root: Path, candidate_path: Path) -> tuple[dict, str]:
    root = root.resolve()
    project_root = root.parents[2]
    p5_root = project_root / "examples/p5-agent-delivery"
    if str(p5_root) not in sys.path:
        sys.path.insert(0, str(p5_root))
    try:
        import release_candidate
    except ImportError as exc:
        raise EvaluationError("candidate verifier is unavailable") from exc

    candidate_path = candidate_path.resolve()
    candidate = _read_json(candidate_path)
    candidate_hash = candidate.get("candidate_hash")
    human_review = candidate.get("human_review")
    if (
        candidate.get("schema") != "p5-release-candidate-v2"
        or candidate.get("hash_profile") != HASH_PROFILE
        or candidate.get("status") != "frozen-candidate"
        or candidate.get("publishable") is not False
        or candidate.get("signature") is not None
        or candidate.get("holdout") != {"status": "not_run", "consumed": False}
        or not isinstance(human_review, dict)
        or human_review.get("status") != "pending"
        or not isinstance(candidate_hash, str)
        or release_candidate.canonical_hash(release_candidate.without_candidate_hash(candidate)) != candidate_hash
        or candidate.get("candidate_id") != f"p5-rc-{candidate_hash[:16]}"
    ):
        raise EvaluationError("candidate manifest hash or state is invalid")
    if not IMAGE_DIGEST.fullmatch(candidate.get("image_digest", "")):
        raise EvaluationError("candidate image digest is invalid")

    manifest = _read_json(root / "release.json")
    manifest_hash = hash_file(root / "release.json")
    if (
        candidate.get("evaluation_release_id") != manifest.get("release_id")
        or candidate.get("evaluation_release_manifest_sha256") != manifest_hash
    ):
        raise EvaluationError("candidate frozen evaluation identity does not match")

    def git(*args: str) -> str:
        try:
            result = subprocess.run(
                ["git", *args], cwd=project_root, capture_output=True, text=True, timeout=15, check=False
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise EvaluationError("cannot inspect candidate source state") from exc
        if result.returncode != 0:
            raise EvaluationError("cannot inspect candidate source state")
        return result.stdout.strip()

    commit_sha = git("rev-parse", "HEAD")
    if candidate.get("commit_sha") != commit_sha:
        raise EvaluationError("candidate source commit does not match current checkout")
    if git("status", "--porcelain", "--untracked-files=all"):
        raise EvaluationError("candidate source checkout is dirty")

    material_paths = release_candidate._material_paths(project_root)
    materials = candidate.get("materials")
    if not isinstance(materials, dict) or set(materials) != set(material_paths):
        raise EvaluationError("candidate material manifest is incomplete")
    tracked = set(git("ls-files").splitlines())
    if set(material_paths) - tracked:
        raise EvaluationError("candidate materials are not in the commit")
    for relative in material_paths:
        path = (project_root / relative).resolve()
        if project_root not in path.parents or not path.is_file():
            raise EvaluationError(f"candidate material is missing or outside checkout: {relative}")
        if hash_file(path) != materials.get(relative):
            raise EvaluationError(f"candidate material hash mismatch: {relative}")

    evidence_root = project_root / "verify-output/stage5-drills"
    try:
        current_drills = release_candidate._collect_drill_evidence(project_root, evidence_root, commit_sha)
    except Exception as exc:
        raise EvaluationError("candidate drill evidence is invalid") from exc
    if candidate.get("drill_evidence") != current_drills:
        raise EvaluationError("candidate drill evidence does not match current evidence")
    return candidate, hash_file(candidate_path)


def _load_scorer(path: Path):
    spec = importlib.util.spec_from_file_location("p5_frozen_scorer", path)
    if spec is None or spec.loader is None:
        raise EvaluationError("cannot load frozen scorer")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not callable(getattr(module, "score_case", None)):
        raise EvaluationError("frozen scorer has no score_case")
    return module.score_case


def _validate_results(cases: list[dict], results: list[dict]) -> dict[str, list[dict]]:
    if not isinstance(cases, list) or not isinstance(results, list):
        raise EvaluationError("cases and results must be lists")
    if not cases:
        raise EvaluationError("dataset is empty")
    if not results:
        raise EvaluationError("results are empty")
    case_map: dict[str, dict] = {}
    seen_tasks: set[str] = set()
    for case in cases:
        case_id = case.get("id")
        if not isinstance(case_id, str) or not case_id.strip():
            raise EvaluationError("dataset has empty case id")
        if case_id in case_map:
            raise EvaluationError(f"dataset has duplicate case id: {case_id}")
        if not isinstance(case.get("task_id"), str) or not case["task_id"].strip():
            raise EvaluationError(f"case has empty task id: {case_id}")
        if case["task_id"] in seen_tasks:
            raise EvaluationError(f"duplicate task id would inflate independent sample size: {case['task_id']}")
        seen_tasks.add(case["task_id"])
        for field in ("target_state", "required_citations", "expect_refusal", "expect_clarification", "hard_gates", "requires_tool"):
            if field not in case:
                raise EvaluationError(f"case missing {field}: {case_id}")
        if not isinstance(case["target_state"], str) or not case["target_state"].strip():
            raise EvaluationError(f"case has invalid target state: {case_id}")
        if not isinstance(case["required_citations"], list) or not all(isinstance(ref, str) and ref for ref in case["required_citations"]):
            raise EvaluationError(f"case has invalid required citations: {case_id}")
        if len(case["required_citations"]) != len(set(case["required_citations"])):
            raise EvaluationError(f"case has duplicate required citations: {case_id}")
        if any(not isinstance(case[field], bool) for field in ("expect_refusal", "expect_clarification", "requires_tool")):
            raise EvaluationError(f"case has invalid expectation flag: {case_id}")
        if not isinstance(case["hard_gates"], list) or not case["hard_gates"] or not all(isinstance(gate, str) and gate.strip() for gate in case["hard_gates"]):
            raise EvaluationError(f"case has invalid hard-gate labels: {case_id}")
        if len(case["hard_gates"]) != len(set(case["hard_gates"])):
            raise EvaluationError(f"case has duplicate hard-gate labels: {case_id}")
        case_map[case_id] = case

    grouped: dict[str, list[dict]] = {case_id: [] for case_id in case_map}
    seen_attempts: set[tuple[str, str]] = set()
    required_fields = {"case_id", "attempt_id", "final_state", "citations", "refusal", "clarification", "hard_gate_passes", "tool_correct", "quality_pass", "token_usage", "external_tool_cost_usd", "latency_ms"}
    for result in results:
        if not isinstance(result, dict) or required_fields - result.keys():
            raise EvaluationError("result missing required fields")
        case_id = result["case_id"]
        if not isinstance(case_id, str) or not case_id.strip():
            raise EvaluationError("empty case id in results")
        if case_id not in case_map:
            raise EvaluationError(f"unknown case id: {case_id}")
        attempt_id = result["attempt_id"]
        if not isinstance(attempt_id, str) or not attempt_id.strip():
            raise EvaluationError(f"empty attempt id: {case_id}")
        key = (case_id, attempt_id)
        if key in seen_attempts:
            raise EvaluationError(f"duplicate result: {case_id}/{attempt_id}")
        seen_attempts.add(key)
        if not isinstance(result["citations"], list) or not all(isinstance(item, str) and item for item in result["citations"]):
            raise EvaluationError(f"invalid citations: {case_id}")
        if len(result["citations"]) != len(set(result["citations"])):
            raise EvaluationError(f"duplicate citations: {case_id}")
        for field in ("refusal", "clarification", "quality_pass"):
            if not isinstance(result[field], bool):
                raise EvaluationError(f"invalid {field}: {case_id}")
        if result["tool_correct"] is not None and not isinstance(result["tool_correct"], bool):
            raise EvaluationError(f"invalid tool_correct: {case_id}")
        if case_map[case_id]["requires_tool"] and result["tool_correct"] is None:
            raise EvaluationError(f"tool result required for case: {case_id}")
        if not isinstance(result["hard_gate_passes"], dict):
            raise EvaluationError(f"invalid hard gate results: {case_id}")
        required_gates = set(case_map[case_id]["hard_gates"])
        if required_gates != result["hard_gate_passes"].keys() or any(not isinstance(result["hard_gate_passes"][gate], bool) for gate in required_gates):
            raise EvaluationError(f"missing or invalid hard gate result: {case_id}")
        if not isinstance(result["final_state"], str) or not result["final_state"].strip():
            raise EvaluationError(f"invalid final_state: {case_id}")
        for field in ("token_usage", "external_tool_cost_usd", "latency_ms"):
            value = result[field]
            if value is not None and (not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value) or value < 0):
                raise EvaluationError(f"invalid {field}: {case_id}")
        grouped[case_id].append(result)
    missing = [case_id for case_id, attempts in grouped.items() if not attempts]
    if missing:
        raise EvaluationError("missing required case results: " + ", ".join(missing))
    return grouped


def _ratio(numerator: int, denominator: int):
    return numerator / denominator if denominator else None


def _mean(values: list[float | int | None]):
    present = [value for value in values if value is not None]
    return sum(present) / len(present) if present else None


def _wilson(successes: int, count: int) -> dict | None:
    if count == 0:
        return None
    z = 1.959963984540054
    p = successes / count
    denom = 1 + z * z / count
    center = (p + z * z / (2 * count)) / denom
    half = z * ((p * (1 - p) / count + z * z / (4 * count * count)) ** 0.5) / denom
    return {"method": "Wilson score, 95%", "lower": max(0.0, center - half), "upper": min(1.0, center + half)}


def evaluate(
    root: Path,
    split: str,
    *,
    run_id: str,
    state_root: Path | None = None,
    candidate_manifest: Path | None = None,
    fixture_only: bool = False,
) -> dict:
    root = root.resolve()
    if split not in {"dev", "holdout"}:
        raise EvaluationError("split must be dev or holdout")
    if not isinstance(run_id, str) or not run_id.strip():
        raise EvaluationError("run id is required")
    if split == "holdout":
        if candidate_manifest is None and not fixture_only:
            raise EvaluationError("holdout requires candidate_manifest or fixture_only")
        if candidate_manifest is not None and fixture_only:
            raise EvaluationError("candidate_manifest and fixture_only are mutually exclusive")
    elif candidate_manifest is not None or fixture_only:
        raise EvaluationError("holdout mode options are only valid for holdout evaluation")
    manifest, hashes = _load_frozen(root)
    candidate = None
    candidate_manifest_hash = None
    if candidate_manifest is not None:
        candidate, candidate_manifest_hash = _load_candidate(root, candidate_manifest)
    dataset_name = f"{split}.json"
    dataset = _read_json(root / dataset_name)
    if dataset.get("split") != split or not isinstance(dataset.get("cases"), list):
        raise EvaluationError("dataset split or cases are invalid")
    results_name = f"{split}-results.json"
    results = _read_json(root / results_name)
    grouped = _validate_results(dataset["cases"], results)
    scorer = _load_scorer(root / "scorer.py")

    evaluation_release_hash = _canonical_hash({
        "hash_profile": HASH_PROFILE,
        "release": manifest,
        "actual_material_hashes": hashes,
    })
    release_hash = _canonical_hash({
        "hash_profile": HASH_PROFILE,
        "evaluation_release_hash": evaluation_release_hash,
        "candidate_id": candidate["candidate_id"] if candidate else None,
        "candidate_hash": candidate["candidate_hash"] if candidate else None,
    })
    consumed_at = datetime.now(timezone.utc).isoformat()
    fixture_replay_consumed = False
    if split == "holdout":
        if state_root is None:
            raise EvaluationError("fixture holdout requires a persistent state_root")
        state_root = state_root.resolve()
        state_root.mkdir(parents=True, exist_ok=True)
        marker = state_root / f"fixture-consumed-{evaluation_release_hash}.json"
        try:
            fd = os.open(marker, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError as exc:
            raise EvaluationError("synthetic fixture already consumed for this frozen evaluation release") from exc
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump({
                "run_id": run_id,
                "consumed_at": consumed_at,
                "evaluation_release_hash": evaluation_release_hash,
                "candidate_id": candidate["candidate_id"] if candidate else None,
                "candidate_hash": candidate["candidate_hash"] if candidate else None,
            }, handle, sort_keys=True)
            handle.write("\n")
        fixture_replay_consumed = True

    task_results = [scorer(case, grouped[case["id"]]) for case in dataset["cases"]]
    n_tasks = len(task_results)
    task_successes = sum(item["task_success"] for item in task_results)
    tool_tasks = [item for item in task_results if item["tool_required"] and item["tool_correct"] is not None]
    refusal_correct = sum(item["refusal_completion_classification_correct"] for item in task_results)
    quality_passes = sum(item["quality_pass"] for item in task_results)
    metrics = {
        "task_success_rate": _ratio(task_successes, n_tasks),
        "quality_pass_rate": _ratio(quality_passes, n_tasks),
        "tool_correctness_rate": _ratio(sum(item["tool_correct"] for item in tool_tasks), len(tool_tasks)),
        "citation_precision": _mean([item["citation_precision"] for item in task_results]),
        "citation_recall": _mean([item["citation_recall"] for item in task_results]),
        "refusal_completion_classification_accuracy": _ratio(refusal_correct, n_tasks),
        "mean_token_usage": _mean([item["mean_token_usage"] for item in task_results]),
        "mean_external_tool_cost_usd": _mean([item["mean_external_tool_cost_usd"] for item in task_results]),
        "mean_latency_ms": _mean([item["mean_latency_ms"] for item in task_results]),
    }
    attempt_classes = [
        {"case_id": case_id, "task_id": task["task_id"], "attempt_id": item["attempt_id"], **{key: item[key] for key in ("expected_state", "observed_state", "expected_refusal", "observed_refusal", "expected_clarification", "observed_clarification", "required_citations", "observed_citations", "hard_gate_results", "task_success", "state_ok", "refusal_ok", "clarification_ok", "hard_gates_pass")}}
        for task in task_results for case_id in [task["case_id"]] for item in task["attempts"]
    ]
    gate_results = {}
    for task in task_results:
        for gate, passed in task["hard_gate_results"].items():
            gate_results.setdefault(gate, []).append(passed)
    return {
        "report_schema": "p5-evaluation-report-v3",
        "hash_profile": HASH_PROFILE,
        "evaluation_scope": "offline_synthetic_fixture",
        "blind_holdout": False,
        "run_id": run_id,
        "release_id": manifest["release_id"],
        "commit": manifest["commit"],
        "lockfile_hash": hashes[manifest["lockfile"]],
        "prompt_hash": hashes[manifest["prompt"]],
        "tool_schema_hash": hashes[manifest["tool_schema"]],
        "dataset_id": dataset["dataset_id"],
        "dataset_hash": hashes[dataset_name],
        "results_hash": hashes[results_name],
        "scorer_hash": _canonical_hash({"scorer.py": hashes["scorer.py"], "scorer.json": hashes["scorer.json"]}),
        "frozen_material_hashes": hashes,
        "holdout_evaluation_release_hash": evaluation_release_hash,
        "release_hash": release_hash,
        "provider": manifest.get("provider", "synthetic"),
        "model": manifest.get("model", "fixture-v1"),
        "evidence_kind": "fixture",
        "evidence_status": "offline_fixture",
        "live_evidence": False,
        "executed_at": consumed_at,
        "split": split,
        "fixture_replay_consumed": fixture_replay_consumed,
        "official_holdout_consumed": False,
        "candidate_manifest_verified": candidate is not None,
        "candidate_id": candidate["candidate_id"] if candidate else None,
        "candidate_hash": candidate["candidate_hash"] if candidate else None,
        "candidate_manifest_sha256": candidate_manifest_hash,
        "fixture_replay_guard_scope": (
            "one synthetic fixture replay per frozen evaluation release in persistent local state_root; the consumed record identifies its candidate, but deleting/replacing it can bypass this teaching guard"
            if candidate else
            "synthetic fixture materials only in persistent local state_root; deleting/replacing it can bypass this teaching guard"
        ),
        "release_review_required": True,
        "publishable": False,
        "sample_size": {
            "independent_tasks": n_tasks,
            "attempts": len(results),
            "note": "Case/task is the independent unit; repeated attempts for one case are grouped and never counted as extra tasks.",
            "task_success_95_percent_interval": _wilson(task_successes, n_tasks),
        },
        "task_results": task_results,
        "attempt_classifications": attempt_classes,
        "metrics": metrics,
        "metric_sample_sizes": {
            "task_success_rate": n_tasks,
            "quality_pass_rate": n_tasks,
            "tool_correctness_rate": len(tool_tasks),
            "citation_precision": sum(item["citation_precision"] is not None for item in task_results),
            "citation_recall": sum(item["citation_recall"] is not None for item in task_results),
            "refusal_completion_classification_accuracy": n_tasks,
            "mean_token_usage": sum(item["mean_token_usage"] is not None for item in task_results),
            "mean_external_tool_cost_usd": sum(item["mean_external_tool_cost_usd"] is not None for item in task_results),
            "mean_latency_ms": sum(item["mean_latency_ms"] is not None for item in task_results),
        },
        "hard_gates": {
            "passed": all(all(values) for values in gate_results.values()),
            "by_gate": {gate: {"passed": all(values), "cases": len(values)} for gate, values in sorted(gate_results.items())},
        },
    }
