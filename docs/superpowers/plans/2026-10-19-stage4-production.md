# Stage 4: Durable Support Service Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents are available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the stage 3 synthetic read-only Agent into a local multi-process PostgreSQL service with tenant authorization, durable tasks, approval recovery, and reconciled local HTTP actions.

**Architecture:** `examples/support_agent/` is the shared runtime package; `examples/p3-controlled-agent/` remains a thin CLI/MCP milestone entry point, while `examples/p4-durable-support/` supplies service, migrations, local sink, and milestone-specific tests. Stage 4 must reuse the Stage 3 provider normalization, tool allowlist/schema validation, and read-only MCP contract rather than fork a second runtime. A FastAPI service authenticates a demo bearer token into a trusted principal, writes tenant-scoped tasks and ordered events to PostgreSQL, and exposes task/approval/event reads. Independent workers claim tasks with expiring leases and monotonically increasing epochs. Approval freezes the action, argument hash, resource and policy versions; an outbox dispatcher sends only authorized actions to a durable local HTTP sink and reconciles ambiguous outcomes by stable external key. The implementation also includes synthetic ACL-filtered retrieval and shared concurrency/budget reservation. Each task adds real PostgreSQL integration evidence; fixtures validate deterministic control flow only.

**Tech Stack:** Python 3.11+, FastAPI, Pydantic, psycopg 3, PostgreSQL 18, HTTPX, pytest, Docker Compose. Pin exact dependency and image versions in project files.

---

## Global Constraints

- Follow `docs/superpowers/specs/2026-10-19-curriculum-reliability-design.md`, especially sections 5.1–5.9 and 6.1–6.4; it is authoritative where this plan is less specific.
- All business data is synthetic. Never connect to real customer systems, send real messages, or perform refunds/order updates.
- The API must derive tenant and subject from the authenticated principal. Request JSON `tenant_id`, model tool arguments, or MCP descriptions are never identity.
- PostgreSQL is the source of truth. SQLite or in-memory state cannot satisfy integration requirements.
- A worker lease/epoch protects database state and action scheduling, not a remote request already sent. Unknown external outcomes enter `reconciling` until checked by external key.
- Read-only MCP calls are at-least-once until their result is durably attached to the frozen action: a worker that loses its lease after the remote read returns cannot persist that result, so a successor may retry the read. Once persisted, later resumes reuse the stored result. Do not imply exactly-once remote reads or replay the full model history.
- A task cannot become `completed` while pending, denied, unknown, or otherwise unresolved actions remain.
- Approval binds tenant, eligible approver, action id, canonical argument hash, resource version, policy version, and expiry. Recheck authorization and versions before dispatch.
- Offline fixtures and real provider observations must be reported separately. Do not claim provider quality or PostgreSQL guarantees from unit tests.
- Secrets must not appear in command arguments, logs, test output, or committed result records. Demo credentials are explicitly local-only and documented as unsuitable for deployment.
- Stage 4 completion requires the Stage 4 criteria in `src/content/curriculum/projects.ts` and the design spec, not just the tasks in this focused plan. The full true-model capstone acceptance is Stage 5; Stage 4 must provide the adapter and an optional bounded call, clearly report unavailable credentials, and must not label the overall project complete.

## Task 1: PostgreSQL service, trusted identity, durable task API

**Files:**

- Create: `examples/support_agent/__init__.py`, `providers.py`, `tool_gateway.py`, `runtime.py` (extracted from Stage 3 with a compatibility wrapper)
- Create: `examples/p4-durable-support/pyproject.toml`, `uv.lock`, `.env.example`, `compose.yaml`, `Dockerfile`, `README.md`
- Create: `examples/p4-durable-support/app/__init__.py`, `app/config.py`, `app/auth.py`, `app/db.py`, `app/models.py`, `app/api.py`, `app/main.py`, `migrations/0001_base.sql`
- Create: `examples/p4-durable-support/tests/conftest.py`, `tests/test_tasks_api.py`, `tests/test_task_idempotency.py`
- Modify: `examples/README.md`

- [x] Add a pinned `uv` project, PostgreSQL Compose service, health check, migration runner, and synthetic seed command. Use versioned SQL migrations; record exact commands in README.
- [x] Define development-only tokens mapped to principal, tenant, and roles. Compare supplied bearer tokens in constant time; request bodies never establish identity.
- [x] Create migrations for tenants, caller identities, tasks, ordered append-only events, and idempotency records. Enforce `(tenant_id, caller_id, idempotency_key)` uniqueness, foreign keys, `(task_id, seq)` uniqueness, and atomic task-plus-first-event creation.
- [x] Implement `POST /v1/tasks`, task and event reads, readiness/liveness. Define response/error schemas, status codes, and cursor semantics in the README; same key/same canonical payload returns the original task, same key/different payload returns 409.
- [x] Use two independently started API processes in the integration harness. Test restart persistence, simultaneous same-key submission with a barrier, same key across different callers, strictly increasing event sequence, cross-tenant task/event denial, forged body `tenant_id`, caller access revocation for task/events/approvals, and readiness failure when PostgreSQL is unavailable.
- [x] Run the named command from `examples/p4-durable-support/`: `uv run pytest -m integration -q`. The pytest harness must start Compose, await healthy PostgreSQL, run tests, then tear services down even on failure; it must fail if Docker/PostgreSQL is unavailable. Document exact setup and distinguish PostgreSQL evidence from unit fixtures.
- [x] Extract the Stage 3 endpoint normalization and runtime/tool boundaries into `examples/support_agent/`: preserve final, tool_calls, refusal, truncated, and transport_error as distinct outcomes; validate tool names with an allowlist and arguments against schemas before MCP invocation. Keep Stage 3's CLI and current tests passing through a thin compatibility entry point. Add contract tests for each normalized outcome and forbidden/invalid tool calls.

## Task 2: Worker ownership, checkpoints, approvals, and recovery

**Files:**

- Create: `examples/p4-durable-support/app/worker.py`, `app/runtime.py`, `app/approvals.py`, `app/actions.py`, `app/retrieval.py`, `app/limits.py`, `migrations/0002_execution.sql`
- Create: `examples/p4-durable-support/tests/test_worker_ownership.py`, `tests/test_approval_recovery.py`, `tests/test_retrieval_acl.py`, `tests/test_index_lifecycle.py`, `tests/test_limits.py`
- Modify: `examples/p4-durable-support/tests/test_tasks_api.py` (make migration assertion version-aware), `compose.yaml`, `README.md`

- [x] Add migrations for worker lease, execution epoch, checkpoint, action ledger, approval, policy/resource versions, synthetic documents/chunks and ACL version, concurrency slots, and budget reservations.
- [x] Implement validated task/action state transitions and atomic claim/renew/checkpoint/event/approval/action-authorization writes fenced by current owner and epoch. Test lease takeover with two OS processes, a synchronization barrier, forced owner death, and assertions that stale checkpoint, event, approval, and action-authorization writes affect zero rows. Task 3 applies the same fence to outbox creation and dispatch.
- [x] Persist every model-proposed action independently. If any action needs approval, checkpoint and pause the whole turn; no proposed call is dropped and no fake tool result is inserted.
- [x] Add `POST /v1/tasks/{id}/cancel`, `GET /v1/tasks/{id}/approvals`, and `POST /v1/approvals/{id}/decision`. Derive approver from authentication, enforce tenant and role, allow only one terminal decision under concurrent requests, and return 409 for duplicate/conflicting or expired decisions.
- [x] Freeze approval to tenant, eligible approver, action id, canonical args hash, resource/policy versions, and expiration. Restart API and worker while waiting; approve, resume only the frozen action, and prove modified args, changed ACL/policy/resource, expired or revoked permission cannot dispatch.
- [x] Build a small synthetic, versioned document/chunk corpus with tenant/resource ACLs and index versions. Construct filters from the authenticated principal before candidate selection; negative PostgreSQL integration tests prove unauthorized and deleted chunks never appear in retrieval results or captured model context.
- [x] Implement document update and index-version cutover: build new version, validate it, atomically switch active version, then retire old version. Test old/new version behavior, immediate query rejection on deletion or ACL revocation, and invalidation of result cache and related memory before returning any context.
- [x] Implement bounded queue admission and per-task concurrency slots. Test queue-full rejection, task deadline and slot release with explicit API responses and database state assertions.
- [x] Implement per-provider concurrency slots and 429 retry scheduling with bounded jitter/deadline checks. Test the stored retry time, deadline expiry, and that retries do not exceed endpoint limits.
- [x] Implement atomic shared token/tool budget reservations and post-response reconciliation. Unknown usage remains reserved; concurrent workers cannot overspend. Test oversubscription using a barrier, unknown usage retention, known usage settlement, and safe release only for unsent requests.
- [x] Run the worker, approval, retrieval, and limits integration tests through the named Compose integration command. Do not infer provider behavior from fixtures.
- [x] Inject lease takeover after a read-only MCP response but before result persistence. Verify the stale worker cannot write the result, the successor may safely retry the read, the durable result is then stored, and later resumes do not call the tool again. Document this at-least-once read boundary.

## Task 3: Transactional outbox, durable HTTP sink, and reconciliation

**Files:**

- Create: `examples/p4-durable-support/app/outbox.py`, `app/delivery.py`, `app/sink.py`, `app/services/__init__.py`, `migrations/0003_delivery.sql`, `migrations/0004_manual_resolution.sql`
- Create: `examples/p4-durable-support/tests/test_delivery_reconciliation.py`, `tests/test_cancel_and_revoke_races.py`, `tests/test_manual_delivery_resolution.py`
- Modify: `examples/p4-durable-support/app/actions.py`, `app/approvals.py`, `app/runtime.py` (include delivery/manual-resolution router), `app/config.py`, `app/db.py` (seed the local-only operator identity), `tests/test_approval_recovery.py` (assert Task 2 approval creates zero outbox rows), `compose.yaml`, `README.md`

- [x] In migration `0003_delivery.sql`, add outbox, durable dispatch token/lease, attempts, external key, sink receipt, and action delivery states. Persist the authorized action transition and outbox row in one transaction, deriving stable `external_key` from action id.
- [x] Dispatcher must use the Task 2 worker epoch fence to atomically claim only still-authorized actions; the same transaction rechecks task cancellation, current permission, approval, parameter hash, and resource/policy versions, then sets action/outbox `dispatching`. That commit is the authorization boundary.
- [x] After `dispatching` commits, cancellation/revocation cannot promise to stop or revoke the already-claimed send. Cancelling a still-queued outbox suppresses it; cancelling a claimed or outcome-unknown action puts the task in `reconciling` and requires a receipt or manual decision. Test the claim-vs-cancel/revoke row-lock ordering.
- [x] Use a durable dispatch token independent of the worker lease to record sink receipts and reconcile after worker expiry/cancellation. A stale worker epoch cannot create or claim outbox work; only the dispatcher token may attach a receipt for its claimed external key.
- [x] Model connection loss after sending as unknown; first query the sink by `external_key`, then retry only when the sink contract proves idempotency. Keep the task `reconciling` until a receipt or explicit manual decision resolves it.
- [x] Add an authenticated local-only `operator` identity and manual-resolution API for irrecoverable unknowns. Require `operator` role, explicit outcome (`effect_applied`, `effect_not_applied`, or `abandon`), evidence reference, and reason; write an append-only audit event/record. Manual resolution closes the action/task as failed or cancelled, never inserts a tool result, never marks the action `succeeded`, and therefore cannot bypass completed-task validation.
- [x] Add explicit injected checkpoints for (a) cancel/revoke before claim, (b) cancel/revoke after DB claim but before network send, and (c) sink commit before receipt persistence. Also test stale-epoch outbox creation after worker takeover. Assert authorized send boundary, event sequence, task state, reconciliation behavior, and sink side-effect count at each point.
- [x] Verify that unresolved, denied, cancelled, or unknown actions cannot produce a successful completed task.

## Task 4: Stage acceptance, evidence, and curriculum handoff

**Files:**

- Create: `examples/p4-durable-support/tests/test_acceptance_integration.py`
- Modify: `examples/manifest.json`, `examples/README.md`, `src/content/curriculum/projects.ts`, `docs/PROGRESS.md`, `AGENTS.md`, `docs/superpowers/plans/2026-10-19-curriculum-reliability.md`
- Create: a sanitized experiment result under `experiments/results/` only for executed integration evidence.

- [x] Add one command that starts required local services, runs PostgreSQL multi-process integration tests, and returns nonzero when Docker/PostgreSQL or a required gate is unavailable; missing integration must not be reported as pass. Exact command: `uv run pytest -m integration -q`.
- [x] Register only the offline-safe suite in `pnpm verify:examples`; keep local PostgreSQL integration and provider-backed calls as explicit commands.
- [x] Update `experiments/registry.json` with separate offline-fixture and PostgreSQL integration records, linked lesson IDs, code/lockfile hashes, dataset/fixture identifiers, invariants, command/environment, result paths, and evidence classifications. No new provider observation was performed.
- [x] Match `experiments/schemas/experiment.schema.json` exactly, including `question`, `scorerVersion`, `status`, and `reviewedAt` along with lesson IDs, code/lock hashes, dataset version, invariants, and result path. Results pass the result field allowlist and sensitive-value scanner; both new records remain `needs-review` until the controller performs the required first human review, and are not treated as publishable evidence.
- [x] Update the project card, setup docs, progress ledger, and main design plan with tested behaviors and explicit unverified boundaries. Stage 4 local PostgreSQL integration is complete; true-model capstone acceptance stays in Stage 5. No bounded model call was run because Stage 4 did not require it and no credential-gated run was requested.
- [x] Run relevant unit, integration, evidence, example, curriculum, type, lint, depth, build, link, and search checks. Visually inspect the modified project page in light and dark themes. The site-wide external link scan still reports 40 pre-existing broken/blocked links; no new external URL was introduced in this task.

## Out of scope until Stage 5

- Independent engineer handoff, release/rollback packet, one-shot frozen holdout quality evaluation, and full capstone acceptance remain Stage 5 work.
- A true-model call may be done only as a separate bounded optional evidence run; it cannot block offline build or integration tests and cannot be claimed when credentials are missing.
