"""Offline whole-lesson checks for the minimal agent-loop tutorial."""

from __future__ import annotations

import contextlib
import io
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/agent-loop/01-minimal-loop.mdx"


def main() -> None:
    text = LESSON.read_text(encoding="utf-8")
    assertions = 0

    def require(condition: bool, message: str) -> None:
        nonlocal assertions
        if not condition:
            raise AssertionError(message)
        assertions += 1

    require("`end_turn` 携带空 `content`" in text, "document the empty end_turn response edge case")
    require("不能据此认定任务成功" in text, "separate turn termination from task success")
    require("模型调用次数不等于工具调用次数" in text, "distinguish model-turn and tool-action budgets")
    require("最后一轮的 tool_use 不执行" in text, "document the final-turn side-effect boundary")

    fences = re.findall(r"```python\s*\n(.*?)\n```", text, re.S)
    full_script = next((item for item in fences if "class FakeModel" in item), None)
    require(full_script is not None, "find the complete local FakeModel program")
    namespace = {"__name__": "__main__"}
    stdout = io.StringIO()
    with contextlib.redirect_stdout(stdout):
        exec(compile(full_script, str(LESSON), "exec"), namespace)
    require("正常路径：结果是 14。（3 步）" in stdout.getvalue(), "complete demo output")

    side_effects: list[str] = []
    namespace["REGISTRY"]["record"] = lambda: side_effects.append("executed") or {"ok": True}
    model = namespace["FakeModel"]([("tool", "record", {})])
    result = namespace["run"]("side effect", model, max_steps=1)
    require(side_effects == [], "do not dispatch a tool when no model turn remains")
    require("最后一轮" in result[0], "return an explicit budget-exhausted state")

    empty_model = namespace["FakeModel"]([("final", "")])
    try:
        namespace["run"]("empty response", empty_model)
    except RuntimeError as exc:
        require("没有可展示文本" in str(exc), "empty end_turn must fail as incomplete")
    else:
        raise AssertionError("empty end_turn was accepted as a successful answer")

    print(f"assertions={assertions} providerCalls=0 externalNetworkCalls=0")


if __name__ == "__main__":
    main()
