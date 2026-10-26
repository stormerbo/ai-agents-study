from __future__ import annotations

import hashlib
import json
import re
import sys
import textwrap
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/tool-calling/03-poka-yoke.mdx"
META = (ROOT / "src/content/chapters/tool-calling/meta.ts").read_text()
RESOURCES = (ROOT / "src/content/curriculum/resources.ts").read_text()
text = LESSON.read_text()
fences = re.findall(r"```python\n(.*?)\n```", text, flags=re.S)
assert len(fences) == 1, f"expected one Python fence, got {len(fences)}"
source = textwrap.dedent(fences[0])
compile(source, str(LESSON), "exec")
namespace: dict[str, object] = {"__name__": "poka_yoke_review_fixture"}
exec(compile(source, str(LESSON), "exec"), namespace)
namespace["local_checks"]()

class Block(types.SimpleNamespace):
    pass


class FakeMessages:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return next(self.responses)


class FakeClient:
    def __init__(self, responses):
        self.messages = FakeMessages(responses)


def response(stop_reason, *blocks):
    return Block(stop_reason=stop_reason, content=list(blocks))


def run_case(responses, *, expect, expected_tool_result=None, service=None, approval_gate=None):
    client = FakeClient(responses)
    fake_module = types.SimpleNamespace(Anthropic=lambda **_: client)
    previous = sys.modules.get("anthropic")
    sys.modules["anthropic"] = fake_module
    import os

    os.environ["VERIFY_MODEL"] = "fixture-model"
    service = service or namespace["FileService"]()
    gate = approval_gate or (lambda *_: True)
    try:
        result = namespace["run_with_anthropic"](
            "fixture task", service, "demo-user", "fixture-session", gate
        )
    finally:
        if previous is None:
            sys.modules.pop("anthropic", None)
        else:
            sys.modules["anthropic"] = previous
    assert result == expect, (result, expect)
    if expected_tool_result is not None:
        assert len(client.messages.calls) == 2
        results = client.messages.calls[1]["messages"][-1]["content"]
        assert results == [expected_tool_result], results
    return result, client, service


run_case(
    [response("end_turn", Block(type="text", text="done"))],
    expect="completed: done",
)
run_case([response("end_turn")], expect="completed_without_text")
for reason in ("max_tokens", "refusal", "pause_turn", "unknown_future_reason"):
    run_case([response(reason)], expect=f"not_completed: stop_reason={reason}")

service = namespace["FileService"]()
rows = json.loads(service.list_files("demo-user", "fixture-session"))["files"]
temporary = next(row for row in rows if row["kind"] == "temporary")
approvals = []
missing_id_call = Block(type="tool_use", name="delete_file", input={"file_id": temporary["file_id"]})
_, client, _ = run_case(
    [response("tool_use", missing_id_call)],
    expect="not_completed: invalid_tool_use_id", service=service,
    approval_gate=lambda *args: approvals.append(args) or True,
)
assert temporary["name"] in service.files and approvals == [] and len(client.messages.calls) == 1

duplicate_id_calls = [
    Block(type="tool_use", id="same-id", name="delete_file", input={"file_id": temporary["file_id"]}),
    Block(type="tool_use", id="same-id", name="delete_file", input={"file_id": temporary["file_id"]}),
]
service = namespace["FileService"]()
rows = json.loads(service.list_files("demo-user", "fixture-session"))["files"]
temporary = next(row for row in rows if row["kind"] == "temporary")
duplicate_id_calls = [
    Block(type="tool_use", id="same-id", name="delete_file", input={"file_id": temporary["file_id"]}),
    Block(type="tool_use", id="same-id", name="delete_file", input={"file_id": temporary["file_id"]}),
]
approvals = []
_, client, _ = run_case(
    [response("tool_use", *duplicate_id_calls)],
    expect="not_completed: duplicate_tool_use_id", service=service,
    approval_gate=lambda *args: approvals.append(args) or True,
)
assert temporary["name"] in service.files and approvals == [] and len(client.messages.calls) == 1

unknown_call = Block(type="tool_use", id="toolu_unknown", name="not_registered", input={})
run_case(
    [response("tool_use", unknown_call), response("end_turn", Block(type="text", text="stopped"))],
    expect="completed: stopped",
    expected_tool_result={
        "type": "tool_result",
        "tool_use_id": "toolu_unknown",
        "content": '{"error": "unknown_tool"}',
        "is_error": True,
    },
)

for phrase in (
    "逐次请求、响应与评分器未归档",
    "分母口径无法重建",
    "file_id` 仍是模型可生成的字符串",
    "宿主验证引用属于当前可信用户/任务",
    "独立确认流程",
    "多副本部署要用共享的、可原子消费的 grant/业务存储",
    "不能加密其中的文件名",
):
    assert phrase in text, f"missing evidence boundary: {phrase}"

poka_meta = re.search(
    r"id: 'tool-calling/poka-yoke',(?P<body>.*?resourceIds: \[(?P<ids>.*?)\])",
    META,
    flags=re.S,
)
assert poka_meta, "missing poka-yoke lesson metadata/resourceIds"
for resource_id in (
    "anthropic-building-effective-agents",
    "anthropic-stop-reasons",
    "anthropic-handle-tool-calls",
    "anthropic-strict-tool-use",
    "owasp-authorization-cheat-sheet",
    "aws-s3-presigned-urls",
    "owasp-rest-security-cheat-sheet",
    "rfc-2104-hmac",
    "json-schema-validation-2020-12",
):
    assert f"'{resource_id}'" in poka_meta.group("ids"), f"not linked by lesson metadata: {resource_id}"
    assert resource_id in RESOURCES, f"missing resource record: {resource_id}"

assert "只要拿到随机引用就有权限" not in text
assert "结构上不可能同时传" not in text

print({
    "lesson": "tool-calling/poka-yoke",
    "python_fences_compiled": len(fences),
    "local_security_checks": 10,
    "fake_provider_cases": 9,
    "checks_passed": 35,
    "source_boundary_checks": 7,
    "resource_checks": 9,
    "status": "passed",
    "lesson_sha256": hashlib.sha256(LESSON.read_bytes()).hexdigest(),
})
