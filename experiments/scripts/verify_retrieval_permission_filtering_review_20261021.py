import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/retrieval/07-permission-filtering.mdx"
RESOURCES = ROOT / "src/content/curriculum/resources.ts"
META = ROOT / "src/content/chapters/retrieval/meta.ts"
source = LESSON.read_text()
resources = RESOURCES.read_text()
meta = META.read_text()
checks = 0


def check(condition, message):
    global checks
    assert condition, message
    checks += 1


safe_tests = subprocess.run(
    [sys.executable, "-m", "unittest", "discover", "-s", "examples/permission-filtering", "-p", "test_*.py", "-v"],
    cwd=ROOT,
    capture_output=True,
    text=True,
)
check(safe_tests.returncode == 0, safe_tests.stdout + safe_tests.stderr)
check("Ran 5 tests" in safe_tests.stderr and "OK" in safe_tests.stderr, safe_tests.stderr)

unsafe = subprocess.run(
    [sys.executable, "examples/permission-filtering/unsafe_retrieval_demo.py"],
    cwd=ROOT,
    capture_output=True,
    text=True,
)
expected = (
    "authenticated principal=alice/tenant-a\n"
    "request tenant_id=tenant-b\n"
    "unsafe result=[('policy-b', 'tenant B policy')]\n"
)
check(unsafe.returncode == 0, unsafe.stderr)
check(unsafe.stdout == expected, unsafe.stdout)
check("故意用请求体的 `tenant_id` 查询正文" in source, "unsafe fixture must be labeled intentional")
check("只用于展示漏洞形状" in source, "unsafe fixture scope must be bounded")
check("https://www.postgresql.org/docs/18/ddl-rowsecurity.html" in source, "lesson must pin PostgreSQL major version")
check("id: 'postgres-row-security'" in resources and "https://www.postgresql.org/docs/18/ddl-rowsecurity.html" in resources, "resource record must match the versioned official URL")
check("sourceIds: ['postgres-row-security']" in meta, "documented checkpoint must point to the reviewed source")

fences = re.findall(r"^```python\n([\s\S]*?)^```\s*$", source, re.M)
check(len(fences) == 1, f"expected one Python fence, found {len(fences)}")
compile(fences[0], str(LESSON), "exec")
example_run = subprocess.run(
    [sys.executable, "-c", fences[0]],
    cwd=ROOT / "examples/permission-filtering",
    capture_output=True,
    text=True,
)
check(example_run.returncode == 0, example_run.stdout + example_run.stderr)
check(example_run.stdout == "" and example_run.stderr == "", "lesson code example executes cleanly")
check('Principal(user_id="alice", tenant_id="tenant-a")' in fences[0] and "retrieve_for_context(principal" in fences[0], "example must pass the trusted principal")
check("最多接受 500 个去重候选" in source and "超过时显式抛出 `ValueError`" in source, "candidate limit and fail-fast behavior documented")
for phrase in (
    "正文水合前",
    "权限撤销要使缓存失效",
    "BYPASSRLS",
    "FORCE ROW LEVEL SECURITY",
    "竞态",
    "连接池复用",
):
    check(phrase in source, f"missing security boundary: {phrase}")

print(json.dumps({"checks": checks, "passed": checks, "providerCalls": 0, "externalNetworkCalls": 0}, ensure_ascii=False))
