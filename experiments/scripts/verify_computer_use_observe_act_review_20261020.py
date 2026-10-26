from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
lesson_path = ROOT / "src/content/chapters/computer-use/02-observe-act-loop.mdx"
lesson = lesson_path.read_text(encoding="utf-8")
meta = (ROOT / "src/content/chapters/computer-use/meta.ts").read_text(encoding="utf-8")
resources = (ROOT / "src/content/curriculum/resources.ts").read_text(encoding="utf-8")

checks: dict[str, bool] = {
    "lesson identifies this as a custom adapter, not native Anthropic computer use":
        "不是 [Anthropic 原生 computer-use tool]" in lesson,
    "historical five-step totals are preserved with missing-trace caveat":
        all(x in lesson for x in ("5,288", "5,347", "5,345", "逐步 usage、完整请求体")),
    "contradictory 5,301 table is explicitly unreconciled":
        "不能确认属于这三次运行" in lesson,
    "image-history arithmetic is derivable":
        "1+2+3+4+5=15" in lesson and "15×283=4,245" in lesson,
    "quadratic image-input claim is conditional":
        "上下文完整保留、每步都加一张近似固定 token 数图像" in lesson
        and "n(n+1)/2" in lesson,
    "historic image token count is date- and endpoint-scoped":
        "283 token 是 2026-10-09 的历史实验值" in lesson
        and "https://api-docs.deepseek.com/guides/vision/" in lesson,
    "unsupported resize savings and universal multipliers are removed":
        "省 34%" not in lesson and "省 58%" not in lesson
        and "3.3 倍" not in lesson and "不能称为“平方根级杠杆”" in lesson,
    "dHash is described as a heuristic with collision/missed-change limits":
        "不同画面碰撞" in lesson and "不能作为任务成功判据" in lesson,
    "hash threshold counts comparisons after a baseline frame":
        "至少四帧" in lesson and "三次连续相等比较" in lesson,
    "nearest-element distance is not mislabeled as target accuracy":
        "不是“点击点到预期目标中心的误差”" in lesson
        and "不能解释为目标点击精度" in lesson,
    "summary example uses verified state and correct prior step id":
        "summary_for_step(old_step, verified_state_log)" in lesson
        and "describe_step(step)" not in lesson,
    "checkpoint no longer requires a screenshot after every action":
        "什么情况下动作后应重新截图或查询应用状态？" in meta
        and "每一步都必须重新截一次图" not in meta,
    "current official references are registered in the curriculum resources":
        "'deepseek-vision': {" in resources
        and "'anthropic-computer-use': {" in resources,
    "complete model-backed example still compiles as Python": False,
    "model-backed example states runtime prerequisites and replay limits":
        "环境和判分逻辑可复现，模型动作、token 用量和路由结果不保证复现" in lesson
        and "ANTHROPIC_AUTH_TOKEN" in lesson,
    "dHash snippet is not misrepresented as integrated or a success criterion":
        "dHash 熔断只是独立片段，尚未集成进完整循环" in lesson
        and "只有 `state[\"done\"]` 和两个字段值都满足本地判据" in lesson,
    "teaching parser is explicitly not a production action safety boundary":
        "不能作为真实浏览器或桌面执行的输入校验与安全边界" in lesson,
}

fences = re.findall(r"^```[^\n]*\n([\s\S]*?)^```\s*$", lesson, flags=re.MULTILINE)
main = next((fence for fence in fences if "计算机使用：一个可控的合成界面环境" in fence), None)
if main is not None:
    try:
        compile(main, str(lesson_path), "exec")
        checks["complete model-backed example still compiles as Python"] = True
    except SyntaxError:
        pass

for name, passed in checks.items():
    print(("PASS" if passed else "FAIL") + ": " + name)

# Independent arithmetic for the illustrative full-history image count.
assert sum(range(1, 6)) == 15
assert sum(range(1, 6)) * 283 == 4245

if not all(checks.values()):
    sys.exit(1)
