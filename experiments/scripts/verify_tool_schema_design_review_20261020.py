from __future__ import annotations

import contextlib
import hashlib
import io
import os
import re
import sys
import textwrap
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/tool-calling/02-schema-design.mdx"
text = LESSON.read_text()
META = (ROOT / "src/content/chapters/tool-calling/meta.ts").read_text()
RESOURCES = (ROOT / "src/content/curriculum/resources.ts").read_text()
fences = re.findall(r"```python\n(.*?)\n```", text, flags=re.S)
assert len(fences) == 3, f"expected 3 Python fences, got {len(fences)}"
for source in fences:
    compile(textwrap.dedent(source), str(LESSON), "exec")

# Exercise the SDK sampler with fake responses only; never contact a provider.
class FakeMessages:
    def __init__(self, response):
        self.responses = list(response) if isinstance(response, list) else [response]
    def create(self, **kwargs):
        return self.responses.pop(0)

def load_probe(response):
    fake_sdk = types.ModuleType("anthropic")
    fake_sdk.Anthropic = lambda **kwargs: types.SimpleNamespace(messages=FakeMessages(response))
    previous_sdk = sys.modules.get("anthropic")
    previous_model = os.environ.get("VERIFY_MODEL")
    sys.modules["anthropic"] = fake_sdk
    os.environ["VERIFY_MODEL"] = "offline-test-model"
    try:
        namespace = {"__name__": "schema_review_probe"}
        exec(compile(textwrap.dedent(fences[1]), str(LESSON), "exec"), namespace)
        return namespace["probe"]("fixture question")
    finally:
        if previous_sdk is None:
            sys.modules.pop("anthropic", None)
        else:
            sys.modules["anthropic"] = previous_sdk
        if previous_model is None:
            os.environ.pop("VERIFY_MODEL", None)
        else:
            os.environ["VERIFY_MODEL"] = previous_model

def run_sampler(responses):
    fake_api = FakeMessages(responses)
    fake_sdk = types.ModuleType("anthropic")
    fake_sdk.Anthropic = lambda **kwargs: types.SimpleNamespace(messages=fake_api)
    previous_sdk = sys.modules.get("anthropic")
    previous_model = os.environ.get("VERIFY_MODEL")
    sys.modules["anthropic"] = fake_sdk
    os.environ["VERIFY_MODEL"] = "offline-test-model"
    output = io.StringIO()
    try:
        namespace = {"__name__": "__main__"}
        with contextlib.redirect_stdout(output):
            exec(compile(textwrap.dedent(fences[1]), str(LESSON), "exec"), namespace)
        return output.getvalue()
    finally:
        if previous_sdk is None:
            sys.modules.pop("anthropic", None)
        else:
            sys.modules["anthropic"] = previous_sdk
        if previous_model is None:
            os.environ.pop("VERIFY_MODEL", None)
        else:
            os.environ["VERIFY_MODEL"] = previous_model

no_call = types.SimpleNamespace(stop_reason="tool_use", content=[])
multiple_calls = types.SimpleNamespace(stop_reason="tool_use", content=[
    types.SimpleNamespace(type="tool_use", name="set_priority", input={"level": "high"}),
    types.SimpleNamespace(type="tool_use", name="set_priority", input={"level": "low"}),
])
assert load_probe(no_call)["status"].startswith("invalid_response:"), "tool_use without a call must not be scored complete"
assert load_probe(multiple_calls)["status"].startswith("invalid_response:"), "multiple calls must not be silently scored as a single probe"
one_call = types.SimpleNamespace(stop_reason="tool_use", content=[
    types.SimpleNamespace(type="tool_use", name="set_priority", input={"level": "high"})
])
assert load_probe(one_call)["status"] == "tool_call"
assert load_probe(types.SimpleNamespace(stop_reason="end_turn", content=[]))["status"] == "complete_no_tool"
malformed_level = load_probe(types.SimpleNamespace(stop_reason="tool_use", content=[
    types.SimpleNamespace(type="tool_use", name="set_priority", input={"level": []})
]))
assert malformed_level["status"] == "tool_call"
assert isinstance(malformed_level["calls"][0]["input"]["level"], list)
assert "ok = isinstance(val, str) and val in LEGAL" in fences[1]
sampler_output = run_sampler([
    one_call,
    types.SimpleNamespace(stop_reason="end_turn", content=[]),
    types.SimpleNamespace(stop_reason="tool_use", content=[
        types.SimpleNamespace(type="tool_use", name="set_priority", input={"level": []})
    ]),
])
assert "✅ 调用了" in sampler_output
assert "✅ 正确地没调" in sampler_output
assert "参数 ❌ 非法：[]" in sampler_output, "non-string enum values must be scored safely"
assert "非 strict enum 不保证非法值消失" in sampler_output

# Run only the offline validator example, not the provider SDK sampler.
namespace: dict[str, object] = {"__name__": "schema_review_fixture"}
exec(compile(textwrap.dedent(fences[-1]), str(LESSON), "exec"), namespace)
validate = namespace["validate_tool_contracts"]
assert callable(validate)
assert validate([{"name": "ok_1", "input_schema": {
    "type": "object", "properties": {"x": {"type": "string"}}, "required": ["x"]
}}]) == []
assert any("name" in e for e in validate([{"name": "bad name", "input_schema": {"type": "object"}}]))
assert any("重复" in e for e in validate([
    {"name": "dup", "input_schema": {"type": "object"}},
    {"name": "dup", "input_schema": {"type": "object"}},
]))
assert any("properties" in e for e in validate([{"name": "req", "input_schema": {
    "type": "object", "properties": {"x": {}}, "required": ["missing"]
}}]))
assert validate({"not": "a list"}) == ["tools 必须是数组"]
assert any("required" in e for e in validate([{"name": "bad", "input_schema": {
    "type": "object", "properties": {}, "required": "x"
}}]))

for source in (
    "strict 模式",
    "原始请求与响应未归档",
    "本项目把它视为接口质量问题",
):
    assert source in text, f"missing reviewed boundary/source: {source}"
for source in ("anthropic-define-tools", "anthropic-strict-tool-use", "json-schema-validation-2020-12"):
    assert source in META and source in RESOURCES, f"missing linked official resource: {source}"
assert "工具唯一的决策依据" not in text
assert "生成时就不存在非法值" not in text
assert "非 strict enum 不保证非法值消失" in text
assert "所有模式仍需宿主校验" in text

print({
    "lesson": "tool-calling/schema-design",
    "python_fences_compiled": len(fences),
    "offline_contract_cases": 6,
    "probe_response_cases": 5,
    "sampler_output_cases": 4,
    "total_assertions_including_fence_compiles": 32,
    "providerCalls": 0,
    "externalNetworkCalls": 0,
    "lesson_sha256": hashlib.sha256(LESSON.read_bytes()).hexdigest(),
    "status": "passed",
})
