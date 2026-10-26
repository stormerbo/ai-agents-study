import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/retrieval/06-index-lifecycle.mdx"
EXAMPLE = ROOT / "examples/index-lifecycle/index_catalog.py"
TESTS = ROOT / "examples/index-lifecycle/test_index_catalog.py"
source = LESSON.read_text()
checks = 0


def check(condition, message):
    global checks
    assert condition, message
    checks += 1


# Re-run the exact bounded example described in the lesson.
run = subprocess.run(
    [sys.executable, "-m", "unittest", "discover", "-s", "examples/index-lifecycle", "-v"],
    cwd=ROOT,
    capture_output=True,
    text=True,
)
check(run.returncode == 0, run.stdout + run.stderr)
check("Ran 6 tests" in run.stderr and "OK" in run.stderr, run.stderr)
check(
    "test_mid_build_write_failure_rolls_back_candidate_and_keeps_active_generation" in run.stderr,
    run.stderr,
)

# Execute the exact Python call-shape fence with a temporary database.
python_fences = re.findall(r"^```python\n(.*?)^```\s*$", source, re.MULTILINE | re.DOTALL)
check(len(python_fences) == 1, f"expected one Python fence, found {len(python_fences)}")
with tempfile.TemporaryDirectory() as directory:
    demo_source = python_fences[0].replace(
        '"index-catalog.db"', repr(str(Path(directory) / "index-catalog.db"))
    )
    demo = subprocess.run(
        [sys.executable, "-c", demo_source],
        cwd=ROOT / "examples/index-lifecycle",
        capture_output=True,
        text=True,
    )
    check(demo.returncode == 0, demo.stdout + demo.stderr)

# Pin the content-hash semantics claimed by this bounded example.
implementation = EXAMPLE.read_text()
check('content.encode("utf-8")' in implementation and "hashlib.sha256" in implementation, "example hash is not explicit UTF-8 SHA-256")

# Exercise additional source-revision contracts through the real SQLite model.
sys.path.insert(0, str(ROOT / "examples/index-lifecycle"))
from index_catalog import IndexCatalog, RevisionConflict, StaleGeneration  # noqa: E402

with tempfile.TemporaryDirectory() as directory:
    catalog = IndexCatalog(os.path.join(directory, "catalog.db"))
    try:
        check(catalog.upsert_document("policy", 3, "14 days") == 1, "initial version")
        check(catalog.upsert_document("policy", 2, "30 days") == 1, "older event ignored")
        try:
            catalog.upsert_document("policy", 3, "7 days")
        except RevisionConflict:
            check(True, "same revision conflict rejected")
        else:
            check(False, "same revision with different content must conflict")

        generation = catalog.build_generation()
        catalog.activate_generation(generation)
        catalog.delete_document("policy", 4)
        check(catalog.active_document_ids() == [], "tombstone suppresses active entry")
        check(catalog.upsert_document("policy", 5, "7 days") == 3, "new revision may restore document")
        check(catalog.active_document_ids() == [], "old generation remains suppressed")

        replacement = catalog.build_generation()
        catalog.activate_generation(replacement)
        check(catalog.active_document_ids() == ["policy"], "replacement generation is queryable")
        try:
            catalog.activate_generation(generation)
        except ValueError:
            check(True, "retired generation cannot reactivate")
        else:
            check(False, "retired generation must not reactivate")
    finally:
        catalog.close()

# Confirm the lesson states the exact evidence boundary supported by this model.
for phrase in (
    "不调用 embedding API，也不模拟向量相似度",
    "不模拟 embedding/向量服务部分失败，也不证明 PostgreSQL 多进程锁、跨服务一致性或生产级重试",
    "严格删除要求",
    "两个独立服务",
    "pipeline_version`、每条 generation entry 对应的 `source_revision`、chunk 内容或向量",
):
    check(phrase in source, f"missing scope boundary: {phrase}")

print(json.dumps({"checks": checks, "passed": checks, "providerCalls": 0, "externalNetworkCalls": 0}, ensure_ascii=False))
