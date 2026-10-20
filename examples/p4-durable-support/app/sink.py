"""Durable *synthetic* notice receiver. No real messages or customer systems.

The receipt/dedup key and local effect commit in a receiver transaction before
HTTP success. This explicit contract is the only basis for safe write retries.
"""
import hmac
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, model_validator
from psycopg.types.json import Jsonb

from .actions import args_hash
from .config import Settings
from .db import connect
from .services import SINK_CONTRACT


class NoticeArgs(BaseModel):
    model_config=ConfigDict(extra='forbid')
    resource_id: str=Field(min_length=1,max_length=200)
    message: str=Field(min_length=1,max_length=8000)


class Notice(BaseModel):
    model_config=ConfigDict(extra='forbid')
    external_key: str
    action_id: UUID
    tenant_id: str=Field(pattern=r'^tenant-[ab]$')
    args: NoticeArgs

    @model_validator(mode='after')
    def stable_key(self):
        if self.external_key!=f'p4-notice:{self.action_id}':
            raise ValueError('Stable synthetic action key required')
        return self


def authenticated(authorization):
    if not hmac.compare_digest(authorization or '', 'Bearer local-only-sink'):
        raise HTTPException(401,detail='Local synthetic sink credential required')


def create_app(settings=None):
    settings=settings or Settings.from_env()
    app=FastAPI(title='Local synthetic durable sink')

    @app.get('/health/ready')
    def ready():
        with connect(settings.database_url) as conn:
            if not conn.execute("SELECT 1 FROM schema_migrations WHERE version='0003_delivery.sql'").fetchone():
                raise HTTPException(503,detail='Delivery migration missing')
        return {'status':'ready','contract':SINK_CONTRACT}

    @app.post('/v1/notices')
    def send(payload:Notice,authorization:Annotated[str|None,Header()]=None):
        authenticated(authorization)
        body=payload.model_dump(mode='json')
        digest=args_hash(body)
        receipt={'external_key':payload.external_key,'action_id':str(payload.action_id),
                 'tenant_id':payload.tenant_id,'payload_hash':digest,'receipt_id':str(uuid4()),'outcome':'applied'}
        with connect(settings.database_url) as conn:
            conn.execute("INSERT INTO sink_requests(external_key,method) VALUES (%s,'POST')",(payload.external_key,))
            inserted=conn.execute('''INSERT INTO sink_receipts(external_key,action_id,tenant_id,payload_hash,receipt)
                VALUES (%s,%s,%s,%s,%s) ON CONFLICT(external_key) DO NOTHING RETURNING external_key''',
                (payload.external_key,payload.action_id,payload.tenant_id,digest,Jsonb(receipt))).fetchone()
            if inserted:
                conn.execute('''INSERT INTO sink_effects(receipt_id,external_key,action_id,tenant_id,resource_id,message)
                    VALUES (%s,%s,%s,%s,%s,%s)''',(UUID(receipt['receipt_id']),payload.external_key,payload.action_id,
                    payload.tenant_id,payload.args.resource_id,payload.args.message))
            else:
                old=conn.execute('SELECT payload_hash,receipt FROM sink_receipts WHERE external_key=%s',(payload.external_key,)).fetchone()
                if old['payload_hash']!=digest:
                    # Persist the audit attempt, but never mutate its prior receipt/effect.
                    conn.commit()
                    raise HTTPException(409,detail='Idempotency payload mismatch')
                receipt=old['receipt']
        return {'contract':SINK_CONTRACT,'receipt':receipt}

    @app.get('/v1/receipts/{external_key}')
    def lookup(external_key:str,authorization:Annotated[str|None,Header()]=None):
        authenticated(authorization)
        if len(external_key)>100:
            raise HTTPException(422,detail='Invalid synthetic key')
        with connect(settings.database_url) as conn:
            conn.execute("INSERT INTO sink_requests(external_key,method) VALUES (%s,'GET')",(external_key,))
            row=conn.execute('SELECT receipt FROM sink_receipts WHERE external_key=%s',(external_key,)).fetchone()
        if row:
            return {'contract':SINK_CONTRACT,'receipt':row['receipt']}
        # A 404 alone is not a retry contract. The versioned response explicitly
        # promises durable dedup across restarts and concurrent same-key requests.
        return JSONResponse(status_code=404,content={'contract':SINK_CONTRACT,'external_key':external_key,'safe_retry':True})
    return app


app=create_app()
