"""Safety boundary tests for the explicitly invoked P5 live runner."""
import asyncio
import json
from concurrent.futures import ThreadPoolExecutor
from threading import Event
from uuid import uuid4

import pytest

import sys
from pathlib import Path

P5 = Path(__file__).resolve().parents[1]
P4 = P5.parent / "p4-durable-support"
for path in (P4.parent, P4, P5):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))


def test_live_opt_in_is_required_before_configuration_or_database_access(monkeypatch):
    import runner

    def forbidden_config(*args, **kwargs):
        raise AssertionError("Non-live invocation must not inspect provider configuration")

    monkeypatch.setattr(runner.LiveConfig, "from_env", forbidden_config)
    result = asyncio.run(runner.run_once(uuid4(), owner="test-owner", live=False))
    assert result["status"] == "live_opt_in_required"


def test_wakeup_release_is_fenced_and_clears_only_matching_slots():
    from app.worker import Lease, release

    task_id = uuid4()

    class Cursor:
        def __init__(self, row=None):
            self.row = row

        def fetchone(self):
            return self.row

    class Connection:
        def __init__(self):
            self.queries = []

        def execute(self, query, params):
            self.queries.append((query, params))
            if query.startswith("SELECT * FROM tasks"):
                return Cursor({"lease_owner": "wake-a", "execution_epoch": 4, "status": "running"})
            if "RETURNING last_event_seq" in query:
                return Cursor({"last_event_seq": 7})
            return Cursor()

    conn = Connection()
    assert release(conn, Lease(task_id, "wake-a", 4)) is True
    assert [params for query, params in conn.queries if query.startswith("DELETE FROM task_slots") or query.startswith("DELETE FROM provider_slots")] == [
        (task_id, "wake-a", 4), (task_id, "wake-a", 4),
    ]
    assert any("lease_owner=NULL,lease_until=NULL" in query for query, _ in conn.queries)
    assert any("task.lease_released" in str(params) for _, params in conn.queries)


def test_stale_wakeup_cannot_release_successor_lease():
    from app.worker import Lease, release

    class Cursor:
        def fetchone(self):
            return {"lease_owner": "wake-b", "execution_epoch": 5, "status": "running"}

    class Connection:
        def __init__(self):
            self.queries = []

        def execute(self, query, params):
            self.queries.append(query)
            return Cursor()

    conn = Connection()
    assert release(conn, Lease(uuid4(), "wake-a", 4)) is False
    assert len(conn.queries) == 1


def test_live_configuration_requires_bounded_provider_and_local_sink(monkeypatch):
    from runner import LiveConfig

    env = {
        "DATABASE_URL": "postgresql://local@127.0.0.1/test",
        "P5_PROVIDER_ENDPOINT": "anthropic-demo",
        "P5_BUDGET_ACCOUNT": "stage5-smoke",
        "VERIFY_MODEL": "configured-model",
        "ANTHROPIC_API_KEY": "do-not-echo-this",
        "P5_SINK_URL": "http://127.0.0.1:8002",
    }
    config = LiveConfig.from_env(env)
    assert config.model == "configured-model"
    assert config.api_key == "do-not-echo-this"
    assert config.max_rounds == 4
    assert config.max_tokens == 512
    assert "do-not-echo-this" not in repr(config)

    unsafe = {**env, "P5_SINK_URL": "https://real-customer.example"}
    with pytest.raises(ValueError, match="local synthetic sink"):
        LiveConfig.from_env(unsafe)


def test_live_configuration_never_accepts_missing_or_unbounded_credentials_and_limits():
    from runner import LiveConfig

    with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
        LiveConfig.from_env({
            "DATABASE_URL": "postgresql://local@127.0.0.1/test",
            "P5_PROVIDER_ENDPOINT": "anthropic-demo",
            "P5_BUDGET_ACCOUNT": "stage5-smoke",
            "VERIFY_MODEL": "configured-model",
            "P5_SINK_URL": "http://localhost:8002",
        })


def test_live_run_with_missing_configuration_writes_a_redacted_preflight_record(tmp_path, monkeypatch):
    import runner

    monkeypatch.setattr(runner, "ROOT", tmp_path)
    result = asyncio.run(runner.run_once(uuid4(), owner="test-owner", live=True, env={}))

    assert result["status"] == "live_config_error"
    assert result["error_type"] == "ValueError"
    assert "ANTHROPIC_API_KEY" not in json.dumps(result)
    report_path = Path(result["report_path"])
    assert report_path.is_file()
    saved = json.loads(report_path.read_text())
    assert saved["status"] == "live_config_error"
    assert saved["evidence_registry_decision"]["decision"] == "not-evaluated"
    assert "ANTHROPIC_API_KEY" not in report_path.read_text()


def test_live_run_persists_unknown_outcome_if_post_call_evidence_read_fails(tmp_path, monkeypatch):
    import runner
    import app.db
    from contextlib import contextmanager
    from runner import LiveConfig

    task_id = uuid4()
    config = LiveConfig(
        database_url="postgresql://local@127.0.0.1/test", endpoint_id="endpoint",
        budget_account="budget", model="model", api_key="secret-provider-key",
    )
    monkeypatch.setattr(runner, "ROOT", tmp_path)
    monkeypatch.setattr(runner.LiveConfig, "from_env", lambda env: config)
    monkeypatch.setattr(runner, "_mcp_components", lambda: (None, None, None))
    monkeypatch.setattr(runner, "create_anthropic_client", lambda *args, **kwargs: object())
    monkeypatch.setattr(runner, "AnthropicMessagesAdapter", lambda client: object())
    monkeypatch.setattr(runner, "_with_mcp_session", lambda callback, components: asyncio.sleep(0, result={"status": "completed"}))

    class Cursor:
        def __init__(self, value=None):
            self.value = value

        def fetchone(self):
            return self.value

    class Connection:
        def execute(self, query, params):
            if "FROM tasks" in query:
                return Cursor({"tenant_id": "tenant-a", "owner_id": "alice",
                               "input": {"prompt": runner.SYNTHETIC_PROMPT}, "release_id": "release-1",
                               "status": "queued"})
            if "FROM provider_endpoints" in query:
                return Cursor({"id": "endpoint"})
            if "FROM budget_accounts" in query:
                return Cursor({"tenant_id": "tenant-a"})
            raise AssertionError(f"Unexpected preflight query: {query}")

    connect_calls = 0

    @contextmanager
    def connect(_dsn):
        nonlocal connect_calls
        connect_calls += 1
        if connect_calls == 1:
            yield Connection()
        else:
            raise RuntimeError("database failure containing secret-provider-key")

    monkeypatch.setattr(app.db, "connect", connect)
    monkeypatch.setattr("app.worker.claim", lambda conn, owner, **kwargs: {"task_id": task_id})

    result = asyncio.run(runner.run_once(task_id, owner="test-owner", live=True, env={}))

    assert result["status"] == "runner_error"
    assert result["task_status"] == "unknown"
    report_path = Path(result["report_path"])
    saved = json.loads(report_path.read_text())
    assert saved["status"] == "runner_error"
    assert saved["error_type"] == "RuntimeError"
    assert saved["evidence_registry_decision"]["decision"] != "passed"
    assert "secret-provider-key" not in report_path.read_text()


def test_live_report_keeps_only_request_identity_usage_and_outcome():
    from runner import _safe_report

    report = _safe_report(run_id=uuid4(), task_id=uuid4(), release_id="release-1",
        status="completed", provider_host="api.anthropic.com", model="model-1",
        prompt_hash="a" * 64, tools_hash="b" * 64, elapsed_ms=123,
        request={"request_id": uuid4(), "stop_reason": "end_turn", "usage_tokens": 10,
                 "usage_tools": 0, "request_body": {"messages": ["private input"]}},
        error_type="ProviderTimeout")
    serialized = json.dumps(report)
    assert "private input" not in serialized
    assert "request_body" not in serialized
    assert "api_key" not in serialized
    assert report["usage_tokens"] == 10
    assert report["stop_reason"] == "end_turn"


def test_live_report_v2_binds_materials_rounds_tools_and_review_without_raw_values():
    from runner import _safe_report

    report = _safe_report(
        run_id=uuid4(), task_id=uuid4(), release_id="release-1",
        status="completed", provider_host="api.anthropic.com", model="model-1",
        prompt_hash="a" * 64, tools_hash="b" * 64, elapsed_ms=123,
        request={"request_id": uuid4(), "stop_reason": "end_turn", "usage_tokens": 10,
                 "usage_tools": 1},
        task_status="completed",
        started_at_utc="2026-10-20T09:00:00+00:00",
        finished_at_utc="2026-10-20T09:00:01+00:00",
        provenance={
            "commit_sha": "c" * 40,
            "worktree_clean": False,
            "worktree_diff_sha256": "d" * 64,
            "lockfile_sha256": "e" * 64,
            "dataset_sha256": "f" * 64,
            "scorer_sha256": "1" * 64,
            "code_sha256": "2" * 64,
        },
        rounds=[{"round_index": 0, "request_id": str(uuid4()), "state": "processed",
                 "stop_reason": "end_turn", "usage_tokens": 10, "usage_tools": 1,
                 "exception_type": None,
                 "tool_calls": [{"tool": "lookup_order", "status": "succeeded",
                                 "arguments": {"customer_note": "must not be copied"}}]}],
        tools=[{"tool": "lookup_order", "status": "succeeded"}],
        output_validation={"status": "passed", "output_sha256": "3" * 64},
    )

    assert report["schema"] == "p5-live-smoke-v3"
    assert report["smoke_case_id"] == "p5-order-notice-smoke-v1"
    assert report["provider"] == "anthropic"
    assert report["started_at_utc"].endswith("+00:00")
    assert report["provenance"]["dataset_sha256"] == "f" * 64
    assert report["rounds"][0]["state"] == "processed"
    assert report["rounds"][0]["tool_calls"] == [{
        "tool": "lookup_order", "status": "succeeded",
    }]
    assert report["tools"][0]["tool"] == "lookup_order"
    assert report["output_validation"]["status"] == "passed"
    assert report["review"]["decision"] == "needs-review"
    assert "request_body" not in json.dumps(report)
    assert "customer_note" not in json.dumps(report)


def test_live_smoke_exports_a_hash_bound_partial_acceptance_evidence_bundle(tmp_path):
    from runner import SYSTEM_PROMPT, SYNTHETIC_PROMPT, _live_provenance, _safe_report, _write_evidence_bundle

    tool_schema = [{"name": "lookup_order", "input_schema": {"type": "object"}}]
    tools_hash = __import__("hashlib").sha256(
        json.dumps(tool_schema, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()
    prompt_hash = __import__("hashlib").sha256(
        json.dumps({"system": SYSTEM_PROMPT, "user": SYNTHETIC_PROMPT},
                   sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()
    provenance = _live_provenance(prompt_hash, tools_hash, tool_schema)
    report = _safe_report(
        run_id=uuid4(), task_id=uuid4(), release_id="release-1",
        status="waiting_approval", provider_host="api.anthropic.com", model="model-1",
        prompt_hash=prompt_hash, tools_hash=tools_hash, elapsed_ms=123,
        started_at_utc="2026-10-20T09:00:00+00:00",
        finished_at_utc="2026-10-20T09:00:01+00:00",
        provenance=provenance,
        output_validation={"status": "not_completed"},
    )

    result = _write_evidence_bundle(report, tool_schema, evidence_root=tmp_path)

    assert result["decision"] == "incomplete"
    assert "live_model_normal" not in result["missing"]
    acceptance = json.loads((tmp_path / "acceptance-report.json").read_text())
    gate_matrix = {item["gate_id"]: item for item in acceptance["gate_matrix"]}
    assert gate_matrix["live_model_normal"]["state"] == "unverified"
    assert gate_matrix["official_blind_holdout"]["state"] == "missing"
    assert acceptance["matrix_authenticated"] is False
    manifest = json.loads((tmp_path / "evidence-manifest.json").read_text())
    assert manifest["run_id"] == report["run_id"]
    assert manifest["artifacts"][0]["kind"] == "live"
    artifact = tmp_path / manifest["artifacts"][0]["locator"]
    payload = json.loads(artifact.read_text())
    assert payload["status"] == "unverified"
    assert payload["smoke_case_id"] == "p5-order-notice-smoke-v1"
    assert "api_key" not in artifact.read_text()
    manifest_before_retry = (tmp_path / "evidence-manifest.json").read_bytes()
    with pytest.raises(FileExistsError):
        _write_evidence_bundle(report, tool_schema, evidence_root=tmp_path)
    assert (tmp_path / "evidence-manifest.json").read_bytes() == manifest_before_retry


def test_frozen_dataset_hash_includes_the_predeclared_live_smoke_case():
    from runner import SMOKE_CASE_ID, _evidence_material_bytes

    materials = _evidence_material_bytes([])
    dataset = json.loads(materials["dataset"])
    smoke_case = json.loads(dataset["live-smoke.json"])

    assert smoke_case["case_id"] == SMOKE_CASE_ID
    assert smoke_case["required_successful_tools"] == ["lookup_order", "send_notice"]
    assert smoke_case["approval_required_tools"] == ["send_notice"]


def test_live_report_is_write_once_for_same_run_id(tmp_path, monkeypatch):
    import runner

    monkeypatch.setattr(runner, "ROOT", tmp_path)
    report = {"run_id": "same-run-id", "status": "runner_error"}

    path = runner._write_report(report, [])
    original = path.read_bytes()

    with pytest.raises(FileExistsError):
        runner._write_report(report, [])
    assert path.read_bytes() == original


def test_live_evidence_publication_is_atomic_for_concurrent_same_path_writers(tmp_path):
    from runner import _write_new_file

    root = tmp_path / "run"
    target = root / "evidence" / "artifact.json"
    payloads = [b'{"writer":"first"}', b'{"writer":"second"}']

    def publish(payload):
        try:
            _write_new_file(root, target, payload)
        except FileExistsError:
            return False
        return True

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(publish, payloads))

    assert sorted(results) == [False, True]
    assert target.read_bytes() in payloads
    assert list(target.parent.iterdir()) == [target]


def test_live_evidence_is_not_visible_until_complete_bytes_are_ready(tmp_path, monkeypatch):
    import runner

    root = tmp_path / "run"
    target = root / "evidence" / "artifact.json"
    content = b'{"complete":true}'
    link_started = Event()
    allow_publish = Event()
    original_link = runner.os.link

    def pause_before_publish(source, destination, *args, **kwargs):
        link_started.set()
        assert allow_publish.wait(timeout=5)
        return original_link(source, destination, *args, **kwargs)

    monkeypatch.setattr(runner.os, "link", pause_before_publish)
    with ThreadPoolExecutor(max_workers=1) as executor:
        pending = executor.submit(runner._write_new_file, root, target, content)
        reached_publish = link_started.wait(timeout=2)
        try:
            assert reached_publish, "writer must stage complete bytes before publishing"
            assert not target.exists()
        finally:
            allow_publish.set()
        pending.result(timeout=5)

    assert target.read_bytes() == content


@pytest.mark.parametrize(
    ("report", "expected"),
    [
        ({"status": "completed", "task_status": "completed", "smoke_case_id": "p5-order-notice-smoke-v1", "tools": [{"tool": "lookup_order", "status": "succeeded"}, {"tool": "send_notice", "status": "succeeded", "approval_verified": True}], "output_validation": {"status": "passed", "output_sha256": "a" * 64}, "rounds": [{"request_id": "req-1", "state": "processed", "usage_tokens": 20, "usage_tools": 1}]}, "passed"),
        ({"status": "completed", "task_status": "completed", "output_validation": {"status": "passed", "output_sha256": "a" * 64}, "rounds": [{"request_id": "req-1", "state": "processed", "usage_tokens": None, "usage_tools": 1}]}, "unverified"),
        ({"status": "completed", "task_status": "completed", "output_validation": {"status": "passed", "output_sha256": "a" * 64}, "rounds": []}, "unverified"),
        ({"status": "runner_error", "task_status": "running", "output_validation": {"status": "not_completed"}, "rounds": []}, "unverified"),
        ({"status": "live_config_error", "task_status": "not_started", "output_validation": {"status": "not_completed"}, "rounds": []}, "unverified"),
        ({"status": "transport_error", "task_status": "failed", "output_validation": {"status": "not_completed"}, "rounds": []}, "failed"),
        ({"status": "truncated", "task_status": "failed", "output_validation": {"status": "not_completed"}, "rounds": []}, "failed"),
        ({"status": "tool_error", "task_status": "failed", "output_validation": {"status": "not_completed"}, "rounds": []}, "failed"),
        ({"status": "protocol_error", "task_status": "failed", "output_validation": {"status": "not_completed"}, "rounds": []}, "failed"),
    ],
)
def test_live_gate_only_passes_with_complete_round_usage_and_validated_output(report, expected):
    from runner import _live_gate_status

    assert _live_gate_status(report) == expected


def test_live_gate_does_not_pass_without_the_predeclared_smoke_case_actions():
    from runner import _live_gate_status

    report = {
        "status": "completed",
        "task_status": "completed",
        "smoke_case_id": "p5-order-notice-smoke-v1",
        "tools": [{"tool": "lookup_order", "status": "succeeded"}],
        "output_validation": {"status": "passed", "output_sha256": "a" * 64},
        "rounds": [{"request_id": "req-1", "state": "processed", "usage_tokens": 20, "usage_tools": 1}],
    }

    assert _live_gate_status(report) == "unverified"


def test_live_gate_requires_a_durable_approval_witness_for_the_write_action():
    from runner import _live_gate_status

    report = {
        "status": "completed",
        "task_status": "completed",
        "smoke_case_id": "p5-order-notice-smoke-v1",
        "tools": [
            {"tool": "lookup_order", "status": "succeeded"},
            {"tool": "send_notice", "status": "succeeded", "approval_verified": False},
        ],
        "output_validation": {"status": "passed", "output_sha256": "a" * 64},
        "rounds": [{"request_id": "req-1", "state": "processed", "usage_tokens": 20, "usage_tools": 1}],
    }

    assert _live_gate_status(report) == "unverified"
