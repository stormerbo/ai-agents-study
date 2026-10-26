"""Host adapter contract and network send boundary on real PostgreSQL."""
import hashlib
import json
import sys
import uuid
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
P4 = Path(__file__).resolve().parents[1]
P5 = P4.parent / "p5-agent-delivery"
for path in (P4, P5):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

pytestmark = pytest.mark.integration


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def test_trusted_tools_are_registry_derived_and_mcp_reads_must_match():
    from host import trusted_provider_tools
    from app.actions import REGISTRY

    peer = [
        {"name": "lookup_order", "inputSchema": REGISTRY["lookup_order"][0]},
        {"name": "search_policy", "inputSchema": REGISTRY["search_policy"][0]},
        {"name": "untrusted_write", "inputSchema": {"type": "object", "properties": {}}},
    ]
    tools = trusted_provider_tools(peer)
    assert [tool["name"] for tool in tools] == ["lookup_order", "search_policy", "send_notice"]
    assert tools[0]["input_schema"] == REGISTRY["lookup_order"][0]
    assert tools[-1]["input_schema"] == REGISTRY["send_notice"][0]
    peer[0]["inputSchema"] = {"type": "object", "properties": {"order_id": {"type": "string"}}}
    with pytest.raises(ValueError, match="schema mismatch"):
        trusted_provider_tools(peer)


def test_provider_network_call_occurs_only_after_committed_sending_and_response_is_durable(service):
    from app.db import connect
    from app.worker import claim
    from app.limits import budget_report
    from test_worker_ownership import new_task
    from host import perform_provider_call

    task_id = new_task(service.dsn)
    endpoint = "host-" + uuid.uuid4().hex
    account = "host-budget-" + uuid.uuid4().hex
    request = {"model": "fixture", "messages": [{"role": "user", "content": "synthetic"}], "tools": []}
    request_id = uuid.uuid4()
    with connect(service.dsn) as conn:
        release_id = conn.execute("SELECT release_id FROM tasks WHERE id=%s", (task_id,)).fetchone()["release_id"]
        conn.execute("INSERT INTO provider_endpoints VALUES (%s,1,3)", (endpoint,))
        conn.execute("INSERT INTO budget_accounts(id,tenant_id,token_limit,tool_limit) VALUES (%s,%s,1000,10)", (account, "tenant-a"))
        lease = claim(conn, "host-owner", task_id=task_id)

    class Adapter:
        max_retries = 0
        def __call__(self, body):
            with connect(service.dsn) as conn:
                row = conn.execute("SELECT state FROM provider_calls WHERE request_id=%s", (request_id,)).fetchone()
                reservation = conn.execute("SELECT sent FROM budget_reservations WHERE id=(SELECT reservation_id FROM provider_calls WHERE request_id=%s)", (request_id,)).fetchone()
                assert row["state"] == "sending"
                assert reservation["sent"] is True
            return {"id": "response-1", "stop_reason": "end_turn", "content": [{"type": "text", "text": "ok"}],
                    "usage": {"input_tokens": 9, "output_tokens": 3, "cache_creation_input_tokens": 4, "cache_read_input_tokens": 8}}

    response = perform_provider_call(
        lambda: connect(service.dsn), lease, request_id=request_id, endpoint=endpoint,
        release_id=release_id, model="fixture", request=request, budget_account=account,
        reserved_tokens=100, reserved_tools=2, provider=Adapter(),
    )
    assert response["stop_reason"] == "end_turn"
    with connect(service.dsn) as conn:
        row = conn.execute("SELECT state,response_body,usage_tokens,usage_tools FROM provider_calls WHERE request_id=%s", (request_id,)).fetchone()
        assert row["state"] == "response_saved"
        assert row["response_body"] == response
        assert (row["usage_tokens"], row["usage_tools"]) == (24, 0)
        assert budget_report(conn, account)["consumed_tokens"] == 24


def test_provider_transport_failure_becomes_unknown_without_implicit_retry(service):
    from app.db import connect
    from app.worker import claim
    from app.limits import budget_report
    from test_worker_ownership import new_task
    from host import perform_provider_call

    task_id = new_task(service.dsn)
    endpoint = "host-fail-" + uuid.uuid4().hex
    account = "host-fail-budget-" + uuid.uuid4().hex
    request = {"model": "fixture", "messages": [{"role": "user", "content": "synthetic"}], "tools": []}
    request_id = uuid.uuid4()
    with connect(service.dsn) as conn:
        release_id = conn.execute("SELECT release_id FROM tasks WHERE id=%s", (task_id,)).fetchone()["release_id"]
        conn.execute("INSERT INTO provider_endpoints VALUES (%s,1,3)", (endpoint,))
        conn.execute("INSERT INTO budget_accounts(id,tenant_id,token_limit,tool_limit) VALUES (%s,%s,1000,10)", (account, "tenant-a"))
        lease = claim(conn, "host-failure", task_id=task_id)

    class Adapter:
        max_retries = 0
        calls = 0
        def __call__(self, body):
            self.calls += 1
            raise TimeoutError("synthetic timeout")
    adapter = Adapter()
    assert perform_provider_call(lambda: connect(service.dsn), lease, request_id=request_id,
        endpoint=endpoint, release_id=release_id, model="fixture", request=request,
        budget_account=account, reserved_tokens=100, reserved_tools=2, provider=adapter) is None
    assert adapter.calls == 1
    with connect(service.dsn) as conn:
        row = conn.execute("SELECT state FROM provider_calls WHERE request_id=%s", (request_id,)).fetchone()
        reservation = conn.execute("SELECT state FROM budget_reservations WHERE id=(SELECT reservation_id FROM provider_calls WHERE request_id=%s)", (request_id,)).fetchone()
        assert row["state"] == "unknown"
        assert reservation["state"] == "unknown"
        report = budget_report(conn, account)
    from conftest import record_drill_observation
    record_drill_observation("budget-unknown", {
        "provider_invocations": adapter.calls,
        "provider_call_states": ["sending", row["state"]],
        "reservation_states": [reservation["state"]],
        "budget_after": {"reserved_tokens": report["reserved_tokens"], "consumed_tokens": report["consumed_tokens"],
                         "reserved_tools": report["reserved_tools"], "consumed_tools": report["consumed_tools"]},
    }, dsn=service.dsn, task_ids=[task_id])


def test_usage_dimensions_reject_boolean_counts():
    from host import _usage
    assert _usage({"usage": {"input_tokens": 1, "output_tokens": 2, "cache_creation_input_tokens": 4, "cache_read_input_tokens": 8}, "content": []}) == (15, 0)
    assert _usage({"usage": {"input_tokens": 1, "output_tokens": 2, "cache_creation_input_tokens": 4, "cache_read_input_tokens": None}, "content": []}) == (None, 0)
    assert _usage({"usage": {"input_tokens": True, "output_tokens": 2, "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0}, "content": []}) == (None, 0)


def test_host_can_persist_multiple_rounds_for_one_task(service):
    from app.db import connect
    from app.worker import claim
    from test_worker_ownership import new_task
    from host import perform_provider_call

    task_id = new_task(service.dsn)
    endpoint = "host-round-" + uuid.uuid4().hex
    account = "host-round-budget-" + uuid.uuid4().hex
    with connect(service.dsn) as conn:
        release_id = conn.execute("SELECT release_id FROM tasks WHERE id=%s", (task_id,)).fetchone()["release_id"]
        conn.execute("INSERT INTO provider_endpoints VALUES (%s,1,3)", (endpoint,))
        conn.execute("INSERT INTO budget_accounts(id,tenant_id,token_limit,tool_limit) VALUES (%s,%s,1000,10)", (account, "tenant-a"))
        lease = claim(conn, "host-rounds", task_id=task_id)
    class Adapter:
        max_retries = 0
        def __call__(self, body):
            return {"id": "response-" + str(body["round"]), "stop_reason": "end_turn", "content": [],
                    "usage": {"input_tokens": 1, "output_tokens": 1, "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0}}
    from app.provider_calls import mark_processed
    for round_index in (0, 1):
        request_id = uuid.uuid4()
        request = {"round": round_index, "messages": [{"role": "user", "content": "synthetic"}]}
        perform_provider_call(lambda: connect(service.dsn), lease, request_id=request_id, endpoint=endpoint,
            release_id=release_id, model="fixture", request=request, budget_account=account,
            reserved_tokens=10, reserved_tools=1, provider=Adapter(), round_index=round_index)
        if round_index == 0:
            with connect(service.dsn) as conn:
                assert mark_processed(conn, lease, request_id)
    with connect(service.dsn) as conn:
        rows = conn.execute("SELECT round_index,state FROM provider_calls WHERE task_id=%s ORDER BY round_index", (task_id,)).fetchall()
        assert [(row["round_index"], row["state"]) for row in rows] == [(0, "processed"), (1, "response_saved")]


def test_durable_driver_runs_tool_round_then_completes_from_saved_continuation(service):
    import asyncio
    from app.actions import REGISTRY
    from app.db import connect
    from app.runtime import execute_reads
    from app.worker import claim
    from test_worker_ownership import new_task
    from host import drive_provider_round

    task_id = new_task(service.dsn)
    endpoint = "driver-" + uuid.uuid4().hex
    account = "driver-budget-" + uuid.uuid4().hex
    mcp_tools = [
        {"name": "lookup_order", "inputSchema": REGISTRY["lookup_order"][0]},
        {"name": "search_policy", "inputSchema": REGISTRY["search_policy"][0]},
    ]
    with connect(service.dsn) as conn:
        from app.retrieval import seed_corpus
        seed_corpus(conn)
        release_id = conn.execute("SELECT release_id FROM tasks WHERE id=%s", (task_id,)).fetchone()["release_id"]
        conn.execute("INSERT INTO provider_endpoints VALUES (%s,1,4)", (endpoint,))
        conn.execute("INSERT INTO budget_accounts(id,tenant_id,token_limit,tool_limit) VALUES (%s,%s,5000,40)",
                     (account, "tenant-a"))
        lease = claim(conn, "durable-driver", task_id=task_id)

    class Adapter:
        max_retries = 0
        calls = []
        def __call__(self, request):
            self.calls.append(request)
            if len(self.calls) == 1:
                return {"id": "driver-tool", "stop_reason": "tool_use",
                    "content": [{"type": "tool_use", "id": "driver-read", "name": "lookup_order",
                                 "input": {"order_id": "A-1001"}}],
                    "usage": {"input_tokens": 12, "output_tokens": 4,
                              "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0}}
            tool_result = json.loads(request["messages"][-1]["content"][0]["content"])
            return {"id": "driver-final", "stop_reason": "end_turn",
                "content": [{"type": "text", "text": json.dumps({"outcome": "answer", "text": "订单已查询。",
                    "citations": tool_result["citations"]}, ensure_ascii=False)}],
                "usage": {"input_tokens": 20, "output_tokens": 8,
                          "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0}}

    class MCP:
        async def list_tools(self):
            return {"tools": mcp_tools}
        async def call_tool(self, name, args):
            return {"isError": False, "content": [{"type": "text", "text": "synthetic order result"}]}

    adapter = Adapter()
    common = {"endpoint": endpoint, "budget_account": account, "provider": adapter,
              "mcp_tools": mcp_tools, "system_prompt": "Return the required JSON shape.",
              "model": "fixture-model", "max_tokens": 128, "max_rounds": 2,
              "reserved_tokens": 512, "reserved_tools": 4}
    first = drive_provider_round(lambda: connect(service.dsn), lease, **common)
    assert first["status"] == "actions_proposed"
    with connect(service.dsn) as conn:
        result = asyncio.run(execute_reads(conn, lease, MCP(), budget_account=account))
        assert result[0]["tool_call_id"] == "driver-read"
        conn.execute("UPDATE tasks SET lease_until=clock_timestamp()-interval '1 second' WHERE id=%s", (task_id,))
        successor = claim(conn, "durable-driver-successor", task_id=task_id)
        assert successor and successor.epoch == lease.epoch + 1
    mismatch = drive_provider_round(lambda: connect(service.dsn), successor, **{**common, "max_rounds": 3})
    assert mismatch["status"] == "run_config_mismatch"
    assert len(adapter.calls) == 1
    final = drive_provider_round(lambda: connect(service.dsn), successor, **common)
    assert final["status"] == "completed"
    assert len(adapter.calls) == 2
    assert adapter.calls[1]["messages"][-1]["content"][0]["tool_use_id"] == "driver-read"
    with connect(service.dsn) as conn:
        assert conn.execute("SELECT status FROM tasks WHERE id=%s", (task_id,)).fetchone()["status"] == "completed"
        assert conn.execute("SELECT count(*) AS n FROM provider_calls WHERE task_id=%s", (task_id,)).fetchone()["n"] == 2
        output = conn.execute("SELECT output FROM final_outputs WHERE task_id=%s", (task_id,)).fetchone()["output"]
        assert output["citations"][0]["resource_id"] == "A-1001"


def test_driver_consumes_response_saved_before_crash_without_resending(service):
    from app.db import connect
    from app.provider_calls import mark_sending, record_response
    from app.retrieval import seed_corpus
    from host import drive_provider_round
    from test_provider_calls import _prepared

    task_id, lease, endpoint, account, slot, reservation, request_id, request, digest, release_id = _prepared(service)
    response = {"id": "saved-before-crash", "stop_reason": "tool_use",
        "content": [{"type": "tool_use", "id": "recover-read", "name": "lookup_order",
                     "input": {"order_id": "A-1001"}}],
        "usage": {"input_tokens": 3, "output_tokens": 2}}
    response_hash = _digest(response)
    with connect(service.dsn) as conn:
        seed_corpus(conn)
        assert mark_sending(conn, lease, request_id)
        assert record_response(conn, request_id, response=response, response_hash=response_hash,
                               stop_reason="tool_use", usage_tokens=5, usage_tools=1)

    class NeverSend:
        max_retries = 0
        def __call__(self, request):
            raise AssertionError("A durable saved response must be consumed, not resent")

    result = drive_provider_round(lambda: connect(service.dsn), lease,
        endpoint=endpoint, budget_account=account, provider=NeverSend(), mcp_tools=[],
        system_prompt="must not be used for recovery", model="ignored", max_rounds=4)
    assert result["status"] == "actions_proposed"
    with connect(service.dsn) as conn:
        assert conn.execute("SELECT count(*) AS n FROM provider_calls WHERE task_id=%s", (task_id,)).fetchone()["n"] == 1
        assert conn.execute("SELECT state FROM provider_calls WHERE request_id=%s", (request_id,)).fetchone()["state"] == "processed"
