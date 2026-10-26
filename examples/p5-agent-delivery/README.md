# P5 Provider Adapter (implementation slice)

This directory contains the Stage 5 provider boundary and bounded model-round
driver. `drive_provider_round()` selects the first request or a saved
continuation, consumes a durable response without resending it, and pins model,
endpoint, prompt/tool hashes, budget reservation and round limit in the task
checkpoint. `resume_agent_turn()` coordinates persisted read actions, approval
resume, scheduling authorized writes, one delivery attempt, and the next model
round. A committed delivery releases the worker lease, so each further write or
model continuation requires a successor claim. An unknown delivery stops the
coordinator for the explicit P4 reconciliation path; it never triggers a model
retry. `runner.py --live` is the explicit bounded live entrypoint: it accepts
only a fixed synthetic task owned by the local demo caller, loopback PostgreSQL,
and the P4 local sink. It caps each model response at 512 output tokens and the
task at four rounds, then writes a redacted per-wakeup report plus a root-bound
partial Task 2a evidence bundle under the ignored
`verify-output/stage5-live/<run-id>/` directory. The bundle registers only
`live_model_normal`; acceptance remains `incomplete` until the remaining gates
are supplied. Live provider behavior remains unverified until a human runs it.

## Dependencies

The Anthropic and MCP SDKs are an optional locked dependency group in the P4
runtime project. Install them only when preparing an explicit live run:

```bash
uv sync --frozen --group provider
```

The default P4 offline environment does not need either SDK. The local example
verifier remains offline and never calls a provider.

## Adapter contract

`provider.AnthropicMessagesAdapter` accepts a configured Anthropic client and
forwards one durable request to `client.messages.create`. Its `max_retries = 0`
declaration satisfies the P5 host boundary, and adapter construction rejects
SDK clients whose exposed retry count is nonzero or missing. Construct production clients with
`create_anthropic_client()` or `build_anthropic_client()`: SDK retries are
disabled, the timeout is finite, and an optional custom base URL must use HTTPS
or exact loopback HTTP. The API key is passed only to client construction; do not put
it in the request object, provider-call record, report, or logs.

The host request uses the Messages API shape, for example:

```python
request = {
    "model": configured_model,
    "max_tokens": 512,
    "system": system_prompt,
    "messages": [{"role": "user", "content": "查询合成订单 A-1001"}],
    "tools": trusted_provider_tools(mcp_tools),
}
```

`perform_provider_call()` persists the request before the adapter is called and
persists the provider response in a separate transaction. `drive_provider_round()`
consumes a saved response on restart, waits when actions remain unresolved, and
reconstructs the next request from exact stored assistant/tool-result blocks. A
lost or ambiguous response remains `unknown`; the adapter must not retry it. Use the locked P4
project environment to test this contract:

```bash
uv run --frozen pytest -q ../p5-agent-delivery/tests/test_host_contract.py
```

The offline contract tests verify schema provenance, usage accounting, exactly
one SDK method invocation, and `max_retries=0` client construction. PostgreSQL
integration coverage verifies tool continuation and approved-write delivery
through a separate local sink process. These checks do not prove authentication,
network connectivity, live provider behavior or production deployment safety.

## Explicit live smoke

For the clean-checkout deployment and bounded live smoke procedure, see
[`RUNBOOK.md`](RUNBOOK.md). For the deterministic task-level PostgreSQL drill
matrix, exact test selectors, observation fields, and evidence record contract,
see [`DRILLS.md`](DRILLS.md). Operational boundaries, incident triage,
receipt/usage reconciliation, migration policy, and containment/rollback
commands are in [`OPERATIONS.md`](OPERATIONS.md). Those tests use synthetic
adapters and local PostgreSQL/sink processes; none of these documents claims
production readiness.

For a future independent release handoff, use [`HANDOFF.md`](HANDOFF.md) and
start from [`HANDOFF-RECORD.template.json`](HANDOFF-RECORD.template.json). The
template is intentionally blank and does not count as a completed handoff.

Run the P4 PostgreSQL, API, and local sink profiles, then initialize the
synthetic corpus. Keep `DATABASE_URL` pointed at the host's loopback-mapped
PostgreSQL port. Configure an endpoint and budget account before the worker can
claim a provider request:

```sql
INSERT INTO provider_endpoints(id, concurrency_limit, max_attempts)
VALUES ('p5-anthropic-smoke', 1, 4) ON CONFLICT DO NOTHING;
INSERT INTO budget_accounts(id, tenant_id, token_limit, tool_limit)
VALUES ('p5-live-smoke', 'tenant-a', 20000, 20) ON CONFLICT DO NOTHING;
```

Create one task through the API with the exact fixed prompt below, then reuse
its returned task id for every wake-up. Export `DATABASE_URL`,
`P5_PROVIDER_ENDPOINT`, `P5_BUDGET_ACCOUNT`, `VERIFY_MODEL`,
`ANTHROPIC_API_KEY` (or `ANTHROPIC_AUTH_TOKEN`) and optional
`ANTHROPIC_BASE_URL`; set `P5_SINK_URL` only to the loopback sink. The key is
passed to SDK client construction and is never placed in the task, durable
request body, report, or command arguments.

```json
{
  "prompt": "查询合成订单 A-1001，并在人工审批后发送通知：订单 A-1001 已发货。只有收到投递回执后才报告通知已发送。",
  "release_id": "p5-local-smoke-v1"
}
```

Run one wake-up from `examples/p4-durable-support`:

```bash
uv run --frozen --group provider python ../p5-agent-delivery/runner.py --live --task "$TASK_ID"
```

If the run returns `waiting_approval`, inspect the task approval through the API
and approve it as the assigned local demo approver. Run the same command again
to resume. Successful delivery ends that lease; run it again so a successor
worker continues the saved provider conversation. If the run returns
`reconciling`, stop and use the P4 reconciliation path before resuming. Each
report contains the observed status, request identity, stop reason, usage,
hashes, SDK/model versions and timing without prompts, arguments, responses,
headers or credentials. A live report applies only to that model/config/task;
it is not a quality or production-readiness claim. The offline example gate
remains isolated and never makes provider requests.
