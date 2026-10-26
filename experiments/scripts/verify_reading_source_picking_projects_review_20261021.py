import contextlib
import hashlib
import io
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/reading-source/02-picking-projects.mdx"
META = ROOT / "src/content/chapters/reading-source/meta.ts"
RESOURCES = ROOT / "src/content/curriculum/resources.ts"
source = LESSON.read_text()
meta = META.read_text()
resources = RESOURCES.read_text()
checks = 0


def check(condition, message):
    global checks
    assert condition, message
    checks += 1


fences = re.findall(r"^```python\n([\s\S]*?)^```\s*$", source, re.M)
check(len(fences) == 1, f"expected one Python fence, found {len(fences)}")
namespace = {"__name__": "__main__"}
captured = io.StringIO()
with contextlib.redirect_stdout(captured):
    exec(compile(fences[0], str(LESSON), "exec"), namespace)
output = captured.getvalue()
bash_fences = re.findall(r"^```bash\n([\s\S]*?)^```\s*$", source, re.M)
check(len(bash_fences) == 1, f"expected one bash fence, found {len(bash_fences)}")
check(max(map(len, bash_fences[0].splitlines())) <= 70, "bash lines must fit the 792px article")
command = subprocess.run(
    bash_fences[0], shell=True, executable="/bin/bash", cwd=ROOT,
    capture_output=True, text=True, check=True,
)
check("langchain_core/tools/convert.py" in command.stdout, command.stdout)
check("_get_filtered_args" in command.stdout, command.stdout)
check("langchain-core       0.3.63" in output and "169" in output and "55,001" in output, output)
check("pydantic             2.14.1" in output and "105" in output and "46,617" in output, output)
check("httpx                0.28.1" in output and "23" in output and "8,828" in output, output)
check(output.count("            0") >= 3, output)
check("langchain            distribution-not-installed" in output, output)
check("anthropic            distribution-not-installed" in output, output)
check("openai               distribution-not-installed" in output, output)
check("不能预测理解难度" in source and "不能推出“一个下午能否读完”" in source, "size must not be presented as reading-time prediction")
check("热度低的价值" not in source and "难十倍" not in source and "大多数会卡在表层" not in source, "unsupported popularity and difficulty claims must be absent")
check("从拥有目标行为的近端模块开始" in source, "the diagram should select by target behavior")
check("$MODULE_FILE" in source and "site-packages/" not in source, "the location command should not assume a fixed install path")
check("readErrors=0" in source, "snapshot should disclose file-read errors")
check("package-size-boundary" in meta, "the checkpoint must teach the scope of size metrics")
check("langchain-core-063-tool-convert" in meta and "langchain-core-063-tool-base" in meta, "lesson sources should be version-pinned")
check("langchain-provider-integration-boundary" in meta, "provider boundary should have a documented checkpoint")
check("langchain-python-integrations" in meta, "provider boundary must cite the official integration docs")
check("https://docs.langchain.com/oss/python/integrations/providers/overview" in resources, "the provider integration docs must be registered")
check("工具 schema：应用代码 → langchain_core.tools → Pydantic schema" in source, "schema construction should have its own trace path")
check("模型请求：  Agent/应用 → provider integration → provider SDK → HTTP transport" in source, "provider requests should have a separate trace path")
check("→ httpx / anthropic（真正发请求的）" not in source, "do not conflate schema generation with network dispatch")

print(json.dumps({"checks": checks, "passed": checks, "pythonFencesCompiled": len(fences), "providerCalls": 0, "fixtureOnly": True}, ensure_ascii=False))
