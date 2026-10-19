import pytest
from app.auth import Principal
from app.db import connect

pytestmark = pytest.mark.integration


def test_principal_filter_precedes_context_and_deleted_chunks(service):
    from app.retrieval import seed_corpus, retrieve, build_context, delete_resource, build_index, validate_index, cutover
    alice = Principal('tenant-a','alice',('caller',))
    mallory = Principal('tenant-b','mallory',('caller',))
    with connect(service.dsn) as conn:
        seed_corpus(conn)
        snapshot=build_index(conn,'tenant-a',{'A-1001':'ALICE-ORDER synthetic order',
                             'policy-public':'Synthetic policy','secret-bob':'BOB-SECRET synthetic restricted document'},readers=['alice'])
        conn.execute("DELETE FROM resource_acl WHERE tenant_id='tenant-a' AND resource_id='secret-bob' AND caller_id='alice'")
        validate_index(conn,'tenant-a',snapshot)
        cutover(conn,'tenant-a',snapshot)
        chunks = retrieve(conn, alice, '')
        assert chunks
        assert all(c['tenant_id']=='tenant-a' and c['resource_id']!='secret-bob' for c in chunks)
        captured = []
        context = build_context(conn, alice, '', capture=captured.append)
        assert captured == [context]
        assert 'ALICE-ORDER' in context
        assert 'BOB-SECRET' not in context and 'MALLORY-SECRET' not in context
        assert 'ALICE-ORDER' not in build_context(conn, mallory, '')
        delete_resource(conn, 'tenant-a', 'A-1001')
        assert 'ALICE-ORDER' not in build_context(conn, alice, '')
        assert conn.execute("SELECT count(*) AS n FROM context_cache WHERE tenant_id='tenant-a' AND resource_id='A-1001'").fetchone()['n'] == 0
        assert conn.execute("SELECT count(*) AS n FROM context_memory WHERE tenant_id='tenant-a' AND resource_id='A-1001'").fetchone()['n'] == 0
        conn.rollback()  # Deletion is tested in this transaction, not leaked into later ownership tests.
