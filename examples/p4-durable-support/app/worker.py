"""Durable task ownership. Every mutating helper uses the same row-lock fence.

The caller owns the transaction: no helper commits independently. Task 3 must use
fence() in the same transaction as action/outbox writes, including dispatch claim.
A lease cannot retract a network request already sent.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from uuid import UUID

from psycopg.types.json import Jsonb

from .db import append_event, connect


@dataclass(frozen=True)
class Lease:
    task_id: UUID
    owner: str
    epoch: int


TRANSITIONS = {
    'queued': {'running','failed','cancelled'},
    'running': {'waiting_approval','reconciling','completed','failed','cancelled'},
    'waiting_approval': {'running','failed','cancelled'},
    'reconciling': {'running','failed','cancelled'},
    'completed': set(), 'failed': set(), 'cancelled': set(),
}


def fence(conn, lease: Lease):
    """Lock current task, then check live DB time (not transaction start time).

    Return None for stale/expired/cancelled ownership before *any* child write.
    Holding this row lock serializes with takeover, cancel and approval decisions.
    """
    row = conn.execute('SELECT * FROM tasks WHERE id=%s FOR UPDATE', (lease.task_id,)).fetchone()
    if row is None or row['lease_owner'] != lease.owner or row['execution_epoch'] != lease.epoch:
        return None
    valid = conn.execute("SELECT lease_until>clock_timestamp() AND deadline>clock_timestamp() AND NOT cancel_requested AND status='running' AS valid FROM tasks WHERE id=%s", (lease.task_id,)).fetchone()
    return row if valid['valid'] else None


def release_slots(conn, task_id):
    conn.execute('DELETE FROM task_slots WHERE task_id=%s', (task_id,))
    conn.execute('DELETE FROM provider_slots WHERE task_id=%s', (task_id,))


def expire_deadlines(conn):
    rows = conn.execute("SELECT id FROM tasks WHERE deadline<=clock_timestamp() AND status IN ('queued','running','waiting_approval') FOR UPDATE").fetchall()
    for row in rows:
        task_id = row['id']
        active_effect = conn.execute("SELECT 1 FROM outbox WHERE task_id=%s AND status IN ('dispatching','unknown') LIMIT 1", (task_id,)).fetchone()
        if active_effect:
            # A possibly sent effect must be reconciled even after the task deadline.
            conn.execute("UPDATE tasks SET status='reconciling',state_version=state_version+1,lease_owner=NULL,lease_until=NULL WHERE id=%s", (task_id,))
            release_slots(conn, task_id)
            append_event(conn, task_id, 'task.deadline_reconciling', {'boundary':'possible_external_effect'})
            continue
        approvals = conn.execute("UPDATE approvals SET status='cancelled' WHERE task_id=%s AND status='pending'", (task_id,)).rowcount
        actions = conn.execute("UPDATE actions SET status='cancelled' WHERE task_id=%s AND status IN ('proposed','waiting_approval','authorized_pending_delivery','authorized')", (task_id,)).rowcount
        outbox = conn.execute("UPDATE outbox SET status='cancelled' WHERE task_id=%s AND status='queued'", (task_id,)).rowcount
        conn.execute("UPDATE tasks SET status='failed',state_version=state_version+1,lease_owner=NULL,lease_until=NULL WHERE id=%s", (task_id,))
        release_slots(conn,row['id'])
        append_event(conn,task_id,'task.deadline_expired',{
            'approvals_cancelled': approvals,
            'actions_cancelled': actions,
            'outbox_cancelled': outbox,
        })
    return len(rows)


def claim(conn, owner, *, task_id=None, lease_seconds=30):
    if not owner or not 0 < lease_seconds <= 300:
        raise ValueError('Invalid owner or lease duration')
    # Global capacity uses one lock; task locks always follow it.
    conn.execute('SELECT pg_advisory_xact_lock(4002001)')
    expire_deadlines(conn)
    conn.execute('''DELETE FROM task_slots s WHERE expires_at<=clock_timestamp() OR NOT EXISTS
        (SELECT 1 FROM tasks t WHERE t.id=s.task_id AND t.lease_owner=s.owner AND t.execution_epoch=s.epoch
         AND t.lease_until>clock_timestamp() AND t.status='running' AND NOT t.cancel_requested)''')
    conn.execute('DELETE FROM provider_slots WHERE expires_at<=clock_timestamp()')
    cap = conn.execute('SELECT task_limit FROM service_limits WHERE singleton').fetchone()['task_limit']
    if conn.execute('SELECT count(*) AS n FROM task_slots').fetchone()['n'] >= cap:
        return None
    row = conn.execute("""SELECT * FROM tasks WHERE (%s::uuid IS NULL OR id=%s)
        AND status IN ('queued','running') AND NOT cancel_requested
        AND deadline>clock_timestamp() AND (next_retry_at IS NULL OR next_retry_at<=clock_timestamp())
        AND (lease_until IS NULL OR lease_until<=clock_timestamp())
        ORDER BY created_at FOR UPDATE SKIP LOCKED LIMIT 1""", (task_id,task_id)).fetchone()
    if row is None:
        return None
    row = conn.execute("""UPDATE tasks SET lease_owner=%s,lease_until=clock_timestamp()+%s*interval '1 second',
        execution_epoch=execution_epoch+1,status='running',state_version=state_version+1 WHERE id=%s RETURNING *""",
        (owner,lease_seconds,row['id'])).fetchone()
    conn.execute('INSERT INTO task_slots VALUES (%s,%s,%s,%s) ON CONFLICT(task_id) DO UPDATE SET owner=excluded.owner,epoch=excluded.epoch,expires_at=excluded.expires_at',
                 (row['id'],owner,row['execution_epoch'],row['lease_until']))
    append_event(conn,row['id'],'task.claimed',{'epoch':row['execution_epoch']})
    return Lease(row['id'],owner,row['execution_epoch'])


def release(conn, lease: Lease) -> bool:
    """Release one completed wake-up so its successor need not wait for lease expiry.

    The task row lock serializes release with takeover and side-effect fences. The
    owner/epoch predicate prevents an old worker from releasing a successor's lease.
    """
    row = conn.execute('SELECT * FROM tasks WHERE id=%s FOR UPDATE', (lease.task_id,)).fetchone()
    if row is None or row['lease_owner'] != lease.owner or row['execution_epoch'] != lease.epoch or row['status'] != 'running':
        return False
    conn.execute('DELETE FROM task_slots WHERE task_id=%s AND owner=%s AND epoch=%s',
                 (lease.task_id, lease.owner, lease.epoch))
    conn.execute('DELETE FROM provider_slots WHERE task_id=%s AND owner=%s AND epoch=%s',
                 (lease.task_id, lease.owner, lease.epoch))
    conn.execute('UPDATE tasks SET lease_owner=NULL,lease_until=NULL,state_version=state_version+1 WHERE id=%s',
                 (lease.task_id,))
    append_event(conn, lease.task_id, 'task.lease_released', {'epoch': lease.epoch})
    return True


def renew(conn, lease, lease_seconds=30):
    if not 0 < lease_seconds <= 300:
        raise ValueError('Invalid lease duration')
    if not fence(conn,lease):
        return False
    until = conn.execute("UPDATE tasks SET lease_until=LEAST(deadline,clock_timestamp()+%s*interval '1 second') WHERE id=%s RETURNING lease_until",(lease_seconds,lease.task_id)).fetchone()['lease_until']
    conn.execute('UPDATE task_slots SET expires_at=%s WHERE task_id=%s AND owner=%s AND epoch=%s',(until,lease.task_id,lease.owner,lease.epoch))
    conn.execute('UPDATE provider_slots SET expires_at=%s WHERE task_id=%s AND owner=%s AND epoch=%s',(until,lease.task_id,lease.owner,lease.epoch))
    return True


def checkpoint(conn, lease, data):
    if not fence(conn,lease):
        return 0
    return conn.execute('UPDATE tasks SET checkpoint=%s,state_version=state_version+1 WHERE id=%s',(Jsonb(data),lease.task_id)).rowcount


def emit(conn, lease, kind, payload):
    if not fence(conn,lease):
        return 0
    append_event(conn,lease.task_id,kind,payload)
    return 1


def transition(conn, lease, status):
    row = fence(conn,lease)
    if not row:
        return 0
    if status not in TRANSITIONS[row['status']]:
        raise ValueError('Invalid task transition')
    if status=='completed':
        unresolved = conn.execute("SELECT 1 FROM actions WHERE task_id=%s AND status!='succeeded' LIMIT 1",(lease.task_id,)).fetchone()
        if unresolved:
            raise ValueError('Completion requires all actions resolved')
        durable_output = conn.execute('SELECT 1 FROM final_outputs WHERE task_id=%s',(lease.task_id,)).fetchone()
        if not durable_output:
            raise ValueError('Completion requires validated output in durable storage')
        # Completion has one trusted entry point (runtime.finalize_output), which
        # validates and stores output in the same transaction as this transition.
        raise ValueError('Use finalize_output to complete a task')
    conn.execute('UPDATE tasks SET status=%s,state_version=state_version+1 WHERE id=%s',(status,lease.task_id))
    if status != 'running':
        release_slots(conn,lease.task_id)
        conn.execute('UPDATE tasks SET lease_owner=NULL,lease_until=NULL WHERE id=%s',(lease.task_id,))
    append_event(conn,lease.task_id,'task.'+status,{})
    return 1


def main():
    from .config import Settings
    parser = argparse.ArgumentParser(description='Claim a durable task; no implicit provider calls or external dispatch')
    parser.add_argument('--once',action='store_true',required=True)
    parser.add_argument('--owner',required=True)
    parser.add_argument('--task',type=UUID)
    args=parser.parse_args()
    with connect(Settings.from_env().database_url) as conn:
        lease=claim(conn,args.owner,task_id=args.task)
    print('claimed' if lease else 'no runnable task')


if __name__=='__main__':
    main()
