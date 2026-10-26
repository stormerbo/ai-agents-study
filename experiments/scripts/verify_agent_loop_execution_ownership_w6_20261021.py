"""Verify the executable SQLite ownership demo and its documented boundaries."""

from __future__ import annotations

import json
import os
import re
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/agent-loop/06-execution-ownership.mdx"
source = LESSON.read_text(encoding="utf-8")
fences = re.findall(r"^```python\s*\n([\s\S]*?)^```\s*$", source, re.MULTILINE)
assert len(fences) == 1, f"expected one Python fence, found {len(fences)}"
compile(fences[0], str(LESSON), "exec")

example_dir = ROOT / "examples/execution-ownership"
sys.path.insert(0, str(example_dir))
with tempfile.TemporaryDirectory(prefix="execution-ownership-w6-") as temp_dir:
    old_cwd = Path.cwd()
    try:
        os.chdir(temp_dir)
        exec(compile(fences[0], str(LESSON), "exec"), {"__name__": "__main__"})
    finally:
        os.chdir(old_cwd)

    with sqlite3.connect(Path(temp_dir) / "tasks.db") as db:
        row = db.execute(
            "SELECT status, owner, epoch, lease_until, checkpoint_seq, checkpoint "
            "FROM tasks WHERE task_id='task-1'"
        ).fetchone()
    assert row == ("running", "worker-b", 2, 120, 2, "step-2")
json_fences = re.findall(r"^\x60{3}json\s*\n([\s\S]*?)^\x60{3}\s*$", source, re.MULTILINE)
assert len(json_fences) == 1
state_sample = json.loads(json_fences[0])
assert state_sample == {
    "task_id": "task-1",
    "status": "running",
    "owner": "worker-b",
    "epoch": 2,
    "lease_until": 120,
    "checkpoint_seq": 2,
    "checkpoint": "step-2",
}

tests = subprocess.run(
    [sys.executable, "-m", "unittest", "discover", "-s", "examples/execution-ownership", "-v"],
    cwd=ROOT,
    capture_output=True,
    text=True,
    check=False,
)
assert tests.returncode == 0, tests.stdout + tests.stderr
assert "Ran 4 tests" in tests.stderr

worker = (ROOT / "examples/p4-durable-support/app/worker.py").read_text(encoding="utf-8")
integration = (ROOT / "examples/p4-durable-support/tests/test_worker_ownership.py").read_text(
    encoding="utf-8"
)
assert "SELECT * FROM tasks WHERE id=%s FOR UPDATE" in worker
assert "lease_until>clock_timestamp()" in worker
assert "clock_timestamp()+%s*interval '1 second'" in worker
assert "os.kill(process.pid, signal.SIGKILL)" in integration
assert "assert not renew(conn, stale)" in integration
assert "execution_epoch'] == stale.epoch + 1" in integration
sqlite_tests_source = (ROOT / "examples/execution-ownership/test_task_ownership.py").read_text(
    encoding="utf-8"
)
assert "test_expired_owner_cannot_renew_its_lease" in sqlite_tests_source
reclaim_test = sqlite_tests_source.split(
    "def test_reclaimed_task_increments_epoch_and_rejects_stale_checkpoint(self):", 1
)[1].split("\n    def test_", 1)[0]
assert reclaim_test.count("self.store.write_checkpoint(") == 2
assert 'self.store.read_checkpoint("task-1"), (1, "current")' in reclaim_test
assert "完整演示先写入 A 的 `step-1`" in source
assert "单元测试 `test_reclaimed_task_increments_epoch_and_rejects_stale_checkpoint`" in source
assert "所以它断言的是 `(1, 'current')`" in source
assert "B 的 checkpoint 序号为 `(2, 'step-2')`" in source

required_boundaries = [
    "租约到期不会自动中止该事务",
    "持锁事务会与接管串行化",
    "不模拟存活中的网络隔离 worker 恢复",
    "接收方幂等键、可查询的操作 ID、outbox/对账流程",
    "不能用自动重试制造重复退款或重复消息",
]
for boundary in required_boundaries:
    assert boundary in source, f"missing evidence boundary: {boundary}"

meta = (ROOT / "src/content/chapters/agent-loop/meta.ts").read_text(encoding="utf-8")
assert "postgres-row-locking-18" in meta
assert "postgres-date-time-functions-18" in meta

print(
    "PASS: snippet compiled/executed; checkpoint row matched; 4 SQLite tests passed; "
    "P4 lock/time/test boundaries and lesson limitations verified."
)
