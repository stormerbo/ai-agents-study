"""Whole-lesson offline checks for coding-agent/file-editing."""

import ast
import json
from contextlib import redirect_stdout
from hashlib import sha256
from io import StringIO
from pathlib import Path
import re
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/coding-agent/03-file-editing.mdx"
META = ROOT / "src/content/chapters/coding-agent/meta.ts"
FIRST_SCRIPT = ROOT / "verify-output/coding-edit.py"
FIRST_LOG = ROOT / "verify-output/coding-edit.log"
PRIOR_AUDIT = ROOT / "experiments/scripts/verify_coding_agent_file_editing_review_20261020.py"

check_count = 0


def check(condition, message):
    global check_count
    check_count += 1
    if not condition:
        raise AssertionError(message)


source = LESSON.read_text(encoding="utf-8")
meta = META.read_text(encoding="utf-8")
fences = re.findall(r"^```python\s*\n([\s\S]*?)^```\s*$", source, re.MULTILINE)
check(len(fences) == 3, "parser, flawed helper, and guarded helper examples must exist")
for index, fence in enumerate(fences):
    compile(fence, f"{LESSON}#python-{index}", "exec")

for phrase in (
    "分别只有 8、5、5 次",
    "没有保存逐次原始模型响应",
    "不能冒充原始输出",
    "不能据此估计格式错误率",
    "有多处候选就拒绝并报告",
    "不能直接把 `count(old_string) == 1` 当成唯一定位证明",
    "可能含重叠位置",
    "写入成功不等于行为正确",
    "不能保证一次提案就能修好",
    "不能与后面的不同 fixture 直接作因果比较",
):
    check(phrase in source, f"lesson boundary missing: {phrase}")

for stale in (
    "差别只在信息可得性",
    "模型编辑文件普遍用的是",
    "模型给出的 `old_string` 大概是",
    "默认用精确匹配替换，匹配失败时降级到整文件重写",
    "最灵敏的健康指标之一",
    "反馈往往一轮就能修好",
    "编辑不是原子的",
):
    check(stale not in source, f"stale or ambiguous generalization remains: {stale}")

check("重叠子串" in meta and "不能单独证明唯一定位" in meta,
      "metadata checkpoint should cover overlapping matches")
check("Aider edit formats" in source and "Anthropic 的 text editor 工具" in source,
      "tool-specific edit-format references missing")

# Use the archived output record; do not execute the credential/API script.
first_log = FIRST_LOG.read_text(encoding="utf-8")
task_rows = [int(value) for value in re.findall(r"^\s*#(\d+)\s+", first_log, re.MULTILINE)]
check(task_rows == list(range(1, 9)), "first historical task rows changed")
check("唯一匹配成功：8 / 8 = 100%" in first_log and "替换后语法合法：8 / 8 = 100%" in first_log,
      "first historical summary no longer matches its recorded 8/8 outputs")

# Run the issue-specific audit, which reconstructs the 83-line case without API calls.
prior = subprocess.run([sys.executable, str(PRIOR_AUDIT)], check=True,
                       capture_output=True, text=True)
check("18/18 checks passed" in prior.stdout,
      "historical empty-string inference and existing parser/helper checks should pass")

parser_match = re.search(r"```python\n(import json\n.*?return value)\n```", source, re.S)
check(parser_match is not None, "strict JSON parser code fence missing")
parser_ns = {}
exec(compile(parser_match.group(1), "file-edit-parser", "exec"), parser_ns)
parse_edit = parser_ns["parse_edit"]
good = '{"old_string":"aa","new_string":"x"}'
check(parse_edit(good) == {"old_string": "aa", "new_string": "x"},
      "valid edit object should parse")
for raw in (
    "prefix " + good,
    good + " trailing",
    "[]",
    '{"old_string":"aa","new_string":"x","path":"p.py"}',
    '{"old_string":1,"new_string":"x"}',
):
    try:
        parse_edit(raw)
    except (ValueError, json.JSONDecodeError):
        check(True, "invalid edit proposal rejected")
    else:
        raise AssertionError("parser accepted a value outside the exact protocol")

edit_match = re.search(
    r"```python\n(class EditError\(ValueError\):\n.*?return src\[:first_match\] \+ new \+ src\[first_match \+ len\(old\):\])\n```",
    source,
    re.S,
)
check(edit_match is not None, "unique replacement helper missing")
edit_ns = {}
exec(compile(edit_match.group(1), "file-edit-guard", "exec"), edit_ns)
apply_edit = edit_ns["apply_edit"]
for src, old in (("abc", ""), ("abc", "z"), ("aba", "a"), ("aaa", "aa")):
    try:
        apply_edit(src, old, "x")
    except ValueError:
        check(True, "empty, missing, repeated, or overlapping match rejected")
    else:
        raise AssertionError("non-unique or empty match was accepted")
check(apply_edit("abc", "b", "X") == "aXc", "unique edit failed")
check(apply_edit("aab", "aa", "X") == "Xb", "one non-overlapping occurrence should edit")

print(f"coding-agent file-editing W6 checks: {check_count}/{check_count}")
print(f"guarded-helper-sha256: {sha256(edit_match.group(1).encode('utf-8')).hexdigest()}")
print("providerCalls: 0")
print("externalNetworkCalls: 0")
