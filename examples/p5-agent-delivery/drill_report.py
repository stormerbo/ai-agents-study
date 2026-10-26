"""Fail-closed validation for a single Stage 5 PostgreSQL drill record."""

from __future__ import annotations

import hashlib
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


class DrillReportError(ValueError):
    """The report or evidence artifact is malformed or does not match."""


def parse_junit(path: Path) -> list[dict[str, str]]:
    """Read test node outcomes from pytest's JUnit XML without guessing pass."""
    try:
        root = ET.parse(path).getroot()
    except (OSError, ET.ParseError) as exc:
        raise DrillReportError("cannot read valid JUnit XML") from exc
    cases = root.findall(".//testcase")
    if not cases:
        raise DrillReportError("JUnit XML contains no test cases")
    results = []
    for case in cases:
        classname = case.get("classname", "").strip()
        name = case.get("name", "").strip()
        if not classname or not name:
            raise DrillReportError("JUnit test case is missing classname or name")
        if case.find("failure") is not None:
            status = "failed"
        elif case.find("error") is not None:
            status = "error"
        elif case.find("skipped") is not None:
            status = "skipped"
        else:
            status = "passed"
        results.append({"node_id": f"{classname}::{name}", "status": status})
    if len({item["node_id"] for item in results}) != len(results):
        raise DrillReportError("JUnit contains duplicate test node ids")
    return results


def merge_observation_records(scenario_id: str, records: list[dict]) -> dict:
    """Merge records emitted by selected integration tests, preserving facts.

    Lists concatenate in execution order, non-boolean numeric counters sum,
    nested mappings merge recursively, and scalar identity/hash fields retain
    the latest value. Scenario-specific cardinality is checked downstream.
    """
    _required_fields(scenario_id)
    if not isinstance(records, list):
        raise DrillReportError("observation records must be a list")
    merged: dict[str, Any] = {}

    def merge_value(old: Any, new: Any) -> Any:
        if old is None:
            return new
        if isinstance(old, list) and isinstance(new, list):
            return old + new
        if isinstance(old, dict) and isinstance(new, dict):
            result = dict(old)
            for key, value in new.items():
                result[key] = merge_value(result.get(key), value)
            return result
        if (isinstance(old, (int, float)) and not isinstance(old, bool)
                and isinstance(new, (int, float)) and not isinstance(new, bool)):
            return old + new
        return new

    for record in records:
        if not isinstance(record, dict) or record.get("scenario_id") != scenario_id:
            raise DrillReportError("observation scenario mismatch")
        node_id = record.get("node_id")
        observed = record.get("observed")
        if not isinstance(node_id, str) or not node_id or not isinstance(observed, dict):
            raise DrillReportError("malformed observation record")
        for key, value in observed.items():
            if not isinstance(key, str) or not key:
                raise DrillReportError("malformed observation field")
            merged[key] = merge_value(merged.get(key), value)
    return merged


REQUIRED_OBSERVATIONS = {
    "approval-pause-resume": (
        "task_statuses", "action_statuses", "outbox_statuses", "sink_effect_count",
        "event_kinds_in_order", "provider_calls", "checkpoint_snapshots", "budget_reservations",
    ),
    "cancel-revoke-race": ("cancel_revoke_cases", "checkpoint_snapshots", "budget_reservations"),
    "idempotency": (
        "response_statuses", "unique_task_ids", "task_count", "event_count", "idempotency_record_count",
        "checkpoint_snapshots", "budget_reservations",
    ),
    "unknown-reconcile": (
        "task_statuses", "action_statuses", "outbox_statuses", "sink_effect_count",
        "event_kinds_in_order", "request_methods", "completion_attempts", "checkpoint_snapshots", "budget_reservations",
    ),
    "lease-takeover": (
        "owner_epochs", "stale_mutation_counts", "checkpoint_sha256", "provider_call_status", "budget",
        "checkpoint_snapshots", "budget_reservations",
    ),
    "budget-unknown": (
        "budget_before", "budget_after", "provider_invocations", "provider_call_states", "reservation_states",
        "checkpoint_snapshots", "budget_reservations",
    ),
}


def _at_path(value: dict, dotted_path: str) -> Any:
    current: Any = value
    for part in dotted_path.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def _validate_artifact(root: Path, name: str, value: Any) -> None:
    if not isinstance(value, dict):
        raise DrillReportError(f"artifact metadata missing: {name}")
    relative = value.get("path")
    expected_hash = value.get("sha256")
    if not isinstance(relative, str) or not relative:
        raise DrillReportError(f"artifact path missing: {name}")
    if not isinstance(expected_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", expected_hash):
        raise DrillReportError(f"artifact hash malformed: {name}")
    artifact = (root / relative).resolve()
    if not artifact.is_relative_to(root):
        raise DrillReportError(f"artifact outside evidence root: {name}")
    if not artifact.is_file():
        raise DrillReportError(f"artifact missing: {name}")
    digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
    if digest != expected_hash:
        raise DrillReportError(f"artifact hash mismatch: {name}")


def _required_fields(scenario_id: str) -> tuple[str, ...]:
    try:
        return REQUIRED_OBSERVATIONS[scenario_id]
    except KeyError as exc:
        raise DrillReportError("unknown scenario_id") from exc


def _missing_observations(scenario_id: str, observed: Any) -> list[str]:
    if not isinstance(observed, dict):
        return [f"observed.{field}" for field in _required_fields(scenario_id)]
    missing: list[str] = []
    for field in _required_fields(scenario_id):
        value = observed.get(field)
        if value is None or value == "" or (value == [] and field != "budget_reservations") or value == {}:
            missing.append(f"observed.{field}")
    snapshots = observed.get("checkpoint_snapshots", [])
    if not isinstance(snapshots, list) or not snapshots or any(
        not isinstance(item, dict) or not isinstance(item.get("task_id"), str)
        or "checkpoint_sha256" not in item or not isinstance(item.get("event_kinds_in_order"), list)
        for item in snapshots
    ):
        missing.append("observed.checkpoint_snapshots[task-status-checkpoint-events]")
    reservations = observed.get("budget_reservations", [])
    if not isinstance(reservations, list) or any(
        not isinstance(item, dict) or not isinstance(item.get("task_id"), str)
        or item.get("state") not in {"reserved", "unknown", "settled", "released"}
        or not isinstance(item.get("tokens"), int) or not isinstance(item.get("tools"), int)
        or not isinstance(item.get("sent"), bool)
        for item in reservations
    ):
        missing.append("observed.budget_reservations[state-tokens-tools-sent]")
    if scenario_id == "cancel-revoke-race":
        cases = observed.get("cancel_revoke_cases")
        required = {
            f"{phase}-{operation}"
            for phase in ("before-claim", "after-claim-before-send", "after-sink-commit-before-receipt")
            for operation in ("cancel", "revoke")
        }
        actual = {case.get("case_id") for case in cases if isinstance(case, dict)} if isinstance(cases, list) else set()
        if not required.issubset(actual):
            missing.append("observed.cancel_revoke_cases[all-six-boundaries]")
    if scenario_id == "lease-takeover":
        epochs = observed.get("owner_epochs")
        if not isinstance(epochs, list) or len(epochs) < 2 or not all(isinstance(v, int) and not isinstance(v, bool) for v in epochs):
            missing.append("observed.owner_epochs[old-and-successor]")
        digest = observed.get("checkpoint_sha256")
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            missing.append("observed.checkpoint_sha256")
    return sorted(set(missing))


def _observation_failures(scenario_id: str, observed: Any) -> list[str]:
    if not isinstance(observed, dict):
        return []
    failures: list[str] = []

    def require_count(name: str, *, minimum: int = 0, exact: int | None = None) -> int | None:
        value = observed.get(name)
        if not isinstance(value, int) or isinstance(value, bool) or value < minimum:
            failures.append(f"observed.{name} must be a non-negative integer")
            return None
        if exact is not None and value != exact:
            failures.append(f"observed.{name} must equal {exact}")
            return None
        return value

    def require_list(name: str) -> list | None:
        value = observed.get(name)
        if not isinstance(value, list):
            failures.append(f"observed.{name} must be a list")
            return None
        return value

    if scenario_id == "approval-pause-resume":
        task_states = require_list("task_statuses") or []
        action_states = require_list("action_statuses") or []
        outbox_states = require_list("outbox_statuses") or []
        events = require_list("event_kinds_in_order") or []
        if not {"waiting_approval", "queued", "completed"}.issubset(task_states):
            failures.append("observed.task_statuses violate approval-resume states")
        if not {"waiting_approval", "succeeded"}.issubset(action_states):
            failures.append("observed.action_statuses violate approval-resume states")
        if "succeeded" not in outbox_states:
            failures.append("observed.outbox_statuses omit succeeded")
        require_count("sink_effect_count", exact=1)
        require_count("provider_calls", exact=2)
        for before, after in (("approval.approved", "action.dispatching"),
                              ("action.dispatching", "outbox.receipt_saved"),
                              ("outbox.receipt_saved", "task.completed")):
            if before not in events or after not in events or events.index(before) >= events.index(after):
                failures.append(f"observed.event_kinds_in_order missing order {before} < {after}")
    elif scenario_id == "cancel-revoke-race":
        cases = observed.get("cancel_revoke_cases")
        if isinstance(cases, list):
            for case in cases:
                if not isinstance(case, dict):
                    continue
                phase, operation = case.get("phase"), case.get("operation")
                before_claim = phase == "before_claim"
                expected = (("cancelled", "cancelled", "cancelled", 0) if before_claim and operation == "cancel"
                            else ("failed", "invalidated", "invalidated", 0) if before_claim
                            else ("cancelled", "succeeded", "succeeded", 1) if operation == "cancel"
                            else ("queued", "succeeded", "succeeded", 1))
                actual = (case.get("task_status"), case.get("action_status"), case.get("outbox_status"), case.get("sink_effect_count"))
                completion_attempted = case.get("completion_attempted")
                completion_rejected = case.get("completion_rejected")
                if actual != expected or not isinstance(completion_attempted, bool):
                    failures.append(f"observed.cancel_revoke_cases[{case.get('case_id')}] violates state/effect contract")
                if completion_attempted and completion_rejected is not True:
                    failures.append(f"observed.cancel_revoke_cases[{case.get('case_id')}] accepted forbidden completion")
                events = case.get("event_kinds_in_order", [])
                if not isinstance(events, list) or "task.completed" in events:
                    failures.append(f"observed.cancel_revoke_cases[{case.get('case_id')}] recorded completion")
    elif scenario_id == "idempotency":
        statuses = require_list("response_statuses") or []
        for field in ("unique_task_ids", "task_count", "event_count", "idempotency_record_count"):
            require_count(field, exact=4)
        if not {200, 201, 409}.issubset(statuses):
            failures.append("observed.response_statuses omit replay/create/conflict")
    elif scenario_id == "unknown-reconcile":
        for field, expected in (("task_statuses", {"reconciling", "queued"}),
                                ("action_statuses", {"unknown", "succeeded"}),
                                ("outbox_statuses", {"unknown", "succeeded"})):
            values = require_list(field) or []
            if not expected.issubset(values):
                failures.append(f"observed.{field} omit unknown/reconciled state")
        require_count("sink_effect_count", exact=2)
        methods = require_list("request_methods") or []
        if not {"POST", "GET", "connection-error", "receipt-query"}.issubset(methods):
            failures.append("observed.request_methods omit ambiguity and receipt reconciliation")
        attempts = require_list("completion_attempts") or []
        if len(attempts) < 2:
            failures.append("observed.completion_attempts omit both blocked completion checks")
    elif scenario_id == "lease-takeover":
        epochs = require_list("owner_epochs") or []
        if not any(isinstance(new, int) and not isinstance(new, bool) and new == old + 1
                   for old, new in zip(epochs, epochs[1:])):
            failures.append("observed.owner_epochs omit successor increment")
        counts = observed.get("stale_mutation_counts")
        if not isinstance(counts, dict) or counts.get("stale_events") != 0 or counts.get("checkpoint_unchanged") != 1 or counts.get("provider_consume_rejected") != 1:
            failures.append("observed.stale_mutation_counts violate stale-epoch fencing")
        if observed.get("provider_call_status") != "processed":
            failures.append("observed.provider_call_status must be processed by successor")
        budget = observed.get("budget")
        if not isinstance(budget, dict) or budget.get("consumed_tokens") != 24 or budget.get("reserved_tokens") != 0:
            failures.append("observed.budget does not show exactly-once late usage settlement")
    elif scenario_id == "budget-unknown":
        require_count("provider_invocations", exact=1)
        calls = require_list("provider_call_states") or []
        reservations = require_list("reservation_states") or []
        if "unknown" not in calls or "response_saved" not in calls:
            failures.append("observed.provider_call_states omit unknown and saved response")
        if not {"unknown", "settled", "released", "reserved"}.issubset(reservations):
            failures.append("observed.reservation_states omit unknown/settled/unsent states")
        reservation_rows = observed.get("budget_reservations", [])
        if not any(item.get("sent") is True for item in reservation_rows if isinstance(item, dict)):
            failures.append("observed.budget_reservations omit sent reservations")
        before, after = observed.get("budget_before"), observed.get("budget_after")
        if (not isinstance(before, dict) or before.get("reserved_tokens") != 70 or before.get("consumed_tokens") != 0
                or not isinstance(after, dict) or after.get("reserved_tokens") != 200 or after.get("consumed_tokens") != 111):
            failures.append("observed budget snapshots differ from the bounded race/unknown-usage contract")
    return failures


def evaluate_report(report: dict, evidence_root: Path) -> dict:
    """Validate bound artifacts and return a verdict without upgrading claims.

    A green pytest run is only test execution evidence. The drill verdict stays
    incomplete until scenario-specific observed state and teardown evidence are
    present and artifact hashes verify under the supplied evidence root.
    """
    if not isinstance(report, dict):
        raise DrillReportError("report must be an object")
    root = evidence_root.resolve()
    if not root.is_dir():
        raise DrillReportError("evidence root does not exist")
    scenario_id = report.get("scenario_id")
    _required_fields(scenario_id)
    status = report.get("test_execution_status")
    if status not in {"passed", "failed", "blocked"}:
        raise DrillReportError("invalid test_execution_status")
    expected = report.get("expected_node_ids")
    results = report.get("test_results")
    if not isinstance(expected, list) or not expected or not all(isinstance(x, str) and x for x in expected):
        raise DrillReportError("expected_node_ids must be a non-empty string list")
    if not isinstance(results, list):
        raise DrillReportError("test_results must be a list")
    result_map: dict[str, str] = {}
    for result in results:
        if not isinstance(result, dict) or not isinstance(result.get("node_id"), str):
            raise DrillReportError("malformed test result")
        node_id = result["node_id"]
        if node_id in result_map or result.get("status") not in {"passed", "failed", "skipped", "error"}:
            raise DrillReportError("duplicate node id or invalid test result status")
        result_map[node_id] = result["status"]
    if len(expected) != len(set(expected)):
        raise DrillReportError("duplicate expected node id")

    artifacts = report.get("artifacts")
    if not isinstance(artifacts, dict):
        raise DrillReportError("artifacts object missing")
    _validate_artifact(root, "junit", artifacts.get("junit"))
    _validate_artifact(root, "console_log", artifacts.get("console_log"))
    observation_artifacts = artifacts.get("observations", [])
    if not isinstance(observation_artifacts, list):
        raise DrillReportError("observation artifacts must be a list")
    for index, artifact in enumerate(observation_artifacts):
        _validate_artifact(root, f"observations[{index}]", artifact)

    cleanup = report.get("cleanup")
    if not isinstance(cleanup, dict):
        raise DrillReportError("cleanup object missing")
    missing: list[str] = []
    if not all(result_map.get(node_id) == "passed" for node_id in expected):
        missing.extend(f"test_results.{node_id}" for node_id in expected if result_map.get(node_id) != "passed")
    if any(result not in {"passed"} for result in result_map.values()):
        missing.extend(f"test_results.{node_id}" for node_id, result in result_map.items() if result != "passed")
    if not cleanup.get("compose_project_removed"):
        missing.append("cleanup.compose_project_removed")
    if not cleanup.get("volume_removed"):
        missing.append("cleanup.volume_removed")
    missing.extend(_missing_observations(scenario_id, report.get("observed")))
    hard_failure = status == "failed" or any(item.get("status") in {"failed", "error"} for item in results)
    observation_failures = _observation_failures(scenario_id, report.get("observed")) if not missing and not hard_failure else []

    if hard_failure or observation_failures:
        verdict = "failed"
    elif status == "blocked":
        verdict = "blocked"
    elif missing:
        verdict = "incomplete"
    else:
        verdict = "passed"
    return {
        "scenario_id": scenario_id,
        "test_execution_status": status,
        "status": verdict,
        "missing_fields": sorted(set(missing)),
        "observation_failures": observation_failures,
        "verified_artifacts": ["junit", "console_log"],
    }
