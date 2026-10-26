"""Offline accuracy and executable-example checks for the Messages API lesson."""

from __future__ import annotations

import ast
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/llm-api-basics/03-messages-api.mdx"
text = LESSON.read_text(encoding="utf-8")


def check(condition: bool, description: str) -> None:
    if not condition:
        raise AssertionError(description)
    print(f"PASS {description}")


python_fences = re.findall(r"```python\n(.*?)\n```", text, flags=re.S)
check(len(python_fences) == 4, "all four Python examples are present")
for index, source in enumerate(python_fences, start=1):
    ast.parse(source, filename=f"messages-api-fence-{index}.py")
check(True, "all Python fences parse without executing provider calls")

validator_source = next(
    source for source in python_fences if "def validate_weather_input" in source
)
module = ast.parse(validator_source)
validator_nodes = [
    node
    for node in module.body
    if (isinstance(node, ast.Assign) and any(
        isinstance(target, ast.Name)
        and target.id in {"ALLOWED_CITIES", "ALLOWED_UNITS"}
        for target in node.targets
    ))
    or (
        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "validate_weather_input"
    )
]
namespace: dict[str, object] = {}
exec(compile(ast.Module(body=validator_nodes, type_ignores=[]), "validator.py", "exec"), namespace)
validate = namespace["validate_weather_input"]
assert callable(validate)
check(
    validate({"city": "北京"}) == {"city": "北京", "unit": "celsius"},
    "validator accepts an allowed city and applies the documented default",
)
for invalid in (
    [],
    {"city": 7},
    {"city": "北京", "unit": 3},
    {"city": "深圳"},
    {"city": "上海", "unit": "kelvin"},
    {"city": "北京", "unexpected": True},
):
    try:
        validate(invalid)
    except ValueError:
        continue
    raise AssertionError(f"validator accepted invalid input: {invalid!r}")
check(True, "validator rejects wrong types, disallowed values, and unknown fields")

required_phrases = (
    "原文中声称的 63/129 个事件",
    "客户端关闭或 SDK 取消不自动证明 provider 已停止生成",
    "等待完整 Message",
    "stop_reason == \"tool_use\"",
    "不会执行任何外部副作用",
    "未知值应进入显式兼容分支",
    "strict tool use",
)
for phrase in required_phrases:
    check(phrase in text, f"lesson states boundary: {phrase}")

withdrawn_claims = (
    "工具参数 18 个分片拼成完整 JSON",
    "省下未生成部分的费用",
    "工具参数的键值对是逐个发送的",
    "把事件之间的间隔误判为卡死",
)
for phrase in withdrawn_claims:
    check(phrase not in text, f"withdrawn unsupported claim absent: {phrase}")

check(True, "offline review complete; providerCalls=0; no external tool executed")
