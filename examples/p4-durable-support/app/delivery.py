"""Short DB transactions around HTTP, durable unknown outcomes and reconciliation.

Only the local synthetic receiver's explicit versioned dedup contract permits
retry. No exceptions or HTTP response bodies are copied into task event logs.
"""
import argparse
from urllib.parse import urlsplit
from uuid import UUID

import httpx

from .actions import args_hash
from .db import connect
from . import outbox
from .services import SINK_CONTRACT


HEADERS={'Authorization':'Bearer local-only-sink'}


def sink_url(url):
    parsed=urlsplit(url)
    if parsed.scheme!='http' or parsed.hostname not in ('127.0.0.1','localhost','sink') or parsed.username or parsed.password or parsed.path not in ('','/') or parsed.query or parsed.fragment:
        raise ValueError('Only a local synthetic sink base URL is supported')
    return url.rstrip('/')


def receipt_for(response, dispatch):
    data=response.json()
    if not isinstance(data,dict):
        raise ValueError('Receiver response must be an object')
    receipt=data.get('receipt')
    if data.get('contract')!=SINK_CONTRACT or not isinstance(receipt,dict):
        raise ValueError('Unproven receiver receipt contract')
    expected={'external_key':dispatch.external_key,'action_id':str(dispatch.action_id),
        'tenant_id':dispatch.payload['tenant_id'],'payload_hash':args_hash(dispatch.payload),'outcome':'applied'}
    if any(receipt.get(k)!=v for k,v in expected.items()):
        raise ValueError('Receipt does not match frozen action')
    if not isinstance(receipt.get('receipt_id'),str):
        raise ValueError('Receipt id must be a UUID string')
    receipt_id=str(UUID(receipt['receipt_id']))
    return {**expected,'receipt_id':receipt_id}


def unknown(dsn, dispatch):
    with connect(dsn) as conn:
        outbox.mark_unknown(conn,dispatch)
    return 'unknown'


def send(dsn, dispatch, url, checkpoint):
    try:
        response=httpx.post(url+'/v1/notices',json=dispatch.payload,headers=HEADERS,timeout=5,trust_env=False)
        response.raise_for_status()
        receipt=receipt_for(response,dispatch)
    except (httpx.HTTPError,ValueError,KeyError,TypeError):
        return unknown(dsn,dispatch)
    checkpoint('after_sink_commit_before_receipt')
    with connect(dsn) as conn:
        saved=outbox.save_receipt(conn,dispatch,receipt)
    return 'succeeded' if saved else 'unknown'


def dispatch_once(dsn, lease, action_id, url, *, checkpoint=lambda phase:None):
    url=sink_url(url)
    checkpoint('before_claim')
    with connect(dsn) as conn:
        dispatch=outbox.claim(conn,lease,action_id)
    if not dispatch:
        return 'unavailable'
    checkpoint('after_claim_before_send')
    return send(dsn,dispatch,url,checkpoint)


def reconcile(dsn, action_id, url, *, checkpoint=lambda phase:None):
    """Claim expired unknown work, query first, retry only with receiver proof.

    A missing/failed/malformed lookup leaves reconciling. The frozen request may
    already have escaped, even when cancellation/permission changed meanwhile.
    """
    url=sink_url(url)
    with connect(dsn) as conn:
        dispatch=outbox.recover(conn,action_id)
    if not dispatch:
        return 'unavailable'
    try:
        response=httpx.get(url+'/v1/receipts/'+dispatch.external_key,headers=HEADERS,timeout=5,trust_env=False)
        if response.status_code==200:
            receipt=receipt_for(response,dispatch)
            with connect(dsn) as conn:
                saved=outbox.save_receipt(conn,dispatch,receipt)
            return 'succeeded' if saved else 'unknown'
        data=response.json()
        if response.status_code!=404 or not isinstance(data,dict) or data.get('contract')!=SINK_CONTRACT or data.get('safe_retry') is not True or data.get('external_key')!=dispatch.external_key:
            return unknown(dsn,dispatch)
    except (httpx.HTTPError,ValueError,KeyError,TypeError):
        return unknown(dsn,dispatch)
    with connect(dsn) as conn:
        if not outbox.retry_intent(conn,dispatch):
            return 'unknown'
    checkpoint('after_query_before_retry')
    return send(dsn,dispatch,url,checkpoint)


def main():
    from .config import Settings
    from .worker import claim
    parser=argparse.ArgumentParser(description='One-shot local synthetic delivery or unknown reconciliation')
    parser.add_argument('command',choices=['dispatch','reconcile'])
    parser.add_argument('--action',type=UUID,required=True)
    parser.add_argument('--sink',default='http://127.0.0.1:8002')
    parser.add_argument('--owner',default='local-dispatcher')
    args=parser.parse_args()
    dsn=Settings.from_env().database_url
    if args.command=='reconcile':
        result=reconcile(dsn,args.action,args.sink)
    else:
        with connect(dsn) as conn:
            row=conn.execute('SELECT task_id FROM actions WHERE id=%s',(args.action,)).fetchone()
            lease=claim(conn,args.owner,task_id=row['task_id']) if row else None
            if lease:
                outbox.schedule(conn,lease,args.action)
        result=dispatch_once(dsn,lease,args.action,args.sink) if lease else 'unavailable'
    print(result)


if __name__=='__main__':
    main()
