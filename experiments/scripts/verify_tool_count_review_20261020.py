from __future__ import annotations

import ast
import re
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LESSON_PATH = ROOT / "src/content/chapters/tool-calling/05-tool-count.mdx"
META_PATH = ROOT / "src/content/chapters/tool-calling/meta.ts"
RESOURCES_PATH = ROOT / "src/content/curriculum/resources.ts"
text = LESSON_PATH.read_text()
meta = META_PATH.read_text()
resources = RESOURCES_PATH.read_text()
fences = re.findall(r"```python\n(.*?)\n```", text, flags=re.S)
assert len(fences) == 3, f"expected 3 Python fences, got {len(fences)}"
for index, source in enumerate(fences, 1):
    ast.parse(source, filename=f"{LESSON_PATH}:fence-{index}")

assert "不含逐次原始请求、响应和 scorer" in text
assert "不要把本节样本的斜率或费用外推到自己的 endpoint" in text
assert "cache_read_input_tokens" in fences[1]
assert "max_tokens" in fences[1]
assert "stop_reason" in fences[1]
assert "len(calls) != 1" in fences[1]
assert "expected not in available" in fences[1]
assert "REPEATS = 5" in fences[1]
assert "len(PROBES) * REPEATS" in fences[1]
assert "MAX_MODEL_CALLS = 85" in fences[1]
assert "planned_calls > MAX_MODEL_CALLS" in fences[1]
assert "TOOLS.extend(" in fences[1] and "range(1, 13)" in fences[1]
assert "cache_creation_input_tokens" in fences[1]
assert "usage.{field} is unavailable" in fences[1]
assert "no hard limit" not in text.lower()
assert "5 题里只有 1 题是货真价实的选择错误" not in text
assert "这笔钱每一轮都要再付一次" not in text
assert "工具数量膨胀后仍全量暴露：选择准确率会明显下降" not in meta

tree = ast.parse(fences[1])
accuracy = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "accuracy")
coverage = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "validate_probe_coverage")
module = ast.Module(body=[coverage, accuracy], type_ignores=[])

class FakeMessages:
    def __init__(self, response):
        self.response = response
        self.calls = 0

    def create(self, **_kwargs):
        self.calls += 1
        return self.response


class FakeClient:
    def __init__(self, response):
        self.messages = FakeMessages(response)


def score(response, tools=None):
    env = {
        "PROBES": [("probe", "lookup")],
        "REPEATS": 1,
        "MODEL": "offline-fixture",
        "client": FakeClient(response),
    }
    exec(compile(module, str(LESSON_PATH), "exec"), env)
    return env["accuracy"](tools or [{"name": "lookup"}])


def response(reason, *blocks):
    return types.SimpleNamespace(stop_reason=reason, content=list(blocks))


tool = lambda name: types.SimpleNamespace(type="tool_use", name=name)

assert score(response("tool_use", tool("lookup"))) == (1, [])
assert score(response("end_turn"))[0] == 0
assert "probe_1_trial_1:incomplete(stop_reason=end_turn)" in score(response("end_turn"))[1]
assert score(response("max_tokens", tool("lookup")))[0] == 0
assert score(response("tool_use", tool("lookup"), tool("other")))[0] == 0
try:
    score(response("tool_use", tool("lookup")), tools=[{"name": "other"}])
except ValueError as exc:
    assert "missing expected tools" in str(exc)
else:
    raise AssertionError("unanswerable probe subset must fail before model scoring")

assert "anthropic-manage-tool-context" in meta
assert "anthropic-tool-use-prompt-caching" in meta
assert "anthropic-manage-tool-context" in resources
assert "anthropic-tool-use-prompt-caching" in resources
# Route selection must reject malformed model-controlled values without raising.
router_tree = ast.parse(fences[0])
route_fn = next(node for node in router_tree.body if isinstance(node, ast.FunctionDef) and node.name == "route")
router_module = ast.Module(body=[route_fn], type_ignores=[])


def route_value(value):
    fake = FakeClient(response(
        "tool_use",
        types.SimpleNamespace(type="tool_use", name="select_tool_group", input={"group": value}),
    ))
    env = {
        "client": fake, "MODEL": "offline-fixture", "GROUP_TOOL": {}, "CORE": [],
        "GROUPS": {"orders": ["safe-read-tool"]},
    }
    exec(compile(router_module, str(LESSON_PATH), "exec"), env)
    return env["route"]("system", "task")


assert route_value("orders") == "orders"
assert route_value("unknown") is None
assert route_value([]) is None

tools_for_fn = next(
    node for node in router_tree.body if isinstance(node, ast.FunctionDef) and node.name == "tools_for"
)
tools_for_module = ast.Module(body=[tools_for_fn], type_ignores=[])
tools_for_env = {"CORE": ["core-read-tool"], "GROUPS": {"orders": ["safe-read-tool"]}}
exec(compile(tools_for_module, str(LESSON_PATH), "exec"), tools_for_env)
assert tools_for_env["tools_for"]("orders") == ["core-read-tool", "safe-read-tool"]
try:
    tools_for_env["tools_for"]([])
except ValueError as exc:
    assert "unknown_tool_group" in str(exc)
else:
    raise AssertionError("non-string group must be rejected as a controlled input error")

validate_fn = next(
    node for node in tree.body
    if isinstance(node, ast.FunctionDef) and node.name == "validate_probe_coverage"
)
validate_module = ast.Module(body=[validate_fn], type_ignores=[])
validate_env = {"PROBES": [("probe", "lookup")]}
exec(compile(validate_module, str(LESSON_PATH), "exec"), validate_env)
assert validate_env["validate_probe_coverage"]([{"name": "lookup"}]) is None
try:
    validate_env["validate_probe_coverage"]([{"name": "other"}])
except ValueError as exc:
    assert "missing expected tools" in str(exc)
else:
    raise AssertionError("an unanswerable probe must fail before any model request")
assert fences[1].index("validate_probe_coverage(TOOLS[:n])") < fences[1].index("baseline_usage =")
assert fences[1].index("planned_calls > MAX_MODEL_CALLS") < fences[1].index("baseline_usage =")

usage_fn = next(
    node for node in tree.body
    if isinstance(node, ast.FunctionDef) and node.name == "request_input_usage"
)
usage_module = ast.Module(body=[usage_fn], type_ignores=[])
usage = types.SimpleNamespace(
    input_tokens=100, cache_read_input_tokens=20, cache_creation_input_tokens=5,
)
usage_env = {"MODEL": "offline-fixture", "client": FakeClient(types.SimpleNamespace(usage=usage))}
exec(compile(usage_module, str(LESSON_PATH), "exec"), usage_env)
assert usage_env["request_input_usage"]([]) == (100, 20, 5)
for bad_usage in (
    types.SimpleNamespace(input_tokens=None),
    types.SimpleNamespace(input_tokens=100, cache_read_input_tokens=-1),
):
    usage_env["client"] = FakeClient(types.SimpleNamespace(usage=bad_usage))
    try:
        usage_env["request_input_usage"]([])
    except ValueError:
        pass
    else:
        raise AssertionError("missing or invalid usage must not be reported as zero")

overhead_tree = ast.parse(fences[2])
overhead_fn = next(
    node for node in overhead_tree.body
    if isinstance(node, ast.FunctionDef) and node.name == "tools_overhead"
)
overhead_env = {}
exec(compile(ast.Module(body=[overhead_fn], type_ignores=[]), str(LESSON_PATH), "exec"), overhead_env)
assert overhead_env["tools_overhead"](
    types.SimpleNamespace(input_tokens=100, cache_read_input_tokens=20, cache_creation_input_tokens=5),
    types.SimpleNamespace(input_tokens=80, cache_read_input_tokens=0, cache_creation_input_tokens=0),
) == 45
try:
    overhead_env["tools_overhead"](
        types.SimpleNamespace(input_tokens=None, cache_read_input_tokens=0, cache_creation_input_tokens=0),
        types.SimpleNamespace(input_tokens=80, cache_read_input_tokens=0, cache_creation_input_tokens=0),
    )
except ValueError:
    pass
else:
    raise AssertionError("missing input usage must not be silently treated as zero")

print({
    "lesson": "tool-calling/tool-count",
    "python_fences_compiled": len(fences),
    "scorer_fixtures": 6,
    "router_fixtures": 5,
    "usage_fixtures": 3,
    "budget_and_preflight_order_checks": 2,
    "overhead_helper_fixtures": 2,
    "status": "passed",
})
