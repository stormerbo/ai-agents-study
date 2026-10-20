"""Trusted local tool registry and durable independent action proposals.

Read tools reuse Stage 3 schema validation. The single write tool targets the
future *local synthetic* sink. No model-supplied risk/approval/identity is trusted.
"""
from hashlib import sha256
import json
from uuid import uuid4

from psycopg.types.json import Jsonb

from support_agent.tool_gateway import validate_tool_arguments, ALLOWED_TOOLS
from .db import append_event
from .worker import fence, checkpoint, transition


def schema(fields):
    return {'type':'object','properties':{name:{'type':'string'} for name in fields},
            'required':list(fields),'additionalProperties':False}


REGISTRY = {
    'lookup_order': ({**schema(('order_id',)), 'properties':{'order_id':{'type':'string','enum':['A-1001','A-1002']}}},False),
    'search_policy': (schema(('query',)),False),
    'send_notice': (schema(('resource_id','message')),True),
}
ACTION_TRANSITIONS = {
    'proposed': {'succeeded','invalidated','cancelled'},
    'waiting_approval': {'authorized_pending_delivery','authorized','denied','invalidated','cancelled'},
    'authorized_pending_delivery': {'authorized','invalidated','cancelled'},
    'authorized': {'dispatching','invalidated','cancelled'},
    'dispatching': {'unknown','succeeded'},
    'unknown': {'succeeded','failed','cancelled'},
    'failed':set(),
    'succeeded':set(), 'denied':set(), 'invalidated':set(), 'cancelled':set(),
}


def args_hash(args):
    return sha256(json.dumps(args,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def resource_scope(tool, args):
    if tool in ALLOWED_TOOLS:
        return args.get('order_id') if tool=='lookup_order' else 'policy-public'
    return args.get('resource_id')


def resource_access(conn, tenant_id, caller_id, resource_id):
    # Locks linearize permission changes with this authorization transaction.
    return conn.execute('''SELECT r.version,r.acl_version,p.version AS policy_version
      FROM resources r JOIN resource_acl a USING(tenant_id,resource_id)
      JOIN caller_identities u ON u.tenant_id=a.tenant_id AND u.caller_id=a.caller_id
      JOIN tenant_policies p ON p.tenant_id=r.tenant_id
      WHERE r.tenant_id=%s AND r.resource_id=%s AND a.caller_id=%s
      AND a.allowed AND u.active AND 'caller'=ANY(u.roles) AND r.deleted_at IS NULL
      FOR SHARE OF r,a,u,p''',(tenant_id,resource_id,caller_id)).fetchone()


def move_action(conn, action, status):
    if status not in ACTION_TRANSITIONS[action['status']]:
        raise ValueError('Invalid action transition')
    conn.execute('UPDATE actions SET status=%s WHERE id=%s',(status,action['id']))
    append_event(conn,action['task_id'],'action.'+status,{'action_id':str(action['id'])})


def propose_turn(conn, lease, calls, *, approval_seconds=300):
    task=fence(conn,lease)
    if not task:
        return []
    if not calls or not 0<approval_seconds<=3600:
        raise ValueError('Non-empty calls and bounded approval lifetime required')
    if task['checkpoint'].get('pending_action_ids'):
        raise ValueError('Resolve stored turn before proposing another')
    ids=[]
    turn_id=uuid4()
    waiting=False
    denied=False
    for position,call in enumerate(calls):
        tool=call.get('name','')
        args=call.get('input',{})
        registered=REGISTRY.get(tool)
        valid=registered is not None and validate_tool_arguments(registered[0],args)[0]
        access=resource_access(conn,task['tenant_id'],task['owner_id'],resource_scope(tool,args)) if valid else None
        requires=bool(registered and registered[1])
        status='waiting_approval' if access and requires else 'proposed' if access else 'denied'
        action_id=uuid4()
        conn.execute('''INSERT INTO actions(id,task_id,tenant_id,turn_epoch,turn_id,position,tool_call_id,tool,args,canonical_args_hash,
            resource_id,resource_version,acl_version,policy_version,requires_approval,status)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''',
            (action_id,lease.task_id,task['tenant_id'],lease.epoch,turn_id,position,call.get('id',''),tool,Jsonb(args),args_hash(args),
             resource_scope(tool,args) if access else None,access['version'] if access else None,
             access['acl_version'] if access else None,access['policy_version'] if access else None,requires,status))
        ids.append(action_id)
        append_event(conn,lease.task_id,'action.proposed',{'action_id':str(action_id),'status':status})
        if status=='waiting_approval':
            eligible=conn.execute("SELECT caller_id FROM caller_identities WHERE tenant_id=%s AND active AND 'approver'=ANY(roles) ORDER BY caller_id FOR SHARE LIMIT 1",(task['tenant_id'],)).fetchone()
            if not eligible:
                raise ValueError('No eligible approver')
            conn.execute('''INSERT INTO approvals(id,task_id,tenant_id,action_id,args_hash,resource_version,acl_version,policy_version,
                eligible_approver,requested_by,expires_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,LEAST(%s,clock_timestamp()+%s*interval '1 second'))''',
                (uuid4(),lease.task_id,task['tenant_id'],action_id,args_hash(args),access['version'],access['acl_version'],access['policy_version'],
                 eligible['caller_id'],task['owner_id'],task['deadline'],approval_seconds))
            waiting=True
        denied=denied or status=='denied'
    checkpoint(conn,lease,{'turn_id':str(turn_id),'pending_action_ids':[str(i) for i in ids]})
    if denied:
        transition(conn,lease,'failed')
    elif waiting:
        transition(conn,lease,'waiting_approval')
    return ids


def validate_frozen(conn, task, action):
    access=resource_access(conn,task['tenant_id'],task['owner_id'],action['resource_id'])
    registered=REGISTRY.get(action['tool'])
    if not access or not registered or not validate_tool_arguments(registered[0],action['args'])[0]:
        return False
    if action['resource_id']!=resource_scope(action['tool'],action['args']):
        return False
    if action['canonical_args_hash']!=args_hash(action['args']):
        return False
    if (action['resource_version'],action['acl_version'],action['policy_version'])!=(access['version'],access['acl_version'],access['policy_version']):
        return False
    if action['requires_approval']:
        approval=conn.execute('''SELECT a.* FROM approvals a JOIN caller_identities u
            ON u.tenant_id=a.tenant_id AND u.caller_id=a.eligible_approver
            WHERE a.action_id=%s AND a.tenant_id=%s AND a.status='approved'
            AND a.decided_by=a.eligible_approver AND a.expires_at>clock_timestamp()
            AND u.active AND 'caller'=ANY(u.roles) AND 'approver'=ANY(u.roles) FOR SHARE OF a,u''',
            (action['id'],task['tenant_id'])).fetchone()
        return bool(approval and (approval['args_hash'],approval['resource_version'],approval['acl_version'],approval['policy_version'])==
                    (action['canonical_args_hash'],action['resource_version'],action['acl_version'],action['policy_version']))
    return True


def authorize_action(conn, lease, action_id):
    """Task 3 must replace this boundary with atomic authorization+outbox insert.

    authorized_pending_delivery is explicitly not a dispatchable state.
    """
    task=fence(conn,lease)
    if not task:
        return 0
    action=conn.execute('SELECT * FROM actions WHERE id=%s AND task_id=%s FOR UPDATE',(action_id,lease.task_id)).fetchone()
    if not action or action['status']!='waiting_approval':
        return 0
    if not validate_frozen(conn,task,action):
        move_action(conn,action,'invalidated')
        return 0
    move_action(conn,action,'authorized_pending_delivery')
    return 1
