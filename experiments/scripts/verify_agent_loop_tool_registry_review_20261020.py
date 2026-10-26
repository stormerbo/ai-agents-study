"""Review the tool registry lesson's authorization, error, and scheduling contracts."""

from __future__ import annotations

import contextlib
import io
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/agent-loop/02-tool-registry.mdx"
META = ROOT / "src/content/chapters/agent-loop/meta.ts"
source = LESSON.read_text(encoding="utf-8")
meta = META.read_text(encoding="utf-8")
fences = re.findall(r"^```python\s*\n([\s\S]*?)^```\s*$", source, re.MULTILINE)
assert len(fences) >= 6, f"expected at least 6 Python fences, found {len(fences)}"
for index, fence in enumerate(fences, start=1):
    compile(fence, f"{LESSON}:python-fence-{index}", "exec")

scheduler_source = next(fence for fence in fences if "def dispatch(blocks, registry):" in fence)
scheduler_demo = io.StringIO()
with contextlib.redirect_stdout(scheduler_demo):
    exec(compile(scheduler_source, "registry-scheduler-demo", "exec"), {"__name__": "__main__"})
demo_output = scheduler_demo.getvalue()
assert "回填顺序：['t1', 't2', 't3']" in demo_output
assert "'created': 'ORD-1'" in demo_output

scheduler: dict[str, object] = {"__name__": "registry_scheduler"}
exec(compile(scheduler_source, "registry-scheduler", "exec"), scheduler)
Registry = scheduler["Registry"]
dispatch = scheduler["dispatch"]
backfill = scheduler["backfill"]
DispatchNeedsReconciliation = scheduler["DispatchNeedsReconciliation"]

events: list[str] = []
registry = Registry()
registry.tool("read", lambda tag: events.append(tag) or {"value": tag}, parallel_safe=True)
registry.tool("write", lambda tag: events.append(tag) or {"value": tag})
ordered_blocks = [
    {"id": "read-before", "name": "read", "input": {"tag": "read-before"}},
    {"id": "write-barrier", "name": "write", "input": {"tag": "write"}},
    {"id": "read-after", "name": "read", "input": {"tag": "read-after"}},
]
ordered_results = dispatch(ordered_blocks, registry)
assert events == ["read-before", "write", "read-after"]
assert list(ordered_results) == ["read-before", "write-barrier", "read-after"]
formatted = backfill(ordered_blocks, ordered_results)
assert [block["tool_use_id"] for block in formatted] == [
    "read-before",
    "write-barrier",
    "read-after",
]
assert all(isinstance(block["content"], str) for block in formatted)

not_executed = dispatch(
    [{"id": "missing", "name": "unregistered", "input": {}}], registry
)
assert backfill([{"id": "missing", "name": "unregistered", "input": {}}], not_executed)[0][
    "is_error"
]
try:
    backfill(
        [{"id": "unknown", "name": "write", "input": {}}],
        {"unknown": {"error": "unknown", "execution": "outcome_unknown"}},
    )
except RuntimeError:
    pass
else:
    raise AssertionError("backfill must reject an unknown side-effect outcome")

events.clear()
failing_batch_registry = Registry()
failing_batch_registry.tool("ok", lambda: events.append("ok") or "done", parallel_safe=True)

def commit_then_raise():
    events.append("committed-before-timeout")
    raise TimeoutError("receipt lost")

failing_batch_registry.tool("uncertain", commit_then_raise, parallel_safe=True)
try:
    dispatch(
        [
            {"id": "ok-id", "name": "ok", "input": {}},
            {"id": "uncertain-id", "name": "uncertain", "input": {}},
        ],
        failing_batch_registry,
    )
except DispatchNeedsReconciliation as exc:
    assert exc.failed_ids == ["uncertain-id"]
    assert exc.partial_results["ok-id"] == "done"
    assert exc.partial_results["uncertain-id"]["execution"] == "outcome_unknown"
else:
    raise AssertionError("a timeout in a parallel batch must pause for reconciliation")
assert set(events) == {"ok", "committed-before-timeout"}

registry_source = next(
    fence for fence in fences if "class KnownToolFailure(Exception):" in fence
)
core: dict[str, object] = {"__name__": "registry_core"}
exec(compile(registry_source, "registry-core", "exec"), core)
registry_core = core["reg"]
core_demo = io.StringIO()
with contextlib.redirect_stdout(core_demo):
    exec(compile(registry_source, "registry-core-demo", "exec"), {"__name__": "__main__"})
assert "五次调用里四次是确定错误" in core_demo.getvalue()
assert registry_core.execute("boom", {})["is_error"] is True
assert registry_core.execute("get_weather", {"city": "北京", "day": "明天"})[
    "temp_c"
] == 31
assert registry_core.validate({"n": True}, {"properties": {"n": {"type": "integer"}}})
assert registry_core.validate({"n": 1}, {"properties": {}, "additionalProperties": False})

registry_core.tool(
    {"name": "write_then_timeout", "input_schema": {"type": "object", "properties": {}}}
)(lambda: (_ for _ in ()).throw(core["OutcomeUnknown"]("receipt missing")))
try:
    registry_core.execute("write_then_timeout", {})
except core["PauseAndReconcile"]:
    pass
else:
    raise AssertionError("unknown side-effect outcome must stop model continuation")

required_text = [
    "注册表是执行入口，不自动构成授权边界",
    "不能只问“会不会改变外部状态”",
    "只把连续的并发安全调用组成一批",
    "结果未知",
    "不要默认把原始参数完整落日志",
]
for phrase in required_text:
    assert phrase in source, f"missing corrected lesson boundary: {phrase}"
assert "动作空间" in source and "封闭" not in source
assert "owasp-authorization-cheat-sheet" in meta
assert "anthropic-parallel-tool-use" in meta

print(
    f"PASS: {len(fences)} Python fences compile and both demos execute; mixed-call order, ID mapping, "
    "unknown-outcome pause, authorization guidance, error classification, and validator boundaries verified."
)
