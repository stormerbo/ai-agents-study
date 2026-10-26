# P5 operations and recovery notes

This document defines how to stop, inspect, and recover the **local synthetic
teaching stack**. It is not a production SRE runbook. The example uses public
demo bearer tokens, one PostgreSQL instance, one synthetic sink, and a
single-process operator workflow. It has no production identity provider,
secret manager, high availability, durable backup service, alerting, or
customer-data controls.

## Architecture and trust boundaries

The API authenticates the local demo caller and persists a task plus its
idempotency record in PostgreSQL. A worker claims a task under a renewable
lease and monotonically increasing epoch. The host—not the model—owns tenant,
caller, ACL, approval, budget, tool registry, and completion decisions. Model
proposals are only candidates: read tools are validated against the trusted
registry, while write actions must pass current authorization and approval
checks before an outbox item can be dispatched.

Provider calls have their own durable `prepared → sending → response_saved`
boundary. A send is permitted only after the `sending` intent and budget
reservation commit. A stale epoch cannot consume a late result. If the process
cannot tell whether a request reached the provider, the call and its reservation
remain `unknown`; the runner does not resend it. The local sink has a separate
database transaction and idempotency key. If a response is lost after the sink
commits, reconcile by querying its receipt before considering a retry.

The model sees only the fixed synthetic task and registered tool results. It
does not receive provider credentials, caller tokens, or a general database or
shell tool. The public demo tokens and synthetic sink protocol are not security
controls for a deployed service. The loopback checks, database constraints,
hashes, and tests establish local example behavior only; they do not establish
production authentication, network isolation, provider identity, or remote
exactly-once effects.

## Stop conditions and first response

Stop the runner and do not start another wake-up when any report is `unknown`,
`reconciling`, `runner_error`, `failed`, `truncated`, or unexpected; when the
report is missing or its hashes fail; when task ownership or release
configuration differs from the frozen values; or when provider usage cannot
be reconciled. Preserve the run id and redacted report. Do not copy prompts,
tool arguments, provider bodies, credentials, or bearer tokens into an incident
record.

For each task, inspect in this order:

1. Read task status and ordered events through the API, then identify the
   current task, action, provider-call, outbox, and receipt IDs.
2. Check the durable records and checkpoint for the current release, model,
   prompt/tool hashes, lease owner/epoch, send state, reservation state, and
   approval version. Treat a stale worker or mismatched frozen configuration
   as a stop condition.
3. For an `unknown` provider call, reconcile usage from trustworthy provider
   evidence before releasing budget or deciding whether a new request is safe.
   Missing usage is not zero. This example intentionally has no automatic
   provider-call retry/reconciliation endpoint; leave it unresolved and do not
   issue another model wake-up.
4. For an `unknown` or `reconciling` delivery, use the Stage 4 receipt-first
   reconciliation procedure in `../p4-durable-support/README.md`. A receipt
   lookup failure or mismatch leaves the task unresolved. Manual resolution is
   an audited non-success closure; it does not prove the external effect did
   or did not occur, and it cannot be used to mark a task completed.
5. Resume only after the authoritative state is resolved and a current worker
   claim can safely proceed. Use the same task id and frozen release. Never
   replay an approved write with altered parameters.

If cancellation or revocation races with a delivery, the dispatch-claim commit
is the authorization boundary. A cancellation before claim prevents the send;
after claim it cannot promise to recall an in-flight request. Reconcile any
claimed effect before closing the task. A task must not become `completed`
unless the final output, citations, action results, receipts, and current
authorization all pass the same transaction's validator.

## Limits and escalation

The local `runner.py --live` invocation is explicitly bounded to a fixed
synthetic task, loopback PostgreSQL and sink, four model rounds, 512 output
tokens per round, zero SDK retries, and a finite request timeout. A report
proves only what that one invocation observed. The integration drills use
synthetic providers and a local PostgreSQL/sink stack; they do not measure
model quality or production reliability.

Keep unresolved provider usage, an unverified sink effect, a stale-epoch write,
a failed authorization check, or a missing artifact as an open incident in the
teaching exercise. Do not resolve uncertainty by editing database rows,
releasing a sent reservation, replaying a provider request, or fabricating a
receipt. This repository has no external on-call service or escalation target;
in a real deployment, the service owner and provider/sink operators must be
identified before launch.

## Migration and rollback policy

Run migrations from the same locked checkout intended for the service, after
PostgreSQL is healthy and before starting API/worker processes:

```bash
uv sync --frozen
uv run python -m app.db migrate
uv run python -m app.db seed
```

Each SQL migration is applied transactionally and recorded with a SHA-256
checksum. Changing an already-applied migration fails closed. Add a new
forward migration; do not edit a migration that is present in
`schema_migrations`. `seed` only inserts missing teaching identities and does
not undo revocations, restore deleted resources, or reset approvals. Verify
`schema_migrations` and service readiness before enabling a worker.

This example has no down migrations. For a bad application release, stop the
stack, check out the previously recorded known-good commit, run its forward
migrations, rebuild the API/sink, and verify readiness as described in
`RUNBOOK.md`. If its code cannot run against the current schema, keep traffic
stopped and restore a verified backup into an isolated database; do not guess
at reverse SQL. The local Compose volume is disposable and is not a backup.

Containment command (stops services and preserves the volume):

```bash
docker compose --profile runtime --profile delivery down --remove-orphans
```

The destructive teaching cleanup is separate and removes the local database
volume:

```bash
docker compose --profile runtime --profile delivery down --volumes --remove-orphans
```

Use the second command only after evidence is saved and the synthetic database
is no longer needed.

## Drill evidence

Run the six selectors and machine-checked report collector in
[`DRILLS.md`](DRILLS.md). A report is `passed` only when the selected tests ran
without skips, required scenario observations were emitted and matched,
JUnit/log/observation hashes verify under the evidence root, and both Compose
project and volume were removed. A passing local drill remains `needs-review`
and does not satisfy the live provider, holdout, release, or independent
handoff gates.
