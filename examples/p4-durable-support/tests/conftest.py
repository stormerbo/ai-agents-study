"""Own a fresh real PostgreSQL and two independent uvicorn processes per run."""
from __future__ import annotations

import os
from pathlib import Path
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
        env.update(DATABASE_URL=self.dsn, PYTHONDONTWRITEBYTECODE="1")
        process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(port), "--no-access-log", "--log-level", "critical"],
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
    harness = ServiceHarness("p4-test-" + uuid.uuid4().hex[:12])
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
