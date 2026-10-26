#!/usr/bin/env python3
"""Whole-lesson source, boundary, SQLite and PostgreSQL drill checks for W6."""
from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/agent-deployment/05-recovery-drills.mdx"
SQLITE_TESTS = ROOT / "examples/reliability/test_fault_models.py"
PG_DRILL = ROOT / "examples/recovery-drills/postgres_restore_drill.sh"
RESOURCES = ROOT / "src/content/curriculum/resources.ts"
META = ROOT / "src/content/chapters/agent-deployment/meta.ts"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    lesson = LESSON.read_text(encoding="utf-8")
    tests = SQLITE_TESTS.read_text(encoding="utf-8")
    drill = PG_DRILL.read_text(encoding="utf-8")
    resources = RESOURCES.read_text(encoding="utf-8")
    meta = META.read_text(encoding="utf-8")
    checks = 0

    # Evidence and scope: each API-specific backup claim has a registered source.
    for source_id in ("postgres-pg-verifybackup", "postgres-pg-dump-restore", "postgres-pitr"):
        require(source_id in resources and source_id in meta, f"unregistered lesson source: {source_id}")
    require("plain 格式" in lesson and "--no-parse-wal" in lesson, "pg_verifybackup WAL format boundary is missing")
    require("对应备份版本的工具" in lesson and "实际恢复和数据正确性检查" in lesson, "version-specific verification / real restore boundary is missing")
    require("pg_dump -Fc" in lesson and "只导出一个数据库" in lesson and "pg_restore" in lesson, "logical dump scope is unclear")
    require("由源 superuser 选择的代码" in meta, "untrusted archive execution warning is not covered")
    checks += 7

    # The local examples state their own evidence limits instead of implying production guarantees.
    require("没有实现租约过期、执行 epoch 或旧 worker 的 fencing 检查" in lesson, "SQLite worker-fencing limitation is missing")
    require("先后导出两个独立数据库" in lesson and "同一时点的一致快照" in lesson, "cross-database snapshot limitation is missing")
    require("容器 tag 而非镜像 digest" in lesson, "mutable image-tag limitation is missing")
    require("WAL/PITR" in lesson and "RTO/RPO" in lesson and "真实副作用重投递" in lesson, "PostgreSQL integration limits are incomplete")
    require("trap cleanup EXIT" in drill and "docker rm -f" in drill and "--rm" in drill, "Docker drill is not self-cleaning")
    require("-p " not in drill and "--publish" not in drill and "--volume" not in drill, "drill unexpectedly publishes or mounts host resources")
    require("--exit-on-error" in drill and "reconciling:unknown:unknown:external_effect_unknown" in drill, "restore command or state assertion missing")
    require("receiver idempotency key" in tests and "test_reconcile_does_not_confirm_receiver_key" in tests, "receiver key/payload conflict boundary is untested")
    checks += 8

    # Run the deterministic SQLite failure-boundary suite.
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    sqlite = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "examples/reliability", "-v"],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=True,
    )
    require(re.search(r"Ran 7 tests[^\n]*\n\nOK", sqlite.stderr) is not None, "SQLite suite did not report 7 passing tests")
    checks += 1

    # Run the isolated PostgreSQL logical-restore drill and check its published invariant.
    pg = subprocess.run(["bash", str(PG_DRILL)], cwd=ROOT, text=True, capture_output=True, check=True, timeout=180)
    match = re.search(r"RESTORE_OK app_state=(\S+) sink_operation_count=(\d+) image=(\S+)", pg.stdout)
    require(match is not None, "PostgreSQL drill did not emit the documented result shape")
    app_state, sink_count, image = match.groups()
    require(app_state == "reconciling:unknown:unknown:external_effect_unknown", "restored app state differs")
    require(sink_count == "1", "restored receiver operation count differs")
    require(image.startswith("postgres:18.0-bookworm"), "unexpected PostgreSQL container image")
    published = "RESTORE_OK app_state=reconciling:unknown:unknown:external_effect_unknown sink_operation_count=1 image=postgres:18.0-bookworm"
    require(published in lesson, "published integration output no longer matches the executed restore invariant")
    checks += 5

    print(f"PASS: {checks} source, boundary, and execution checks")
    print("PASS: SQLite failure-boundary suite 7/7")
    print(f"PASS: PostgreSQL 18 logical restore app_state={app_state} sink_operation_count={sink_count}")
    print("providerCalls=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
