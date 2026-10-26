"""Durable provider response consumption survives task-owner changes."""
import hashlib
import json
import uuid

import pytest
from pathlib import Path
import sys

P5 = Path(__file__).resolve().parents[2] / "p5-agent-delivery"
if str(P5) not in sys.path:
    sys.path.insert(0, str(P5))

from app.db import connect
from app.provider_calls import mark_sending, record_response
from app.runtime import consume_saved_response
from test_provider_calls import _prepared

pytestmark = pytest.mark.integration


def _response(value):
    return value, hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def test_tool_response_is_consumed_once_into_actions_with_request_identity(service):
    from app.provider_calls import get_call

    task_id, lease, endpoint, account, slot, reservation, request_id, request, digest, release_id = _prepared(service)
    from app.retrieval import seed_corpus
    with connect(service.dsn) as conn:
        seed_corpus(conn)
    response, response_hash = _response({"id": "tool-response", "stop_reason": "tool_use",
        "content": [{"type": "tool_use", "id": "lookup-1", "name": "lookup_order", "input": {"order_id": "A-1001"}}],
        "usage": {"input_tokens": 10, "output_tokens": 5}})
    with connect(service.dsn) as conn:
        assert mark_sending(conn, lease, request_id)
        assert record_response(conn, request_id, response=response, response_hash=response_hash,
                               stop_reason="tool_use", usage_tokens=15, usage_tools=1)
    with connect(service.dsn) as conn:
        result = consume_saved_response(conn, lease, request_id)
        assert result["status"] == "actions_proposed"
        action = conn.execute("SELECT * FROM actions WHERE task_id=%s", (task_id,)).fetchone()
        assert action["tool_call_id"] == "lookup-1"
        assert str(action["turn_id"]) == str(request_id)
        assert conn.execute("SELECT state FROM provider_calls WHERE request_id=%s", (request_id,)).fetchone()["state"] == "processed"
        checkpoint = conn.execute("SELECT checkpoint FROM tasks WHERE id=%s", (task_id,)).fetchone()["checkpoint"]
        assert checkpoint["provider_request_id"] == str(request_id)
        assert checkpoint["pending_action_ids"] == [str(action["id"])]


def test_truncated_response_fails_closed_and_cannot_complete_task(service):
    task_id, lease, endpoint, account, slot, reservation, request_id, request, digest, release_id = _prepared(service)
    response, response_hash = _response({"id": "truncated", "stop_reason": "max_tokens", "content": []})
    with connect(service.dsn) as conn:
        assert mark_sending(conn, lease, request_id)
        assert record_response(conn, request_id, response=response, response_hash=response_hash,
                               stop_reason="max_tokens", usage_tokens=10, usage_tools=0)
    with connect(service.dsn) as conn:
        assert consume_saved_response(conn, lease, request_id)["status"] == "failed"
        assert conn.execute("SELECT status FROM tasks WHERE id=%s", (task_id,)).fetchone()["status"] == "failed"
        assert conn.execute("SELECT task_id FROM final_outputs WHERE task_id=%s", (task_id,)).fetchone() is None


def test_continuation_replays_exact_assistant_blocks_and_tool_result_ids(service):
    from app.provider_calls import get_call
    from app.runtime import consume_saved_response
    from host import build_continuation
    from psycopg.types.json import Jsonb

    task_id, lease, endpoint, account, slot, reservation, request_id, request, digest, release_id = _prepared(service)
    from app.retrieval import seed_corpus
    with connect(service.dsn) as conn:
        seed_corpus(conn)
    assistant_blocks = [
        {"type": "thinking", "thinking": "brief reasoning", "signature": "synthetic-signature"},
        {"type": "tool_use", "id": "tool-id-7", "name": "lookup_order", "input": {"order_id": "A-1001"}},
    ]
    response, response_hash = _response({"id": "response-turn", "stop_reason": "tool_use", "content": assistant_blocks})
    with connect(service.dsn) as conn:
        assert mark_sending(conn, lease, request_id)
        assert record_response(conn, request_id, response=response, response_hash=response_hash,
                               stop_reason="tool_use", usage_tokens=11, usage_tools=1)
    with connect(service.dsn) as conn:
        assert consume_saved_response(conn, lease, request_id)["status"] == "actions_proposed"
        conn.execute("UPDATE actions SET status='succeeded',result=%s WHERE task_id=%s", (Jsonb({"status": "shipped"}), task_id))
        from app.worker import checkpoint
        checkpoint(conn, lease, {"pending_action_ids": []})
        messages = build_continuation(conn, lease, request_id)
        assert messages[1] == {"role": "assistant", "content": assistant_blocks}
        assert messages[2]["content"] == [{"type": "tool_result", "tool_use_id": "tool-id-7", "content": '{"status":"shipped"}'}]


def test_resume_driver_waits_for_saved_response_and_resolved_actions_before_next_round(service):
    from app.retrieval import seed_corpus
    from host import next_provider_request
    from psycopg.types.json import Jsonb

    task_id, lease, endpoint, account, slot, reservation, request_id, request, digest, release_id = _prepared(service)
    assistant_blocks = [{"type": "tool_use", "id": "resume-read", "name": "lookup_order",
                         "input": {"order_id": "A-1001"}}]
    response, response_hash = _response({"id": "resume-response", "stop_reason": "tool_use",
        "content": assistant_blocks, "usage": {"input_tokens": 4, "output_tokens": 3}})
    with connect(service.dsn) as conn:
        seed_corpus(conn)
        assert mark_sending(conn, lease, request_id)
        assert record_response(conn, request_id, response=response, response_hash=response_hash,
                               stop_reason="tool_use", usage_tokens=7, usage_tools=1)
    with connect(service.dsn) as conn:
        assert next_provider_request(conn, lease)["status"] == "response_saved"
        assert consume_saved_response(conn, lease, request_id)["status"] == "actions_proposed"
    with connect(service.dsn) as conn:
        waiting = next_provider_request(conn, lease)
        assert waiting == {"status": "actions_pending", "request_id": str(request_id)}
        action = conn.execute("SELECT * FROM actions WHERE task_id=%s", (task_id,)).fetchone()
        conn.execute("UPDATE actions SET status='succeeded',result=%s WHERE id=%s",
                     (Jsonb({"status": "shipped"}), action["id"]))
        task = conn.execute("SELECT checkpoint FROM tasks WHERE id=%s", (task_id,)).fetchone()
        from app.worker import checkpoint
        checkpoint(conn, lease, {**task["checkpoint"], "pending_action_ids": []})
        ready = next_provider_request(conn, lease)
        assert ready["status"] == "ready"
        assert ready["round_index"] == 1
        assert ready["request"]["messages"] == [
            *request["messages"],
            {"role": "assistant", "content": assistant_blocks},
            {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "resume-read",
                                               "content": '{"status":"shipped"}'}]},
        ]


def test_provider_refusal_is_persisted_as_terminal_refusal_output(service):
    task_id, lease, endpoint, account, slot, reservation, request_id, request, digest, release_id = _prepared(service)
    response, response_hash = _response({"id": "refusal-1", "stop_reason": "refusal",
        "content": [{"type": "refusal", "refusal": "I cannot perform that request."}]})
    with connect(service.dsn) as conn:
        assert mark_sending(conn, lease, request_id)
        assert record_response(conn, request_id, response=response, response_hash=response_hash,
                               stop_reason="refusal", usage_tokens=12, usage_tools=0)
    with connect(service.dsn) as conn:
        assert consume_saved_response(conn, lease, request_id)["status"] == "completed"
        task = conn.execute("SELECT status FROM tasks WHERE id=%s", (task_id,)).fetchone()
        output = conn.execute("SELECT output FROM final_outputs WHERE task_id=%s", (task_id,)).fetchone()["output"]
        assert task["status"] == "completed"
        assert output == {"outcome": "refuse", "text": "I cannot perform that request.", "citations": []}


def test_revoked_read_result_cannot_be_rebuilt_or_sent_in_next_model_round(service):
    from app.db import connect
    from app.worker import claim
    from app.provider_calls import get_call
    from app.runtime import consume_saved_response
    from app.retrieval import revoke, seed_corpus
    from app.actions import REGISTRY
    from host import build_continuation, perform_provider_call
    from psycopg.types.json import Jsonb

    task_id, lease, endpoint, account, slot, reservation, request_id, request, digest, release_id = _prepared(service)
    with connect(service.dsn) as conn:
        seed_corpus(conn)
        baseline_acl_version = conn.execute(
            "SELECT acl_version FROM resources WHERE tenant_id='tenant-a' AND resource_id='A-1001'"
        ).fetchone()["acl_version"]
    response, response_hash = _response({"id": "response-read", "stop_reason": "tool_use",
        "content": [{"type": "tool_use", "id": "revoked-tool", "name": "lookup_order", "input": {"order_id": "A-1001"}}]})
    with connect(service.dsn) as conn:
        assert mark_sending(conn, lease, request_id)
        assert record_response(conn, request_id, response=response, response_hash=response_hash,
                               stop_reason="tool_use", usage_tokens=5, usage_tools=1)
    with connect(service.dsn) as conn:
        assert consume_saved_response(conn, lease, request_id)["status"] == "actions_proposed"
        action = conn.execute("SELECT * FROM actions WHERE task_id=%s", (task_id,)).fetchone()
        conn.execute("UPDATE actions SET status='succeeded',result=%s WHERE id=%s", (Jsonb({"private": "order state"}), action["id"]))
        messages = build_continuation(conn, lease, request_id)
        assert messages[-1]["content"][0]["tool_use_id"] == "revoked-tool"
    class Adapter:
        max_retries = 0
        calls = 0
        def __call__(self, body):
            self.calls += 1
            raise AssertionError("provider must not receive revoked tool data")
    adapter = Adapter()
    next_request = {"model": "fixture", "messages": messages, "tools": []}
    connections = 0
    def revoke_before_send():
        nonlocal connections
        connections += 1
        if connections == 2:
            with connect(service.dsn) as conn:
                revoke(conn, "tenant-a", "A-1001", "alice")
        return connect(service.dsn)
    next_id = uuid.uuid4()
    try:
        assert perform_provider_call(revoke_before_send, lease, request_id=next_id,
            endpoint=endpoint, release_id=release_id, model="fixture", request=next_request,
            budget_account=account, reserved_tokens=10, reserved_tools=1, provider=adapter, round_index=1) is None
        assert adapter.calls == 0
        with connect(service.dsn) as conn:
            call = conn.execute("SELECT state,reservation_id FROM provider_calls WHERE request_id=%s", (next_id,)).fetchone()
            assert call["state"] == "failed"
            assert conn.execute("SELECT state FROM budget_reservations WHERE id=%s", (call["reservation_id"],)).fetchone()["state"] == "released"
    finally:
        # The authorization race must be visible to a separate transaction while
        # it runs, but this shared integration database must retain its corpus for
        # later tests. Restore the exact baseline so active index ACL versions stay coherent.
        with connect(service.dsn) as conn:
            conn.execute("UPDATE resource_acl SET allowed=true WHERE tenant_id='tenant-a' AND resource_id='A-1001' AND caller_id='alice'")
            conn.execute("UPDATE resources SET acl_version=%s WHERE tenant_id='tenant-a' AND resource_id='A-1001'",
                         (baseline_acl_version,))
