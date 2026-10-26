"""Build an immutable, non-publishable Stage 5 release-candidate manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

P5 = Path(__file__).resolve().parent
EVALUATION_DIR = P5 / "evaluation"
if str(EVALUATION_DIR) not in sys.path:
    sys.path.insert(0, str(EVALUATION_DIR))
from canonicalization import HASH_PROFILE, canonical_sha256, parse_json_strict


REQUIRED_DRILLS = (
    "approval-pause-resume",
    "cancel-revoke-race",
    "idempotency",
    "unknown-reconcile",
    "lease-takeover",
    "budget-unknown",
)
REQUIRED_FILES = (
    "examples/p4-durable-support/Dockerfile",
    "examples/p4-durable-support/compose.yaml",
    "examples/p4-durable-support/pyproject.toml",
    "examples/p4-durable-support/uv.lock",
    "examples/support_agent/__init__.py",
    "examples/p5-agent-delivery/README.md",
    "examples/p5-agent-delivery/RUNBOOK.md",
    "examples/p5-agent-delivery/DRILLS.md",
    "examples/p5-agent-delivery/OPERATIONS.md",
    "examples/p5-agent-delivery/HANDOFF.md",
    "examples/p5-agent-delivery/HANDOFF-RECORD.template.json",
    "examples/p5-agent-delivery/HANDOFF-RECORD.schema.json",
    "examples/p5-agent-delivery/runner.py",
    "examples/p5-agent-delivery/host.py",
    "examples/p5-agent-delivery/provider.py",
    "examples/p5-agent-delivery/run_drills.py",
    "examples/p5-agent-delivery/drill_report.py",
    "examples/p5-agent-delivery/release_candidate.py",
    "examples/p5-agent-delivery/evaluation/release.json",
    "examples/p5-agent-delivery/evaluation/canonicalization.py",
    "examples/p5-agent-delivery/evaluation/dev.json",
    "examples/p5-agent-delivery/evaluation/dev-results.json",
    "examples/p5-agent-delivery/evaluation/live-smoke.json",
    "examples/p5-agent-delivery/evaluation/holdout.json",
    "examples/p5-agent-delivery/evaluation/holdout-results.json",
    "examples/p5-agent-delivery/evaluation/prompt.txt",
    "examples/p5-agent-delivery/evaluation/tool-schema.json",
    "examples/p5-agent-delivery/evaluation/scorer.json",
    "examples/p5-agent-delivery/evaluation/scorer.py",
    "examples/p5-agent-delivery/evaluation/evaluation.py",
    "examples/p5-agent-delivery/evaluation/official_holdout.py",
    "examples/p5-agent-delivery/evaluation/subprocess_candidate.py",
    "examples/p5-agent-delivery/evaluation/run_fixture.py",
    "examples/p5-agent-delivery/evaluation/README.md",
    "examples/p5-agent-delivery/evaluation/test_evaluation.py",
    "examples/p5-agent-delivery/evaluation/test_official_holdout_runner.py",
    "examples/capstone-acceptance/acceptance.py",
    "examples/capstone-acceptance/test_acceptance.py",
    "examples/p5-agent-delivery/tests/test_release_candidate.py",
    "examples/manifest.json",
    "src/content/chapters/capstone/06-acceptance.mdx",
    "src/content/chapters/agent-deployment/05-recovery-drills.mdx",
)
DOC_FILES = (
    "docs/PROGRESS.md",
    "docs/superpowers/specs/2026-10-19-curriculum-reliability-design.md",
    "docs/superpowers/plans/2026-10-20-stage5-capstone.md",
    "docs/superpowers/evidence/2026-10-20-stage5-cold-start.md",
)
IMAGE_DIGEST = re.compile(r"sha256:[0-9a-f]{64}\Z")
COMMIT = re.compile(r"[0-9a-f]{40,64}\Z")


class ReleaseCandidateError(ValueError):
    """The source snapshot or its required evidence cannot be frozen."""


def canonical_hash(value: Any) -> str:
    return canonical_sha256(value)


def without_candidate_hash(manifest: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in manifest.items() if key not in {"candidate_id", "candidate_hash"}}


def _git(root: Path, *args: str) -> str:
    try:
        result = subprocess.run(
            ["git", *args], cwd=root, capture_output=True, text=True, timeout=15, check=False
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ReleaseCandidateError("cannot inspect Git source state") from exc
    if result.returncode != 0:
        raise ReleaseCandidateError("cannot inspect Git source state")
    return result.stdout.strip()


def _inside_file(root: Path, relative: str) -> Path:
    path = (root / relative).resolve()
    if root not in path.parents or not path.is_file():
        raise ReleaseCandidateError(f"required material is missing or escapes project root: {relative}")
    return path


def _material_paths(root: Path) -> list[str]:
    paths = set(REQUIRED_FILES) | set(DOC_FILES)
    for folder, suffix in (
        ("examples/p4-durable-support/app", ".py"),
        ("examples/p4-durable-support/migrations", ".sql"),
        ("examples/p4-durable-support/tests", ".py"),
        ("examples/support_agent", ".py"),
        ("examples/p5-agent-delivery/tests", ".py"),
    ):
        base = root / folder
        if not base.is_dir():
            raise ReleaseCandidateError(f"required material directory is missing: {folder}")
        for path in base.rglob(f"*{suffix}"):
            relative = path.relative_to(root).as_posix()
            _inside_file(root, relative)
            paths.add(relative)
    return sorted(paths)


def _frozen_evaluation(root: Path) -> tuple[str, str]:
    eval_root = root / "examples/p5-agent-delivery/evaluation"
    try:
        manifest = parse_json_strict((eval_root / "release.json").read_text(encoding="utf-8"))
        frozen = manifest["materials"]
        release_id = manifest["release_id"]
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise ReleaseCandidateError("frozen evaluation release manifest is invalid") from exc
    if manifest.get("hash_profile") != HASH_PROFILE:
        raise ReleaseCandidateError("frozen evaluation hash profile is unsupported")
    if not isinstance(release_id, str) or not release_id or not isinstance(frozen, dict) or not frozen:
        raise ReleaseCandidateError("frozen evaluation release manifest is incomplete")
    for name, expected_hash in frozen.items():
        if not isinstance(name, str) or Path(name).is_absolute() or ".." in Path(name).parts:
            raise ReleaseCandidateError("frozen evaluation material path is invalid")
        path = _inside_file(root, f"examples/p5-agent-delivery/evaluation/{name}")
        actual_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual_hash != expected_hash:
            raise ReleaseCandidateError(f"frozen evaluation material hash mismatch: {name}")
    smoke = manifest.get("live_smoke")
    if (
        not isinstance(smoke, dict)
        or smoke.get("file") != "live-smoke.json"
        or not isinstance(smoke.get("sha256"), str)
        or not re.fullmatch(r"[0-9a-f]{64}", smoke["sha256"])
    ):
        raise ReleaseCandidateError("predeclared live smoke case is invalid")
    smoke_path = _inside_file(root, "examples/p5-agent-delivery/evaluation/live-smoke.json")
    if hashlib.sha256(smoke_path.read_bytes()).hexdigest() != smoke["sha256"]:
        raise ReleaseCandidateError("predeclared live smoke case hash mismatch")
    return release_id, hashlib.sha256((eval_root / "release.json").read_bytes()).hexdigest()


def _collect_drill_evidence(root: Path, evidence_root: Path, commit_sha: str) -> list[dict[str, str]]:
    try:
        from drill_report import evaluate_report
    except ImportError as exc:
        raise ReleaseCandidateError("P5 drill report verifier is unavailable") from exc
    root = root.resolve()
    evidence_root = evidence_root.resolve()
    if not evidence_root.is_dir() or root not in evidence_root.parents:
        raise ReleaseCandidateError("drill evidence root must exist inside the project root")
    reports: dict[str, list[tuple[datetime, Path, dict[str, Any]]]] = {name: [] for name in REQUIRED_DRILLS}
    for discovered_path in evidence_root.glob("**/report.json"):
        relative_path = discovered_path.relative_to(root).as_posix()
        path = _inside_file(root, relative_path)
        try:
            report = parse_json_strict(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ReleaseCandidateError("drill report is unreadable") from exc
        if not isinstance(report, dict):
            continue
        scenario_id = report.get("scenario_id")
        if not isinstance(scenario_id, str) or scenario_id not in reports:
            continue
        run_id = report.get("run_id")
        finished_at = report.get("finished_at_utc")
        if not isinstance(run_id, str) or not run_id or not isinstance(finished_at, str):
            continue
        try:
            finished = datetime.fromisoformat(finished_at.replace("Z", "+00:00"))
        except ValueError:
            continue
        if finished.tzinfo is None or finished.utcoffset() is None or finished.utcoffset().total_seconds() != 0:
            continue
        report_materials = report.get("materials")
        if not isinstance(report_materials, dict):
            continue
        if report_materials.get("commit") != commit_sha:
            continue
        if report_materials.get("worktree_clean") is not True:
            continue
        try:
            verdict = evaluate_report(report, evidence_root)
        except Exception as exc:
            raise ReleaseCandidateError("matching drill report failed evidence validation") from exc
        if verdict.get("status") != "passed" or report.get("status") != "passed":
            continue
        reports[scenario_id].append((finished.astimezone(timezone.utc), path, report))

    selected = []
    for scenario in REQUIRED_DRILLS:
        candidates = reports[scenario]
        if not candidates:
            raise ReleaseCandidateError(f"missing clean passing drill evidence: {scenario}")
        _, path, report = max(candidates, key=lambda item: item[0])
        selected.append({
            "scenario_id": scenario,
            "run_id": report["run_id"],
            "report_path": path.relative_to(root).as_posix(),
            "report_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        })
    return selected


def build_release_candidate(
    project_root: Path,
    *,
    image_digest: str,
    evidence_root: Path | None = None,
) -> dict[str, Any]:
    """Freeze a clean source snapshot only after all six same-commit drills pass.

    The output records an unsigned candidate, not a publication approval.
    """
    root = project_root.resolve()
    if not IMAGE_DIGEST.fullmatch(image_digest or ""):
        raise ReleaseCandidateError("image must be supplied as an immutable sha256 digest")
    commit_sha = _git(root, "rev-parse", "HEAD")
    if not COMMIT.fullmatch(commit_sha):
        raise ReleaseCandidateError("Git commit identity is invalid")
    if _git(root, "status", "--porcelain", "--untracked-files=all"):
        raise ReleaseCandidateError("release candidate requires a clean worktree")
    evaluation_release_id, evaluation_manifest_hash = _frozen_evaluation(root)
    material_paths = _material_paths(root)
    tracked = set(_git(root, "ls-files").splitlines())
    untracked_materials = sorted(set(material_paths) - tracked)
    if untracked_materials:
        raise ReleaseCandidateError("release materials must be tracked by the candidate commit")
    materials = {
        relative: hashlib.sha256(_inside_file(root, relative).read_bytes()).hexdigest()
        for relative in material_paths
    }
    evidence_root = evidence_root or root / "verify-output/stage5-drills"
    drill_evidence = _collect_drill_evidence(root, evidence_root, commit_sha)
    if _git(root, "rev-parse", "HEAD") != commit_sha or _git(
        root, "status", "--porcelain", "--untracked-files=all"
    ):
        raise ReleaseCandidateError("source state changed while freezing release candidate")
    manifest: dict[str, Any] = {
        "schema": "p5-release-candidate-v2",
        "hash_profile": HASH_PROFILE,
        "status": "frozen-candidate",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "commit_sha": commit_sha,
        "image_digest": image_digest,
        "evaluation_release_id": evaluation_release_id,
        "evaluation_release_manifest_sha256": evaluation_manifest_hash,
        "materials": materials,
        "drill_evidence": drill_evidence,
        "holdout": {"status": "not_run", "consumed": False},
        "human_review": {"status": "pending", "reviewer": None, "reviewed_at_utc": None},
        "publishable": False,
        "signature": None,
    }
    manifest["candidate_hash"] = canonical_hash(manifest)
    manifest["candidate_id"] = f"p5-rc-{manifest['candidate_hash'][:16]}"
    return manifest


def write_new_manifest(path: Path, manifest: dict[str, Any]) -> None:
    """Write once; never overwrite or mutate an earlier candidate record."""
    path.parent.mkdir(parents=True, exist_ok=True)
    data = (json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
    fd, staged_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    staged = Path(staged_name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        # Publish a complete, flushed file without replacing an earlier candidate.
        os.link(staged, path)
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    except FileExistsError as exc:
        raise ReleaseCandidateError("candidate manifest already exists; choose a new output path") from exc
    finally:
        try:
            staged.unlink()
        except FileNotFoundError:
            pass


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Freeze a verified Stage 5 release-candidate manifest")
    parser.add_argument("--repo", type=Path, default=P5.parents[1])
    parser.add_argument("--image-digest", required=True, help="immutable OCI sha256 manifest digest")
    parser.add_argument("--evidence-root", type=Path)
    parser.add_argument("--output", type=Path, required=True, help="new path under ignored verify-output/ or outside the checkout")
    args = parser.parse_args(argv)
    try:
        repo = args.repo.resolve()
        output = args.output.resolve()
        if repo in output.parents and output.relative_to(repo).parts[0] != "verify-output":
            raise ReleaseCandidateError("manifest output must stay outside tracked source files")
        manifest = build_release_candidate(
            args.repo, image_digest=args.image_digest, evidence_root=args.evidence_root
        )
        write_new_manifest(output, manifest)
    except ReleaseCandidateError as exc:
        parser.exit(2, f"release candidate not frozen: {exc}\n")
    print(json.dumps({"candidate_id": manifest["candidate_id"], "candidate_hash": manifest["candidate_hash"], "output": str(output)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
