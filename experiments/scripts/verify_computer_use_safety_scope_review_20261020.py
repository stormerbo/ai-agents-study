from __future__ import annotations

import contextlib
import io
import re
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
lesson_path = ROOT / "src/content/chapters/computer-use/04-safety-and-scope.mdx"
lesson = lesson_path.read_text(encoding="utf-8")
meta = (ROOT / "src/content/chapters/computer-use/meta.ts").read_text(encoding="utf-8")

fences = re.findall(r"^```python\n([\s\S]*?)^```\s*$", lesson, flags=re.MULTILINE)
main = next((fence for fence in fences if "class Guard:" in fence), None)
checks: dict[str, bool] = {
    "scope prose limits coordinate zones to one policy layer":
        "不能证明点击对象的语义正确" in lesson and "不能代替动作级授权" in lesson,
    "budget prose distinguishes preflight reservation from usage reconciliation":
        "事后记账" in lesson and "响应回来后用实际 usage 对账" in lesson,
    "stagnation threshold counts adjacent comparisons and labels the signal heuristic":
        "至少 4 次观测" in lesson and "不能证明界面完全相同" in lesson,
    "approval binds task and parameters and is not authenticated by a string":
        "绑定到具体任务、目标和参数" in lesson
        and "字符串引用本身不提供身份认证" in lesson,
    "logging includes data minimization and retention constraints":
        "最小化、脱敏、访问控制与保留期限" in lesson,
    "tool result protocol is separated from custom JSON and does not promise model recovery":
        "不要把自定义 JSON 对象伪装成 Anthropic tool_result" in lesson
        and "不保证模型一定采取某种恢复策略" in lesson,
    "checkpoint no longer requires confirmation for every irreversible action":
        "后者必须走确认" not in meta and "最小可行集" not in meta,
    "complete Guard fence exists and compiles": main is not None,
}

if main is not None:
    try:
        compile(main, str(lesson_path), "exec")
        output = io.StringIO()
        module = types.ModuleType("lesson_guard_review")
        module.__dict__["__name__"] = "__main__"
        sys.modules[module.__name__] = module
        namespace = module.__dict__
        with contextlib.redirect_stdout(output):
            exec(compile(main, str(lesson_path), "exec"), namespace)
        Guard = namespace["Guard"]
        guard = Guard(safe_zones=[], no_change_limit=3, step_budget=10, token_budget=100)
        same_frame: list[bool] = []
        for _ in range(4):
            started, _ = guard.begin_request(0)
            same_frame.append(started and guard.finish_request(0, "same-frame")[0])
        checks["three unchanged adjacent comparisons stop at observation four"] = same_frame == [True, True, True, False]

        action = {"action": "click", "x": 1, "y": 1}
        approval_guard = Guard(safe_zones=[(0, 0, 2, 2)])
        approval_guard.approve_once("task-a", action, "grant-a")
        approved = approval_guard.allow(action, task_id="task-a", approval_ref="grant-a", requires_approval=True)[0]
        replayed = approval_guard.allow(action, task_id="task-a", approval_ref="grant-a", requires_approval=True)[0]
        altered = approval_guard.allow({**action, "x": 2}, task_id="task-a", approval_ref="grant-a", requires_approval=True)[0]
        checks["grant is action-bound and consumed once"] = approved and not replayed and not altered

        cap = Guard(safe_zones=[], step_budget=1, token_budget=10)
        first = cap.begin_request(10)[0]
        second = cap.begin_request(0)[0]
        checks["step budget is enforced before the next provider call"] = first and not second

        overrun = Guard(safe_zones=[], step_budget=2, token_budget=10)
        preflight = overrun.begin_request(10)[0]
        after_response = overrun.finish_request(11, "frame")[0]
        checks["actual usage overrun blocks the returned action"] = preflight and not after_response
        checks["complete Guard fence executes without provider or UI calls"] = (
            "launch-shell" in output.getvalue()
            and "already consumed approval" in output.getvalue()
        )
    except Exception as exc:  # the verifier should report an executable failure
        print(f"ERROR executing lesson fence: {type(exc).__name__}: {exc}")
        checks["complete Guard fence executes without provider or UI calls"] = False

for name, passed in checks.items():
    print(("PASS" if passed else "FAIL") + ": " + name)

if not all(checks.values()):
    sys.exit(1)
