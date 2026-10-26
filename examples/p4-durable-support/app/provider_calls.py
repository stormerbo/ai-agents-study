"""Durable provider request lifecycle; caller owns every transaction.

The network boundary belongs to the host: commit ``mark_sending`` before
performing HTTP. A lost owner can mark a sending request unknown, never retry
it. A late response can settle that request's usage without a task lease, but
only a current lease can move the saved response into task processing.
"""
from __future__ import annotations

from hashlib import sha256
import json
from uuid import UUID

from psycopg.types.json import Jsonb

from .limits import reconcile, release_unsent
from .worker import Lease, fence
from .db import append_event

MAX_REQUEST_BYTES = 262144
MAX_RESPONSE_BYTES = 1048576


def _canonical(value):
    try:
        encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ValueError("Provider call payload must be finite JSON") from exc
    return encoded


def _check_digest(value, supplied, label):
    digest = sha256(_canonical(value).encode("utf-8")).hexdigest()
    if not isinstance(supplied, str) or supplied != digest:
        raise ValueError(f"{label} hash does not match canonical payload")
    return digest


def prepare(conn, lease: Lease, *, request_id: UUID, endpoint: str, slot_id: UUID,
            reservation_id: UUID, release_id: str, model: str, request: dict,
            request_hash: str, round_index: int = 0):
    """Persist immutable request identity and resource bindings while fenced."""
    if not isinstance(request_id, UUID) or not isinstance(slot_id, UUID) or not isinstance(reservation_id, UUID):
        raise ValueError("UUID request, provider slot, and reservation identities are required")
    if not isinstance(round_index, int) or isinstance(round_index, bool) or round_index < 0:
        raise ValueError("Non-negative integer round index required")
    if not isinstance(request, dict):
        raise ValueError("Provider request must be a JSON object")
    digest = _check_digest(request, request_hash, "Request")
    if len(_canonical(request).encode("utf-8")) > MAX_REQUEST_BYTES:
        raise ValueError("Provider request exceeds durable size limit")
    task = fence(conn, lease)
    if not task or task["release_id"] != release_id:
        return False

    old = conn.execute("SELECT * FROM provider_calls WHERE request_id=%s FOR UPDATE", (request_id,)).fetchone()
    if old:
        return bool(old["task_id"] == lease.task_id and old["round_index"] == round_index
                    and old["endpoint"] == endpoint and old["release_id"] == release_id
                    and old["model"] == model and old["owner"] == lease.owner
                    and old["epoch"] == lease.epoch and old["provider_slot_id"] == slot_id
                    and old["reservation_id"] == reservation_id and old["request_hash"] == digest
                    and old["request_body"] == request and old["state"] == "prepared")

    slot = conn.execute("""SELECT id FROM provider_slots WHERE id=%s AND endpoint=%s AND task_id=%s
        AND owner=%s AND epoch=%s AND expires_at>clock_timestamp() FOR UPDATE""",
        (slot_id, endpoint, lease.task_id, lease.owner, lease.epoch)).fetchone()
    reservation = conn.execute("""SELECT r.id FROM budget_reservations r
        JOIN budget_accounts b ON b.id=r.account JOIN tasks t ON t.id=r.task_id
        WHERE r.id=%s AND r.task_id=%s AND r.owner=%s AND r.epoch=%s AND r.state='reserved'
          AND NOT r.sent AND b.tenant_id=t.tenant_id FOR UPDATE OF r""",
        (reservation_id, lease.task_id, lease.owner, lease.epoch)).fetchone()
    if not slot or not reservation:
        return False
    inserted = conn.execute("""INSERT INTO provider_calls
            (request_id,task_id,round_index,endpoint,release_id,model,owner,epoch,provider_slot_id,
             reservation_id,request_hash,request_body)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT DO NOTHING RETURNING request_id""",
            (request_id, lease.task_id, round_index, endpoint, release_id, model, lease.owner,
             lease.epoch, slot_id, reservation_id, digest, Jsonb(request))).fetchone()
    return inserted is not None


def abandon_prepared(conn, lease: Lease, request_id: UUID):
    """Fenced successor releases a request proven never to have crossed send."""
    if not fence(conn, lease):
        return False
    row = conn.execute("SELECT * FROM provider_calls WHERE request_id=%s FOR UPDATE", (request_id,)).fetchone()
    if (not row or row["task_id"] != lease.task_id or row["state"] != "prepared"
            or lease.epoch < row["epoch"]
            or (lease.epoch == row["epoch"] and lease.owner != row["owner"])):
        return False
    reservation = conn.execute("SELECT sent,state FROM budget_reservations WHERE id=%s FOR UPDATE",
                               (row["reservation_id"],)).fetchone()
    if not reservation or reservation["sent"] or reservation["state"] != "reserved":
        return False
    if not release_unsent(conn, row["reservation_id"]):
        return False
    conn.execute("DELETE FROM provider_slots WHERE id=%s AND task_id=%s", (row["provider_slot_id"], lease.task_id))
    conn.execute("UPDATE provider_calls SET state='failed' WHERE request_id=%s AND state='prepared'", (request_id,))
    append_event(conn, lease.task_id, "provider.call_abandoned", {
        "request_id": str(request_id), "prepared_epoch": row["epoch"], "recovery_epoch": lease.epoch,
    })
    return True


def mark_sending(conn, lease: Lease, request_id: UUID):
    """Make the send intent durable; caller must commit before any network I/O."""
    task = fence(conn, lease)
    if not task:
        return False
    row = conn.execute("SELECT * FROM provider_calls WHERE request_id=%s FOR UPDATE", (request_id,)).fetchone()
    if not row or row["task_id"] != lease.task_id or row["owner"] != lease.owner or row["epoch"] != lease.epoch or row["state"] != "prepared":
        return False
    slot = conn.execute("""SELECT id FROM provider_slots WHERE id=%s AND task_id=%s AND owner=%s
        AND epoch=%s AND expires_at>clock_timestamp() FOR UPDATE""",
        (row["provider_slot_id"], lease.task_id, lease.owner, lease.epoch)).fetchone()
    reservation = conn.execute("""SELECT id FROM budget_reservations WHERE id=%s AND task_id=%s
        AND owner=%s AND epoch=%s AND state='reserved' AND NOT sent FOR UPDATE""",
        (row["reservation_id"], lease.task_id, lease.owner, lease.epoch)).fetchone()
    if not slot or not reservation:
        return False
    conn.execute("UPDATE budget_reservations SET sent=true WHERE id=%s", (row["reservation_id"],))
    conn.execute("UPDATE provider_calls SET state='sending',sending_at=clock_timestamp() WHERE request_id=%s", (request_id,))
    return True


def mark_unknown(conn, request_id: UUID):
    """Record ambiguous delivery. This state has no transition back to sending."""
    row = conn.execute("SELECT * FROM provider_calls WHERE request_id=%s FOR UPDATE", (request_id,)).fetchone()
    if not row or row["state"] != "sending":
        return False
    if not reconcile(conn, row["reservation_id"], tokens=None, tools=None):
        return False
    conn.execute("UPDATE provider_calls SET state='unknown' WHERE request_id=%s AND state='sending'", (request_id,))
    return True


def record_response(conn, request_id: UUID, *, response: dict, response_hash: str,
                    stop_reason: str, usage_tokens: int | None, usage_tools: int | None):
    """Idempotently persist a response and settle usage, even after lease loss."""
    if not isinstance(response, dict):
        raise ValueError("Provider response must be a JSON object")
    digest = _check_digest(response, response_hash, "Response")
    if len(_canonical(response).encode("utf-8")) > MAX_RESPONSE_BYTES:
        raise ValueError("Provider response exceeds durable size limit")
    if not isinstance(stop_reason, str) or not stop_reason or len(stop_reason) > 100:
        raise ValueError("Bounded provider stop reason required")
    for usage in (usage_tokens, usage_tools):
        if usage is not None and (not isinstance(usage, int) or isinstance(usage, bool) or usage < 0):
            raise ValueError("Usage dimensions must be non-negative integers or unknown")
    row = conn.execute("SELECT * FROM provider_calls WHERE request_id=%s FOR UPDATE", (request_id,)).fetchone()
    if not row:
        return False
    if row["state"] in ("response_saved", "processed"):
        if not (row["response_hash"] == digest and row["response_body"] == response
                and row["stop_reason"] == stop_reason
                and (usage_tokens is None or row["usage_tokens"] is None or row["usage_tokens"] == usage_tokens)
                and (usage_tools is None or row["usage_tools"] is None or row["usage_tools"] == usage_tools)):
            return False
        tokens = row["usage_tokens"] if row["usage_tokens"] is not None else usage_tokens
        tools = row["usage_tools"] if row["usage_tools"] is not None else usage_tools
        if tokens == row["usage_tokens"] and tools == row["usage_tools"]:
            return True
        if tokens is not None and tools is not None:
            if not reconcile(conn, row["reservation_id"], tokens=tokens, tools=tools):
                return False
        conn.execute("UPDATE provider_calls SET usage_tokens=%s,usage_tools=%s WHERE request_id=%s",
                     (tokens, tools, request_id))
        return True
    if row["state"] not in ("sending", "unknown"):
        return False
    if not reconcile(conn, row["reservation_id"], tokens=usage_tokens, tools=usage_tools):
        return False
    conn.execute("""UPDATE provider_calls SET state='response_saved',response_hash=%s,response_body=%s,
        stop_reason=%s,usage_tokens=%s,usage_tools=%s,response_at=clock_timestamp() WHERE request_id=%s""",
        (digest, Jsonb(response), stop_reason, usage_tokens, usage_tools, request_id))
    conn.execute("DELETE FROM provider_slots WHERE id=%s", (row["provider_slot_id"],))
    return True


def mark_processed(conn, lease: Lease, request_id: UUID):
    """Consume permission is fenced independently from late response settlement."""
    if not fence(conn, lease):
        return False
    row = conn.execute("SELECT * FROM provider_calls WHERE request_id=%s FOR UPDATE", (request_id,)).fetchone()
    if not row or row["task_id"] != lease.task_id or row["state"] != "response_saved":
        return False
    # A successor may consume the response, but the original request epoch is
    # retained as provenance and is never rewritten.
    conn.execute("UPDATE provider_calls SET state='processed',processed_at=clock_timestamp() WHERE request_id=%s", (request_id,))
    return True


def get_call(conn, request_id: UUID):
    return conn.execute("SELECT * FROM provider_calls WHERE request_id=%s", (request_id,)).fetchone()
