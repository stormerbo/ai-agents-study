"""Final output is durable, grounded, and atomically coupled to completion."""
from uuid import uuid4

import pytest

from app.auth import Principal
from app.db import connect, create_task
from app.models import TaskCreate
from app.retrieval import seed_corpus
from app.worker import claim
from app.runtime import finalize_output

pytestmark = pytest.mark.integration


def make_task(service):
    with connect(service.dsn) as conn:
        row, _ = create_task(conn, Principal('tenant-a', 'alice', ('caller',)), uuid4().hex,
                             TaskCreate(prompt='Synthetic task'))
        seed_corpus(conn)
        lease = claim(conn, 'final-output-test', task_id=row['id'])
        source = conn.execute('''SELECT c.id AS chunk_id,c.resource_id,d.doc_version
            FROM chunks c JOIN documents d ON d.id=c.document_id
            WHERE c.tenant_id='tenant-a' AND c.resource_id='policy-public'
            ORDER BY c.position LIMIT 1''').fetchone()
        return row['id'], lease, source


def valid_output(source):
    return {'outcome': 'answer', 'text': '订单 A-1001 已找到。', 'citations': [
        {'resource_id': source['resource_id'], 'version': source['doc_version'], 'chunk_id': str(source['chunk_id'])}
    ]}


def test_completion_rejects_missing_durable_output(service):
    task_id, lease, _ = make_task(service)
    from app.worker import transition
    with connect(service.dsn) as conn:
        with pytest.raises(ValueError):
            transition(conn, lease, 'completed')
        assert conn.execute('SELECT status FROM tasks WHERE id=%s', (task_id,)).fetchone()['status'] == 'running'


@pytest.mark.parametrize('citation_change', [
    {'resource_id': 'A-1002'},
    {'version': 999},
    {'chunk_id': str(uuid4())},
])
def test_rejects_forged_or_stale_citation(service, citation_change):
    task_id, lease, source = make_task(service)
    output = valid_output(source)
    output['citations'][0].update(citation_change)
    with connect(service.dsn) as conn:
        with pytest.raises(ValueError):
            finalize_output(conn, lease, output)
        assert conn.execute('SELECT status FROM tasks WHERE id=%s', (task_id,)).fetchone()['status'] == 'running'
        assert conn.execute('SELECT count(*) AS n FROM final_outputs WHERE task_id=%s', (task_id,)).fetchone()['n'] == 0


@pytest.mark.parametrize('output', [
    {'outcome': 'invented', 'text': 'answer', 'citations': []},
    {'outcome': ['answer'], 'text': 'answer', 'citations': []},
    {'outcome': 'answer', 'text': '   ', 'citations': []},
    {'outcome': 'answer', 'text': 'answer', 'citations': [], 'trusted': True},
])
def test_rejects_invalid_final_output_contract(service, output):
    task_id, lease, _ = make_task(service)
    with connect(service.dsn) as conn:
        with pytest.raises(ValueError):
            finalize_output(conn, lease, output)
        assert conn.execute('SELECT status FROM tasks WHERE id=%s', (task_id,)).fetchone()['status'] == 'running'


def test_rejects_completion_with_unresolved_action(service):
    task_id, lease, source = make_task(service)
    from app.actions import propose_turn
    with connect(service.dsn) as conn:
        seed_corpus(conn)
        propose_turn(conn, lease, [{'id': 'pending-read', 'name': 'lookup_order', 'input': {'order_id': 'A-1001'}}])
        with pytest.raises(ValueError):
            finalize_output(conn, lease, valid_output(source))
        assert conn.execute('SELECT status FROM tasks WHERE id=%s', (task_id,)).fetchone()['status'] == 'running'


def test_valid_final_output_and_completion_commit_together(service):
    task_id, lease, source = make_task(service)
    output = valid_output(source)
    with connect(service.dsn) as conn:
        assert finalize_output(conn, lease, output) == 1
        task = conn.execute('SELECT status,state_version,lease_owner FROM tasks WHERE id=%s', (task_id,)).fetchone()
        saved = conn.execute('SELECT output,output_hash,execution_epoch FROM final_outputs WHERE task_id=%s', (task_id,)).fetchone()
        event = conn.execute("SELECT kind,payload FROM events WHERE task_id=%s AND kind='task.completed'", (task_id,)).fetchone()
        assert task['status'] == 'completed' and task['lease_owner'] is None
        assert saved['output'] == output and saved['execution_epoch'] == lease.epoch
        assert len(saved['output_hash']) == 64
        assert event is not None


def test_stale_lease_cannot_finalize(service):
    task_id, stale, source = make_task(service)
    with connect(service.dsn) as conn:
        conn.execute('UPDATE tasks SET lease_until=clock_timestamp()-interval \'1 second\' WHERE id=%s', (task_id,))
        current = claim(conn, 'new-final-output-owner', task_id=task_id)
        assert current.epoch == stale.epoch + 1
        assert finalize_output(conn, stale, valid_output(source)) == 0
        assert conn.execute('SELECT status FROM tasks WHERE id=%s', (task_id,)).fetchone()['status'] == 'running'
        assert conn.execute('SELECT count(*) AS n FROM final_outputs WHERE task_id=%s', (task_id,)).fetchone()['n'] == 0

