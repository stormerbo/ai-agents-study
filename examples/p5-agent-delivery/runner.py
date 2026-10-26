"""Explicit, bounded live smoke runner for the synthetic P5 capstone task."""
from __future__ import annotations

import argparse
import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
from urllib.parse import urlsplit
from uuid import UUID, uuid4

ROOT = Path(__file__).resolve().parents[2]
EXAMPLES = ROOT / "examples"
P5_ROOT = Path(__file__).resolve().parent
P4_ROOT = EXAMPLES / "p4-durable-support"
for import_path in (EXAMPLES, P4_ROOT):
    if str(import_path) not in sys.path:
        sys.path.insert(0, str(import_path))

from host import resume_agent_turn, trusted_provider_tools
from provider import AnthropicMessagesAdapter, create_anthropic_client

SYNTHETIC_PROMPT = "查询合成订单 A-1001，并在人工审批后发送通知：订单 A-1001 已发货。只有收到投递回执后才报告通知已发送。"
SMOKE_CASE_ID = "p5-order-notice-smoke-v1"
SMOKE_REQUIRED_TOOLS = ("lookup_order", "send_notice")
SMOKE_APPROVAL_TOOLS = ("send_notice",)
SYSTEM_PROMPT = (
    "你是售后订单助手。只使用当前提供的工具与证据；不能猜测订单或政策。"
    "send_notice 是会产生外部效果的合成动作，必须等待审批，不得声称已发送，直到收到工具结果。"
    "引用只能复制工具结果中的 citations 条目，不得编造 resource_id、version 或 chunk_id。"
    "最终只返回 JSON：{outcome, text, citations}；每条 citation 必须是 {resource_id, version, chunk_id}。"
)
MAX_ROUNDS = 4
MAX_OUTPUT_TOKENS = 512
RESERVED_TOKENS = 4096
RESERVED_TOOLS = 4
MAX_PROVIDER_TIMEOUT = 45.0
MCP_SERVER = ROOT / "examples" / "p3-controlled-agent" / "server.py"


@dataclass(frozen=True)
class LiveConfig:
    database_url: str = field(repr=False)
    endpoint_id: str
    budget_account: str
    model: str
    api_key: str = field(repr=False)
    base_url: str | None = field(default=None, repr=False)
    sink_url: str = "http://127.0.0.1:8002"
    max_rounds: int = MAX_ROUNDS
    max_tokens: int = MAX_OUTPUT_TOKENS
    reserved_tokens: int = RESERVED_TOKENS
    reserved_tools: int = RESERVED_TOOLS
    timeout: float = MAX_PROVIDER_TIMEOUT

    @classmethod
    def from_env(cls, env=None) -> "LiveConfig":
        env = os.environ if env is None else env
        database_url = env.get("DATABASE_URL", "").strip()
        endpoint_id = env.get("P5_PROVIDER_ENDPOINT", "").strip()
        budget_account = env.get("P5_BUDGET_ACCOUNT", "").strip()
        model = env.get("VERIFY_MODEL", "").strip()
        api_key = (env.get("ANTHROPIC_AUTH_TOKEN") or env.get("ANTHROPIC_API_KEY") or "").strip()
        sink = env.get("P5_SINK_URL", "http://127.0.0.1:8002").strip()
        base_url = env.get("ANTHROPIC_BASE_URL") or None
        missing = [name for name, value in (
            ("DATABASE_URL", database_url), ("P5_PROVIDER_ENDPOINT", endpoint_id),
            ("P5_BUDGET_ACCOUNT", budget_account), ("VERIFY_MODEL", model),
            ("ANTHROPIC_API_KEY (or ANTHROPIC_AUTH_TOKEN)", api_key),
        ) if not value]
        if missing:
            raise ValueError("Missing live configuration: " + ", ".join(missing))
        if len(endpoint_id) > 200 or len(budget_account) > 200 or len(model) > 200:
            raise ValueError("Endpoint, budget account, and model identifiers must be bounded")
        parsed_dsn = urlsplit(database_url)
        if parsed_dsn.scheme not in {"postgres", "postgresql"} or parsed_dsn.hostname not in {"127.0.0.1", "localhost"}:
            raise ValueError("Live runner is restricted to a loopback PostgreSQL database")
        from app.delivery import sink_url
        try:
            sink = sink_url(sink)
        except ValueError as exc:
            raise ValueError("P5_SINK_URL must name the local synthetic sink") from exc
        # Reuse the adapter's strict HTTPS/loopback check before any database work.
        if base_url is not None:
            _validate_provider_base_url(base_url)
        return cls(database_url=database_url, endpoint_id=endpoint_id,
                   budget_account=budget_account, model=model, api_key=api_key,
                   base_url=base_url, sink_url=sink)


def _validate_provider_base_url(value: str) -> None:
    from provider import build_anthropic_client

    class ValidationClient:
        def __init__(self, **kwargs):
            pass

    build_anthropic_client(ValidationClient, "validation-only", value, timeout=MAX_PROVIDER_TIMEOUT)


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _safe_report(
    *,
    run_id,
    task_id,
    release_id,
    status,
    provider_host,
    model,
    prompt_hash,
    tools_hash,
    elapsed_ms,
    request=None,
    task_status=None,
    error_type=None,
    started_at_utc=None,
    finished_at_utc=None,
    provenance=None,
    rounds=None,
    tools=None,
    output_validation=None,
) -> dict:
    """Create a versioned report from allowlisted metadata, never raw provider data."""
    finished = finished_at_utc or datetime.now(timezone.utc).isoformat()
    report = {
        "schema": "p5-live-smoke-v3",
        "smoke_case_id": SMOKE_CASE_ID,
        "run_id": str(run_id),
        "task_id": str(task_id),
        "release_id": release_id,
        "provider": "anthropic",
        "timestamp_utc": finished,
        "started_at_utc": started_at_utc or finished,
        "finished_at_utc": finished,
        "provider_host": provider_host,
        "model": model,
        "prompt_sha256": prompt_hash,
        "tool_schema_sha256": tools_hash,
        "provenance": dict(provenance or {}),
        "budgets": {
            "max_rounds": MAX_ROUNDS,
            "max_output_tokens_per_round": MAX_OUTPUT_TOKENS,
            "reserved_tokens_per_call": RESERVED_TOKENS,
            "reserved_tools_per_call": RESERVED_TOOLS,
            "request_timeout_seconds": MAX_PROVIDER_TIMEOUT,
        },
        "rounds": [
            {
                **{
                    key: row.get(key)
                    for key in (
                        "round_index", "request_id", "state", "stop_reason",
                        "usage_tokens", "usage_tools", "started_at_utc",
                        "finished_at_utc", "latency_ms", "exception_type",
                    )
                    if key in row
                },
                "tool_calls": [
                    {key: call.get(key) for key in ("tool", "status", "approval_verified") if key in call}
                    for call in row.get("tool_calls", [])
                    if isinstance(call, dict)
                ],
            }
            for row in (rounds or [])
            if isinstance(row, dict)
        ],
        "tools": [
            {key: row.get(key) for key in ("tool", "status", "approval_verified") if key in row}
            for row in (tools or [])
            if isinstance(row, dict)
        ],
        "output_validation": {
            key: value
            for key, value in (output_validation or {}).items()
            if key in {"status", "output_sha256", "citation_count"}
        },
        "status": status,
        "task_status": task_status,
        "elapsed_ms": elapsed_ms,
        "sdk_versions": {},
        "review": {"decision": "needs-review", "reviewer": None, "reviewed_at_utc": None},
    }
    if request:
        report.update(
            {
                "request_id": str(request["request_id"]),
                "stop_reason": request["stop_reason"],
                "usage_tokens": request["usage_tokens"],
                "usage_tools": request["usage_tools"],
            }
        )
    if error_type:
        report["error_type"] = error_type
    return report


def _live_gate_status(report: dict) -> str:
    """Classify the live gate conservatively from durable run facts."""
    if report.get("status") in {"failed", "truncated", "protocol_error", "transport_error", "tool_error"}:
        return "failed"
    if report.get("status") != "completed" or report.get("task_status") != "completed":
        return "unverified"
    if report.get("smoke_case_id") != SMOKE_CASE_ID:
        return "unverified"
    tools = report.get("tools")
    if not isinstance(tools, list) or any(not isinstance(row, dict) for row in tools):
        return "unverified"
    successful_tools = {
        row.get("tool") for row in tools if row.get("status") == "succeeded"
    }
    if any(
        any(row.get("tool") == name and row.get("status") == "failed" for row in tools)
        for name in SMOKE_REQUIRED_TOOLS
    ):
        return "failed"
    if not set(SMOKE_REQUIRED_TOOLS).issubset(successful_tools):
        return "unverified"
    for name in SMOKE_APPROVAL_TOOLS:
        witnesses = [row for row in tools if row.get("tool") == name]
        if not witnesses or any(row.get("approval_verified") is not True for row in witnesses):
            return "unverified"
    output = report.get("output_validation")
    if not isinstance(output, dict) or output.get("status") != "passed":
        return "unverified"
    output_hash = output.get("output_sha256")
    if not isinstance(output_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", output_hash):
        return "unverified"
    rounds = report.get("rounds")
    if not isinstance(rounds, list) or not rounds:
        return "unverified"
    for row in rounds:
        if not isinstance(row, dict) or not row.get("request_id") or row.get("state") != "processed":
            return "unverified"
        for key in ("usage_tokens", "usage_tools"):
            value = row.get(key)
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                return "unverified"
    return "passed"


def _load_action_evidence(conn, task_id):
    """Load sanitized tool status and verify the exact durable approval binding."""
    return conn.execute("""SELECT a.turn_id,a.tool,a.status,
        CASE WHEN a.requires_approval THEN EXISTS (
            SELECT 1 FROM approvals p WHERE p.action_id=a.id AND p.task_id=a.task_id
            AND p.status='approved' AND p.decided_by=p.eligible_approver AND p.decided_at IS NOT NULL
            AND p.args_hash=a.canonical_args_hash AND p.resource_version=a.resource_version
            AND p.acl_version=a.acl_version AND p.policy_version=a.policy_version
        ) ELSE NULL END AS approval_verified
        FROM actions a WHERE a.task_id=%s ORDER BY a.turn_epoch,a.turn_id,a.position""", (task_id,)).fetchall()


def _git_value(args: list[str]) -> str | None:
    try:
        completed = subprocess.run(
            ["git", *args], cwd=ROOT, capture_output=True, text=True, timeout=10, check=False
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    return completed.stdout.strip() if completed.returncode == 0 else None


def _evidence_material_bytes(tool_schema: list[dict]) -> dict[str, bytes]:
    evaluation_root = P5_ROOT / "evaluation"
    manifest_path = evaluation_root / "release.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    frozen = manifest.get("materials")
    if not isinstance(frozen, dict) or not frozen:
        raise RuntimeError("Frozen evaluation manifest is incomplete")
    actual = {}
    contents = {}
    for name, expected in frozen.items():
        path = (evaluation_root / name).resolve()
        if path.parent != evaluation_root.resolve() or not path.is_file():
            raise RuntimeError("Frozen evaluation material is missing")
        content = path.read_bytes()
        digest = hashlib.sha256(content).hexdigest()
        if digest != expected:
            raise RuntimeError("Frozen evaluation material hash mismatch")
        actual[name] = digest
        contents[name] = content.decode("utf-8")
    live_smoke = manifest.get("live_smoke")
    if (
        not isinstance(live_smoke, dict)
        or live_smoke.get("file") != "live-smoke.json"
        or not isinstance(live_smoke.get("sha256"), str)
        or not re.fullmatch(r"[0-9a-f]{64}", live_smoke["sha256"])
    ):
        raise RuntimeError("Predeclared live smoke case is not frozen")
    smoke_path = (evaluation_root / "live-smoke.json").resolve()
    if smoke_path.parent != evaluation_root.resolve() or not smoke_path.is_file():
        raise RuntimeError("Predeclared live smoke case is missing")
    smoke_content = smoke_path.read_bytes()
    if hashlib.sha256(smoke_content).hexdigest() != live_smoke["sha256"]:
        raise RuntimeError("Predeclared live smoke case hash mismatch")
    contents["live-smoke.json"] = smoke_content.decode("utf-8")
    material_map = {
        "lockfile": (P4_ROOT / "uv.lock").read_bytes(),
        "prompt": json.dumps(
            {"system": SYSTEM_PROMPT, "user": SYNTHETIC_PROMPT},
            sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        ).encode("utf-8"),
        "tool_schema": json.dumps(
            tool_schema, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        ).encode("utf-8"),
        "dataset": json.dumps(
            {name: contents[name] for name in ("dev.json", "holdout.json", "live-smoke.json")},
            sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        ).encode("utf-8"),
        "scorer": json.dumps(
            {name: contents[name] for name in ("scorer.json", "scorer.py", "evaluation.py")},
            sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        ).encode("utf-8"),
    }
    smoke_case = json.loads(contents["live-smoke.json"])
    if (
        smoke_case.get("case_id") != SMOKE_CASE_ID
        or smoke_case.get("prompt") != SYNTHETIC_PROMPT
        or smoke_case.get("required_successful_tools") != list(SMOKE_REQUIRED_TOOLS)
        or smoke_case.get("approval_required_tools") != list(SMOKE_APPROVAL_TOOLS)
        or smoke_case.get("max_rounds") != MAX_ROUNDS
        or smoke_case.get("max_output_tokens_per_round") != MAX_OUTPUT_TOKENS
    ):
        raise RuntimeError("Predeclared live smoke case does not match the bounded runner")
    return material_map


def _live_provenance(prompt_hash: str, tools_hash: str, tool_schema: list[dict]) -> dict:
    """Hash current release inputs and verify frozen synthetic eval materials."""
    materials = _evidence_material_bytes(tool_schema)
    actual_hashes = {
        name: hashlib.sha256(content).hexdigest()
        for name, content in materials.items()
    }
    if actual_hashes["prompt"] != prompt_hash or actual_hashes["tool_schema"] != tools_hash:
        raise RuntimeError("Live prompt or tool schema hash changed during preparation")
    source_paths = [P5_ROOT / "runner.py", P5_ROOT / "host.py", P5_ROOT / "provider.py"]
    source_paths.extend([MCP_SERVER, MCP_SERVER.parent / "fixtures.py"])
    source_paths.extend(sorted((P4_ROOT / "app").glob("*.py")))
    source_paths.extend(sorted((P4_ROOT / "migrations").glob("*.sql")))
    code_hashes = {
        path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in source_paths
        if path.is_file()
    }
    diff = _git_value(["diff", "--binary", "HEAD"]) or ""
    untracked = _git_value(["ls-files", "--others", "--exclude-standard"]) or ""
    untracked_hashes = {}
    for name in sorted(filter(None, untracked.splitlines())):
        path = (ROOT / name).resolve()
        if ROOT.resolve() in path.parents and path.is_file():
            untracked_hashes[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    diff_hash = _sha256(json.dumps(
        {"tracked_diff": diff, "untracked": untracked_hashes},
        sort_keys=True, separators=(",", ":"),
    ))
    status = _git_value(["status", "--porcelain"])
    return {
        "commit_sha": _git_value(["rev-parse", "HEAD"]),
        "worktree_clean": status == "",
        "worktree_diff_sha256": diff_hash,
        "lockfile_sha256": actual_hashes["lockfile"],
        "prompt_sha256": actual_hashes["prompt"],
        "tool_schema_sha256": actual_hashes["tool_schema"],
        "dataset_sha256": actual_hashes["dataset"],
        "scorer_sha256": actual_hashes["scorer"],
        "code_sha256": _sha256(json.dumps(code_hashes, sort_keys=True, separators=(",", ":"))),
        "code_file_sha256": code_hashes,
        "frozen_evaluation_release_sha256": hashlib.sha256(
            (P5_ROOT / "evaluation" / "release.json").read_bytes()
        ).hexdigest(),
    }


def _write_new_file(root: Path, path: Path, content: bytes) -> None:
    root = root.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    parent = path.parent.resolve()
    if parent != root and root not in parent.parents:
        raise ValueError("Evidence output path escapes its run root")
    fd, staged_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=parent)
    staged = Path(staged_name)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        # A hard link publishes only the complete staged bytes and fails if the
        # run-id path already exists; unlike replace(), it cannot overwrite it.
        os.link(staged, path)
        directory_fd = os.open(parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        try:
            staged.unlink()
        except FileNotFoundError:
            pass


def _write_evidence_bundle(report: dict, tool_schema: list[dict], *, evidence_root: Path) -> dict:
    """Write a root-bound live artifact and a partial Task 2a acceptance report."""
    acceptance_root = EXAMPLES / "capstone-acceptance"
    if str(acceptance_root) not in sys.path:
        sys.path.insert(0, str(acceptance_root))
    from acceptance import AcceptanceReport, Evidence, build_acceptance_matrix, decide

    root = evidence_root.resolve()
    root.mkdir(parents=True, exist_ok=True)

    material_bytes = _evidence_material_bytes(tool_schema)
    provenance = report["provenance"]
    material_hashes = {}
    materials = {}
    for name, content in material_bytes.items():
        digest = hashlib.sha256(content).hexdigest()
        if digest != provenance.get(f"{name}_sha256"):
            raise RuntimeError("Evidence material changed after live-run preparation")
        locator = f"materials/{name}.bin"
        path = root / locator
        _write_new_file(root, path, content)
        material_hashes[name] = digest
        materials[name] = {"locator": locator, "sha256": digest}

    status = _live_gate_status(report)
    executed_at = report["finished_at_utc"]
    payload = {
        "gate_id": "live_model_normal",
        "kind": "live",
        "status": status,
        "release_id": report["release_id"],
        "run_id": report["run_id"],
        "smoke_case_id": report["smoke_case_id"],
        "provider": report["provider"],
        "model": report["model"],
        "executed_at": executed_at,
    }
    content = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    digest = hashlib.sha256(content).hexdigest()
    artifact_locator = "artifacts/live_model_normal.json"
    artifact_path = root / artifact_locator
    _write_new_file(root, artifact_path, content)
    manifest = {
        "version": 2,
        "release_id": report["release_id"],
        "run_id": report["run_id"],
        "commit_sha": provenance["commit_sha"],
        "provider": report["provider"],
        "model": report["model"],
        "executed_at": executed_at,
        "materials": materials,
        **{f"{name}_sha256": digest for name, digest in material_hashes.items()},
        "artifacts": [{
            "gate_id": "live_model_normal",
            "kind": "live",
            "status": status,
            "locator": artifact_locator,
            "sha256": digest,
            "bytes": len(content),
            "release_id": report["release_id"],
            "run_id": report["run_id"],
        }],
    }
    _write_new_file(
        root,
        root / "evidence-manifest.json",
        (json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8"),
    )
    evidence = Evidence(
        "live_model_normal", status, "live", artifact_locator, digest,
        report["release_id"], report["run_id"],
    )
    acceptance = AcceptanceReport(
        version=2,
        release_id=report["release_id"],
        run_id=report["run_id"],
        commit_sha=provenance["commit_sha"],
        lockfile_sha256=material_hashes["lockfile"],
        prompt_sha256=material_hashes["prompt"],
        tool_schema_sha256=material_hashes["tool_schema"],
        dataset_sha256=material_hashes["dataset"],
        scorer_sha256=material_hashes["scorer"],
        provider=report["provider"],
        model=report["model"],
        executed_at=executed_at,
        evidence=[evidence],
        # A smoke run is not a frozen release candidate; the required holdout
        # gate remains absent, so the classifier must return incomplete.
        candidate_sha256=None,
        image_digest=None,
        holdout_version=None,
        executor_sha256=provenance["code_sha256"],
    )
    decision = decide(acceptance, root)
    matrix = build_acceptance_matrix(acceptance, root)
    acceptance_document = {
        "version": 2,
        "release_id": acceptance.release_id,
        "run_id": acceptance.run_id,
        "commit_sha": acceptance.commit_sha,
        "lockfile_sha256": acceptance.lockfile_sha256,
        "prompt_sha256": acceptance.prompt_sha256,
        "tool_schema_sha256": acceptance.tool_schema_sha256,
        "dataset_sha256": acceptance.dataset_sha256,
        "scorer_sha256": acceptance.scorer_sha256,
        "candidate_sha256": acceptance.candidate_sha256,
        "image_digest": acceptance.image_digest,
        "holdout_version": acceptance.holdout_version,
        "executor_sha256": acceptance.executor_sha256,
        "provider": acceptance.provider,
        "model": acceptance.model,
        "executed_at": acceptance.executed_at,
        "evidence": [{
            "gate_id": evidence.gate_id,
            "status": evidence.status,
            "kind": evidence.kind,
            "locator": evidence.locator,
            "sha256": evidence.sha256,
            "release_id": evidence.release_id,
            "run_id": evidence.run_id,
        }],
        "decision": decision,
        "gate_matrix": matrix["gates"],
        "matrix_authenticated": matrix["authenticated"],
        "matrix_evidence_scope": matrix["evidence_scope"],
    }
    _write_new_file(
        root,
        root / "acceptance-report.json",
        (json.dumps(acceptance_document, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8"),
    )
    return decision


def _write_report(report: dict, tool_schema: list[dict]) -> Path:
    directory = ROOT / "verify-output" / "stage5-live" / report["run_id"]
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "report.json"
    try:
        report["evidence_registry_decision"] = _write_evidence_bundle(
            report, tool_schema, evidence_root=directory / "evidence"
        )
    except Exception as exc:
        report["evidence_registry_decision"] = {
            "decision": "invalid-report", "reason": type(exc).__name__
        }
    _write_new_file(
        directory,
        path,
        (json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8"),
    )
    return path


def _write_preflight_report(report: dict) -> Path:
    """Persist an explicit live attempt that stopped before provider evidence exists."""
    directory = ROOT / "verify-output" / "stage5-live" / report["run_id"]
    directory.mkdir(parents=True, exist_ok=True)
    report["evidence_registry_decision"] = {
        "decision": "not-evaluated",
        "reason": "preflight-failed-before-provider-evidence",
    }
    path = directory / "report.json"
    _write_new_file(
        directory,
        path,
        (json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8"),
    )
    return path


def _mcp_components():
    try:
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client
    except ImportError as exc:
        raise RuntimeError("Install the P5 provider dependency group, including MCP, before --live") from exc
    return ClientSession, StdioServerParameters, stdio_client


async def _with_mcp_session(callback, components):
    ClientSession, StdioServerParameters, stdio_client = components
    child_env = {"PATH": os.environ.get("PATH", ""), "PYTHONDONTWRITEBYTECODE": "1"}
    params = StdioServerParameters(command=sys.executable, args=[str(MCP_SERVER)], env=child_env)
    async with stdio_client(params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            return await callback(session)


async def run_once(task_id: UUID, *, owner: str, live: bool, env=None) -> dict:
    """Claim and advance exactly one synthetic task wake-up; no implicit retries."""
    if not live:
        return {"status": "live_opt_in_required"}
    if not isinstance(task_id, UUID) or not re.fullmatch(r"[A-Za-z0-9._-]{1,100}", owner or ""):
        return {"status": "invalid_run_arguments"}
    run_id = uuid4()
    started_at_utc = datetime.now(timezone.utc).isoformat()
    started = time.monotonic()
    prompt_hash = _sha256(json.dumps({"system": SYSTEM_PROMPT, "user": SYNTHETIC_PROMPT}, sort_keys=True, separators=(",", ":"), ensure_ascii=False))

    def preflight_failure(status: str, error_type: str, *, model: str = "unconfigured", provider_host: str = "unconfigured"):
        report = _safe_report(
            run_id=run_id, task_id=task_id, release_id="unresolved",
            status=status, provider_host=provider_host, model=model,
            prompt_hash=prompt_hash, tools_hash=_sha256("unavailable"),
            elapsed_ms=round((time.monotonic() - started) * 1000),
            task_status="not_started", error_type=error_type,
            started_at_utc=started_at_utc,
            finished_at_utc=datetime.now(timezone.utc).isoformat(),
            provenance={}, output_validation={"status": "not_completed"},
        )
        for package in ("anthropic", "mcp"):
            try:
                report["sdk_versions"][package] = importlib.metadata.version(package)
            except importlib.metadata.PackageNotFoundError:
                report["sdk_versions"][package] = None
        path = _write_preflight_report(report)
        return {**report, "report_path": str(path)}

    try:
        config = LiveConfig.from_env(env)
    except ValueError as exc:
        return preflight_failure("live_config_error", type(exc).__name__)
    try:
        mcp_components = _mcp_components()
        client = create_anthropic_client(config.api_key, config.base_url, timeout=config.timeout)
        adapter = AnthropicMessagesAdapter(client)
    except Exception as exc:
        host = urlsplit(config.base_url).hostname if config.base_url else "api.anthropic.com"
        return preflight_failure("runner_error", type(exc).__name__, model=config.model, provider_host=host)
    from app.db import connect
    from app.worker import claim

    report_host = urlsplit(config.base_url).hostname if config.base_url else "api.anthropic.com"
    try:
        with connect(config.database_url) as conn:
            task = conn.execute("SELECT tenant_id,owner_id,input,release_id,status FROM tasks WHERE id=%s", (task_id,)).fetchone()
            if not task:
                return preflight_failure("task_not_found", "TaskNotFound", model=config.model, provider_host=report_host)
            if (task["tenant_id"], task["owner_id"]) != ("tenant-a", "alice") or not isinstance(task["input"], dict) or task["input"].get("prompt") != SYNTHETIC_PROMPT:
                return preflight_failure("synthetic_task_required", "UnsafeTaskIdentity", model=config.model, provider_host=report_host)
            if not conn.execute("SELECT 1 FROM provider_endpoints WHERE id=%s", (config.endpoint_id,)).fetchone():
                return preflight_failure("provider_endpoint_not_configured", "ProviderEndpointNotConfigured", model=config.model, provider_host=report_host)
            account = conn.execute("SELECT tenant_id FROM budget_accounts WHERE id=%s", (config.budget_account,)).fetchone()
            if not account or account["tenant_id"] != task["tenant_id"]:
                return preflight_failure("budget_account_not_configured", "BudgetAccountNotConfigured", model=config.model, provider_host=report_host)
            lease = claim(conn, owner, task_id=task_id, lease_seconds=120)
            if not lease:
                return preflight_failure("task_not_claimable", "TaskNotClaimable", model=config.model, provider_host=report_host)
            release_id = task["release_id"]
    except Exception as exc:
        return preflight_failure("runner_error", type(exc).__name__, model=config.model, provider_host=report_host)

    result = None
    tools_hash = [_sha256("unavailable")]
    provenance = [{}]
    tool_schema_docs = [[]]
    error_type = None
    try:
        async def advance(session):
            listed = await session.list_tools()
            tools = list(getattr(listed, "tools", []))
            schemas = trusted_provider_tools(tools)
            tools_hash[0] = _sha256(json.dumps(schemas, sort_keys=True, separators=(",", ":"), ensure_ascii=False))
            tool_schema_docs[0] = schemas
            provenance[0] = _live_provenance(prompt_hash, tools_hash[0], schemas)
            return await resume_agent_turn(
                lambda: connect(config.database_url), lease, mcp_session=session,
                delivery_dsn=config.database_url, sink_url=config.sink_url,
                endpoint=config.endpoint_id, budget_account=config.budget_account,
                provider=adapter, mcp_tools=tools, system_prompt=SYSTEM_PROMPT,
                model=config.model, max_tokens=config.max_tokens, max_rounds=config.max_rounds,
                reserved_tokens=config.reserved_tokens, reserved_tools=config.reserved_tools)
        result = await _with_mcp_session(advance, mcp_components)
    except Exception as exc:
        error_type = type(exc).__name__
        result = {"status": "runner_error"}

    # A completed wake-up has no work running in this process. Release its
    # owner/epoch-fenced lease immediately so a successor can continue without
    # waiting for the full timeout. Crashes still rely on normal lease expiry.
    try:
        from app.worker import release
        with connect(config.database_url) as conn:
            release(conn, lease)
    except Exception as exc:
        if error_type is None:
            error_type = type(exc).__name__

    try:
        with connect(config.database_url) as conn:
            current = conn.execute("SELECT status FROM tasks WHERE id=%s", (task_id,)).fetchone()
            latest = conn.execute("""SELECT request_id,stop_reason,usage_tokens,usage_tools FROM provider_calls
                WHERE task_id=%s ORDER BY round_index DESC LIMIT 1""", (task_id,)).fetchone()
            call_rows = conn.execute("""SELECT request_id,round_index,state,stop_reason,usage_tokens,usage_tools,
                created_at,response_at FROM provider_calls WHERE task_id=%s ORDER BY round_index""", (task_id,)).fetchall()
            action_rows = _load_action_evidence(conn, task_id)
            final_output = conn.execute("SELECT output_hash,output FROM final_outputs WHERE task_id=%s", (task_id,)).fetchone()
    except Exception as exc:
        # A provider call may already have happened. Preserve an explicit, conservative
        # record instead of losing the attempt or claiming that no evidence exists.
        report = _safe_report(
            run_id=run_id, task_id=task_id, release_id=release_id,
            status="runner_error", provider_host=report_host, model=config.model,
            prompt_hash=prompt_hash, tools_hash=tools_hash[0],
            elapsed_ms=round((time.monotonic() - started) * 1000),
            task_status="unknown", error_type=type(exc).__name__,
            started_at_utc=started_at_utc,
            finished_at_utc=datetime.now(timezone.utc).isoformat(),
            provenance=provenance[0],
            output_validation={"status": "not_completed"},
        )
        for package in ("anthropic", "mcp"):
            try:
                report["sdk_versions"][package] = importlib.metadata.version(package)
            except importlib.metadata.PackageNotFoundError:
                report["sdk_versions"][package] = None
        report_path = _write_report(report, tool_schema_docs[0])
        return {**report, "report_path": str(report_path)}
    status = result.get("status", "runner_error")
    rounds = []
    for row in call_rows:
        created_at = row["created_at"]
        response_at = row["response_at"]
        latency_ms = round((response_at - created_at).total_seconds() * 1000) if response_at else None
        matching_tools = [
            {"tool": action["tool"], "status": action["status"], "approval_verified": action["approval_verified"]}
            for action in action_rows
            if action["turn_id"] == row["request_id"]
        ]
        rounds.append({
            "round_index": row["round_index"], "request_id": str(row["request_id"]),
            "state": row["state"], "stop_reason": row["stop_reason"],
            "usage_tokens": row["usage_tokens"], "usage_tools": row["usage_tools"],
            "started_at_utc": row["created_at"].isoformat(),
            "finished_at_utc": row["response_at"].isoformat() if row["response_at"] else None,
            "latency_ms": latency_ms,
            "exception_type": error_type if row is call_rows[-1] else None,
            "tool_calls": matching_tools,
        })
    validation_status = "passed" if final_output else "not_completed"
    output_validation = {
        "status": validation_status,
        "output_sha256": final_output["output_hash"] if final_output else None,
    }
    report = _safe_report(run_id=run_id, task_id=task_id, release_id=release_id,
        status=status, provider_host=report_host, model=config.model,
        prompt_hash=prompt_hash, tools_hash=tools_hash[0],
        elapsed_ms=round((time.monotonic() - started) * 1000), request=latest,
        task_status=current["status"] if current else None, error_type=error_type,
        started_at_utc=started_at_utc, finished_at_utc=datetime.now(timezone.utc).isoformat(),
        provenance=provenance[0], rounds=rounds,
        tools=[{"tool": action["tool"], "status": action["status"], "approval_verified": action["approval_verified"]} for action in action_rows],
        output_validation=output_validation)
    for package in ("anthropic", "mcp"):
        try:
            report["sdk_versions"][package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            report["sdk_versions"][package] = None
    report_path = _write_report(report, tool_schema_docs[0])
    return {**report, "report_path": str(report_path)}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Run one bounded P5 synthetic task wake-up against a real provider")
    parser.add_argument("--live", action="store_true", help="explicitly enable provider network calls")
    parser.add_argument("--task", type=UUID, required=True, help="pre-created synthetic task id")
    parser.add_argument("--owner", default="p5-live-runner", help="bounded worker owner identifier")
    args = parser.parse_args(argv)
    if not args.live:
        parser.error("--live is required; this command is the only path that makes provider requests")
    report = asyncio.run(run_once(args.task, owner=args.owner, live=True))
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0 if report["status"] in {"completed", "waiting_approval", "delivery_succeeded"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
