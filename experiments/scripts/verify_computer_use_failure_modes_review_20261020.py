from __future__ import annotations

import ast
import json
import re
import sys
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
lesson_path = ROOT / "src/content/chapters/computer-use/03-failure-modes.mdx"
lesson = lesson_path.read_text(encoding="utf-8")
fixture_path = ROOT / "experiments/fixtures/computer-use-failure-modes-archive-20261009.json"
fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
nearby = "\n".join(
    (ROOT / path).read_text(encoding="utf-8")
    for path in (
        "src/content/chapters/computer-use/01-what-differs.mdx",
        "src/content/chapters/computer-use/04-safety-and-scope.mdx",
        "src/content/chapters/computer-use/05-when-not-to-use.mdx",
        "src/content/chapters/agent-loop/03-budgets-and-guards.mdx",
        "docs/DATA.md",
    )
)
meta = (ROOT / "src/content/chapters/computer-use/meta.ts").read_text(encoding="utf-8")

run_map = {run["variant"]: run for run in fixture["runs"]}
archive_sources = {item["path"]: item for item in fixture["sourceReferences"]}
optional_archive_checks = True
for archive_name, reference in archive_sources.items():
    archived_path = ROOT / archive_name
    if archived_path.exists():
        actual_hash = hashlib.sha256(archived_path.read_bytes()).hexdigest()
        optional_archive_checks &= actual_hash == reference["sha256"]
        if archive_name.endswith("cu-failures.py"):
            archived_source = archived_path.read_text(encoding="utf-8")
            optional_archive_checks &= fixture["harnessFacts"]["scoreExpression"] in archived_source

checks: dict[str, bool] = {
    "tracked archive fixture records tiny 4, decoy 2 and noop 1 runs":
        [(run_map[v]["variant"], run_map[v]["configuredRuns"], run_map[v]["stepCap"]) for v in ("tiny", "decoy", "noop")]
        == [("tiny", 4, 12), ("decoy", 2, 12), ("noop", 1, 8)],
    "tracked archive fixture preserves the scorer, labels, totals and evidence limits":
        fixture["harnessFacts"]["scoreExpression"] == 'st["done"] and st["v"]["name"] == "Zhang San"'
        and run_map["tiny"]["archivedLabels"] == ["pass", "fail", "fail", "pass"]
        and run_map["tiny"]["tokenTotals"] == [5015, 19209, 26568, 5027]
        and all("No original" in limit or "not verified" in limit for limit in fixture["limitations"]),
    "source archive references are hash-pinned and still match when available":
        all(re.fullmatch(r"[a-f0-9]{64}", item["sha256"]) for item in archive_sources.values())
        and optional_archive_checks,
    "lesson reports four tiny old-score labels without treating them as task success":
        "旧 harness 的判分标签" in lesson and "本节不报告目标尺寸对应的成功率" in lesson,
    "lesson withdraws unsupported 12-run 75-percent statement":
        "12 次、3 次失败、75% 成功率" in lesson and "必须撤回" in lesson,
    "lesson does not claim repeated identical coordinates":
        "不能据这份日志断言它反复点了同一个坐标" in lesson,
    "distance metric is scoped to nearest registered element center":
        "最近距离" in lesson and "不是一定到 Create 中心的距离" in lesson,
    "empty-space click feedback is acknowledged":
        fixture["harnessFacts"]["emptyClickFeedback"] in lesson and "把这段错误画在下一张截图底部" in lesson,
    "noop run is described as one archived summary, not model awareness":
        "只列出一条 noop 运行" in lesson and "行为动机不可知" in lesson,
    "decoy labels are not used to claim the model selected the correct target":
        "无法据此断言两次都点中了 Create" in lesson
        and run_map["decoy"]["actionSequencesRetained"] is False,
    "swap is explicitly a constructed fixture and not an archived variant":
        "`swap` 不在本节完整脚本的 `VARIANTS` 中" in lesson and "不是模型端到端实测" in lesson
        and fixture["harnessFacts"]["swapVariantPresent"] is False,
    "local scorer is identified as checking name but not email":
        'st["done"] and st["v"]["name"] == "Zhang San"' in lesson
        and "既不核对 email" in lesson,
    "historical token totals are retained with bounded interpretation":
        all(term in lesson for term in ("19,209", "26,568", "11,827", "不能视为失败成本倍数的可靠估计")),
    "controller completion, budget exhaustion and verified success are distinguished":
        all(term in lesson for term in ("succeeded", "failed_unconfirmed", "budget_exhausted", "业务后置条件")),
    "lesson states runtime prerequisites and model output replay limits":
        all(term in lesson for term in ("Pillow", "VERIFY_MODEL", "ANTHROPIC_BASE_URL", "ANTHROPIC_AUTH_TOKEN", "模型输出、usage 与路由不保证复现"))
        and fixture["harnessFacts"]["environmentPrerequisites"] == ["Pillow", "font file at configured path", "network", "VERIFY_MODEL", "ANTHROPIC_BASE_URL", "ANTHROPIC_AUTH_TOKEN"],
    "adjacent lessons no longer repeat unsupported failure multipliers or success rates":
        not re.search(r"(?:2\.4 到 5\.3 倍|成功率是 75% 到 100%|12,000 到 27,000|平均误差 1\.3 到 2\.6 px|成功率越高)", nearby),
    "metadata no longer teaches silent failure as universally most dangerous":
        "它比报错危险得多" not in meta and "它最典型的失败不是报错" not in meta,
    "complete Python fence compiles without making a provider request": False,
}

fences = re.findall(r"^```python\n([\s\S]*?)^```\s*$", lesson, flags=re.MULTILINE)
main = next((fence for fence in fences if '"""失败模式注入：小目标 / 诱饵按钮 / 点击无效。' in fence), None)
if main is not None:
    try:
        compile(main, str(lesson_path), "exec")
        checks["complete Python fence compiles without making a provider request"] = True
    except SyntaxError:
        pass

for name, passed in checks.items():
    print(("PASS" if passed else "FAIL") + ": " + name)

if not all(checks.values()):
    sys.exit(1)
