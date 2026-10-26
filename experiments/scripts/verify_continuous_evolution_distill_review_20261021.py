"""Offline audit of the distillation lesson's historical evidence and scorer example."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LESSON_PATH = ROOT / "src/content/chapters/continuous-evolution/02-distill-and-test.mdx"
META_PATH = ROOT / "src/content/chapters/continuous-evolution/meta.ts"
RESOURCES_PATH = ROOT / "src/content/curriculum/resources.ts"
ARCHIVE_PATH = ROOT / "experiments/results/exp-continuous-evolution-distill-review-20261021/historical-log.txt"
SCORER_FACTS_PATH = ROOT / "experiments/results/exp-continuous-evolution-distill-review-20261021/inspected-scorer-facts.txt"
lesson = LESSON_PATH.read_text(encoding="utf-8")
meta = META_PATH.read_text(encoding="utf-8")
resources = RESOURCES_PATH.read_text(encoding="utf-8")
archive = ARCHIVE_PATH.read_text(encoding="utf-8")
scorer_facts = SCORER_FACTS_PATH.read_text(encoding="utf-8")
checks = 0


def check(condition: bool, message: str) -> None:
    global checks
    checks += 1
    assert condition, message


check("处理其余 7 条：6 条通过" in archive, "archived historical counter remains intact")
check('12-10-2026                 错 -> 2026-10-12' in archive, "mismatched visible score row is preserved")
check("f928ea2947c3fac8b39c323807aa702c55d748933039b693c76d7f2a55f1a7e1" in scorer_facts, "inspected current-source hash is recorded")
check("2026-10-10 17:32:50 CST" in scorer_facts and "2026-10-10 17:30:08 CST" in scorer_facts, "script and log modification times are recorded")
check("return (s[1] in out, out[:26])" in scorer_facts, "weak substring scoring behavior is preserved as evidence")
check("A 7/7" in lesson and "A 6/7" in lesson, "lesson discloses the conflicting historical counts")
check("可见错题行的期望/实际值相同" in lesson, "label/output inconsistency is explained")
check("原实验效果未知" in lesson, "the historical experiment is not presented as a confirmed result")
check("旧实验无法从现有材料重建" in lesson, "missing raw records are explicit")
check("基线必须在中间区间”不是通用规则" in lesson, "mid-range baseline is not a universal requirement")
check("代表目标分布的主评测集" in lesson and "压力切片" in lesson, "representative and targeted evaluation slices are distinguished")
check("受控 cohort" in lesson and "不能由此断言规则带来改善" in lesson, "correlation is distinguished from causal evidence")
check('"rule_version"' in lesson and '"evaluation_version"' in lesson, "event example pins rule and evaluator versions")
check("outcome_evidence_ref" in lesson and "避免把敏感原文放进普通日志" in lesson, "event logging avoids raw sensitive content")
check("不要把固定频率当普遍答案" in lesson, "no unsupported daily/N failure trigger is prescribed")
check("expected in out" in lesson and "截断标记拼到输出文本上" in lesson, "the archived scorer defect is identified")
check("stop_reason` 是必要诊断字段之一，不是唯一判据" in lesson, "response completion is not reduced to one field")
check("工具定义、工具调用结果及传给模型的输出仍可能消耗 token" in lesson, "code-versus-prompt cost claim is scoped")
check("anthropic-stop-reasons" in meta and "anthropic-extended-thinking" in meta, "official Anthropic references are in checkpoint metadata")
check("deepseek-anthropic-api" in meta and "https://api-docs.deepseek.com/guides/anthropic_api/" in resources, "compatibility claims are scoped to the DeepSeek endpoint documentation")
check("sourceIds: ['anthropic-stop-reasons', 'anthropic-extended-thinking', 'deepseek-anthropic-api']" in meta, "documented checkpoint sources resolve to the resource registry")
check("distill-no-gain" in meta and "basis: 'inferred'" in meta, "historical outcome is not marked as officially documented")
check("基线成绩是多少" not in lesson and "不能断言测法饱和" in lesson, "unsupported saturation diagnosis is explicitly rejected")
check("**实跑状态**：上面这段候选规则评估器已用离线正例/反例运行" in lesson, "the lesson discloses the actual status of its runnable example")

python_fences = re.findall(r"^```python\s*\n(.*?)^```\s*$", lesson, flags=re.M | re.S)
check(len(python_fences) == 1, "one complete Python rule-evaluation example is present")
namespace: dict[str, object] = {}
exec(compile(python_fences[0], "distill-rule-example.py", "exec"), namespace)
check(callable(namespace.get("evaluate_candidate_rule")), "example executes and exposes the candidate-rule evaluator")
evaluate = namespace["evaluate_candidate_rule"]
assert callable(evaluate)
result = evaluate(r"\d{4}年\d{1,2}月\d{1,2}[日号]", ["2026年10月10日"], ["2026/10/11"])
check(result["positive_coverage"] == 1.0 and result["false_positive_rate"] == 0.0, "positive and negative fixture rates are correct")
try:
    evaluate("[", ["x"], ["y"])
except re.error:
    invalid_pattern_rejected = True
else:
    invalid_pattern_rejected = False
check(invalid_pattern_rejected, "invalid candidate patterns fail explicitly")
try:
    evaluate("x", ["x"], [])
except ValueError:
    empty_class_rejected = True
else:
    empty_class_rejected = False
check(empty_class_rejected, "missing positive or negative examples fail explicitly")

print(f"offline assertions passed: {checks}; providerCalls=0; historicalRunsReplayed=0")
