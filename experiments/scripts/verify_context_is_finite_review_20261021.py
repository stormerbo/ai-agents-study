from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
lesson = (ROOT / "src/content/chapters/context-engineering/01-context-is-finite.mdx").read_text(encoding="utf-8")
meta = (ROOT / "src/content/chapters/context-engineering/meta.ts").read_text(encoding="utf-8")
resources = (ROOT / "src/content/curriculum/resources.ts").read_text(encoding="utf-8")
data = (ROOT / "docs/DATA.md").read_text(encoding="utf-8")

checks: dict[str, bool] = {
    "chapter-zero mechanical marker is identified as an earlier baseline, not a new rerun":
        "第 0 章的机械标记（本节未重测）" in lesson
        and "不能和本节四组重测合并" in lesson,
    "historical model summaries disclose missing raw trace, model pin, sample map and scorer":
        all(term in lesson for term in (
            "原始逐次请求/响应", "精确模型版本", "样本与 scorer 未归档", "不能独立复核",
        )),
    "early max_tokens observations are incomplete and the thinking explanation remains unverified":
        "未完成样本" in lesson
        and "这个因果解释无法独立确认" in lesson
        and "不能据此确认思考 token 是唯一原因" in lesson,
    "cost and latency statements distinguish input volume, provider billing and measurement":
        "这不是金额" in lesson
        and "目标 provider" in lesson
        and "应在目标 endpoint 测量" in lesson,
    "primary source IDs exist for research terminology and provider stop/compatibility semantics":
        all(source_id in resources and source_id in meta for source_id in (
            "chroma-context-rot", "anthropic-stop-reasons", "deepseek-anthropic-api",
        )),
    "DATA summary carries the historical scoring and raw-response limitations":
        "评分器未归档" in data
        and "归为未完成样本" in data,
}

fences = re.findall(r"^```python\s*\n([\s\S]*?)^```\s*$", lesson, flags=re.MULTILINE)
sample = next((fence for fence in fences if "lost_in_middle_test.py" in fence), None)
if sample is None:
    checks["teaching Python sample compiles and contains a strict exact-output scorer"] = False
else:
    try:
        tree = ast.parse(sample)
        compile(tree, "lost_in_middle_test.py", "exec")
        scorer = next(
            node for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "score_answer"
        )
        scorer_module = ast.Module(body=[scorer], type_ignores=[])
        namespace = {"ANSWER": "P-0302", "re": re}
        exec(compile(scorer_module, "score_answer", "exec"), namespace)
        score = namespace["score_answer"]
        fixtures = {
            "exact end_turn ID": score("P-0302", "end_turn") == "correct",
            "wrong ID": score("P-0303", "end_turn") == "wrong",
            "extra text containing the answer": score("The answer is P-0302 but uncertain", "end_turn") == "format_or_extra_text",
            "multiple IDs": score("P-0302 P-0302", "end_turn") == "format_or_extra_text",
            "truncated answer": score("P-0302", "max_tokens") == "incomplete",
            "refusal or unknown stop": score("P-0302", "refusal") == "nonfinal",
        }
        checks["teaching Python sample compiles and contains a strict exact-output scorer"] = all(fixtures.values())
        for name, passed in fixtures.items():
            checks[f"scorer fixture: {name}"] = passed
    except (SyntaxError, StopIteration, TypeError, ValueError):
        checks["teaching Python sample compiles and contains a strict exact-output scorer"] = False

for name, passed in checks.items():
    print(("PASS" if passed else "FAIL") + ": " + name)

if not all(checks.values()):
    sys.exit(1)
