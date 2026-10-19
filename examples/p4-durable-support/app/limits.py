"""Shared DB capacity and conservative usage accounting, independent of provider."""
from datetime import timedelta
from math import isfinite
from uuid import uuid4

from .worker import fence, Lease, transition


def acquire_provider(conn, lease, endpoint):
    task=fence(conn,lease)
    if not task:
        return None
    config=conn.execute('SELECT * FROM provider_endpoints WHERE id=%s FOR UPDATE',(endpoint,)).fetchone()
    if not config:
        raise ValueError('Unknown endpoint')
    conn.execute('DELETE FROM provider_slots WHERE endpoint=%s AND expires_at<=clock_timestamp()',(endpoint,))
    count=conn.execute('SELECT count(*) AS n FROM provider_slots WHERE endpoint=%s',(endpoint,)).fetchone()['n']
    eligible=conn.execute('SELECT next_retry_at IS NULL OR next_retry_at<=clock_timestamp() AS ok FROM tasks WHERE id=%s',(lease.task_id,)).fetchone()['ok']
    attempt=conn.execute('SELECT attempts FROM provider_attempts WHERE task_id=%s AND endpoint=%s',(lease.task_id,endpoint)).fetchone()
    if count>=config['concurrency_limit'] or not eligible or (attempt and attempt['attempts']>=config['max_attempts']):
        return None
    slot=uuid4()
    conn.execute('INSERT INTO provider_slots VALUES (%s,%s,%s,%s,%s,%s)',(slot,endpoint,lease.task_id,lease.owner,lease.epoch,task['lease_until']))
    conn.execute('INSERT INTO provider_attempts VALUES (%s,%s,1) ON CONFLICT(task_id,endpoint) DO UPDATE SET attempts=provider_attempts.attempts+1',(lease.task_id,endpoint))
    return slot


def schedule_429(conn, lease, endpoint, slot, *, retry_after, jitter):
    """Trusted adapter supplies parsed Retry-After and sampled jitter in [0,1].

    Fixture tests prove scheduling only, never actual provider rate-limit behavior.
    """
    if not all(isinstance(v,(int,float)) and isfinite(v) and v>=0 for v in (retry_after,jitter)) or jitter>1 or retry_after>300:
        raise ValueError('Invalid bounded retry interval')
    task=fence(conn,lease)
    if not task:
        return None
    owned=conn.execute('DELETE FROM provider_slots WHERE id=%s AND endpoint=%s AND task_id=%s AND owner=%s AND epoch=%s RETURNING id',
                       (slot,endpoint,lease.task_id,lease.owner,lease.epoch)).fetchone()
    if not owned:
        return None
    limit=conn.execute('SELECT max_attempts FROM provider_endpoints WHERE id=%s',(endpoint,)).fetchone()['max_attempts']
    attempt=conn.execute('SELECT attempts FROM provider_attempts WHERE task_id=%s AND endpoint=%s',(lease.task_id,endpoint)).fetchone()['attempts']
    now=conn.execute('SELECT clock_timestamp() AS now').fetchone()['now']
    retry=now+timedelta(seconds=retry_after+jitter)
    if retry>=task['deadline'] or attempt>=limit:
        transition(conn,lease,'failed')
        return None
    conn.execute('UPDATE tasks SET next_retry_at=%s WHERE id=%s',(retry,lease.task_id))
    from .db import append_event
    append_event(conn,lease.task_id,'provider.retry_scheduled',{'endpoint':endpoint,'attempt':attempt,'next_retry_at':retry.isoformat()})
    return retry


def reserve(conn, lease, account, *, tokens, tools):
    if any(not isinstance(v,int) or isinstance(v,bool) or v<0 for v in (tokens,tools)):
        raise ValueError('Non-negative integral reservation required')
    task=fence(conn,lease)
    if not task:
        return None
    row=conn.execute('''UPDATE budget_accounts SET reserved_tokens=reserved_tokens+%s,reserved_tools=reserved_tools+%s
        WHERE id=%s AND tenant_id=%s AND consumed_tokens+reserved_tokens+%s<=token_limit
          AND consumed_tools+reserved_tools+%s<=tool_limit RETURNING id''',
        (tokens,tools,account,task['tenant_id'],tokens,tools)).fetchone()
    if not row:
        return None
    reservation=uuid4()
    conn.execute('INSERT INTO budget_reservations(id,account,task_id,owner,epoch,tokens,tools) VALUES (%s,%s,%s,%s,%s,%s,%s)',
                 (reservation,account,lease.task_id,lease.owner,lease.epoch,tokens,tools))
    return reservation


def mark_sent(conn, reservation):
    row=conn.execute('SELECT * FROM budget_reservations WHERE id=%s',(reservation,)).fetchone()
    if not row or not fence(conn,Lease(row['task_id'],row['owner'],row['epoch'])):
        return False
    return bool(conn.execute("UPDATE budget_reservations SET sent=true WHERE id=%s AND state='reserved' AND NOT sent",(reservation,)).rowcount)


def reconcile(conn, reservation, *, tokens, tools):
    """Trusted usage settlement may arrive after the worker lease expires.

    Unknown any dimension retains the entire reservation. Actual overage is
    recorded faithfully and stops future reservations, never truncated to estimate.
    """
    if any(v is not None and (not isinstance(v,int) or isinstance(v,bool) or v<0) for v in (tokens,tools)):
        raise ValueError('Invalid actual usage')
    row=conn.execute('SELECT * FROM budget_reservations WHERE id=%s FOR UPDATE',(reservation,)).fetchone()
    if not row or not row['sent'] or row['state'] not in ('reserved','unknown'):
        return False
    if tokens is None or tools is None:
        conn.execute("UPDATE budget_reservations SET state='unknown' WHERE id=%s",(reservation,))
        return True
    conn.execute('UPDATE budget_accounts SET reserved_tokens=reserved_tokens-%s,reserved_tools=reserved_tools-%s,consumed_tokens=consumed_tokens+%s,consumed_tools=consumed_tools+%s WHERE id=%s',
                 (row['tokens'],row['tools'],tokens,tools,row['account']))
    conn.execute("UPDATE budget_reservations SET state='settled',actual_tokens=%s,actual_tools=%s WHERE id=%s",(tokens,tools,reservation))
    return True


def release_unsent(conn, reservation):
    row=conn.execute('SELECT * FROM budget_reservations WHERE id=%s FOR UPDATE',(reservation,)).fetchone()
    if not row or row['sent'] or row['state']!='reserved':
        return False
    conn.execute('UPDATE budget_accounts SET reserved_tokens=reserved_tokens-%s,reserved_tools=reserved_tools-%s WHERE id=%s',(row['tokens'],row['tools'],row['account']))
    conn.execute("UPDATE budget_reservations SET state='released' WHERE id=%s",(reservation,))
    return True


def budget_report(conn, account):
    row=conn.execute('SELECT * FROM budget_accounts WHERE id=%s',(account,)).fetchone()
    if not row:
        raise ValueError('Unknown account')
    return {**row,'available_tokens':max(0,row['token_limit']-row['consumed_tokens']-row['reserved_tokens']),
            'available_tools':max(0,row['tool_limit']-row['consumed_tools']-row['reserved_tools'])}


def release_provider(conn, lease, slot):
    """Release a completed request's slot without releasing task ownership."""
    if not fence(conn,lease):
        return False
    return bool(conn.execute('DELETE FROM provider_slots WHERE id=%s AND task_id=%s AND owner=%s AND epoch=%s',
                             (slot,lease.task_id,lease.owner,lease.epoch)).rowcount)
