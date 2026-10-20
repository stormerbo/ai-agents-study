"""Transactional scheduling and the committed dispatch authorization boundary.

Helpers own no commits. Lock order is task → action → outbox → authorization.
Worker fence applies to scheduling/initial claim. Dispatch tokens, not worker
leases, fence unknown-outcome recovery after a committed claim.
"""
from dataclasses import dataclass
from uuid import UUID, uuid4

from psycopg.types.json import Jsonb

from .actions import validate_frozen, move_action
from .db import append_event
from .worker import fence, release_slots, transition


@dataclass(frozen=True)
class Dispatch:
    action_id: UUID
    task_id: UUID
    token: UUID
    external_key: str
    payload: dict


def payload_for(action):
    return {'external_key':f"p4-notice:{action['id']}",'action_id':str(action['id']),
            'tenant_id':action['tenant_id'],'args':action['args']}


def schedule(conn, lease, action_id):
    """Atomic authorized action + queued outbox; stale workers affect zero rows."""
    task=fence(conn,lease)
    if not task:
        return 0
    action=conn.execute('SELECT * FROM actions WHERE id=%s AND task_id=%s FOR UPDATE',(action_id,lease.task_id)).fetchone()
    if not action or action['status'] not in ('waiting_approval','authorized_pending_delivery'):
        return 0
    valid=action['tool']=='send_notice' and action['requires_approval'] and validate_frozen(conn,task,action)
    # Authorization row locks may have waited beyond the lease/deadline.
    if not fence(conn,lease):
        return 0
    if not valid:
        if not transition(conn,lease,'failed'):
            return 0
        move_action(conn,action,'invalidated')
        return 0
    payload=payload_for(action)
    move_action(conn,action,'authorized')
    conn.execute('''INSERT INTO outbox(action_id,task_id,tenant_id,external_key,payload,scheduled_epoch)
        VALUES (%s,%s,%s,%s,%s,%s)''',
        (action_id,lease.task_id,task['tenant_id'],payload['external_key'],Jsonb(payload),lease.epoch))
    append_event(conn,lease.task_id,'outbox.queued',{'action_id':str(action_id)})
    return 1


def locked(conn, action_id):
    found=conn.execute('SELECT task_id FROM outbox WHERE action_id=%s',(action_id,)).fetchone()
    if not found:
        return None,None,None
    task=conn.execute('SELECT * FROM tasks WHERE id=%s FOR UPDATE',(found['task_id'],)).fetchone()
    action=conn.execute('SELECT * FROM actions WHERE id=%s FOR UPDATE',(action_id,)).fetchone()
    row=conn.execute('SELECT *,claim_until<=clock_timestamp() AS expired FROM outbox WHERE action_id=%s FOR UPDATE',(action_id,)).fetchone()
    return task,action,row


def claim(conn, lease, action_id, *, claim_seconds=30):
    if not 0<claim_seconds<=300:
        raise ValueError('Bounded dispatch lease required')
    task=fence(conn,lease)
    if not task:
        return None
    task,action,row=locked(conn,action_id)
    if not row or task['id']!=lease.task_id or row['status']!='queued' or action['status']!='authorized':
        return None
    valid=row['payload']==payload_for(action) and validate_frozen(conn,task,action)
    if not fence(conn,lease):
        return None
    if not valid:
        if not transition(conn,lease,'failed'):
            return None
        move_action(conn,action,'invalidated')
        conn.execute("UPDATE outbox SET status='invalidated' WHERE action_id=%s",(action_id,))
        return None
    # Require the fenced state transition before mutating dispatch intent. All
    # authorization locks are already held; no network crosses this transaction.
    if not transition(conn,lease,'reconciling'):
        return None
    token=uuid4()
    move_action(conn,action,'dispatching')
    conn.execute("""UPDATE outbox SET status='dispatching',dispatch_token=%s,
        claim_until=clock_timestamp()+%s*interval '1 second',attempts=attempts+1 WHERE action_id=%s""",
        (token,claim_seconds,action_id))
    # From this commit, cancellation cannot promise retraction. No long DB locks
    # cross HTTP; worker leases deliberately stop being usable for new work.
    return Dispatch(action_id,task['id'],token,row['external_key'],row['payload'])


def current(conn, dispatch):
    task,action,row=locked(conn,dispatch.action_id)
    if not row or row['dispatch_token']!=dispatch.token or row['expired'] or row['status'] not in ('dispatching','unknown'):
        return None,None,None
    return task,action,row


def mark_unknown(conn, dispatch):
    task,action,row=current(conn,dispatch)
    if not row:
        return 0
    if action['status']=='dispatching':
        move_action(conn,action,'unknown')
    conn.execute("UPDATE outbox SET status='unknown',claim_until=clock_timestamp() WHERE action_id=%s",(dispatch.action_id,))
    return 1


def recover(conn, action_id, *, claim_seconds=30):
    """Acquire expired dispatch/unknown capability; never repeat authorization."""
    if not 0<claim_seconds<=300:
        raise ValueError('Bounded reconciliation lease required')
    task,action,row=locked(conn,action_id)
    if not row or row['status'] not in ('dispatching','unknown') or not row['expired']:
        return None
    if task['status']!='reconciling':
        return None
    if action['status']=='dispatching':
        move_action(conn,action,'unknown')
    token=uuid4()
    conn.execute("""UPDATE outbox SET status='unknown',dispatch_token=%s,
        claim_until=clock_timestamp()+%s*interval '1 second' WHERE action_id=%s""",(token,claim_seconds,action_id))
    append_event(conn,task['id'],'outbox.reconciliation_query',{'action_id':str(action_id)})
    return Dispatch(action_id,task['id'],token,row['external_key'],row['payload'])


def retry_intent(conn, dispatch):
    task,action,row=current(conn,dispatch)
    if not row:
        return 0
    conn.execute('UPDATE outbox SET attempts=attempts+1 WHERE action_id=%s',(dispatch.action_id,))
    append_event(conn,task['id'],'outbox.idempotent_retry',{'action_id':str(dispatch.action_id)})
    return 1


def save_receipt(conn, dispatch, receipt):
    task,action,row=current(conn,dispatch)
    if not row:
        return 0
    conn.execute("UPDATE outbox SET status='succeeded',receipt=%s,claim_until=NULL WHERE action_id=%s",(Jsonb(receipt),dispatch.action_id))
    conn.execute('UPDATE actions SET result=%s WHERE id=%s',(Jsonb(receipt),dispatch.action_id))
    move_action(conn,action,'succeeded')
    append_event(conn,task['id'],'outbox.receipt_saved',{'action_id':str(dispatch.action_id),'external_key':dispatch.external_key})
    pending=conn.execute("SELECT 1 FROM outbox WHERE task_id=%s AND status IN ('dispatching','unknown') LIMIT 1",(task['id'],)).fetchone()
    if pending:
        return 1
    # Preserve prior real tool results; never turn a receipt into model output.
    checkpoint=dict(task['checkpoint'])
    checkpoint['pending_action_ids']=[i for i in checkpoint.get('pending_action_ids',[]) if i!=str(dispatch.action_id)]
    results=list(checkpoint.get('tool_results',[]))
    results.append({'action_id':str(dispatch.action_id),'tool_call_id':action['tool_call_id'],'result':receipt})
    checkpoint['tool_results']=results
    if task['cancel_requested']:
        status,kind='cancelled','task.cancelled'
    elif conn.execute("SELECT 1 FROM actions WHERE task_id=%s AND status IN ('denied','invalidated','cancelled') LIMIT 1",(task['id'],)).fetchone():
        status,kind='failed','task.failed'
    else:
        status,kind='queued','task.delivery_resolved'
    conn.execute('''UPDATE tasks SET status=%s,checkpoint=%s,state_version=state_version+1,
        lease_owner=NULL,lease_until=NULL WHERE id=%s''',(status,Jsonb(checkpoint),task['id']))
    release_slots(conn,task['id'])
    append_event(conn,task['id'],kind,{'boundary':'claimed_effect_receipt_confirmed'})
    return 1
