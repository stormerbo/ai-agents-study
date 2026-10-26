"""Audit the coding-agent search lesson's historical fixture and local examples."""
from __future__ import annotations

import ast
import re
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/coding-agent/02-search-strategy.mdx"
HISTORY = ROOT / "verify-output/coding-search.py"
LOG = ROOT / "verify-output/coding-search.log"
checks = 0


def check(condition: bool, message: str) -> None:
    global checks
    checks += 1
    if not condition:
        raise AssertionError(message)


lesson = LESSON.read_text(encoding="utf-8")
history_source = HISTORY.read_text(encoding="utf-8")
history_tree = ast.parse(history_source)
selected: list[ast.stmt] = []
for node in history_tree.body:
    if isinstance(node, (ast.For, ast.Assign)) and any(
        isinstance(child, ast.Name) and child.id in {"FILES", "GREP", "INDEX", "FULL"}
        for child in ast.walk(node)
    ):
        selected.append(node)
history_ns: dict[str, object] = {}
exec(compile(ast.Module(body=selected, type_ignores=[]), str(HISTORY), "exec"), history_ns)
files = history_ns["FILES"]
check(len(files) == 11, "fixture should contain 9 module files plus billing.py and api.py")
check("12 文件" in history_source and len(files) != 12, "legacy header's 12-file count should be identified as stale")

full = "仓库所有文件：\n" + history_ns["FULL"]
grep_context = "grep compute_total 的结果：\n" + history_ns["GREP"] + "\n\n仓库里所有函数定义：\n" + history_ns["INDEX"]
symbol_context = "仓库里所有函数定义：\n" + history_ns["INDEX"]
check([len(full), len(grep_context), len(symbol_context)] == [2460, 1012, 717], "context lengths differ from archived log")
check("exp.lower() in txt.lower().replace(\" \", \"\")" in history_source, "legacy substring scorer should be disclosed")
check("grep 调用行 + 全部定义" in lesson and "不能支持“grep 相比全文”" in lesson, "confounded condition should be bounded")
check("最大单问输入 token" in lesson and "不是平均值" in lesson, "token statistic should be labeled as maximum")

blocks = re.findall(r"```python\n(.*?)\n```", lesson, re.S)
check(len(blocks) >= 3, "expected ranking, AST, and partial-index examples")
for block in blocks:
    ast.parse(block)
rank_ns: dict[str, object] = {}
exec(compile(blocks[0], "lesson-rank-and-truncate", "exec"), rank_ns)
with tempfile.TemporaryDirectory() as temp_dir:
    a = Path(temp_dir) / "a.py"
    b = Path(temp_dir) / "b.py"
    a.write_text("def a():\n    return 1\n", encoding="utf-8")
    b.write_text("def b():\n    return 2\n", encoding="utf-8")
    hits = {str(a): [1, 2, 99], str(b): [1]}
    rows = rank_ns["rank_and_truncate"](hits, top_k=2, per_file=2)
    check(len(rows) == 3 and all(str(p) in "\n".join(rows) for p in (a, b)), "ranking output should preserve full paths and cap rows")
    try:
        rank_ns["rank_and_truncate"](hits, top_k=-1)
    except ValueError:
        check(True, "negative ranking limit rejected")
    else:
        raise AssertionError("negative ranking limit accepted")

index_ns: dict[str, object] = {}
exec(compile(blocks[1], "lesson-lexical-index", "exec"), index_ns)
fixture_ns = index_ns
exec(compile(blocks[2], "lesson-partial-index-fixture", "exec"), fixture_ns)
check(fixture_ns["skipped"] == {"broken.py": 1}, "syntax-invalid file should be reported as skipped")
check("broken.py" in fixture_ns["context"] and "索引不完整" in fixture_ns["context"], "incomplete status should reach caller")
source = {"one.py": "obj.target()\n", "two.py": "other.target()\n"}
defines, refs, skipped = index_ns["build_index"](source)
check(len(refs["target"]) == 2 and not defines and not skipped, "attribute suffixes should be exposed as lexical candidates")
check("词法级候选索引" in lesson and "不是解析后的 symbol identity" in lesson, "AST reference precision limits should be explicit")
check("提交加脏工作树 hash" in lesson or "commit 加脏工作树" in lesson, "index freshness should include uncommitted workspace changes")
check("工具定义占 62%" not in lesson or "本地估算" in lesson, "62% should be labeled as a local estimate")
check("0 条命中与搜索失败" not in lesson, "old two-state search failure claim should be removed")

print(f"coding-agent search-strategy audit: {checks}/{checks} checks passed")
