# Stage 5 task-level drill matrix

This matrix composes the Stage 4 PostgreSQL drills with the Stage 5 host
integration tests. It does not duplicate their fixtures or claim that a test
name alone proves a pass. Run one row at a time from
`examples/p4-durable-support`; every command must exit zero, and the matching
assertions must be present in the JUnit/test output. Missing Docker, failed
PostgreSQL readiness, a skipped test, or a nonzero exit is **blocked/failed**,
never a pass.

Before each execution, record the git commit, Python/uv/Docker versions, exact
command, UTC start/end, and a fresh report/run id. Preserve the JUnit XML and
the redacted console log under the run's evidence directory. Do not include
DSNs, credentials, task prompts, or raw provider bodies. These tests use
synthetic provider adapters; they do not call a live provider.

## Repeatable scenarios

| Drill                                                                   | Command from `examples/p4-durable-support`                                                                                    | Authoritative assertions in the test                                                                                                                                                                                                                           | Collected database facts                                                                                      |
| ----------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| Approval pause, approve, deliver once, continue from saved conversation | `uv run --frozen python ../p5-agent-delivery/run_drills.py --scenario approval-pause-resume --evidence-root "$EVIDENCE_ROOT"` | Task enters `waiting_approval`; approval is made by `dev-approver`; one sink effect; delivery returns task to `queued`; successor resumes matching `tool_use_id`; final validator records `completed`; provider called twice, never while approval is pending. | Actual task/action/outbox statuses, sink effect count, ordered event kinds and provider-call count.           |
| Cancel/revoke racing a claimed delivery                                 | `uv run --frozen python ../p5-agent-delivery/run_drills.py --scenario cancel-revoke-race --evidence-root "$EVIDENCE_ROOT"`    | Runner executes all six combinations: cancel/revoke × before claim/after claim/before receipt. Pre-claim blocks delivery; a claimed effect is reconciled; stale/unauthorized completion is rejected; no `task.completed` event is emitted.                     | Six actual node outcomes, phase/operation, outbox/action/task statuses, effect counts and event order.        |
| Idempotency across API processes                                        | `uv run --frozen python ../p5-agent-delivery/run_drills.py --scenario idempotency --evidence-root "$EVIDENCE_ROOT"`           | Concurrent same-scope/same-payload requests converge on one task id; key scope does not merge different callers/tenants; conflicting payload does not overwrite the original task.                                                                             | HTTP statuses, unique task-id count, task/event/idempotency-row counts.                                       |
| Sink commit with lost response, then reconcile by receipt               | `uv run --frozen python ../p5-agent-delivery/run_drills.py --scenario unknown-reconcile --evidence-root "$EVIDENCE_ROOT"`     | Ambiguous result remains `unknown`/`reconciling`; completion is rejected; receipt lookup precedes safe retry; a committed sink effect is deduplicated and final effect count remains one.                                                                      | Actual action/task/outbox states, POST/GET sequence, effect counts and completion-attempt result.             |
| Worker lease takeover and stale-epoch fencing                           | `uv run --frozen python ../p5-agent-delivery/run_drills.py --scenario lease-takeover --evidence-root "$EVIDENCE_ROOT"`        | A separately launched process takes over after owner death; epoch increments; stale writes produce no event/action/checkpoint mutation. A late provider response may settle usage once but old epoch cannot consume it.                                        | Actual owner epochs, stale-write counts, checkpoint hash, provider-call and reservation states, usage totals. |
| Shared budget race and unknown usage                                    | `uv run --frozen python ../p5-agent-delivery/run_drills.py --scenario budget-unknown --evidence-root "$EVIDENCE_ROOT"`        | Concurrent reservations cannot exceed the shared account; sent calls with missing/ambiguous usage remain reserved/unknown; unsent reservation can be released; later reliable usage settles once; ambiguous provider call is not resent.                       | Actual reserved/consumed token and tool counts, reservation/call states, provider invocation count.           |

Use an evidence directory outside the source tree or under the ignored
`verify-output/` directory. For example, from the P4 project directory:

```bash
export EVIDENCE_ROOT="$PWD/../../verify-output/stage5-drills"
mkdir -p "$EVIDENCE_ROOT"
```

Each collector invocation uses a fresh Compose project, strips provider and
database credentials from the child environment, runs the exact frozen test
selectors, writes JUnit/console/observation artifacts and checks whether the
Compose project and volume were removed. The JSON report's `status` stays
`incomplete` when tests pass but expected observations or teardown evidence are
missing. Never convert an assertion failure, skipped integration test,
unavailable Docker daemon, or cleanup failure into `passed`.

## Evidence record and verdict

`run_drills.py` creates a fresh UUID directory and writes `report.json`,
JUnit, redacted console output, and one observation JSON file per selected test
node. Parameterized cancel/revoke cases therefore remain separate observations.
The report includes the current Git commit plus a worktree-diff hash; a dirty
worktree is disclosed and does not become a clean release artifact. Reports
are written beneath the supplied evidence root, which should be outside the
source tree or ignored by Git.

The machine-readable contract is:

```json
{
  "schema": "p5-drill-report-v1",
  "run_id": "uuid",
  "scenario_id": "approval-pause-resume",
  "status": "incomplete",
  "started_at_utc": "timestamp",
  "finished_at_utc": "timestamp",
  "elapsed_ms": 0,
  "command": "exact argv with secrets redacted",
  "environment": { "python": "", "uv": "", "docker": "", "postgres_image": "" },
  "materials": { "commit": "git commit id", "worktree_clean": false, "worktree_diff_sha256": "" },
  "test_execution_status": "passed",
  "test_exit_code": 0,
  "expected_node_ids": [],
  "test_results": [{ "node_id": "", "status": "passed" }],
  "artifacts": {
    "junit": { "path": "relative path under evidence root", "sha256": "" },
    "console_log": { "path": "relative path under evidence root", "sha256": "" },
    "observations": [{ "path": "relative path under evidence root", "sha256": "" }]
  },
  "observed": {},
  "cleanup": { "compose_project_removed": true, "volume_removed": true },
  "review": { "reviewer": null, "reviewed_at_utc": null, "decision": "needs-review" },
  "missing_fields": []
}
```

Allowed `status` values are `passed`, `failed`, `blocked`, and `incomplete`.
The `observed` object is scenario-specific and preserves test-node facts such as
task/action/outbox states, event order, sink effects, checkpoint hashes, lease
epochs, provider-call states, and budget reservations. It is not a universal
flat schema; `drill_report.py` validates the required facts and their expected
values for each scenario.

Observations are emitted by the selected integration test after it reads the
database state; the collector binds each record to the JUnit node id, hashes
each artifact, and checks that artifact paths stay under the evidence root.
A scenario is `passed` only if every expected node executed (none skipped),
all assertions passed, scenario-specific actual-state facts are present and
match, every JUnit/log/observation hash verifies, and both Compose project and
volume were removed. An unexpected actual value is `failed`; environmental
inability to execute is `blocked`; absent or unbound evidence is `incomplete`.
All six scenarios currently have passing synthetic local reports under the
ignored `verify-output/stage5-drills/` directory. These are run evidence from a
dirty development worktree, not a frozen release or independent review.

These local tests verify deterministic synthetic database and HTTP behavior.
They do not attest to provider quality, real sink semantics, production
identity, high availability, independent human review, or deployment safety.
Operational stop conditions, receipt-first reconciliation, migration limits,
and rollback/containment commands are in [`OPERATIONS.md`](OPERATIONS.md).
