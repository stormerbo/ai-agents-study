"""Synthetic lexical corpus: SQL ACL filtering occurs before candidate selection.

There are no embeddings or provider calls here. Cache/memory hold provenance only;
every context is rebuilt from live authorized rows, never from a cached body.
"""
from hashlib import sha256
from uuid import uuid4


def _tenant_lock(conn, tenant_id):
    # Exclusive lifecycle lock linearizes context construction with ACL/deletion.
    conn.execute('SELECT pg_advisory_xact_lock(hashtextextended(%s,4002002))',(tenant_id,))


def invalidate(conn, tenant_id, resource_id=None):
    for table in ('context_cache','context_memory'):
        conn.execute(f'DELETE FROM {table} WHERE tenant_id=%s AND (%s::text IS NULL OR resource_id=%s)',
                     (tenant_id,resource_id,resource_id))


def build_index(conn, tenant_id, contents, *, readers):
    """Build a complete replacement snapshot with deterministic one-chunk docs."""
    if not contents or not readers or any(not isinstance(v,str) or not v.strip() for v in contents.values()):
        raise ValueError('Non-empty synthetic documents and readers required')
    _tenant_lock(conn,tenant_id)
    conn.execute('INSERT INTO tenant_policies(tenant_id) VALUES (%s) ON CONFLICT DO NOTHING',(tenant_id,))
    index_id=uuid4()
    conn.execute('INSERT INTO index_versions(id,tenant_id) VALUES (%s,%s)',(index_id,tenant_id))
    for resource_id,body in contents.items():
        conn.execute('INSERT INTO resources(tenant_id,resource_id) VALUES (%s,%s) ON CONFLICT DO NOTHING',(tenant_id,resource_id))
        resource=conn.execute('SELECT * FROM resources WHERE tenant_id=%s AND resource_id=%s FOR UPDATE',(tenant_id,resource_id)).fetchone()
        for reader in readers:
            conn.execute('INSERT INTO resource_acl(tenant_id,resource_id,caller_id) VALUES (%s,%s,%s) ON CONFLICT DO NOTHING',(tenant_id,resource_id,reader))
        document_id=uuid4()
        conn.execute('INSERT INTO documents(id,tenant_id,resource_id,doc_version,content_hash,acl_version,index_version) VALUES (%s,%s,%s,%s,%s,%s,%s)',
                     (document_id,tenant_id,resource_id,resource['version']+1,sha256(body.encode()).hexdigest(),resource['acl_version'],index_id))
        conn.execute('INSERT INTO chunks VALUES (%s,%s,%s,%s,0,%s)',(uuid4(),document_id,tenant_id,resource_id,body))
    return index_id


def validate_index(conn, tenant_id, index_id):
    _tenant_lock(conn,tenant_id)
    docs=conn.execute('SELECT d.*,c.body FROM documents d JOIN chunks c ON c.document_id=d.id WHERE d.tenant_id=%s AND d.index_version=%s',(tenant_id,index_id)).fetchall()
    if not docs or any(sha256(d['body'].encode()).hexdigest()!=d['content_hash'] for d in docs):
        raise ValueError('Invalid snapshot content/hash')
    changed=conn.execute("UPDATE index_versions SET state='validated' WHERE id=%s AND tenant_id=%s AND state='building'",(index_id,tenant_id)).rowcount
    if not changed:
        raise ValueError('Index not building')


def cutover(conn, tenant_id, index_id):
    _tenant_lock(conn,tenant_id)
    row=conn.execute('SELECT state FROM index_versions WHERE id=%s AND tenant_id=%s FOR UPDATE',(index_id,tenant_id)).fetchone()
    if row is None or row['state']!='validated':
        raise ValueError('Validate index before cutover')
    # Freeze validated snapshot freshness: reject a resource changed while building.
    stale=conn.execute('''SELECT 1 FROM documents d JOIN resources r USING(tenant_id,resource_id)
        WHERE d.index_version=%s AND (d.acl_version!=r.acl_version OR d.doc_version!=r.version+1 OR r.deleted_at IS NOT NULL)''',(index_id,)).fetchone()
    if stale:
        raise ValueError('Snapshot resource/ACL changed; rebuild required')
    conn.execute("UPDATE index_versions SET state='retired' WHERE tenant_id=%s AND state='active'",(tenant_id,))
    conn.execute("UPDATE index_versions SET state='active' WHERE id=%s",(index_id,))
    conn.execute('''UPDATE resources r SET version=d.doc_version FROM documents d
        WHERE d.index_version=%s AND r.tenant_id=d.tenant_id AND r.resource_id=d.resource_id''',(index_id,))
    invalidate(conn,tenant_id)


def revoke(conn, tenant_id, resource_id, caller_id):
    _tenant_lock(conn,tenant_id)
    conn.execute('UPDATE resources SET acl_version=acl_version+1 WHERE tenant_id=%s AND resource_id=%s',(tenant_id,resource_id))
    conn.execute('UPDATE resource_acl SET allowed=false WHERE tenant_id=%s AND resource_id=%s AND caller_id=%s',(tenant_id,resource_id,caller_id))
    invalidate(conn,tenant_id,resource_id)


def delete_resource(conn, tenant_id, resource_id):
    _tenant_lock(conn,tenant_id)
    conn.execute('UPDATE resources SET deleted_at=clock_timestamp(),version=version+1 WHERE tenant_id=%s AND resource_id=%s',(tenant_id,resource_id))
    conn.execute('UPDATE documents SET deleted_at=clock_timestamp() WHERE tenant_id=%s AND resource_id=%s',(tenant_id,resource_id))
    invalidate(conn,tenant_id,resource_id)


def retrieve(conn, principal, query, *, index_version=None, limit=20):
    if not isinstance(query,str) or not 1<=limit<=100:
        raise ValueError('Invalid query or result limit')
    _tenant_lock(conn,principal.tenant_id)
    # Drop provenance on every query before constructing new context: callers cannot
    # bypass current membership, deletion, versions or ACL through older cache rows.
    invalidate(conn,principal.tenant_id)
    return conn.execute('''SELECT c.id AS chunk_id,c.tenant_id,c.resource_id,c.body,d.doc_version,d.index_version,d.acl_version
        FROM chunks c JOIN documents d ON c.document_id=d.id
        JOIN resources r ON r.tenant_id=d.tenant_id AND r.resource_id=d.resource_id
        JOIN resource_acl a ON a.tenant_id=r.tenant_id AND a.resource_id=r.resource_id
        JOIN caller_identities u ON u.tenant_id=a.tenant_id AND u.caller_id=a.caller_id
        JOIN index_versions i ON i.id=d.index_version
        WHERE c.tenant_id=%s AND a.caller_id=%s AND a.allowed AND u.active AND 'caller'=ANY(u.roles)
          AND r.deleted_at IS NULL AND d.deleted_at IS NULL AND d.doc_version=r.version
          AND i.state='active' AND (%s::uuid IS NULL OR i.id=%s)
          AND position(lower(%s) in lower(c.body))>0
        ORDER BY c.resource_id,c.position LIMIT %s''',
        (principal.tenant_id,principal.caller_id,index_version,index_version,query,limit)).fetchall()


def build_context(conn, principal, query, *, capture=None):
    rows=retrieve(conn,principal,query)
    for row in rows:
        for table in ('context_cache','context_memory'):
            conn.execute(f'INSERT INTO {table}(tenant_id,caller_id,resource_id,chunk_id) VALUES (%s,%s,%s,%s) ON CONFLICT DO NOTHING',
                         (principal.tenant_id,principal.caller_id,row['resource_id'],row['chunk_id']))
    context='\n'.join(f"[{r['resource_id']}@{r['doc_version']}:{r['chunk_id']}] {r['body']}" for r in rows)
    if capture:
        capture(context)
    return context


def seed_corpus(conn):
    """Idempotent synthetic corpus, never undo deletion or revocation."""
    for tenant,contents,readers in [
        ('tenant-a',{'A-1001':'ALICE-ORDER synthetic order','policy-public':'Synthetic return policy'},['alice']),
        ('tenant-b',{'B-1001':'MALLORY-SECRET synthetic order'},['mallory']),
    ]:
        _tenant_lock(conn,tenant)
        if conn.execute('SELECT 1 FROM index_versions WHERE tenant_id=%s',(tenant,)).fetchone():
            continue
        if tenant=='tenant-a':
            contents={**contents,'secret-bob':'BOB-SECRET restricted synthetic document'}
        index_id=build_index(conn,tenant,contents,readers=readers)
        if tenant=='tenant-a':
            conn.execute("DELETE FROM resource_acl WHERE tenant_id='tenant-a' AND resource_id='secret-bob'")
            conn.execute("INSERT INTO resource_acl VALUES ('tenant-a','secret-bob','bob',true)")
        validate_index(conn,tenant,index_id)
        cutover(conn,tenant,index_id)
