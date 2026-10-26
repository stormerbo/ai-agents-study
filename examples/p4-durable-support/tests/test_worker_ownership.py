"""Real PostgreSQL fencing evidence; workers are independent spawn processes."""
import importlib.util
import hashlib
import json
import multiprocessing as mp
import os
import signal
import subprocess
import sys
import time
import uuid
from pathlib import Path

import httpx
import pytest

from app.db import connect, create_task
from app.auth import Principal
from app.models import TaskCreate
from conftest import unused_port, subprocess_environment

pytestmark = pytest.mark.integration


def new_task(dsn):
    with connect(dsn) as conn:
        return create_task(conn, Principal('tenant-a', 'alice', ('caller',)), uuid.uuid4().hex,
                           TaskCreate(prompt='Synthetic task'))[0]['id']


@pytest.fixture
def execution_service(service):
    """Use the Task 2 factory without changing Task 1's compatibility entrypoint."""
    class API:
        def start(self):
            port = unused_port()
            env = {**subprocess_environment(), 'DATABASE_URL': service.dsn,
                   'PYTHONPATH': str(Path(__file__).resolve().parents[2])}
            self.process = subprocess.Popen([sys.executable, '-m', 'uvicorn', 'app.runtime:create_app',
                '--factory', '--host', '127.0.0.1', '--port', str(port), '--no-access-log', '--log-level', 'critical'],
                cwd=Path(__file__).resolve().parents[1], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.url = f'http://127.0.0.1:{port}'
            for _ in range(200):
                if self.process.poll() is not None:
                    raise RuntimeError('Task 2 API exited')
                try:
                    if httpx.get(self.url+'/health/ready', timeout=.2).status_code == 200:
                        return
                except httpx.HTTPError:
                    pass
                time.sleep(.05)
            raise RuntimeError('Task 2 API readiness timeout')

        def stop(self):
            self.process.terminate()
            self.process.wait(timeout=5)

        def restart(self):
            self.stop()
            self.start()

        def request(self, method, path, token='dev-alice', **kwargs):
            return httpx.request(method, self.url+path,
                headers={'Authorization': 'Bearer '+token, **kwargs.pop('headers', {})}, timeout=10, **kwargs)
    api = API()
    api.start()
    api.dsn = service.dsn
    try:
        yield api
    finally:
        api.stop()


def owner_process(dsn, task_id, barrier, channel):
    from app.worker import claim
    with connect(dsn) as conn:
        lease = claim(conn, 'owner-a', task_id=task_id, lease_seconds=1)
    channel.send(lease)
    barrier.wait(timeout=10)
    signal.pause()


def test_execution_modules_exist():
    assert importlib.util.find_spec('app.worker') is not None


def test_takeover_fences_all_writes_and_dead_owner(service):
    from app.worker import claim, checkpoint, emit, renew
    from app.actions import propose_turn, authorize_action
    task_id = new_task(service.dsn)
    from app.retrieval import seed_corpus
    with connect(service.dsn) as conn:
        seed_corpus(conn)
        setup_lease=claim(conn,'setup-approval',task_id=task_id)
        existing_action=propose_turn(conn,setup_lease,[{'id':'frozen','name':'send_notice','input':{'resource_id':'A-1001','message':'frozen'}}])[0]
        conn.execute("UPDATE approvals SET status='approved',decided_by=eligible_approver,decided_at=clock_timestamp() WHERE action_id=%s",(existing_action,))
        conn.execute("UPDATE tasks SET status='queued' WHERE id=%s",(task_id,))
    context = mp.get_context('spawn')
    barrier = context.Barrier(2)
    reader, writer = context.Pipe(False)
    process = context.Process(target=owner_process, args=(service.dsn, task_id, barrier, writer))
    process.start()
    try:
        stale = reader.recv()
        barrier.wait(timeout=10)
        os.kill(process.pid, signal.SIGKILL)
        process.join(timeout=5)
        time.sleep(1.05)
        # A separately connected OS process claims after forced owner death.
        result = subprocess.run([sys.executable, '-m', 'app.worker', '--once', '--task', str(task_id), '--owner', 'owner-b'],
            env={**subprocess_environment(), 'DATABASE_URL': service.dsn}, capture_output=True, text=True, timeout=10)
        assert result.returncode == 0, result.stderr
        with connect(service.dsn) as conn:
            current = conn.execute('SELECT * FROM tasks WHERE id=%s', (task_id,)).fetchone()
            assert current['lease_owner'] == 'owner-b'
            assert current['execution_epoch'] == stale.epoch + 1
            assert not renew(conn, stale)
            assert checkpoint(conn, stale, {'bad': True}) == 0
            assert emit(conn, stale, 'stale.event', {}) == 0
            assert propose_turn(conn, stale, [{'id':'x', 'name':'send_notice', 'input':{'resource_id':'A-1001','message':'hi'}}]) == []
            assert authorize_action(conn, stale, existing_action) == 0
            assert conn.execute('SELECT status FROM actions WHERE id=%s',(existing_action,)).fetchone()['status']=='waiting_approval'
            assert conn.execute('SELECT count(*) AS n FROM approvals WHERE task_id=%s', (task_id,)).fetchone()['n'] == 1
            assert conn.execute('SELECT count(*) AS n FROM actions WHERE task_id=%s', (task_id,)).fetchone()['n'] == 1
            assert conn.execute("SELECT count(*) AS n FROM events WHERE task_id=%s AND kind='stale.event'",(task_id,)).fetchone()['n']==0
            assert conn.execute('SELECT checkpoint FROM tasks WHERE id=%s',(task_id,)).fetchone()['checkpoint']==current['checkpoint']
            checkpoint_hash=hashlib.sha256(json.dumps(current['checkpoint'],sort_keys=True,default=str).encode()).hexdigest()
            stale_event_count=conn.execute("SELECT count(*) AS n FROM events WHERE task_id=%s AND kind='stale.event'",(task_id,)).fetchone()['n']
            action_count=conn.execute('SELECT count(*) AS n FROM actions WHERE task_id=%s',(task_id,)).fetchone()['n']
            approval_count=conn.execute('SELECT count(*) AS n FROM approvals WHERE task_id=%s',(task_id,)).fetchone()['n']
        from conftest import record_drill_observation
        record_drill_observation('lease-takeover', {
            'owner_epochs':[stale.epoch,current['execution_epoch']],
            'stale_mutation_counts':{'actions_present':action_count,'approvals_present':approval_count,
                                     'stale_events':stale_event_count,'checkpoint_unchanged':1},
            'checkpoint_sha256':checkpoint_hash,
        }, dsn=service.dsn, task_ids=[task_id])
    finally:
        if process.is_alive():
            process.kill()
        process.join(timeout=5)


def test_finished_wakeup_releases_only_its_own_lease_for_immediate_successor(service):
    from app.worker import claim, release
    task_id = new_task(service.dsn)
    with connect(service.dsn) as conn:
        first = claim(conn, 'wakeup-one', task_id=task_id, lease_seconds=120)
        assert first is not None
        assert release(conn, first) is True
        second = claim(conn, 'wakeup-two', task_id=task_id, lease_seconds=120)
        assert second is not None
        assert second.epoch == first.epoch + 1
        assert release(conn, first) is False
        assert conn.execute('SELECT lease_owner FROM tasks WHERE id=%s', (task_id,)).fetchone()['lease_owner'] == 'wakeup-two'


def test_transitions_and_completion_require_resolved_actions(service):
    from app.worker import claim, transition
    from app.actions import propose_turn
    from app.retrieval import seed_corpus
    task_id = new_task(service.dsn)
    with connect(service.dsn) as conn:
        seed_corpus(conn)
        lease = claim(conn, 'states', task_id=task_id)
        with pytest.raises(ValueError):
            transition(conn, lease, 'queued')
        propose_turn(conn, lease, [{'id':'m1','name':'lookup_order','input':{'order_id':'A-1001'}}])
        with pytest.raises(ValueError):
            transition(conn, lease, 'completed')


def test_one_lease_can_persist_multiple_completed_read_turns(service):
    from app.worker import claim, checkpoint
    from app.actions import propose_turn
    from app.retrieval import seed_corpus
    task_id=new_task(service.dsn)
    with connect(service.dsn) as conn:
        seed_corpus(conn)
        lease=claim(conn,'multi-turn',task_id=task_id)
        call={'id':'read','name':'lookup_order','input':{'order_id':'A-1001'}}
        first=propose_turn(conn,lease,[call])
        conn.execute("UPDATE actions SET status='succeeded',result='{}' WHERE id=%s",(first[0],))
        checkpoint(conn,lease,{'pending_action_ids':[]})
        second=propose_turn(conn,lease,[call])
        assert first[0]!=second[0]
        assert conn.execute('SELECT count(*) AS n FROM actions WHERE task_id=%s',(task_id,)).fetchone()['n']==2
