from __future__ import annotations

import re
import sys
import textwrap
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/tool-calling/04-parallel-and-errors.mdx"
text = LESSON.read_text()
META = (ROOT / "src/content/chapters/tool-calling/meta.ts").read_text()
RESOURCES = (ROOT / "src/content/curriculum/resources.ts").read_text()
required_sources = (
    "anthropic-parallel-tool-use",
    "anthropic-handle-tool-calls",
    "anthropic-stop-reasons",
    "anthropic-extended-thinking",
    "anthropic-api-errors",
    "stripe-idempotency-keys",
)
for source_id in required_sources:
    assert f"'{source_id}'" in META, f"lesson metadata missing {source_id}"
    assert f"'{source_id}': {{" in RESOURCES, f"resource registry missing {source_id}"
assert "不能确认分母、复算行为或推断普遍因果" in META
assert "不能支持模型通常谨慎或重复风险很低的结论" in META
fences = re.findall(r"```python\n(.*?)\n```", text, flags=re.S)
assert len(fences) == 2, f"expected the idempotency and tool-loop examples, found {len(fences)}"
sources = [textwrap.dedent(source) for source in fences]
for index, source in enumerate(sources, 1):
    compile(source, f"{LESSON}:python-fence-{index}", "exec")

def execute_fixture(name: str, source: str) -> dict[str, object]:
    module = types.ModuleType(name)
    sys.modules[name] = module
    try:
        exec(compile(source, f"{LESSON}:{name}", "exec"), module.__dict__)
        module.local_checks()
        return module.__dict__
    finally:
        sys.modules.pop(name, None)


idempotency_ns = execute_fixture("parallel_idempotency_fixture", sources[0])
tool_loop_ns = execute_fixture("parallel_tool_loop_fixture", sources[1])

idempotency, tool_loop = sources
assert "tool_use.id" not in idempotency, "protocol correlation ID must not be presented as durable business idempotency"
assert "BEGIN IMMEDIATE" in idempotency and "PRIMARY KEY" in idempotency
assert "request_hash" in idempotency, "same key with different action arguments must be rejected"
assert 'resp.stop_reason == "end_turn"' in tool_loop
assert 'completed_without_text' in tool_loop, "empty end_turn must not be reported as a completed answer"
assert "不要把相同的空响应原样回放" in text
assert 'resp.stop_reason != "tool_use"' in tool_loop
assert "ThreadPoolExecutor(max_workers=min(MAX_WORKERS, len(blocks)))" in tool_loop
assert "is_error" in tool_loop and "tool_use_id" in tool_loop
assert "len(ids) != len(set(ids))" in tool_loop, "duplicate tool IDs must fail before dispatch"
assert "all(isinstance(block.id, str) and block.id.strip() for block in blocks)" in tool_loop
assert 'or not isinstance(block.id, str)' in tool_loop and 'or not block.id.strip()' in tool_loop
assert "except Exception" in tool_loop, "one tool exception must not abort the whole batch without a matching result"
assert "retryable" not in tool_loop or "model may ignore" in text
assert "模型在这些场景里比传言中谨慎得多" not in text
assert "本节没有测量普遍重试倾向" in text
assert "首次调用" not in text or "同一 action_id" in text
assert text.count("幂等键应该由") <= 1, "duplicate advice paragraph"

print({
    "lesson": "tool-calling/parallel-and-errors",
    "python_fences_compiled": len(sources),
    "fixture_checks": 2,
    "new_regressions": [
        "empty_end_turn_is_distinct_from_answer",
        "duplicate_ids_fail_before_dispatch",
        "missing_nonstring_and_whitespace_ids_fail_closed",
    ],
    "status": "passed",
})
