from __future__ import annotations

import ast
import os
import re
import sys
import types
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
            "chroma-context-rot", "anthropic-stop-reasons", "deepseek-anthropic-api", "anthropic-python-sdk",
        )),
    "DATA summary carries the historical scoring and raw-response limitations":
        "评分器未归档" in data
        and "归为未完成样本" in data,
    "provider context-window stop is documented and not conflated with request rejection":
        "model_context_window_exceeded" in lesson
        and "有的请求会被拒绝，有的会返回专门的停止状态" in lesson,
    "credential source checkpoint distinguishes SDK token resolution from compatible endpoints":
        "anthropic-sdk-auth" in meta
        and "不把两类凭据混作一个 api_key" in meta,
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
            "context-window stop": score("P-0302", "model_context_window_exceeded") == "incomplete",
            "refusal or unknown stop": score("P-0302", "refusal") == "nonfinal",
        }
        checks["teaching Python sample compiles and contains a strict exact-output scorer"] = all(fixtures.values())
        for name, passed in fixtures.items():
            checks[f"scorer fixture: {name}"] = passed
    except (SyntaxError, StopIteration, TypeError, ValueError):
        checks["teaching Python sample compiles and contains a strict exact-output scorer"] = False

# Instantiate the complete teaching sample with a fake SDK to ensure bearer
# credentials are resolved by the SDK rather than relabeled as API keys.
if sample is not None:
    captured_kwargs: list[dict[str, object]] = []
    class FakeMessages:
        def create(self, **kwargs: object) -> None:
            raise AssertionError("offline audit must never send a request")
    class FakeAnthropic:
        def __init__(self, **kwargs: object) -> None:
            captured_kwargs.append(kwargs)
            self.messages = FakeMessages()
    fake_anthropic = types.ModuleType("anthropic")
    fake_anthropic.Anthropic = FakeAnthropic  # type: ignore[attr-defined]
    old_env = {key: os.environ.get(key) for key in (
        "ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_BASE_URL", "VERIFY_MODEL"
    )}
    old_module = sys.modules.get("anthropic")
    try:
        os.environ.pop("ANTHROPIC_API_KEY", None)
        os.environ["ANTHROPIC_AUTH_TOKEN"] = "fixture-bearer-token"
        os.environ["ANTHROPIC_BASE_URL"] = "https://fixture.invalid/anthropic"
        os.environ["VERIFY_MODEL"] = "fixture-model"
        sys.modules["anthropic"] = fake_anthropic
        sample_namespace = {"__name__": "offline_audit"}
        exec(compile(sample, "context-is-finite-auth-fixture", "exec"), sample_namespace)
        checks["SDK bearer-token resolution is not passed through the api_key parameter"] = (
            captured_kwargs == [{"base_url": "https://fixture.invalid/anthropic"}]
        )
        corpus = sample_namespace["build_corpus"]()
        sample_namespace["check_criterion"]()
        qualifying = [
            row for row in corpus
            if "风险等级：高" in row
            and int(re.search(r"预算：(\d+)万元", row).group(1)) > 200
        ]
        checks["synthetic corpus has exactly one jointly qualifying item"] = (
            len(corpus) == 400 and qualifying == [corpus[302]] and corpus[302].startswith("P-0302")
        )
        build_doc = sample_namespace["build_doc"]
        checks["needle placement is exact at all five tested positions"] = all(
            next(i for i, row in enumerate(build_doc(pos).split("\n\n")) if row.startswith("P-0302")) == pos
            for pos in (0, 100, 200, 300, 399)
        )
    except Exception:
        checks["SDK bearer-token resolution is not passed through the api_key parameter"] = False
    finally:
        for key, value in old_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        if old_module is None:
            sys.modules.pop("anthropic", None)
        else:
            sys.modules["anthropic"] = old_module

for name, passed in checks.items():
    print(("PASS" if passed else "FAIL") + ": " + name)

if not all(checks.values()):
    sys.exit(1)
