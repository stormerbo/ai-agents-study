import contextlib
import io
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/reading-source/05-outputs.mdx"
META = ROOT / "src/content/chapters/reading-source/meta.ts"
RESOURCES = ROOT / "src/content/curriculum/resources.ts"
DEMO = ROOT / "experiments/scripts/verify_reading_source_tool_063.py"
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
check(max(map(len, fences[0].splitlines())) <= 70, "lesson Python fence must not overflow a 792px article")
namespace = {"__name__": "__main__"}
captured = io.StringIO()
with contextlib.redirect_stdout(captured):
    exec(compile(fences[0], str(LESSON), "exec"), namespace)
output = captured.getvalue()
try:
    namespace["make_note"]("问题", str.upper, "结论", "脚本")
except ValueError as exc:
    check("inspect 无法定位" in str(exc), "unsupported inspect targets should fail with a clear diagnostic")
else:
    raise AssertionError("inspect should reject built-in method locations")
check("langchain_core/tools/base.py:95" in output and "langchain_core/tools/convert.py:71" in output, output)
check("位置是手写的" in output and "base.py:999" in output, output)
check("experiments/scripts/verify_reading_source_tool_063.py" in output, output)
check("位置已校验" not in source, "inspect-derived path must not be described as a validation of correctness")
check("四种产出（价值递增）" not in source, "the lesson must not claim a universal ranking")
check("不能自动发现上游行为变化" in source, "a pinned script does not automatically test a new upstream version")
check("在目标版本环境中更新依赖快照并重跑断言" in source, "the upgrade-check procedure must require an updated target-version environment")
check("## 完整可运行代码\n" in source, "the heading must be separated from preceding prose")
check("verify-output/` 是本地验证产物目录，已被 Git 忽略" in source, "ignored local output must be disclosed")
check(DEMO.is_file(), "the cited version-pinned reproduction must be checked in")
check(hashlib.sha256(DEMO.read_bytes()).hexdigest() == "d81f427c51205728159729d40e0b7d550afd75b47f75f214f88422a1187c7e74", "the tracked reproduction script hash changed; review it and update the evidence record")
check("langchain-core==0.3.63" in DEMO.read_text(), "the reproduction must pin the package version")
check("langchain-core-063-tool-convert" in meta and "langchain-core-063-tool-base" in meta, "documented checkpoint must cite both version-pinned files")
check("https://github.com/langchain-ai/langchain/blob/langchain-core%3D%3D0.3.63/libs/core/langchain_core/tools/convert.py" in resources, "version-pinned convert source must be registered")
check("https://github.com/langchain-ai/langchain/blob/langchain-core%3D%3D0.3.63/libs/core/langchain_core/tools/base.py" in resources, "version-pinned base source must be registered")
run = subprocess.run([sys.executable, str(DEMO)], capture_output=True, text=True, check=True)
check("离线断言通过：6 项" in run.stdout, run.stdout)
check("langchain_core/tools/convert.py:71" in run.stdout and "langchain_core/tools/base.py:95" in run.stdout, run.stdout)

print(json.dumps({"checks": checks, "passed": checks, "pythonFencesCompiled": len(fences), "providerCalls": 0, "fixtureOnly": True}, ensure_ascii=False))
