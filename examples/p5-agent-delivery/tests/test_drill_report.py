import hashlib
import json
import sys
from pathlib import Path

import pytest

P5 = Path(__file__).resolve().parents[1]
P4_TESTS = P5.parent / "p4-durable-support" / "tests"
if str(P5) not in sys.path:
    sys.path.insert(0, str(P5))
if str(P4_TESTS) not in sys.path:
    sys.path.insert(0, str(P4_TESTS))

from drill_report import DrillReportError, evaluate_report, merge_observation_records, parse_junit
from run_drills import SCENARIOS, _test_environment


def _artifact(root: Path, name: str, content: str) -> dict:
    path = root / name
    path.write_text(content, encoding="utf-8")
    return {"path": name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def _report(root: Path, scenario: str, observed: dict) -> dict:
    return {
        "scenario_id": scenario,
        "test_execution_status": "passed",
        "expected_node_ids": ["test_module::test_case"],
        "test_results": [{"node_id": "test_module::test_case", "status": "passed"}],
        "cleanup": {"compose_project_removed": True, "volume_removed": True},
        "observed": {
            **observed,
            "checkpoint_snapshots": [{"task_id": "synthetic", "status": "completed", "execution_epoch": 1,
                                       "checkpoint_sha256": None, "event_kinds_in_order": []}],
            "budget_reservations": [],
        },
        "artifacts": {
            "junit": _artifact(root, "junit.xml", "<testsuite/>") ,
            "console_log": _artifact(root, "console.log", "1 passed"),
        },
        "review": {"decision": "needs-review", "reviewer": None},
    }


def test_all_tests_and_artifacts_can_pass_with_complete_observations(tmp_path):
    observed = {
        "task_statuses": ["waiting_approval", "queued", "completed"],
        "action_statuses": ["waiting_approval", "succeeded"],
        "outbox_statuses": ["succeeded"],
        "sink_effect_count": 1,
        "event_kinds_in_order": ["approval.approved", "action.dispatching", "outbox.receipt_saved", "task.completed"],
        "provider_calls": 2,
    }
    verdict = evaluate_report(_report(tmp_path, "approval-pause-resume", observed), tmp_path)
    assert verdict["status"] == "passed"
    assert verdict["test_execution_status"] == "passed"


def test_green_tests_without_observed_database_facts_stay_incomplete(tmp_path):
    verdict = evaluate_report(_report(tmp_path, "approval-pause-resume", {}), tmp_path)
    assert verdict["status"] == "incomplete"
    assert "observed.task_statuses" in verdict["missing_fields"]


def test_skipped_expected_test_cannot_pass(tmp_path):
    report = _report(tmp_path, "approval-pause-resume", {
        "task_statuses": ["waiting_approval", "queued", "completed"],
        "action_statuses": ["waiting_approval", "succeeded"],
        "outbox_statuses": ["succeeded"], "sink_effect_count": 1,
        "event_kinds_in_order": ["approval.approved", "task.completed"], "provider_calls": 2,
    })
    report["test_results"][0]["status"] = "skipped"
    verdict = evaluate_report(report, tmp_path)
    assert verdict["status"] == "incomplete"
    assert verdict["missing_fields"] == ["test_results.test_module::test_case"]


def test_failed_assertion_is_failed_even_with_complete_observations(tmp_path):
    report = _report(tmp_path, "approval-pause-resume", {
        "task_statuses": ["waiting_approval", "queued", "completed"],
        "action_statuses": ["waiting_approval", "succeeded"],
        "outbox_statuses": ["succeeded"], "sink_effect_count": 1,
        "event_kinds_in_order": ["approval.approved", "task.completed"], "provider_calls": 2,
    })
    report["test_results"][0]["status"] = "failed"
    assert evaluate_report(report, tmp_path)["status"] == "failed"


def test_report_fails_when_observed_state_contradicts_approval_contract(tmp_path):
    report = _report(tmp_path, "approval-pause-resume", {
        "task_statuses": ["waiting_approval", "queued", "completed"],
        "action_statuses": ["waiting_approval", "succeeded"],
        "outbox_statuses": ["succeeded"], "sink_effect_count": 2,
        "event_kinds_in_order": ["approval.approved", "action.dispatching", "outbox.receipt_saved", "task.completed"],
        "provider_calls": 2,
    })
    verdict = evaluate_report(report, tmp_path)
    assert verdict["status"] == "failed"
    assert "observed.sink_effect_count must equal 1" in verdict["observation_failures"]


def test_report_fails_when_idempotency_observation_has_invalid_fact_type(tmp_path):
    report = _report(tmp_path, "idempotency", {
        "response_statuses": [200, 201, 409], "unique_task_ids": "one",
        "task_count": 1, "event_count": 1, "idempotency_record_count": 1,
    })
    verdict = evaluate_report(report, tmp_path)
    assert verdict["status"] == "failed"
    assert "observed.unique_task_ids must be a non-negative integer" in verdict["observation_failures"]


@pytest.mark.parametrize("artifact_path", ["../outside.xml", "/tmp/outside.xml"])
def test_artifact_path_cannot_escape_evidence_root(tmp_path, artifact_path):
    report = _report(tmp_path, "approval-pause-resume", {})
    report["artifacts"]["junit"]["path"] = artifact_path
    with pytest.raises(DrillReportError, match="outside evidence root"):
        evaluate_report(report, tmp_path)


def test_artifact_hash_mismatch_is_rejected(tmp_path):
    report = _report(tmp_path, "approval-pause-resume", {})
    report["artifacts"]["junit"]["sha256"] = "0" * 64
    with pytest.raises(DrillReportError, match="hash mismatch"):
        evaluate_report(report, tmp_path)


def test_cleanup_failure_cannot_pass(tmp_path):
    report = _report(tmp_path, "approval-pause-resume", {
        "task_statuses": ["waiting_approval", "queued", "completed"],
        "action_statuses": ["waiting_approval", "succeeded"],
        "outbox_statuses": ["succeeded"], "sink_effect_count": 1,
        "event_kinds_in_order": ["approval.approved", "task.completed"], "provider_calls": 2,
    })
    report["cleanup"]["volume_removed"] = False
    verdict = evaluate_report(report, tmp_path)
    assert verdict["status"] == "incomplete"
    assert "cleanup.volume_removed" in verdict["missing_fields"]


def test_junit_parser_records_parametrized_nodes_and_skip_as_nonpass(tmp_path):
    xml = tmp_path / "results.xml"
    xml.write_text('''<testsuite tests="2" failures="0" errors="0" skipped="1">
      <testcase classname="test_race" name="test_boundary[before_claim-cancel]"/>
      <testcase classname="test_race" name="test_boundary[before_claim-revoke]"><skipped/></testcase>
    </testsuite>''', encoding="utf-8")
    assert parse_junit(xml) == [
        {"node_id": "test_race::test_boundary[before_claim-cancel]", "status": "passed"},
        {"node_id": "test_race::test_boundary[before_claim-revoke]", "status": "skipped"},
    ]


def test_runner_has_exactly_the_six_documented_scenarios():
    assert set(SCENARIOS) == {
        "approval-pause-resume", "cancel-revoke-race", "idempotency",
        "unknown-reconcile", "lease-takeover", "budget-unknown",
    }
    assert all(SCENARIOS.values())


def test_runner_environment_does_not_forward_provider_credentials():
    env = _test_environment({
        "PATH": "/usr/bin", "HOME": "/tmp/home", "DOCKER_CONTEXT": "local",
        "ANTHROPIC_API_KEY": "secret", "DATABASE_URL": "postgresql://secret",
        "OPENAI_API_KEY": "secret", "P4_TEST_COMPOSE_PROJECT": "ignored",
    }, compose_project="p4-test-run-1")
    assert env["P4_TEST_COMPOSE_PROJECT"] == "p4-test-run-1"
    assert env["DOCKER_CONTEXT"] == "local"
    assert "ANTHROPIC_API_KEY" not in env
    assert "OPENAI_API_KEY" not in env
    assert "DATABASE_URL" not in env


def test_observation_records_merge_lists_counts_and_scenario_cases():
    merged = merge_observation_records("unknown-reconcile", [
        {"scenario_id": "unknown-reconcile", "node_id": "test_a", "observed": {
            "task_statuses": ["reconciling"], "sink_effect_count": 1,
            "request_methods": ["POST", "GET"], "completion_attempts": ["rejected"],
        }},
        {"scenario_id": "unknown-reconcile", "node_id": "test_b", "observed": {
            "task_statuses": ["reconciling", "queued"], "sink_effect_count": 0,
            "request_methods": ["GET"], "completion_attempts": ["rejected"],
        }},
    ])
    assert merged["task_statuses"] == ["reconciling", "reconciling", "queued"]
    assert merged["sink_effect_count"] == 1
    assert merged["request_methods"] == ["POST", "GET", "GET"]


def test_observation_aggregation_rejects_cross_scenario_records():
    with pytest.raises(DrillReportError, match="scenario mismatch"):
        merge_observation_records("idempotency", [
            {"scenario_id": "lease-takeover", "node_id": "x", "observed": {}}
        ])


def test_postgres_test_helper_binds_observation_to_the_current_node(tmp_path, monkeypatch):
    from conftest import record_drill_observation

    monkeypatch.setenv("P5_DRILL_OBSERVATIONS_DIR", str(tmp_path))
    monkeypatch.setenv("PYTEST_CURRENT_TEST", "tests/test_example.py::test_case[param] (call)")
    record_drill_observation("idempotency", {"unique_task_ids": 2})
    records = list(tmp_path.glob("*.json"))
    assert len(records) == 1
    record = json.loads(records[0].read_text(encoding="utf-8"))
    assert record == {
        "scenario_id": "idempotency",
        "node_id": "tests.test_example::test_case[param]",
        "observed": {"unique_task_ids": 2, "checkpoint_snapshots": [], "budget_reservations": []},
    }
