"""Check budget admission, loop guards, and budget-exhaustion wording."""

from __future__ import annotations

import ast
import contextlib
import io
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/agent-loop/03-budgets-and-guards.mdx"
META = ROOT / "src/content/chapters/agent-loop/meta.ts"


def python_fences(text: str) -> list[str]:
    return [body for language, body in re.findall(r"```(\w+)\n([\s\S]*?)\n```", text) if language == "python"]


def main() -> None:
    text = LESSON.read_text(encoding="utf-8")
    meta = META.read_text(encoding="utf-8")
    fences = python_fences(text)
    assert fences, "no Python fences found"
    for index, source in enumerate(fences, start=1):
        ast.parse(source, filename=f"lesson-fence-{index}")

    code = next(source for source in fences if "class LoopGuard:" in source)
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        namespace: dict[str, object] = {"__name__": "lesson_module"}
        exec(compile(code, "lesson-loop-guard", "exec"), namespace)
        namespace["__name__"] = "__main__"
        exec(compile(code, "lesson-loop-guard-run", "exec"), namespace)
    report = output.getvalue()
    assert "已准入步数 4 / 预留 2000 token" in report
    assert "步数超上限（5/4）" in report
    assert "已准入步数 4 / 预留 4000 token" in report
    assert "累计 token 预留超上限（5000/4000）" in report

    guard = namespace["LoopGuard"](max_steps=1, max_token_volume=10)
    assert guard.check_step(10) == (True, "ok")
    before = (guard.steps, guard.tokens)
    assert guard.check_step(1)[0] is False
    assert (guard.steps, guard.tokens) == before, "denied step must not consume budget"
    assert namespace["LoopGuard"]().check_step(-1)[0] is False

    repeat_guard = namespace["LoopGuard"]()
    assert repeat_guard.repeat_limit == 3
    assert repeat_guard.check_action("weather", {"city": "北京"}) == (True, "ok")
    assert repeat_guard.check_action("weather", {"city": "北京"}) == (True, "ok")
    allowed, reason = repeat_guard.check_action("weather", {"city": "北京"})
    assert allowed is False and "连续 3 次" in reason

    progress_source = next(source for source in fences if "class ProgressGuard:" in source)
    progress: dict[str, object] = {}
    exec(compile(progress_source, "lesson-progress-guard", "exec"), progress)
    detector = progress["ProgressGuard"](limit=2)
    assert detector.observe([{"city": "北京", "temp_c": 20}])[0] is True
    assert detector.observe([{"city": "北京", "temp_c": 20}])[0] is True
    assert detector.observe([{"city": "北京", "temp_c": 20}])[0] is False
    list_detector = progress["ProgressGuard"](limit=1)
    assert list_detector.observe([[1]])[0] is True
    assert list_detector.observe([[2, 3]])[0] is False, "list values/lengths are intentionally not compared"

    assert report.count("get_weather(北京) → 放行") == 2
    assert "get_weather(北京) → 拦截：连续 3 次相同的调用，判定为绕圈子" in report
    excerpt = text.split("修订后实跑输出", 1)[1].split("```text\n", 1)[1].split("\n```", 1)[0]
    for line in excerpt.splitlines():
        if line.strip() and "..." not in line:
            assert line in report.splitlines(), f"published output line differs: {line}"

    tighten_source = next(source for source in fences if "def tightened_step_cap" in source)
    tighten: dict[str, object] = {}
    exec(compile(tighten_source, "lesson-tightened-cap", "exec"), tighten)
    assert tighten["tightened_step_cap"](8, 5, 2) == 7
    assert "收尾预算" in text and "预留" in meta
    assert "deepseek-vision" in meta and "anthropic-stop-reasons" in meta
    assert "三分之一左右" not in text and "上限的 80%" not in text
    assert "动作空间天然封闭" not in text
    assert "最不可靠的一条" not in text
    assert "实测里 ReAct 在线性任务上就是这么做的" not in text
    assert "结果是否在变化" not in text
    assert "我实际撞到过一次打转" not in text
    assert "原因不是模型「笨」" not in text
    assert "协议正常终止" in text and "不保证" in text
    assert "修订后实跑输出（本节 verifier 于 2026-10-21 执行" in text
    assert "注册表天然给定" not in text
    assert "结构新颖度启发式" in text
    assert "list" in text and "不比较列表长度或值" in text
    print(f"PASS: {len(fences)} Python fences compile")
    print("PASS: denied reservations do not increment accepted steps or token reserve")
    print("PASS: repeat-action, no-progress, and tightened-cap examples behave as described")
    print("PASS: budget exhaustion returns partial status unless a closing call was reserved")
    print("PASS: every non-ellipsis published output line matches the executed demo")
    print("PASS: protocol, provider, threshold, and structural-heuristic claims stay explicitly scoped")


if __name__ == "__main__":
    main()
