"""Whole-lesson offline checks for coding-agent/search-strategy."""

from contextlib import redirect_stdout
from hashlib import sha256
from io import StringIO
from pathlib import Path
import re
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/coding-agent/02-search-strategy.mdx"
META = ROOT / "src/content/chapters/coding-agent/meta.ts"
PRIOR_AUDIT = ROOT / "experiments/scripts/verify_coding_agent_search_strategy_review_20261020.py"


check_count = 0


def check(condition, message):
    global check_count
    check_count += 1
    if not condition:
        raise AssertionError(message)


source = LESSON.read_text(encoding="utf-8")
meta = META.read_text(encoding="utf-8")
blocks = re.findall(r"^```python\s*\n([\s\S]*?)^```\s*$", source, re.MULTILINE)
check(len(blocks) == 3, "ranking, AST, and partial-index examples should all be present")
for index, block in enumerate(blocks):
    compile(block, f"{LESSON}#python-{index}", "exec")

for phrase in (
    "一次四题 API 观察",
    "不能据此估计模型可靠性",
    "不是单独的 grep",
    "最大单问输入 token",
    "只建一个**词法级候选索引**",
    "不是解析后的 symbol identity",
    "commit 加脏工作树",
    "agent 会以为“仓库里没有这个符号”",
    "在限额前过滤非整数与越界行号",
    "制定路径授权与读取失败策略",
    "第 18 章的 62% 是固定工具数、每轮重复输入与历史 token 假设下的本地模型",
):
    check(phrase in source, f"lesson boundary missing: {phrase}")

for stale in (
    "grep 普遍省 token 且准确率不降",
    "grep 比全文更准确",
    "精确调用图",
    "62% 的工具成本",
):
    check(stale not in source, f"unbounded historical or semantic claim returned: {stale}")

check("区分「找到了 0 条」「某些文件未索引」和「搜索失败」" in source,
      "the three search outcomes must remain distinct")
check("定义列表本身没有调用记录" in meta,
      "metadata checkpoint must distinguish definitions from call references")
check("原始响应未保留" in meta,
      "metadata checkpoint must retain the scorer evidence limit")

rank_ns = {"__name__": "rank_demo"}
exec(compile(blocks[0], "rank-demo", "exec"), rank_ns)
with tempfile.TemporaryDirectory(prefix="coding-search-w6-") as tmp:
    root = Path(tmp)
    paths = [root / "a.py", root / "b.py"]
    paths[0].write_text("def a():\n    return 1\ndef aa():\n    return 2\n", encoding="utf-8")
    paths[1].write_text("def b():\n    return 3\n", encoding="utf-8")
    hits = {str(paths[0]): [True, 1, 2, 2, 0, 99], str(paths[1]): [1]}
    rows = rank_ns["rank_and_truncate"](hits, top_k=2, per_file=2)
    check(len(rows) == 3, "top_k/per_file cap or duplicate-line removal changed")
    check(all(str(path) in "\n".join(rows) for path in paths), "full paths were dropped")
    check(rows[0].startswith(f"{paths[0]}:1:") and rows[1].startswith(f"{paths[0]}:2:"),
          "ranker should emit source lines in ascending order within the file")
    for kwargs in (
        {"top_k": -1}, {"per_file": -1},
        {"top_k": True}, {"per_file": True},
        {"top_k": 1.5}, {"per_file": 1.5},
    ):
        try:
            rank_ns["rank_and_truncate"](hits, **kwargs)
        except ValueError:
            pass
        else:
            raise AssertionError(f"negative bound accepted: {kwargs}")

index_ns = {"__name__": "index_demo"}
exec(compile(blocks[1], "lexical-index", "exec"), index_ns)
fixture_ns = dict(index_ns)
exec(compile(blocks[2], "partial-index-fixture", "exec"), fixture_ns)
check(fixture_ns["skipped"] == {"broken.py": 1}, "invalid file should be reported, not erased")
check("索引不完整" in fixture_ns["context"] and "broken.py" in fixture_ns["context"],
      "partial-index diagnostic should reach the caller")

source_fixture = {
    "aliases.py": "from package import target as alias\nalias()\n",
    "same_names.py": "left.save()\nright.save()\n",
}
defines, refs, skipped = index_ns["build_index"](source_fixture)
check(not defines and not skipped, "lexical call fixture should parse without definitions")
check(refs["alias"] == [("aliases.py", 2)], "import aliases should be reported lexically")
check(refs["save"] == [("same_names.py", 1), ("same_names.py", 2)],
      "same-named attributes should remain candidate collisions")
check(index_ns["answer_context"]("absent", defines, refs, skipped) == "",
      "complete index with no match should not invent a partial-index diagnostic")

prior = subprocess.run([sys.executable, str(PRIOR_AUDIT)], check=True,
                       capture_output=True, text=True)
check("16/16 checks passed" in prior.stdout,
      "the issue-specific archived fixture/context audit should still pass")

print(f"coding-agent search-strategy W6 checks: {check_count}/{check_count}")
print(f"ranking-fence-sha256: {sha256(blocks[0].encode('utf-8')).hexdigest()}")
print("providerCalls: 0")
print("externalNetworkCalls: 0")
