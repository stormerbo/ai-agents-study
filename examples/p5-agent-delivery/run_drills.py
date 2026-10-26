"""Run one deterministic P5 PostgreSQL drill and bind its evidence artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from uuid import UUID, uuid4

from drill_report import DrillReportError, evaluate_report, merge_observation_records, parse_junit


P5_ROOT = Path(__file__).resolve().parent
REPO_ROOT = P5_ROOT.parents[1]
P4_ROOT = P5_ROOT.parent / "p4-durable-support"
SCENARIOS = {
    "approval-pause-resume": [
        "tests/test_delivery_reconciliation.py::test_p5_coordinator_resumes_approved_write_dispatches_once_then_continues_model",
    ],
    "cancel-revoke-race": [
        "tests/test_cancel_and_revoke_races.py::test_three_cancel_revoke_boundaries",
    ],
    "idempotency": [
        "tests/test_task_idempotency.py::test_simultaneous_same_key_across_two_api_processes",
        "tests/test_task_idempotency.py::test_same_key_is_scoped_to_tenant_and_caller",
    ],
    "unknown-reconcile": [
        "tests/test_delivery_reconciliation.py::test_lost_http_response_after_sink_commit_is_unknown_then_queries_receipt",
        "tests/test_delivery_reconciliation.py::test_connection_failure_unknown_blocks_completion_and_unavailable_query_does_not_retry",
    ],
    "lease-takeover": [
        "tests/test_worker_ownership.py::test_takeover_fences_all_writes_and_dead_owner",
        "tests/test_provider_calls.py::test_late_response_settles_usage_but_stale_epoch_cannot_process_it",
    ],
    "budget-unknown": [
        "tests/test_limits.py::test_shared_budget_barrier_unknown_usage_and_unsent_release",
        "tests/test_p5_host.py::test_provider_transport_failure_becomes_unknown_without_implicit_retry",
        "tests/test_provider_calls.py::test_sending_call_can_be_marked_unknown_but_never_retried",
        "tests/test_provider_calls.py::test_saved_response_with_missing_usage_can_be_reconciled_later",
    ],
}
_ALLOWED_ENV = (
    "PATH", "HOME", "TMPDIR", "TMP", "TEMP", "SYSTEMROOT", "DOCKER_HOST", "DOCKER_CONTEXT",
    "DOCKER_CONFIG", "DOCKER_CERT_PATH", "DOCKER_TLS_VERIFY", "XDG_RUNTIME_DIR",
)


def _test_environment(source: dict[str, str], *, compose_project: str, observation_dir: Path | None = None) -> dict[str, str]:
    env = {key: source[key] for key in _ALLOWED_ENV if key in source}
    env.update({"P4_TEST_COMPOSE_PROJECT": compose_project, "PYTHONDONTWRITEBYTECODE": "1"})
    if observation_dir is not None:
        env["P5_DRILL_OBSERVATIONS_DIR"] = str(observation_dir)
    return env


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _redact(text: str) -> str:
    text = re.sub(r"(?i)(authorization\s*[:=]\s*bearer\s+)\S+", r"\1[REDACTED]", text)
    text = re.sub(r"(?i)(api[_-]?key|auth[_-]?token)(\s*[:=]\s*)\S+", r"\1\2[REDACTED]", text)
    text = re.sub(r"(?i)postgres(?:ql)?://[^\s'\"]+", "postgresql://[REDACTED]", text)
    text = re.sub(r"sk-ant-[A-Za-z0-9_-]+", "[REDACTED_PROVIDER_KEY]", text)
    return text


def _command_output(args: list[str], *, env: dict[str, str] | None = None, cwd: Path = REPO_ROOT) -> tuple[int, str]:
    try:
        result = subprocess.run(args, cwd=cwd, env=env, capture_output=True, text=True, timeout=20, check=False)
        return result.returncode, _redact(result.stdout + result.stderr).strip()
    except (OSError, subprocess.TimeoutExpired) as exc:
        return 127, type(exc).__name__


def _cleanup_state(project: str, env: dict[str, str]) -> dict[str, bool]:
    compose = ["docker", "compose", "-p", project, "-f", str(P4_ROOT / "compose.yaml")]
    ps_code, ps_output = _command_output(compose + ["ps", "--all", "-q"], env=env, cwd=P4_ROOT)
    volume_code, volume_output = _command_output([
        "docker", "volume", "ls", "-q", "--filter", f"label=com.docker.compose.project={project}"
    ], env=env)
    return {
        "compose_project_removed": ps_code == 0 and not ps_output,
        "volume_removed": volume_code == 0 and not volume_output,
    }


def _versions(env: dict[str, str]) -> dict[str, str | None]:
    python = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    uv_code, uv = _command_output(["uv", "--version"], env=env)
    docker_code, docker = _command_output(["docker", "version", "--format", "{{.Client.Version}}/{{.Server.Version}}"], env=env)
    postgres_code, postgres = _command_output(["docker", "image", "inspect", "postgres:18.0-bookworm", "--format", "{{.Id}}"], env=env)
    return {
        "python": python,
        "uv": uv if uv_code == 0 else None,
        "docker": docker if docker_code == 0 else None,
        "postgres_image": postgres if postgres_code == 0 else "postgres:18.0-bookworm (fixed tag)",
    }


def _write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_scenario(scenario_id: str, evidence_root: Path, run_id: str | None = None) -> dict:
    if scenario_id not in SCENARIOS:
        raise DrillReportError("unknown scenario_id")
    run_id = run_id or str(uuid4())
    try:
        run_id = str(UUID(run_id))
    except ValueError as exc:
        raise DrillReportError("run_id must be a UUID") from exc
    root = evidence_root.expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    run_dir = root / run_id / scenario_id
    if run_dir.exists():
        raise DrillReportError("run evidence directory already exists")
    run_dir.mkdir(parents=True)
    project = "p5-drill-" + run_id.replace("-", "")[:16]
    observations_dir = run_dir / "observations"
    env = _test_environment(os.environ, compose_project=project, observation_dir=observations_dir)
    junit_path = run_dir / "junit.xml"
    log_path = run_dir / "console.log"
    started = datetime.now(timezone.utc).isoformat()
    start = time.monotonic()
    preflight = _command_output(["docker", "info", "--format", "{{.ServerVersion}}"], env=env)
    execution_status = "blocked"
    result_code = 127
    output = f"Preflight: {preflight[1]}"
    if preflight[0] == 0:
        command = [
            "uv", "run", "--frozen", "pytest", "-m", "integration", "-q",
            *SCENARIOS[scenario_id], f"--junitxml={junit_path}",
        ]
        try:
            result = subprocess.run(command, cwd=P4_ROOT, env=env, capture_output=True,
                                    text=True, timeout=600, check=False)
            result_code = result.returncode
            output = _redact(result.stdout + result.stderr)
            if junit_path.is_file():
                execution_status = "passed" if result_code == 0 else "failed"
            else:
                execution_status = "blocked"
        except (OSError, subprocess.TimeoutExpired) as exc:
            result_code = 127
            execution_status = "blocked"
            output += f"\nRunner exception: {type(exc).__name__}\n"
    log_path.write_text(output, encoding="utf-8")
    try:
        results = parse_junit(junit_path) if junit_path.is_file() else []
    except DrillReportError:
        results = []
        execution_status = "failed"
    if not results:
        # Missing/empty JUnit is a machine-readable harness error, never a pass.
        node_status = "error" if execution_status == "failed" else "skipped"
        results = [{"node_id": "runner::integration-harness", "status": node_status}]
    cleanup = _cleanup_state(project, env)
    git_code, commit = _command_output(["git", "rev-parse", "HEAD"], env=env)
    status_code, status_output = _command_output(["git", "status", "--porcelain"], env=env)
    diff_code, diff = _command_output(["git", "diff", "--binary", "HEAD"], env=env)
    materials = {
        "commit": commit if git_code == 0 else None,
        "worktree_clean": status_code == 0 and not status_output,
        "worktree_diff_sha256": hashlib.sha256(diff.encode()).hexdigest() if diff_code == 0 else None,
    }
    observation_records = []
    if observations_dir.is_dir():
        for path in sorted(observations_dir.glob("*.json")):
            try:
                record = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise DrillReportError("invalid test observation artifact") from exc
            if not isinstance(record, dict) or record.get("scenario_id") != scenario_id:
                raise DrillReportError("observation record does not match selected scenario")
            if record.get("node_id") not in {item["node_id"] for item in results}:
                raise DrillReportError("observation node id is not in JUnit results")
            observation_records.append({
                "path": path.relative_to(root).as_posix(), "sha256": _sha256(path),
            })
    observed = merge_observation_records(scenario_id, [
        json.loads((root / artifact["path"]).read_text(encoding="utf-8"))
        for artifact in observation_records
    ]) if observation_records else {}
    report = {
        "schema": "p5-drill-report-v1",
        "run_id": run_id,
        "scenario_id": scenario_id,
        "started_at_utc": started,
        "finished_at_utc": datetime.now(timezone.utc).isoformat(),
        "elapsed_ms": round((time.monotonic() - start) * 1000),
        "test_execution_status": execution_status,
        "test_exit_code": result_code,
        "expected_node_ids": [item["node_id"] for item in results],
        "test_results": results,
        "command": "uv run --frozen pytest -m integration -q " + " ".join(SCENARIOS[scenario_id]),
        "materials": materials,
        "environment": _versions(env),
        "cleanup": cleanup,
        "artifacts": {
            "junit": {"path": junit_path.relative_to(root).as_posix(), "sha256": _sha256(junit_path)} if junit_path.is_file() else None,
            "console_log": {"path": log_path.relative_to(root).as_posix(), "sha256": _sha256(log_path)},
            "observations": observation_records,
        },
        "observed": observed,
        "review": {"reviewer": None, "reviewed_at_utc": None, "decision": "needs-review"},
    }
    # The evaluator requires both artifacts. A blocked run without JUnit is
    # represented by a local synthetic JUnit node, explicitly marked skipped.
    if report["artifacts"]["junit"] is None:
        junit_path.write_text(
            '<testsuite tests="1" failures="0" errors="1" skipped="0">'
            '<testcase classname="runner" name="integration-harness"><error/></testcase></testsuite>\n'
            if execution_status == "failed" else
            '<testsuite tests="1" failures="0" errors="0" skipped="1">'
            '<testcase classname="runner" name="integration-harness"><skipped/></testcase></testsuite>\n',
            encoding="utf-8",
        )
        report["expected_node_ids"] = ["runner::integration-harness"]
        report["test_results"] = [{"node_id": "runner::integration-harness", "status": node_status}]
        report["artifacts"]["junit"] = {"path": junit_path.relative_to(root).as_posix(), "sha256": _sha256(junit_path)}
    verdict = evaluate_report(report, root)
    report["status"] = verdict["status"]
    report["missing_fields"] = verdict["missing_fields"]
    report_path = run_dir / "report.json"
    _write_json(report_path, report)
    return {"report": str(report_path), "status": report["status"], "test_execution_status": execution_status,
            "test_exit_code": result_code, "missing_fields": verdict["missing_fields"]}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run one Stage 5 synthetic PostgreSQL drill and collect evidence")
    parser.add_argument("--scenario", choices=sorted(SCENARIOS), required=True)
    parser.add_argument("--evidence-root", type=Path, required=True)
    parser.add_argument("--run-id", help="UUID; defaults to a fresh UUID")
    args = parser.parse_args(argv)
    try:
        result = run_scenario(args.scenario, args.evidence_root, args.run_id)
    except DrillReportError as exc:
        parser.error(str(exc))
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "passed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
