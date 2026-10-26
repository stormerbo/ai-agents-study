from __future__ import annotations

import ast
import contextlib
import io
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
lesson_path = ROOT / "src/content/chapters/computer-use/05-when-not-to-use.mdx"
lesson = lesson_path.read_text(encoding="utf-8")
meta = (ROOT / "src/content/chapters/computer-use/meta.ts").read_text(encoding="utf-8")
data = (ROOT / "docs/DATA.md").read_text(encoding="utf-8")
fences = re.findall(r"^\x60\x60\x60python\n([\s\S]*?)^\x60\x60\x60\s*$", lesson, flags=re.MULTILINE)
checks: dict[str, bool] = {
    "historic comparison disclaims end-to-end cost and success claims":
        "不能作为两种路线的端到端成本或成功率对照" in lesson,
    "historical 14.4 ratio is explicitly non-comparable":
        "不是可用于选型的成本结论" in lesson and "不应作为选型规则" in lesson,
    "current tool guidance distinguishes browser from desktop":
        "Browser Use" in lesson and "整桌面截图/坐标是宽泛 UI 路线" in lesson,
    "mixed-route pseudocode reconciles unknown outcomes before retry":
        "state == \"applied\"" in lesson and "state != \"definitely_not_applied\"" in lesson,
    "historical DATA entry records execution-boundary limitation":
        "没有执行工具" in data and "执行边界与成功判据不同" in data,
    "lesson metadata includes the new primary references":
        all(x in meta for x in ("anthropic-tool-combinations", "anthropic-browser-use", "playwright-locators")),
    "all lesson Python fences compile":
        len(fences) == 3,
    "synthetic CSV fixture returns its documented counts":
        False,
}

try:
    for i, fence in enumerate(fences, start=1):
        compile(fence, f"{lesson_path}:fence-{i}", "exec")
    fixture = next(fence for fence in fences if "def sample_csv()" in fence)
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        exec(compile(fixture, f"{lesson_path}:synthetic-csv", "exec"), {"__name__": "__main__"})
    expected = (
        "原始行数：103\n可提交：98 条\n被挡下：5 条\n"
        "   重复         User 010 / user010@example.com\n"
        "   重复         User 020 / user020@example.com\n"
        "   重复         User 030 / user030@example.com\n"
        "   格式预检未通过    No Email / not-an-email\n"
        "   格式预检未通过    Bad Domain / x@nodot\n"
    )
    checks["synthetic CSV fixture returns its documented counts"] = output.getvalue() == expected
except Exception as exc:
    print(f"ERROR executing lesson fixture: {type(exc).__name__}: {exc}")

for name, passed in checks.items():
    print(("PASS" if passed else "FAIL") + ": " + name)

if not all(checks.values()):
    sys.exit(1)
