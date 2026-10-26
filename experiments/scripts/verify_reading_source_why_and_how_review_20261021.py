import contextlib
import hashlib
import inspect
import io
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/reading-source/01-why-and-how.mdx"
META = ROOT / "src/content/chapters/reading-source/meta.ts"
source = LESSON.read_text()
meta = META.read_text()
from langchain_core.tools import base as base_mod, structured as structured_mod

structured_from_source = inspect.getsource(structured_mod.StructuredTool.from_function)
input_schema_source = inspect.getsource(base_mod.BaseTool.get_input_schema)
tool_call_schema_source = inspect.getsource(base_mod.BaseTool.tool_call_schema.fget)
checks = 0


def check(condition, message):
    global checks
    assert condition, message
    checks += 1


check("create_schema_from_function" in structured_from_source, "default inference must call the pinned schema builder")
check("args_schema is None" in structured_from_source and "infer_schema" in structured_from_source, "inspect both inferred and explicit schema routes")
check("create_schema_from_function" in input_schema_source, "input-schema fallback must call the schema builder")
check("get_input_schema" in tool_call_schema_source and "_create_subset_model" in tool_call_schema_source, "model-visible tool schema must be derived from the input schema")
check("_get_filtered_args" not in structured_from_source + input_schema_source + tool_call_schema_source, "do not misidentify an unused helper as a call-chain node")

fences = re.findall(r"^```python\n([\s\S]*?)^```\s*$", source, re.M)
check(len(fences) == 3, f"expected three Python fences, found {len(fences)}")
check(max(map(len, fences[-1].splitlines())) <= 88, "the executable Python fence must fit the article")
check('return tool_.tool_call_schema.model_json_schema()["properties"]["day"]' in fences[-1], "inspect the model-visible tool schema rather than only args_schema")
compile(fences[-1], str(LESSON), "exec")
captured = io.StringIO()
with contextlib.redirect_stdout(captured):
    exec(compile(fences[-1], str(LESSON), "exec"), {"__name__": "__main__"})
output = captured.getvalue()
check('A default {"title": "Day", "type": "string"}' in output, output)
check('B parsed {"description": "只能是「明天」或「后天」"' in output, output)
check('C Literal {"description": "查询的日期", "enum": ["明天", "后天"]' in output, output)
check('D args_schema {"description": "显式 schema 的日期", "enum": ["明天", "后天"]' in output, output)
check("default tool description contains Args: True" in output, output)
check("langchain_core/tools/convert.py" in output and "langchain_core/tools/base.py" in output, output)
check("langchain_core/tools/structured.py" in output, output)
check("StructuredTool.from_function" in output and "tool_call_schema" in output, output)
check('assert version("langchain-core") == "0.3.63"' in fences[-1], "the script must fail closed on a different version")
check('assert "description" not in field_schema(a_default)' in fences[-1], "default field description must be asserted")
check('assert "Args:" in (a_default.description or "")' in fences[-1], "tool-level raw docstring must be asserted")
check('assert "enum" not in field_schema(b_parsed)' in fences[-1], "natural-language prose must not be mistaken for enum")
check('field_schema(c_literal)["enum"]' in fences[-1] and 'field_schema(d_explicit)["enum"]' in fences[-1], "both constraint construction routes must be asserted")
check("本地四组断言只验证该版本" in source, "runtime and provider limitations must be explicit")
check("生成期执行与否取决于 endpoint" in source, "generation-time enum enforcement must be endpoint-scoped")
check("工具宿主必须在副作用发生前校验" in source, "host validation must precede side effects")
check("机器可读" in source and "本地安全边界" in source, "distinguish schema representation from host enforcement")
check("源码能提供关于特定版本实现的**一手材料**" in source, "source inspection must not be equated with runtime verification")
check("不能证明某种标签普遍安全" in source, "historical injection example must stay fixture-scoped")
check("通常只要几分钟" not in source and "十几分钟" not in source and "一小时" not in source, "remove unsupported universal duration estimates")
check("title: 什么时候该读源码，以及怎样核实实现边界" in source, "title must match the conditional, not mandatory, framing")
check("title: '什么时候该读源码，以及怎样核实实现边界'" in meta, "metadata title must match lesson")
check("id: 'langchain-docstring-schema-boundary'" in meta and "basis: 'documented'" in meta, "lesson needs a documented schema checkpoint")
check("sourceIds: ['langchain-core-063-tool-convert', 'langchain-core-063-tool-structured', 'langchain-core-063-tool-base', 'pydantic-json-schema']" in meta, "checkpoint source IDs must cover the full schema path")
check("model_json_schema() 导出已经构造的 schema" in meta, "the checkpoint must distinguish construction from export")
check("_get_filtered_args" in source and "不能将 `_get_filtered_args` 的定义误当作此处的调用节点" in source, "a definition hit is not call-path evidence")
check("langchain-core-063-tool-convert" in meta, "convert.py source ID must be present")
check("langchain-core-063-tool-base" in meta, "base.py source ID must be present")
check("被丢掉的" not in source and "请求不会报错" not in source and "生成阶段就被挡掉" not in source, "withdraw overgeneralized claims")

print(json.dumps({"checks": checks, "passed": checks, "pythonFencesCompiled": 1, "providerCalls": 0, "fixtureOnly": True}, ensure_ascii=False))
