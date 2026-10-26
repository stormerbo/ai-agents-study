#!/usr/bin/env python3
"""Offline audit checks for the memory cost/evaluation lesson."""
from __future__ import annotations

import contextlib
import io
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/memory/05-memory-cost-and-eval.mdx"
META = ROOT / "src/content/chapters/memory/meta.ts"
RESOURCES = ROOT / "src/content/curriculum/resources.ts"
BODY = LESSON.read_text(encoding="utf-8")
META_TEXT = META.read_text(encoding="utf-8")
RESOURCE_TEXT = RESOURCES.read_text(encoding="utf-8")
FENCES = re.findall(r"^```python\s*\n(.*?)^```\s*$", BODY, re.MULTILINE | re.DOTALL)
TEXT_FENCES = re.findall(r"^```text\s*\n(.*?)^```\s*$", BODY, re.MULTILINE | re.DOTALL)

checks = 0


def check(condition: bool, message: str) -> None:
    global checks
    checks += 1
    if not condition:
        raise AssertionError(message)


check(len(FENCES) == 2, f"expected 2 Python fences, got {len(FENCES)}")
for index, fence in enumerate(FENCES):
    compile(fence, f"{LESSON}#python-fence-{index}", "exec")
    check(True, f"Python fence {index} compiles")

# Exercise the deterministic stub and ensure its output is explicitly synthetic.
eval_ns: dict[str, object] = {"__name__": "memory_cost_eval_fixture"}
exec(compile(FENCES[0], str(LESSON), "exec"), eval_ns)
tasks = eval_ns["TASKS"]
run_one = eval_ns["run_one"]
check(len(tasks) == 3, "the compact code fixture contains three tasks")
run_study = eval_ns.get("run_study")
check(callable(run_study), "the sample randomizes paired condition order")
rows_in_order = run_study(tasks, seed=20261022)
order_by_task: dict[str, list[bool]] = {}
for row in rows_in_order:
    order_by_task.setdefault(row["id"], []).append(row["memory"])
check(all(sorted(order) == [False, True] for order in order_by_task.values()), "each task runs once in both conditions")
check({tuple(order) for order in order_by_task.values()} == {(False, True), (True, False)}, "fixed seed exercises both condition orders")
check("真实实验应生成并记录本轮 seed 与逐题顺序" in BODY, "live experiments must retain their randomized assignment")
off = [run_one(task, False) for task in tasks]
on = [run_one(task, True) for task in tasks]
check(sum(row["done"] for row in off) == 0, "stub baseline is 0/3")
check(sum(row["done"] for row in on) == 1, "stub memory condition is 1/3")
check(all(row["clarified"] == 0 and row["misremembered"] == 0 for row in off + on), "stub reports no user-behavior metrics")
check("不验证记忆抽取或检索质量" in FENCES[0], "stub limitation is disclosed in code")
check("provider 请求/响应适配" in FENCES[0], "provider integration is not presented as a one-line swap")
check("ctx2 is not ctx1 and ctx2 == []" in FENCES[0], "new session checks identity and emptiness")

# Recompute the input-token arithmetic; storage is kept outside the sum.
cost_ns: dict[str, object] = {"__name__": "memory_cost_fixture"}
exec(compile(FENCES[1], str(LESSON), "exec"), cost_ns)
cost = cost_ns["cost"]
expected = {0: (8300, 0, 8300), 3: (8300, 2400, 10700), 10: (8300, 8000, 16300), 30: (8300, 24000, 32300)}
for keep, values in expected.items():
    result = cost(20, memories=keep, inject_per_turn=keep)
    observed = (result["写入输入token"], result["注入输入token"], result["模型输入token合计"])
    check(observed == values, f"token arithmetic for {keep} memories: {observed}")
    check(result["存储条数"] == keep, f"storage count remains separate for {keep} memories")

cost_out = io.StringIO()
with contextlib.redirect_stdout(cost_out):
    exec(compile(FENCES[1], str(LESSON), "exec"), {"__name__": "__main__"})
golden = next((item for item in TEXT_FENCES if "10700" in item and "32300" in item), None)
normalize = lambda value: re.sub(r"\s+", " ", value).strip()
check(golden is not None and normalize(cost_out.getvalue()) == normalize(golden), "cost output matches displayed golden")

# Guard against the exact unsupported statements removed by this review.
for forbidden in (
    "标准误约 ±13 个百分点",
    "8 到 10 组",
    "这一个对照不需要评测集，跑两次就能回答",
    "唯一的负向指标是",
    "20 轮、每条记忆 40 token 算一笔账",
    "只注入来源可靠且稳定的条目",
):
    check(forbidden not in BODY, f"obsolete claim absent: {forbidden}")

check("配对二项方法（例如 McNemar 检验）" in BODY, "paired binary analysis is specified")
check("仅知道两个边际比例无法完成配对检验" in BODY, "matched task outcomes are required")
check("nist-mcnemar-test" in META_TEXT and "paired-binomial-tests-intervals-fagerland" in META_TEXT, "checkpoint cites paired test and interval references")
check("id: 'nist-mcnemar-test'" in RESOURCE_TEXT, "McNemar reference is registered")
check("不能直接用 token 相加" in BODY, "cost units are separated")
check("用户可能没有注意到静默错误" in BODY, "correction rate is not treated as complete negative metric")
check("进程重启、存储故障、用户/租户隔离" in BODY, "batch simulation limits are explicit")

print(f"memory cost/eval review: {checks} checks passed")
