import uuid
import pytest
from app.auth import Principal
from app.db import connect

pytestmark = pytest.mark.integration


def test_validate_cutover_retire_and_immediate_revocation(service):
    from app.retrieval import build_index, validate_index, cutover, retrieve, build_context, revoke, seed_corpus
    caller = Principal('tenant-a','alice',('caller',))
    resource = 'version-'+uuid.uuid4().hex
    with connect(service.dsn) as conn:
        seed_corpus(conn)
        first = build_index(conn, 'tenant-a', {resource:'OLD-CONTENT'}, readers=['alice'])
        with pytest.raises(ValueError):
            cutover(conn, 'tenant-a', first)
        validate_index(conn, 'tenant-a', first)
        cutover(conn, 'tenant-a', first)
        assert 'OLD-CONTENT' in build_context(conn, caller, '')
        second = build_index(conn, 'tenant-a', {resource:'NEW-CONTENT'}, readers=['alice'])
        assert 'OLD-CONTENT' in build_context(conn, caller, '')
        validate_index(conn, 'tenant-a', second)
        cutover(conn, 'tenant-a', second)
        assert 'NEW-CONTENT' in build_context(conn, caller, '')
        assert 'OLD-CONTENT' not in build_context(conn, caller, '')
        assert retrieve(conn, caller, '', index_version=first) == []
        assert conn.execute('SELECT state FROM index_versions WHERE tenant_id=%s AND id=%s',('tenant-a',first)).fetchone()['state'] == 'retired'
        revoke(conn, 'tenant-a', resource, 'alice')
        assert 'NEW-CONTENT' not in build_context(conn, caller, '')
        for table in ('context_cache','context_memory'):
            assert conn.execute(f'SELECT count(*) AS n FROM {table} WHERE tenant_id=%s AND resource_id=%s',('tenant-a',resource)).fetchone()['n'] == 0
        conn.rollback()  # Each lifecycle test owns its snapshot; never replace another test's corpus.
