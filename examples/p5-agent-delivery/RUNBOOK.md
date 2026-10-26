# P5 bounded synthetic smoke runbook

This runbook starts the local PostgreSQL/API/sink stack from a clean checkout,
creates the one permitted synthetic task, and runs one provider wake-up at a
time. It is an operator procedure for a **bounded smoke observation**. It is
not a production deployment guide, reliability estimate, or substitute for the
Stage 4 fault-injection suite.

## Preconditions and safety boundary

- Docker Engine with Compose v2, `uv`, and a provider credential authorized for
  a small test request are available.
- Use only the fixed synthetic prompt below. The runner rejects other tasks,
  non-loopback PostgreSQL, and non-local sinks.
- The local demo tokens and sink are public teaching credentials. Do not put
  real customer data or credentials into the synthetic service.
- The runner makes a provider request only with explicit `--live`; it uses at
  most four rounds, 512 output tokens per round, no SDK retries, and a finite
  timeout. A provider request marked `unknown` is not retried automatically.
- Keep the resulting redacted report as evidence. Do not paste API keys or
  raw request/response bodies into the report or issue tracker.

## Start from a clean checkout

From the repository root, install the locked P4 runtime dependencies and start
the database. Port `55432` must be available; choose another fixed loopback
port if needed and use it consistently below.

```bash
cd examples/p4-durable-support
uv sync --frozen
export P4_POSTGRES_PORT=55432
docker compose up -d --wait --wait-timeout 90 postgres
export DATABASE_URL=postgresql://support:local-only-demo@127.0.0.1:55432/support
uv run python -m app.db migrate
uv run python -m app.db seed
```

Initialize the synthetic retrieval corpus and the bounded provider/budget
records. These statements are safe to repeat and do not restore revoked demo
identities or approvals.

```bash
PYTHONPATH=.. uv run python - <<'PY'
from app.config import Settings
from app.db import connect
from app.retrieval import seed_corpus

with connect(Settings.from_env().database_url) as conn:
    seed_corpus(conn)
    conn.execute("""
        INSERT INTO provider_endpoints(id, concurrency_limit, max_attempts)
        VALUES ('p5-anthropic-smoke', 1, 4)
        ON CONFLICT (id) DO NOTHING
    """)
    conn.execute("""
        INSERT INTO budget_accounts(id, tenant_id, token_limit, tool_limit)
        VALUES ('p5-live-smoke', 'tenant-a', 20000, 20)
        ON CONFLICT (id) DO NOTHING
    """)
PY
```

Start the API and synthetic sink. Both bind only to loopback on the host.

```bash
docker compose --profile runtime --profile delivery up -d --build api sink
curl --fail http://127.0.0.1:8000/health/ready
curl --fail http://127.0.0.1:8002/health/ready
```

If the repository is on a non-default port, set `P4_API_PORT` and
`P4_SINK_PORT` before `docker compose up`, and adjust the URLs below. A
readiness failure is a stop condition; do not continue with an old or partial
stack.

## Create the fixed task

Create the task as Alice. Save the returned `id` as `TASK_ID`; the id is not a
secret, but it should be used only with this local synthetic database.

```bash
TASK_RESPONSE=$(curl --fail --silent --show-error \
  -X POST http://127.0.0.1:8000/v1/tasks \
  -H 'Authorization: Bearer dev-alice' \
  -H 'Idempotency-Key: p5-local-smoke-v1' \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"查询合成订单 A-1001，并在人工审批后发送通知：订单 A-1001 已发货。只有收到投递回执后才报告通知已发送。","release_id":"p5-local-smoke-v1"}')
TASK_ID=$(printf '%s' "$TASK_RESPONSE" | python -c 'import json,sys; print(json.load(sys.stdin)["id"])')
printf 'TASK_ID=%s\n' "$TASK_ID"
```

Verify `GET /v1/tasks/$TASK_ID` reports `queued`, and verify the returned
release id is `p5-local-smoke-v1`. If the task was created earlier and its
state has advanced, do not treat an idempotent replay as a fresh run; create a
new task with a new idempotency key.

## Configure the explicit provider wake-up

In the host shell where the runner will execute, set the endpoint and budget
account ids created above, the exact model identifier intended for this smoke,
and a provider key. The runner reads the key from the environment; do not pass
it on the command line. An optional custom base URL is accepted only over
HTTPS or exact loopback HTTP.

```bash
export DATABASE_URL=postgresql://support:local-only-demo@127.0.0.1:55432/support
export P5_PROVIDER_ENDPOINT=p5-anthropic-smoke
export P5_BUDGET_ACCOUNT=p5-live-smoke
export VERIFY_MODEL='your-explicit-model-id'
export P5_SINK_URL=http://127.0.0.1:8002
# Read without echoing the credential into the terminal or command history.
read -s -r ANTHROPIC_API_KEY
export ANTHROPIC_API_KEY
printf '\n'
uv sync --frozen --group provider
uv run --frozen --group provider python ../p5-agent-delivery/runner.py --help
```

Avoid shell tracing (`set -x`) while exporting credentials. For a shared or
recorded terminal, inject the key through a local secret manager instead of
typing it into a command that may be retained in shell history.

## Advance one wake-up at a time

Run the same command for the saved task id. Each invocation claims and advances
one bounded wake-up, then writes a redacted report and partial evidence bundle
under `verify-output/stage5-live/<run-id>/`.
After a wake-up returns, the runner releases its matching owner/epoch lease so
the next explicit invocation can continue immediately. If the process crashes,
ordinary lease expiry and fenced takeover still apply.

The only predeclared online smoke case is
[`evaluation/live-smoke.json`](evaluation/live-smoke.json). Its case id and
dataset hash are recorded in the report; the gate requires both order lookup
and the approved synthetic notice action to succeed. This is one bounded
end-to-end observation, not an accuracy or production reliability estimate.

```bash
uv run --frozen --group provider python ../p5-agent-delivery/runner.py --live --task "$TASK_ID"
```

Expected human-controlled transitions:

1. On `waiting_approval`, read `GET /v1/tasks/$TASK_ID/approvals` as Alice.
   Decide only after checking the frozen action and eligible approver. Submit
   the approval id with `POST /v1/approvals/$APPROVAL_ID/decision` using the
   local `dev-approver` token and `{"decision":"approved"}`. Then invoke the
   runner once again with the same task id.
   Approval expires with the task deadline. After expiry the API rejects the
   decision; the next worker claim marks the task failed and cancels pending
   approvals/actions and queued delivery intents. Create a fresh synthetic
   task with a new idempotency key for another smoke; never revive the expired
   action.
2. On `delivery_succeeded`, invoke the runner once again with the same task id
   so a successor worker can consume the receipt and continue the saved model
   conversation. Do not infer business completion from the delivery status.
3. On `reconciling`, stop the runner. Use the Stage 4 delivery reconciliation
   procedure and establish the sink receipt before any further wake-up.
4. On `unknown`, `runner_error`, `failed`, `truncated`, or any unexpected
   status, stop. Preserve the report and task events, inspect the matching
   provider-call/action/delivery state, and do not manually replay a provider
   request or mark the task complete.
5. Stop when the task is terminal or the runner reaches its four-round limit.
   A nonterminal task at the limit is an incomplete observation, not a pass.

The `p5-live-smoke-v3` report records run start/end, release/model/provider host, commit and
worktree provenance, lockfile/prompt/tool/dataset/scorer/code hashes, SDK
versions, per-round request state, stop reason, usage, latency, persisted tool
statuses, output-validation state, and exception type when available. It
deliberately excludes the prompt, tool arguments, provider response, headers
and credentials. Each run also writes `evidence/evidence-manifest.json` and a
Task 2a `acceptance-report.json` bound to the `live_model_normal` artifact.
That report is expected to remain `incomplete` until the other acceptance
gates have evidence. `review.decision` remains `needs-review`; local hashes do
not prove provider identity or human review.

The `live_model_normal` artifact can pass only when the task and final output
are durably completed, the output hash is valid, and every recorded provider
round is processed with a request id and both usage dimensions. Missing usage,
an absent round, or an ambiguous runner outcome stays `unverified`; known
protocol/transport/truncation failures stay non-passing.

## Stop, preserve evidence, and recover

Stop the stack after saving the report and any required local event/receipt
evidence. This removes the teaching database volume; copy only the redacted
artifacts needed for review before cleanup.

```bash
docker compose --profile runtime --profile delivery down --remove-orphans
```

This stops containers while retaining the local teaching database volume. To
delete the synthetic database after copying any needed evidence, explicitly
run `docker compose --profile runtime --profile delivery down --volumes
--remove-orphans`; this is destructive and cannot be undone without a backup.

If an API, worker, or sink release misbehaves, stop new work first and preserve
the redacted reports plus task/action/outbox/receipt identifiers. The local
stack has no traffic router or rolling deploy: the containment command above
stops all services. For a code rollback, check out the previously recorded
known-good commit in a clean checkout, rebuild, then run migrations and
readiness checks before accepting new work:

```bash
git switch --detach "$KNOWN_GOOD_COMMIT"
cd examples/p4-durable-support
export P4_POSTGRES_PORT=55432
export DATABASE_URL=postgresql://support:local-only-demo@127.0.0.1:55432/support
docker compose up -d --wait --wait-timeout 90 postgres
uv run python -m app.db migrate
docker compose --profile runtime --profile delivery up -d --build api sink
curl --fail http://127.0.0.1:8000/health/ready
curl --fail http://127.0.0.1:8002/health/ready
```

Migrations are forward-only and checksum-pinned; there is no downgrade
command. If the known-good code is incompatible with the current schema, keep
the services stopped and restore a database backup into an isolated database
using the database operator's verified restore procedure. Never delete the
volume as a schema rollback. This local example has no production backup,
traffic failover, credential rotation, or customer-data recovery procedure.

For a task-level incident, use [`OPERATIONS.md`](OPERATIONS.md) to triage
unknown provider usage and delivery outcomes, audit the lease/approval boundary,
and decide when the system must remain stopped. The six deterministic drills
and their machine-checked, per-run evidence are documented in
[`DRILLS.md`](DRILLS.md); all six currently have passing local synthetic runs,
but they do not certify provider quality, production availability, or an
independent handoff.

When preparing an independent handoff, use [`HANDOFF.md`](HANDOFF.md) and copy
[`HANDOFF-RECORD.template.json`](HANDOFF-RECORD.template.json) to a new durable
evidence location. The blank template is not a completed review record.
