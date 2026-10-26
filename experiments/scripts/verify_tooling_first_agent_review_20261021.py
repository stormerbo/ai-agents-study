"""Audit the LangGraph first-agent lesson without contacting a model provider."""

from __future__ import annotations

import os
from pathlib import Path
import re
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/tooling/04-first-agent.mdx"
TEXT = LESSON.read_text(encoding="utf-8")
FENCES = re.findall(r"^```python\n(.*?)^```\s*$", TEXT, flags=re.M | re.S)
PYTHON = os.environ.get("LANGGRAPH_REVIEW_PYTHON", sys.executable)


def check(condition: bool, label: str) -> None:
    if not condition:
        raise AssertionError(label)
    print(f"PASS {label}")


def main() -> None:
    check(len(FENCES) == 2, "the lesson has exactly two Python examples")
    for index, source in enumerate(FENCES, start=1):
        compile(source, f"lesson-fence-{index}.py", "exec")
    check(True, "both complete Python fences compile")

    required_scope = (
        "不是一个完整可交互的 Agent",
        "不是杀进程或重启测试",
        "没有真实数据库、网络副作用或 provider 调用",
        "thread_id` 不是用户身份凭证",
        "task` 可以保存已完成 task 的结果",
        "外部副作用的 exactly-once 保证",
    )
    for phrase in required_scope:
        check(phrase in TEXT, f"lesson states boundary: {phrase}")

    for stale in (
        "LangGraph 的检查点在节点返回之后才写",
        "恢复后整节点重跑，副作用因此重复",
        "跨进程恢复（换 checkpointer 即可）",
        "库里三条相同记录",
        "用 LangGraph 搭一个最小 agent",
    ):
        check(stale not in TEXT, f"stale claim removed: {stale}")

    runtime = subprocess.run(
        [
            PYTHON,
            "-c",
            "import importlib.metadata as m, sys; print(sys.version.split()[0]); print(m.version('langgraph')); print(m.version('langchain-core'))",
        ],
        check=True,
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    python_version, langgraph_version, core_version = runtime.stdout.splitlines()
    check(langgraph_version == "1.2.14", "runtime LangGraph version is 1.2.14")
    check(core_version == "1.6.12", "runtime langchain-core version is 1.6.12")

    for index, source in enumerate(FENCES, start=1):
        result = subprocess.run(
            [PYTHON, "-c", source],
            check=True,
            capture_output=True,
            text=True,
            cwd=ROOT,
        )
        check("".join(result.args).find("ANTHROPIC") == -1, "no provider credentials are passed")
        if index == 1:
            check(result.returncode == 0, "the graph skeleton runs offline")
        else:
            check(
                "work 节点被执行 3 次" in result.stdout
                and "测试列表中的 user: ['u2', 'u2', 'u2']" in result.stdout,
                "node failure and same-thread retry produce three list entries",
            )
            check(
                "内存列表，不代表真实数据库或外部服务" in result.stdout,
                "the result explicitly disclaims database/provider coverage",
            )

    print(f"runtime: Python {python_version}, langgraph {langgraph_version}, langchain-core {core_version}")
    print(f"providerCalls: 0; Python fences executed: {len(FENCES)}")


if __name__ == "__main__":
    main()
