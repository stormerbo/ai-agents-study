"""Own a fresh real PostgreSQL and two independent uvicorn processes per run."""
from __future__ import annotations

import os
from pathlib import Path
import re
import json
import hashlib
import socket
import subprocess
import sys
import time
import uuid

import httpx
import pytest

HERE = Path(__file__).resolve().parents[1]


def subprocess_environment():
    allowed = ("PATH", "HOME", "TMPDIR", "SYSTEMROOT", "DOCKER_HOST", "DOCKER_CONTEXT",
               "DOCKER_CONFIG", "DOCKER_CERT_PATH", "DOCKER_TLS_VERIFY", "XDG_RUNTIME_DIR")
    return {key: os.environ[key] for key in allowed if key in os.environ}


def unused_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def record_drill_observation(scenario_id, observed, *, dsn=None, task_ids=()):
    """Write assertion-backed facts only when the P5 collector requests them."""
    evidence_dir = os.environ.get("P5_DRILL_OBSERVATIONS_DIR")
    if not evidence_dir:
        return
    observed = dict(observed)
    if dsn is not None:
        from app.db import connect
        snapshots = []
        reservations = []
        with connect(dsn) as conn:
            for task_id in task_ids:
                task = conn.execute('SELECT id,status,checkpoint,execution_epoch FROM tasks WHERE id=%s', (task_id,)).fetchone()
                if task is None:
                    raise RuntimeError("Drill observation task is missing")
                checkpoint = task['checkpoint']
                checkpoint_hash = hashlib.sha256(json.dumps(
                    checkpoint, sort_keys=True, ensure_ascii=False, default=str).encode('utf-8')).hexdigest() if checkpoint is not None else None
                event_kinds = [row['kind'] for row in conn.execute(
                    'SELECT kind FROM events WHERE task_id=%s ORDER BY seq', (task_id,)).fetchall()]
                snapshots.append({"task_id": str(task['id']), "status": task['status'],
                                  "execution_epoch": task['execution_epoch'],
                                  "checkpoint_sha256": checkpoint_hash,
                                  "event_kinds_in_order": event_kinds})
                reservations.extend({"task_id": str(task_id), "state": row['state'], "tokens": row['tokens'],
                                     "tools": row['tools'], "sent": row['sent']}
                    for row in conn.execute(
                        'SELECT state,tokens,tools,sent FROM budget_reservations WHERE task_id=%s ORDER BY id',
                        (task_id,)).fetchall())
        observed["checkpoint_snapshots"] = snapshots
        observed["budget_reservations"] = reservations
    else:
        observed.setdefault("checkpoint_snapshots", [])
        observed.setdefault("budget_reservations", [])
    current = os.environ.get("PYTEST_CURRENT_TEST", "").split(" (", 1)[0]
    file_name, separator, test_name = current.rpartition("::")
    if not separator or not test_name or not isinstance(observed, dict):
        raise RuntimeError("Cannot bind drill observation to a pytest node id")
    source_path = Path(file_name).resolve()
    try:
        module_path = source_path.relative_to(HERE).with_suffix("")
        module_name = ".".join(module_path.parts)
    except ValueError:
        module_name = source_path.stem
    node_id = f"{module_name}::{test_name}"
    record = {"scenario_id": scenario_id, "node_id": node_id, "observed": observed}
    root = Path(evidence_dir).resolve()
    root.mkdir(parents=True, exist_ok=True)
    name = hashlib.sha256(node_id.encode("utf-8")).hexdigest() + ".json"
    target = root / name
    temporary = target.with_suffix(".tmp")
    temporary.write_text(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(target)


class ServiceHarness:
    def __init__(self, project):
        self.project = project
        self.dsn = ""
        self.processes = {}
        self.urls = []
        self.postgres_port = unused_port()

    def compose(self, *args, check=True):
        return subprocess.run(
            ["docker", "compose", "-p", self.project, "-f", str(HERE / "compose.yaml"), *args],
            cwd=HERE, env={**subprocess_environment(), "P4_POSTGRES_PORT": str(self.postgres_port)},
            capture_output=True, text=True, check=check, timeout=180,
        )

    def start_api(self, index):
        port = unused_port()
        env = subprocess_environment()
        env.update(DATABASE_URL=self.dsn, PYTHONDONTWRITEBYTECODE="1", PYTHONPATH=str(HERE.parent))
        process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "app.runtime:create_app", "--factory", "--host", "127.0.0.1", "--port", str(port), "--no-access-log", "--log-level", "critical"],
            cwd=HERE, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        self.processes[index] = process
        url = f"http://127.0.0.1:{port}"
        if len(self.urls) <= index:
            self.urls.append(url)
        else:
            self.urls[index] = url
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise RuntimeError("API process exited before readiness")
            try:
                if httpx.get(url + "/health/ready", timeout=1).status_code == 200:
                    return
            except httpx.HTTPError:
                pass
            time.sleep(0.05)
        raise RuntimeError("API readiness deadline exceeded")

    def stop_api(self, index):
        process = self.processes.pop(index)
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)

    def restart_api(self, index):
        self.stop_api(index)
        self.start_api(index)

    def request(self, method, path, *, index=0, token="dev-alice", **kwargs):
        return httpx.request(method, self.urls[index] + path,
                             headers={"Authorization": f"Bearer {token}", **kwargs.pop("headers", {})},
                             timeout=10, **kwargs)


@pytest.fixture(scope="session")
def service():
    configured_project = os.environ.get("P4_TEST_COMPOSE_PROJECT")
    if configured_project is not None and not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,62}", configured_project):
        raise ValueError("Invalid isolated Compose project name")
    harness = ServiceHarness(configured_project or "p4-test-" + uuid.uuid4().hex[:12])
    try:
        # No external database override and no skip fallback: this is real evidence.
        harness.compose("up", "-d", "--wait", "--wait-timeout", "90", "postgres")
        address = harness.compose("port", "postgres", "5432").stdout.strip()
        port = int(address.rsplit(":", 1)[1])
        harness.dsn = f"postgresql://support:local-only-demo@127.0.0.1:{port}/support"
        from app.db import migrate, seed
        migrate(harness.dsn)
        seed(harness.dsn)
        harness.start_api(0)
        harness.start_api(1)
        yield harness
    finally:
        for index in list(harness.processes):
            harness.stop_api(index)
        # Runs even when pull, health checks, migrations or tests fail.
        harness.compose("down", "--volumes", "--remove-orphans", check=False)


@pytest.fixture
def task(service):
    response = service.request("POST", "/v1/tasks", json={"prompt": "查询合成订单 A-1001"},
                               headers={"Idempotency-Key": uuid.uuid4().hex})
    assert response.status_code == 201, response.text
    return response.json()
