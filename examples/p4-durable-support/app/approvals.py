"""Authenticated approval decisions and owner cancellation; no delivery semantics."""
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict

from .actions import REGISTRY, args_hash
from .api import authorized_connection
from .db import append_event, owned_task
from .worker import release_slots

router=APIRouter()
REVIEWABLE_FIELDS = {'send_notice': ('resource_id', 'message')}


def conflict(message):
    raise HTTPException(409,detail={'code':'approval_conflict','message':message})


class Decision(BaseModel):
    model_config=ConfigDict(extra='forbid')
    decision: Literal['approved','denied']


@router.get('/v1/tasks/{task_id}/approvals')
def list_approvals(task_id:UUID,context=Depends(authorized_connection,scope='function')):
    conn,principal=context
    owned_task(conn,principal,task_id)
    rows=conn.execute('SELECT id,action_id,status,expires_at,eligible_approver,decided_by FROM approvals WHERE task_id=%s AND tenant_id=%s ORDER BY id',(task_id,principal.tenant_id)).fetchall()
    return {'approvals':rows}


@router.get('/v1/approvals/{approval_id}/review')
def review_approval(approval_id:UUID,context=Depends(authorized_connection,scope='function')):
    conn,principal=context
    if 'approver' not in principal.roles:
        raise HTTPException(404,detail={'code':'not_found','message':'Approval not found'})
    row=conn.execute('''SELECT a.id,a.task_id,a.status,a.eligible_approver,a.requested_by,a.expires_at,a.args_hash,
        a.resource_version AS approved_resource_version,a.acl_version AS approved_acl_version,
        a.policy_version AS approved_policy_version,
        x.id AS action_id,x.tool,x.args,x.canonical_args_hash,x.resource_id,x.resource_version,x.acl_version,
        x.policy_version,x.requires_approval
        FROM approvals a JOIN actions x ON x.id=a.action_id AND x.tenant_id=a.tenant_id
        WHERE a.id=%s AND a.tenant_id=%s AND a.eligible_approver=%s''',
        (approval_id,principal.tenant_id,principal.caller_id)).fetchone()
    if not row:
        raise HTTPException(404,detail={'code':'not_found','message':'Approval not found'})
    if row['status']!='pending':
        conflict('Approval is no longer pending')
    if not isinstance(row['args'],dict):
        conflict('Action arguments do not match the trusted schema')
    actual_hash=args_hash(row['args'])
    if (row['args_hash']!=actual_hash or row['canonical_args_hash']!=actual_hash or not row['requires_approval'] or
        (row['resource_version'],row['acl_version'],row['policy_version'])!=(
            row['approved_resource_version'],row['approved_acl_version'],row['approved_policy_version'])):
        conflict('Approval does not match the frozen action')
    schema=REGISTRY.get(row['tool'])
    fields=REVIEWABLE_FIELDS.get(row['tool'])
    if not schema or not schema[1] or not fields or any(field not in schema[0]['properties'] for field in fields):
        conflict('Action has no trusted review projection')
    if set(row['args'])!=set(schema[0]['properties']):
        conflict('Action arguments do not match the trusted schema')
    return {
        'approval': {
            'id':row['id'],'task_id':row['task_id'],'status':row['status'],
            'eligible_approver':row['eligible_approver'],'requested_by':row['requested_by'],
            'expires_at':row['expires_at'],'args_hash':row['args_hash'],
        },
        'action': {
            'id':row['action_id'],'tool':row['tool'],
            'arguments':{field:row['args'][field] for field in fields},
            'resource_id':row['resource_id'],'resource_version':row['resource_version'],
            'acl_version':row['acl_version'],'policy_version':row['policy_version'],
            'canonical_args_hash':row['canonical_args_hash'],
        },
    }


@router.post('/v1/approvals/{approval_id}/decision')
def decide(approval_id:UUID,payload:Decision,context=Depends(authorized_connection,scope='function')):
    conn,principal=context
    # Lookup does not expose cross-tenant existence. Lock task before approval:
    # same lock order as worker/resume/cancel, avoiding approval/task deadlocks.
    found=conn.execute('SELECT task_id FROM approvals WHERE id=%s AND tenant_id=%s',(approval_id,principal.tenant_id)).fetchone()
    if not found:
        raise HTTPException(404,detail={'code':'not_found','message':'Approval not found'})
    if 'approver' not in principal.roles:
        raise HTTPException(403,detail={'code':'approver_required','message':'Current approver role required'})
    task=conn.execute('SELECT *,deadline<=clock_timestamp() AS expired FROM tasks WHERE id=%s FOR UPDATE',(found['task_id'],)).fetchone()
    row=conn.execute('SELECT *,expires_at<=clock_timestamp() AS expired FROM approvals WHERE id=%s FOR UPDATE',(approval_id,)).fetchone()
    if row['eligible_approver']!=principal.caller_id:
        raise HTTPException(403,detail={'code':'approver_required','message':'Approval assigned to another principal'})
    if row['status']!='pending' or row['expired'] or task['status']!='waiting_approval' or task['cancel_requested'] or task['expired']:
        conflict('Approval already decided, expired or task stopped')
    conn.execute('UPDATE approvals SET status=%s,decided_by=%s,decided_at=clock_timestamp() WHERE id=%s',(payload.decision,principal.caller_id,approval_id))
    append_event(conn,task['id'],'approval.'+payload.decision,{'approval_id':str(approval_id)})
    if payload.decision=='denied':
        conn.execute("UPDATE actions SET status='denied' WHERE id=%s",(row['action_id'],))
        conn.execute("UPDATE tasks SET status='failed',state_version=state_version+1 WHERE id=%s",(task['id'],))
        append_event(conn,task['id'],'task.failed',{'reason':'approval_denied'})
    elif not conn.execute("SELECT 1 FROM approvals WHERE task_id=%s AND status='pending'",(task['id'],)).fetchone():
        conn.execute("UPDATE tasks SET status='queued',state_version=state_version+1 WHERE id=%s",(task['id'],))
        append_event(conn,task['id'],'task.approval_ready',{})
    return {'id':row['id'],'status':payload.decision}


@router.post('/v1/tasks/{task_id}/cancel')
def cancel(task_id:UUID,context=Depends(authorized_connection,scope='function')):
    conn,principal=context
    owned_task(conn,principal,task_id)
    task=conn.execute('SELECT * FROM tasks WHERE id=%s FOR UPDATE',(task_id,)).fetchone()
    if task['status'] in ('completed','failed','cancelled'):
        raise HTTPException(409,detail={'code':'task_terminal','message':'Task already terminal'})
    # Task lock serializes this operation with queued → dispatching. A committed
    # claim may still send; cancellation cannot turn that promise into retraction.
    active=conn.execute("SELECT 1 FROM outbox WHERE task_id=%s AND status IN ('dispatching','unknown') LIMIT 1",(task_id,)).fetchone()
    status='reconciling' if active else 'cancelled'
    conn.execute('UPDATE tasks SET status=%s,cancel_requested=true,state_version=state_version+1,lease_owner=NULL,lease_until=NULL WHERE id=%s',(status,task_id))
    conn.execute("UPDATE actions SET status='cancelled' WHERE task_id=%s AND status IN ('proposed','waiting_approval','authorized_pending_delivery','authorized')",(task_id,))
    conn.execute("UPDATE outbox SET status='cancelled' WHERE task_id=%s AND status='queued'",(task_id,))
    conn.execute("UPDATE approvals SET status='cancelled' WHERE task_id=%s AND status='pending'",(task_id,))
    release_slots(conn,task_id)
    append_event(conn,task_id,'task.cancel_requested' if active else 'task.cancelled',
                 {'boundary':'claimed_effect_requires_reconciliation' if active else 'before_dispatch_claim'})
    return {'id':task_id,'status':status}
