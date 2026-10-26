"""Durable provider boundary and bounded model-round driver.

The adapter is injected and must declare ``max_retries = 0``. Provider calls
never run while a PostgreSQL transaction is open. Tool execution, approval,
and delivery remain explicit calls into the P4 runtime/outbox boundaries.
"""
from __future__ import annotations

from hashlib import sha256
import json
from uuid import UUID, uuid4

from app.actions import REGISTRY, validate_frozen
from app.limits import acquire_provider, release_provider, reserve, release_unsent
from app.provider_calls import mark_sending, mark_unknown, prepare, record_response
from app.worker import fence
from support_agent.providers import _plain, _value
from support_agent.tool_gateway import ALLOWED_TOOLS

MAX_TOOL_SCHEMA_BYTES = 65536


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def trusted_provider_tools(mcp_tools):
    """Build schemas from P4's registry; require exact peer agreement for reads."""
    peer = {}
    for item in mcp_tools:
        name = _value(item, "name")
        if not isinstance(name, str) or name in peer:
            raise ValueError("MCP tool names must be unique strings")
        peer[name] = _plain(_value(item, "inputSchema", _value(item, "input_schema")))
    tools = []
    for name, (schema, requires_approval) in REGISTRY.items():
        if name in ALLOWED_TOOLS:
            if peer.get(name) != schema:
                raise ValueError(f"MCP schema mismatch for registered read tool: {name}")
        encoded = _canonical(schema).encode("utf-8")
        if len(encoded) > MAX_TOOL_SCHEMA_BYTES:
            raise ValueError("Trusted tool schema exceeds size limit")
        tools.append({
            "name": name,
            "description": "Read-only synthetic lookup." if not requires_approval else "Approval-gated synthetic notice; never dispatch directly.",
            "input_schema": schema,
        })
    return tools


def _usage(response):
    usage = _value(response, "usage", {}) or {}
    dimensions = [_value(usage, field) for field in (
        "input_tokens", "output_tokens", "cache_creation_input_tokens", "cache_read_input_tokens",
    )]
    # Anthropic's input_tokens is only the uncached remainder. Missing/null or
    # malformed cache dimensions are unknown, never silently treated as zero.
    valid = all(isinstance(value, int) and not isinstance(value, bool) and value >= 0
                for value in dimensions)
    tokens = sum(dimensions) if valid else None
    content = _value(response, "content", []) or []
    tool_count = sum(1 for block in content if _value(block, "type") == "tool_use")
    return tokens, tool_count


def _request_sources_current(conn, lease, request):
    """Reauthorize every stored tool result at both prepare and send boundaries."""
    from app.worker import fence
    task = fence(conn, lease)
    if not task:
        return False
    identity = conn.execute("""SELECT 1 FROM caller_identities WHERE tenant_id=%s AND caller_id=%s
        AND active AND 'caller'=ANY(roles) FOR SHARE""", (task["tenant_id"], task["owner_id"])).fetchone()
    if not identity:
        return False
    messages = request.get("messages") if isinstance(request, dict) else None
    if not isinstance(messages, list):
        return False
    results = []
    for message in messages:
        if not isinstance(message, dict):
            continue
        content = message.get("content")
        if not isinstance(content, list):
            continue
        results.extend(block for block in content if isinstance(block, dict) and block.get("type") == "tool_result")
    seen = set()
    for result in results:
        tool_id = result.get("tool_use_id")
        if not isinstance(tool_id, str) or not tool_id or tool_id in seen:
            return False
        seen.add(tool_id)
        action = conn.execute("SELECT * FROM actions WHERE task_id=%s AND tool_call_id=%s FOR SHARE",
                              (lease.task_id, tool_id)).fetchone()
        if (not action or action["status"] != "succeeded" or action["result"] is None
                or result.get("content") != _canonical(action["result"])
                or not validate_frozen(conn, task, action)):
            return False
        if action["tool"] == "send_notice":
            receipt = conn.execute("SELECT 1 FROM outbox WHERE action_id=%s AND status='succeeded' AND receipt IS NOT NULL",
                                   (action["id"],)).fetchone()
            if not receipt:
                return False
    return True


def perform_provider_call(conn_factory, lease, *, request_id: UUID, endpoint: str,
                          release_id: str, model: str, request: dict,
                          budget_account: str, reserved_tokens: int, reserved_tools: int,
                          provider, round_index: int = 0):
    """Prepare, commit send intent, call once, then durably save response/usage.

    Returns the normalized JSON response, or ``None`` for a transport ambiguity.
    A saved response is consumed by a separate currently fenced transaction.
    """
    if getattr(provider, "max_retries", None) != 0 or not callable(provider):
        raise ValueError("Provider adapter must be callable and declare max_retries=0")
    request_hash = sha256(_canonical(request).encode("utf-8")).hexdigest()
    slot = reservation = None
    with conn_factory() as conn:
        if not _request_sources_current(conn, lease, request):
            return None
        slot = acquire_provider(conn, lease, endpoint)
        if slot is None:
            return None
        reservation = reserve(conn, lease, budget_account, tokens=reserved_tokens, tools=reserved_tools)
        if reservation is None:
            release_provider(conn, lease, slot)
            return None
        if not prepare(conn, lease, request_id=request_id, endpoint=endpoint, slot_id=slot,
                       reservation_id=reservation, release_id=release_id, model=model,
                       request=request, request_hash=request_hash, round_index=round_index):
            release_unsent(conn, reservation)
            release_provider(conn, lease, slot)
            return None
    # Exiting the context above commits prepared; sending is a separate committed transition.
    with conn_factory() as conn:
        if not _request_sources_current(conn, lease, request):
            from app.provider_calls import abandon_prepared
            abandon_prepared(conn, lease, request_id)
            return None
        if not mark_sending(conn, lease, request_id):
            return None
    try:
        response = _plain(provider(request))
        if not isinstance(response, dict):
            raise ValueError("Provider adapter must return an object response")
    except Exception:
        with conn_factory() as conn:
            mark_unknown(conn, request_id)
        return None
    tokens, tool_count = _usage(response)
    response_hash = sha256(_canonical(response).encode("utf-8")).hexdigest()
    try:
        with conn_factory() as conn:
            if not record_response(conn, request_id, response=response,
                                   response_hash=response_hash,
                                   stop_reason=_value(response, "stop_reason", "") or "",
                                   usage_tokens=tokens, usage_tools=tool_count):
                return None
    except Exception:
        # The provider may have answered even though persistence failed. Leave the
        # durable send intent ambiguous; recovery cannot replay it automatically.
        return None
    return response


def build_continuation(conn, lease, request_id: UUID):
    """Rebuild the next Messages turn from immutable response and action results."""
    from app.provider_calls import get_call
    from support_agent.tool_gateway import MAX_TOOL_CALLS

    from app.worker import fence
    call = get_call(conn, request_id)
    task = fence(conn, lease)
    if not task or not call or call["task_id"] != lease.task_id or call["state"] != "processed" or call["stop_reason"] != "tool_use":
        raise ValueError("Only a processed tool-use response can continue")
    response = call["response_body"]
    blocks = response.get("content")
    if not isinstance(blocks, list):
        raise ValueError("Saved assistant content is missing")
    tool_blocks = [block for block in blocks if isinstance(block, dict) and block.get("type") == "tool_use"]
    tool_ids = [block.get("id") for block in tool_blocks]
    if not tool_ids or len(tool_ids) > MAX_TOOL_CALLS or any(not isinstance(item, str) or not item for item in tool_ids):
        raise ValueError("Saved tool-use ids are invalid")
    if len(set(tool_ids)) != len(tool_ids):
        raise ValueError("Saved tool-use ids are duplicated")
    actions = conn.execute("""SELECT a.*,o.status AS delivery_status,o.receipt AS delivery_receipt
        FROM actions a LEFT JOIN outbox o ON o.action_id=a.id
        WHERE a.task_id=%s AND a.turn_id=%s""", (call["task_id"], request_id)).fetchall()
    by_tool_id = {action["tool_call_id"]: action for action in actions}
    if len(actions) != len(tool_ids) or len(by_tool_id) != len(tool_ids) or set(by_tool_id) != set(tool_ids):
        raise ValueError("Saved action mapping does not match assistant tool-use ids")
    results = []
    for tool_id in tool_ids:
        action = by_tool_id[tool_id]
        if (action["status"] != "succeeded" or action["result"] is None
                or not validate_frozen(conn, task, action)
                or (action["tool"] == "send_notice" and
                    (action["delivery_status"] != "succeeded" or action["delivery_receipt"] is None))):
            raise ValueError("Every tool-use id needs a currently authorized durable result")
        results.append({"type": "tool_result", "tool_use_id": tool_id,
                        "content": _canonical(action["result"])})
    request = call["request_body"]
    messages = request.get("messages") if isinstance(request, dict) else None
    if not isinstance(messages, list):
        raise ValueError("Saved request messages are missing")
    continuation = [*messages, {"role": "assistant", "content": blocks}, {"role": "user", "content": results}]
    if len(_canonical(continuation).encode("utf-8")) > 262144:
        raise ValueError("Durable conversation exceeds request size limit")
    if not _request_sources_current(conn, lease, {"messages": continuation}):
        raise ValueError("Conversation includes a revoked or stale tool result")
    return continuation


def next_provider_request(conn, lease):
    """Select the only safe next driver step from durable task/provider state.

    A saved response must be consumed before planning; an interrupted/unknown
    send is never replayed; a processed tool turn waits until every frozen
    action has a durable result. Only then is its exact continuation returned.
    """
    task = fence(conn, lease)
    if not task:
        return {"status": "stale"}
    call = conn.execute("""SELECT * FROM provider_calls WHERE task_id=%s
        ORDER BY round_index DESC LIMIT 1""", (lease.task_id,)).fetchone()
    if call is None:
        prompt = task["input"].get("prompt") if isinstance(task["input"], dict) else None
        if not isinstance(prompt, str) or not prompt.strip():
            return {"status": "invalid_task_input"}
        return {"status": "initial", "round_index": 0, "release_id": task["release_id"], "prompt": prompt}
    if call["state"] in {"prepared", "sending", "unknown", "response_saved", "failed"}:
        return {"status": call["state"], "request_id": str(call["request_id"])}
    if call["state"] != "processed" or call["stop_reason"] != "tool_use":
        return {"status": "terminal", "request_id": str(call["request_id"])}
    pending = task["checkpoint"].get("pending_action_ids", [])
    if not isinstance(pending, list) or pending:
        return {"status": "actions_pending", "request_id": str(call["request_id"])}
    try:
        messages = build_continuation(conn, lease, call["request_id"])
    except ValueError:
        return {"status": "continuation_rejected", "request_id": str(call["request_id"])}
    request = dict(call["request_body"])
    request["messages"] = messages
    return {"status": "ready", "request_id": str(call["request_id"]),
            "round_index": call["round_index"] + 1, "release_id": call["release_id"],
            "endpoint": call["endpoint"], "model": call["model"], "request": request}


def drive_provider_round(conn_factory, lease, *, endpoint, budget_account, provider,
                         mcp_tools, system_prompt, model, max_tokens=512,
                         max_rounds=4, reserved_tokens=4096, reserved_tools=4):
    """Execute one bounded provider round or recover the saved response.

    Tool execution, approval, and external delivery remain explicit separate
    steps. Reinvoking after those steps advances from durable action results;
    this function never replans an unresolved/approved tool turn.
    """
    from app.runtime import consume_saved_response
    if (not isinstance(max_rounds, int) or isinstance(max_rounds, bool) or not 1 <= max_rounds <= 32
            or not isinstance(max_tokens, int) or isinstance(max_tokens, bool) or not 1 <= max_tokens <= 8192
            or not isinstance(system_prompt, str) or not system_prompt.strip() or len(system_prompt) > 20000):
        raise ValueError("Bounded rounds, output tokens, and non-empty system prompt are required")
    with conn_factory() as conn:
        state = next_provider_request(conn, lease)
    if state["status"] == "response_saved":
        with conn_factory() as conn:
            return consume_saved_response(conn, lease, UUID(state["request_id"]))
    if state["status"] not in {"initial", "ready"}:
        return state
    if state["round_index"] >= max_rounds:
        from app.worker import transition
        with conn_factory() as conn:
            transition(conn, lease, "failed")
        return {"status": "round_limit"}
    if state["status"] == "initial":
        provider_tools = trusted_provider_tools(mcp_tools)
        request = {"model": model, "max_tokens": max_tokens, "system": system_prompt,
                   "messages": [{"role": "user", "content": state["prompt"]}],
                   "tools": provider_tools}
        call_endpoint = endpoint
        call_model = model
        release_id = state["release_id"]
    else:
        request = state["request"]
        call_endpoint = state["endpoint"]
        call_model = state["model"]
        release_id = state["release_id"]
    run_config = {
        "endpoint": call_endpoint,
        "model": call_model,
        "release_id": release_id,
        "budget_account": budget_account,
        "max_rounds": max_rounds,
        "max_tokens": request["max_tokens"],
        "reserved_tokens": reserved_tokens,
        "reserved_tools": reserved_tools,
        "system_hash": sha256(str(request.get("system", "")).encode("utf-8")).hexdigest(),
        "tools_hash": sha256(_canonical(request.get("tools", [])).encode("utf-8")).hexdigest(),
    }
    from app.worker import checkpoint, fence
    with conn_factory() as conn:
        task = fence(conn, lease)
        if not task:
            return {"status": "stale"}
        saved_config = task["checkpoint"].get("provider_run_config")
        if saved_config is None:
            if state["status"] != "initial":
                return {"status": "run_config_missing"}
            if not checkpoint(conn, lease, {**task["checkpoint"], "provider_run_config": run_config}):
                return {"status": "stale"}
        elif saved_config != run_config:
            return {"status": "run_config_mismatch"}
    request_id = uuid4()
    response = perform_provider_call(conn_factory, lease, request_id=request_id,
        endpoint=call_endpoint, release_id=release_id, model=call_model, request=request,
        budget_account=budget_account, reserved_tokens=reserved_tokens,
        reserved_tools=reserved_tools, provider=provider, round_index=state["round_index"])
    if response is None:
        with conn_factory() as conn:
            row = conn.execute("SELECT state FROM provider_calls WHERE request_id=%s", (request_id,)).fetchone()
        return {"status": row["state"] if row else "admission_denied", "request_id": str(request_id)}
    with conn_factory() as conn:
        result = consume_saved_response(conn, lease, request_id)
    return {**result, "request_id": str(request_id), "round_index": state["round_index"]}


async def resume_agent_turn(conn_factory, lease, *, mcp_session, delivery_dsn, sink_url,
                            endpoint, budget_account, provider, mcp_tools, system_prompt,
                            model, max_tokens=512, max_rounds=4,
                            reserved_tokens=4096, reserved_tools=4):
    """Coordinate one fenced task wake-up across reads, approval and delivery.

    A wake-up may send at most one external write. Dispatch commits a state
    transition that releases this worker lease, so remaining outbox rows and
    model continuation require a successor claim. Unknown dispatches are left
    for the explicit P4 reconciliation path; this coordinator never retries or
    calls the model while any frozen action remains unresolved.
    """
    from app.delivery import dispatch_once
    from app.runtime import execute_reads

    with conn_factory() as conn:
        task = fence(conn, lease)
        if not task:
            return {"status": "stale"}
        pending_ids = task["checkpoint"].get("pending_action_ids", [])
        if not isinstance(pending_ids, list):
            return {"status": "invalid_pending_actions"}
        if pending_ids:
            await execute_reads(conn, lease, mcp_session, budget_account=budget_account)

    with conn_factory() as conn:
        task = fence(conn, lease)
        if not task:
            return {"status": "stale"}
        pending_ids = task["checkpoint"].get("pending_action_ids", [])
        if not isinstance(pending_ids, list):
            return {"status": "invalid_pending_actions"}
        action_ids = [UUID(item) for item in pending_ids]
        actions = conn.execute("""SELECT * FROM actions WHERE task_id=%s AND id=ANY(%s::uuid[])
            ORDER BY position FOR UPDATE""", (lease.task_id, action_ids)).fetchall() if action_ids else []
        if len(actions) != len(action_ids):
            return {"status": "missing_action"}
        if any(action["status"] in {"denied", "invalidated", "failed", "cancelled"} for action in actions):
            return {"status": "action_failed"}
        for action in actions:
            if action["status"] == "authorized_pending_delivery":
                from app.outbox import schedule
                if not schedule(conn, lease, action["id"]):
                    return {"status": "delivery_schedule_rejected", "action_id": str(action["id"])}

        # Reuse an already committed outbox item after a crash between schedule
        # and dispatch. Never recreate it or dispatch more than one per lease.
        queued = conn.execute("""SELECT o.action_id FROM outbox o
            JOIN actions a ON a.id=o.action_id
            WHERE o.task_id=%s AND o.status='queued' AND a.status='authorized'
            ORDER BY a.position LIMIT 1""", (lease.task_id,)).fetchone()
        unresolved = conn.execute("""SELECT id,status FROM actions WHERE task_id=%s
            AND status NOT IN ('succeeded','denied','invalidated','failed','cancelled')
            ORDER BY position""", (lease.task_id,)).fetchall()
        if queued:
            action_id = queued["action_id"]
        elif unresolved:
            status = unresolved[0]["status"]
            if status == "waiting_approval":
                return {"status": "waiting_approval", "action_id": str(unresolved[0]["id"])}
            if status == "proposed":
                return {"status": "read_actions_pending"}
            return {"status": "actions_pending", "action_id": str(unresolved[0]["id"]),
                    "action_status": status}
        elif action_ids:
            # The action list was resolved in this wake-up. The checkpoint may
            # still be stale only if a concurrent transition has occurred.
            task = fence(conn, lease)
            if not task or task["checkpoint"].get("pending_action_ids"):
                return {"status": "actions_pending"}
            action_id = None
        else:
            action_id = None

    if action_id is not None:
        outcome = dispatch_once(delivery_dsn, lease, action_id, sink_url)
        mapped = {"succeeded": "delivery_succeeded", "unknown": "reconciling",
                  "unavailable": "delivery_unavailable"}.get(outcome, "delivery_unavailable")
        return {"status": mapped, "action_id": str(action_id)}

    return drive_provider_round(conn_factory, lease, endpoint=endpoint,
        budget_account=budget_account, provider=provider, mcp_tools=mcp_tools,
        system_prompt=system_prompt, model=model, max_tokens=max_tokens,
        max_rounds=max_rounds, reserved_tokens=reserved_tokens,
        reserved_tools=reserved_tools)
