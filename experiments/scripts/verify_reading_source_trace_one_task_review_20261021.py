import contextlib
import hashlib
import inspect
import io
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/reading-source/03-trace-one-task.mdx"
META = ROOT / "src/content/chapters/reading-source/meta.ts"
source = LESSON.read_text()
meta = META.read_text()
from langchain_core.tools import base as base_mod, structured as structured_mod

structured_from_source = inspect.getsource(structured_mod.StructuredTool.from_function)
input_schema_source = inspect.getsource(base_mod.BaseTool.get_input_schema)
tool_call_schema_source = inspect.getsource(base_mod.BaseTool.tool_call_schema.fget)
create_schema_source = inspect.getsource(base_mod.create_schema_from_function)
checks = 0


def check(condition, message):
    global checks
    assert condition, message
    checks += 1


check("create_schema_from_function" in structured_from_source, "default schema inference must use the pinned constructor")
check("args_schema is None" in structured_from_source and "infer_schema" in structured_from_source, "distinguish inferred and explicit schema branches")
check("create_schema_from_function" in input_schema_source, "fallback input schema must invoke the constructor")
check("get_input_schema" in tool_call_schema_source and "_create_subset_model" in tool_call_schema_source, "tool-call schema must derive from the input model")
check("_get_filtered_args" not in structured_from_source + input_schema_source + tool_call_schema_source, "the symbol definition is not part of this traced call path")
check("model_json_schema" not in structured_from_source + input_schema_source + tool_call_schema_source + create_schema_source, "the traced construction functions do not perform JSON Schema export")

fences = re.findall(r"^```python\n([\s\S]*?)^```\s*$", source, re.M)
check(len(fences) == 3, f"expected three Python fences, found {len(fences)}")
bash_fences = re.findall(r"^```bash\n([\s\S]*?)^```\s*$", source, re.M)
check(max(map(len, bash_fences[0].splitlines())) <= 88, "the first shell fence must not overflow the article")
compile(fences[-1], str(LESSON), "exec")
check(max(map(len, fences[-1].splitlines())) <= 88, "the executable Python fence must not overflow the article")
namespace = {"__name__": "__main__"}
captured = io.StringIO()
with contextlib.redirect_stdout(captured):
    exec(compile(fences[-1], str(LESSON), "exec"), namespace)
output = captured.getvalue()
check('"type": "string"' in output and '"enum": ["明天", "后天"]' in output, output)
check('"description": "只能是「明天」或「后天」"' in output, output)
check('"description": "显式 schema 的日期", "enum": ["明天", "后天"]' in output, output)
check('参数说明没有进入字段 schema；本例完整 docstring 出现在工具级 description。' in output, output)
check("显式 args_schema" in output and "类型标注" in output, output)
check('assert summary(d_explicit)["enum"] == ["明天", "后天"]' in fences[-1], "explicit Pydantic args_schema must have an executable enum assertion")
check("base.py:214" in source and "tool_call_schema.model_json_schema()" in source, "trace the schema constructor and model-visible export")
check("_get_filtered_args`（base.py:95）" in source and "实际调用链节点" in source, "do not treat the helper definition as a caller")
check("BaseTool.get_input_schema（base.py:487）" in source and "BaseTool.tool_call_schema（base.py:464）" in source, "pin source locations to the executed package")
check("StructuredTool.from_function" in fences[-1] and "BaseTool.tool_call_schema.fget" in fences[-1], "execute the real source-path inspection")
check('return t.tool_call_schema.model_json_schema()["properties"]["day"]' in fences[-1], "inspect the model-visible tool-call schema")
check("parse_docstring 默认是 False" in output, output)
check("散文描述本身不构成机器校验约束。" in output, output)
check("最终 tool-call schema 和构造来源共同判定" in source, "final schema and construction source should be checked")
check("显式 `args_schema`" in source, "explicit args_schema must be included")
check("参数说明没有进入字段 schema" in source and "完整函数文档字符串" in source, "distinguish field description from tool description")
check('assert "只能是「明天」或「后天」" in (a_default.description or "")' in fences[-1], "assert docstring text appears in the default tool description")
check("model_json_schema()" in source and "不在此处创建字段约束" in source, "describe schema export rather than constraint origin")
check("langchain-core==0.3.63" in source, "claims must be version-scoped")
check("langchain-core%3D%3D0.3.63" in source, "source links must be immutable version links")
check("rg -n" in source and "搜索到一个同名符号不能证明" in source, "rg matches are candidates, not call-chain proof")
check("\\\\n\\\\n" not in source, "literal backslash-n should not leak into prose")
check("被静默丢弃" not in source and "约束完全由类型决定" not in source, "withdraw inaccurate absolute claims")
check("id: 'langchain-parse-docstring-behavior'" in meta, "trace lesson needs a documented checkpoint")
check("id: 'langchain-tool-call-schema-path'" in meta and "langchain-core-063-tool-structured" in meta and "pydantic-json-schema" in meta, "documented checkpoint must cite the actual call path and JSON Schema sources")
check("id: 'reading-source/trace-one-task'" in meta and "resourceIds: ['claude-agent-sdk', 'openai-agents-sdk-python', 'langchain-core-063-tool-convert', 'langchain-core-063-tool-base', 'langchain-core-063-tool-structured', 'python-typing-overload-314', 'pydantic-json-schema']" in meta, "trace lesson must register its sources")
check("providerCalls=0" not in output, "lesson code should not claim a verifier count")

print(json.dumps({"checks": checks, "passed": checks, "pythonFencesCompiled": 1, "providerCalls": 0, "fixtureOnly": True}, ensure_ascii=False))
