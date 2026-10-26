"""Recheck the coding-agent file-editing lesson against its archived fixtures."""
from __future__ import annotations

import ast
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/coding-agent/03-file-editing.mdx"
LEGACY_SCRIPT = ROOT / "verify-output/coding-edit2.py"
LEGACY_LOG = ROOT / "verify-output/coding-edit2.log"
checks = 0


def check(condition: bool, message: str) -> None:
    global checks
    checks += 1
    if not condition:
        raise AssertionError(message)


lesson = LESSON.read_text(encoding="utf-8")
legacy_tree = ast.parse(LEGACY_SCRIPT.read_text(encoding="utf-8"))

# Rebuild only the archived fixture string; do not execute API or credential code.
selected = []
needed = {"Q", "BLK", "parts", "FILE"}
for node in legacy_tree.body:
    if isinstance(node, ast.Assign) and any(
        isinstance(target, ast.Name) and target.id in needed for target in node.targets
    ):
        selected.append(node)
    elif isinstance(node, ast.For) and any(
        isinstance(child, ast.Name) and child.id == "parts" for child in ast.walk(node)
    ):
        selected.append(node)
fixture_ns: dict[str, object] = {}
exec(compile(ast.Module(body=selected, type_ignores=[]), str(LEGACY_SCRIPT), "exec"), fixture_ns)
fixture = fixture_ns["FILE"]
log = LEGACY_LOG.read_text(encoding="utf-8")
check(len(fixture) == 1878, "archived fixture length changed")
check(fixture.count("") == 1879, "Python empty-string count should be len(text) + 1")
check("匹配 1879 次" in log, "archived log no longer reports the count being audited")

# The lesson parser must reject malformed JSON rather than guessing at braces.
parser_block = re.search(r"```python\n(import json\n.*?return value)\n```", lesson, re.S)
check(parser_block is not None, "strict JSON parser example missing")
parser_ns: dict[str, object] = {}
exec(compile(parser_block.group(1), "lesson-parse-edit", "exec"), parser_ns)
parse_edit = parser_ns["parse_edit"]
valid = json.dumps({"old_string": "x", "new_string": '{"nested": true}'})
check(parse_edit(valid)["new_string"] == '{"nested": true}', "nested JSON string should parse")
for invalid in ("prefix {\"old_string\":\"x\",\"new_string\":\"y\"}", "{} trailing"):
    try:
        parse_edit(invalid)
    except (ValueError, json.JSONDecodeError):
        pass
    else:
        raise AssertionError("strict parser accepted non-protocol output")
    check(True, "strict parser rejected output outside the protocol")

# Extract and execute the guarded replacement example.
edit_block = re.search(r"```python\n(class EditError\(ValueError\):\n.*?return src\[:first_match\] \+ new \+ src\[first_match \+ len\(old\):\])\n```", lesson, re.S)
check(edit_block is not None, "guarded replacement example missing")
edit_ns: dict[str, object] = {}
exec(compile(edit_block.group(1), "lesson-apply-edit", "exec"), edit_ns)
apply_edit = edit_ns["apply_edit"]
for source, old in (("abc", ""), ("abc", "z"), ("aba", "a"), ("aaa", "aa")):
    try:
        apply_edit(source, old, "x")
    except ValueError:
        pass
    else:
        raise AssertionError("empty, missing, or repeated match was not rejected")
    check(True, "replacement rejected empty, missing, or repeated match")
check(apply_edit("abc", "b", "X") == "aXc", "unique edit failed")

for stale in (
    "差别只在信息可得性",
    "模型编辑文件普遍用的是",
    "模型给出的 `old_string` 大概是",
    "默认用精确匹配替换，匹配失败时降级到整文件重写",
    "最灵敏的健康指标之一",
):
    check(stale not in lesson, f"stale claim remains: {stale}")

print(f"coding-agent file-editing audit: {checks}/{checks} checks passed")
