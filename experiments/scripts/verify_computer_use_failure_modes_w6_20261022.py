"""W6 full-scope checks for computer-use/failure-modes; does not call a model."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
LESSON_PATH = ROOT / "src/content/chapters/computer-use/03-failure-modes.mdx"
META_PATH = ROOT / "src/content/chapters/computer-use/meta.ts"
RESOURCES_PATH = ROOT / "src/content/curriculum/resources.ts"
ARCHIVE_PATH = ROOT / "experiments/fixtures/computer-use-failure-modes-archive-20261009.json"
OLD_VERIFIER = ROOT / "experiments/scripts/verify_computer_use_failure_modes_review_20261020.py"
checks = 0


def check(condition: bool, message: str) -> None:
    global checks
    checks += 1
    if not condition:
        raise AssertionError(message)


lesson = LESSON_PATH.read_text(encoding="utf-8")
meta = META_PATH.read_text(encoding="utf-8")
resources = RESOURCES_PATH.read_text(encoding="utf-8")
archive = json.loads(ARCHIVE_PATH.read_text(encoding="utf-8"))

# Revalidate original archive sources as data; do not execute either historical script.
refs = {item["path"]: item for item in archive["sourceReferences"]}
check(len(refs) == 2, "expected two archived source references")
for source_path, record in refs.items():
    raw = (ROOT / source_path).read_bytes()
    check(hashlib.sha256(raw).hexdigest() == record["sha256"], f"historical source hash changed: {source_path}")
old_source = (ROOT / "verify-output/cu-failures.py").read_text(encoding="utf-8")
check('st["done"] and st["v"]["name"] == "Zhang San"' in old_source, "archived scorer differs from tracked summary")
check("Clicked empty space." in old_source, "archived adapter feedback missing")
check('if variant == "noop":\n                    pass' in old_source, "archived noop behavior differs")

# Keep archived labels separate from verified task outcomes.
runs = {run["variant"]: run for run in archive["runs"]}
check([(key, runs[key]["configuredRuns"]) for key in ("tiny", "decoy", "noop")] == [("tiny", 4), ("decoy", 2), ("noop", 1)], "archived run counts drifted")
check(runs["tiny"]["archivedLabels"] == ["pass", "fail", "fail", "pass"], "tiny labels drifted")
check(runs["decoy"]["actionSequencesRetained"] is False, "decoy trace retention changed")
check(archive["limitations"] and all("No original" in x or "not verified" in x for x in archive["limitations"]), "archive evidence limits missing")
for phrase in (
    "本节不报告目标尺寸对应的成功率",
    "脚本插入记录中的旧 harness `token` 数值",
    "不是经核实的 token 总量",
    "不能视为失败成本倍数的可靠估计或预算预测",
    "缺少逐次原始响应，无法判断它是否读到了提示",
    "无法据此断言两次都点中了 Create",
    "`swap` 不在本节完整脚本的 `VARIANTS` 中",
    "不代表真实网站或计算机使用系统的总体失败率",
):
    check(phrase in lesson, f"evidence boundary missing: {phrase}")

# Compile the external-call harness but never invoke its online entry point.
fences = re.findall(r"^```python\s*\n([\s\S]*?)^```\s*$", lesson, re.MULTILINE)
check(len(fences) == 2, f"expected helper plus model-backed harness, got {len(fences)}")
helper = next((code for code in fences if 'def check_record(' in code), None)
main = next((code for code in fences if '失败模式注入：小目标 / 诱饵按钮 / 点击无效。' in code), None)
check(helper is not None and main is not None, "expected local helper and full harness fences")
compile(helper, str(LESSON_PATH), "exec")
compile(main, str(LESSON_PATH), "exec")
check("VERIFY_MODEL" in main and "ANTHROPIC_BASE_URL" in main and "ANTHROPIC_AUTH_TOKEN" in main, "external runtime requirements are not explicit")
check("本轮未重跑在线请求" in main and "不提供生产级动作校验、授权或隔离" in lesson, "online and production limits missing")

expected_output = (
    "[界面层] SUCCESS 页显示：user created: zhang@example.com  -> 看起来成功 ✅\n"
    "[数据层] 查回记录 {'name': 'zhang@example.com', 'email': 'Zhang San'} -> ❌ 2 处不一致\n"
    "  name: 期望 'Zhang San'，实际 'zhang@example.com'\n"
    "  email: 期望 'zhang@example.com'，实际 'Zhang San'\n"
    "[对照：正确提交] -> ✅ 一致\n"
)
with tempfile.TemporaryDirectory(prefix="computer-use-failure-w6-") as temp_dir:
    program = Path(temp_dir) / "check_record.py"
    program.write_text(helper, encoding="utf-8")
    result = subprocess.run([sys.executable, "-I", str(program)], capture_output=True, text=True, check=True)
check(result.stdout == expected_output, "helper output differs from the published example")
check(result.stderr == "", "helper unexpectedly wrote stderr")
check("fields=(\"name\", \"email\")" in helper and "assert len(mismatches) == 2" in helper, "helper does not check both swapped fields")
check("不证明身份、数据来源或授权" in lesson and "并发更新语义" in lesson, "business-source and concurrency limits missing")

# The displayed historical counter is only an implementation sum, not a documented billing total.
check("u.get(\"input_tokens\", 0) + u.get(\"cache_read_input_tokens\", 0)" in main, "historical aggregation expression changed")
check("当前 [DeepSeek Anthropic 兼容说明]" in lesson, "current compatibility documentation is not cited")
check("没有定义这段求和是否等于可计费总量" in lesson, "usage aggregation/billing boundary missing")
check("'deepseek-anthropic-api': {" in resources, "DeepSeek compatibility source missing from resource registry")
check("resourceIds: ['twelve-factor-agents', 'claude-messages-api', 'deepseek-anthropic-api']" in meta, "lesson metadata does not surface current endpoint source")

# Prior audit remains a separate evidence record and must still match the current claims.
previous = subprocess.run([sys.executable, str(OLD_VERIFIER)], capture_output=True, text=True, check=True)
check(sum(line.startswith("PASS:") for line in previous.stdout.splitlines()) == 18 and "FAIL:" not in previous.stdout, "prior ERR-065 review no longer passes")

print(f"{checks}/{checks} checks passed; helper=executed; providerCalls=0; externalNetworkCalls=0; archivedHarness=notExecuted")
