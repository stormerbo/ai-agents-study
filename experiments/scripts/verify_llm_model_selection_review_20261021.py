#!/usr/bin/env python3
"""Offline checks for the model-selection lesson's claims and routing example."""

from __future__ import annotations

import contextlib
import io
import os
import re
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/llm-api-basics/04-model-selection.mdx"
META = ROOT / "src/content/chapters/llm-api-basics/meta.ts"
RESOURCES = ROOT / "src/content/curriculum/resources.ts"
text = LESSON.read_text(encoding="utf-8")
meta = META.read_text(encoding="utf-8")
resources = RESOURCES.read_text(encoding="utf-8")
checks = 0


def check(condition: bool, label: str) -> None:
    global checks
    checks += 1
    if not condition:
        raise AssertionError(label)


check("Σ(各类 billable usage × 对应单价)" in text, "cost formula must be usage-class aware")
check("“缓存相关费用”整项额外叠加会重复计费" in text, "double-counting cache usage is not warned")
check("不将其称为可复现的账单实测" in text, "historical multi-turn summary overclaims reproducibility")
check("`342 token / 58%` 归因已撤回" in text, "unsupported new-vs-repeated token attribution remains")
check("只有在每轮都把完整对话历史重新放进请求" in text, "quadratic-growth assumptions are missing")
check("服务端会话或托管状态" in text, "client-resend model is presented as universal API behavior")
check("质量、延迟和每个成功任务成本" in text, "model selection omits measured workload criteria")
check("没有本地评测时，不应预设" in text, "universal cheap-model share or quality claim remains")
check("不直接等同于模型能力档位" in text and "服务端授权" in text, "model tier is conflated with authorization")
check("manual_review_required" in text and "stop_reason" in text, "classifier error and truncation do not fail closed")
check("不是实测价格、任务质量或生产收益" in text, "scenario arithmetic is presented as a measured routing gain")
check("由 provider、模型、缓存时长和平台决定" in text, "cache pricing is overgeneralized")
check("不据此推断固定调整周期" in meta, "pricing volatility is asserted as a fixed schedule")

for source_id in (
    "openai-model-selection",
    "anthropic-choosing-model",
    "anthropic-cost-intelligence",
    "claude-pricing",
    "owasp-authorization-cheat-sheet",
):
    check(f"'{source_id}'" in meta, f"chapter metadata missing {source_id}")
    check(f"id: '{source_id}'" in resources, f"resource registry missing {source_id}")

fences = re.findall(r"```python\s*\n(.*?)\n```", text, re.DOTALL)
check(len(fences) == 2, f"expected two Python fences, found {len(fences)}")
for code in fences:
    compile(code, str(LESSON), "exec")

router = fences[0]
class FakeMessages:
    def __init__(self) -> None:
        self.response = types.SimpleNamespace(stop_reason="end_turn", content=[types.SimpleNamespace(type="text", text="mid")])
        self.error: Exception | None = None
        self.calls = 0

    def count_tokens(self, **_kwargs: object) -> object:
        return types.SimpleNamespace(input_tokens=75)

    def create(self, **_kwargs: object) -> object:
        self.calls += 1
        if self.error is not None:
            raise self.error
        return self.response


fake_messages = FakeMessages()
fake_client = types.SimpleNamespace(messages=fake_messages)
fake_sdk = types.ModuleType("anthropic")
fake_sdk.Anthropic = lambda **_kwargs: fake_client  # type: ignore[attr-defined]
sys.modules["anthropic"] = fake_sdk
os.environ["VERIFY_MODEL"] = "test-classifier"
# Execute both examples with a fake SDK. The mock ensures no provider call occurs.
os.environ["CONTEXT_GROWTH_PER_TURN"] = "32"
cost_namespace: dict[str, object] = {"__name__": "reviewed_cost_estimator"}
cost_output = io.StringIO()
with contextlib.redirect_stdout(cost_output):
    exec(compile(fences[1], str(LESSON), "exec"), cost_namespace)
check(cost_namespace["cumulative_input"](75, 32, 10) == 2190, "base-plus-growth cost formula is wrong")
check("2,190 token" in cost_output.getvalue(), "displayed scenario output differs from the formula")
check("1,095,000 token" in cost_output.getvalue(), "daily scenario output differs from the formula")

namespace: dict[str, object] = {"__name__": "reviewed_router"}
exec(compile(router, str(LESSON), "exec"), namespace)
route = namespace["route"]
check(callable(route), "router function was not defined")
assert callable(route)

check(route("把这条评论分类并打标签") == "cheap-model", "rule tier routing changed")
check(fake_messages.calls == 0, "rule route should avoid classifier call")
check(route("帮我重构这个模块") == "strong-model", "reasoning proxy rule did not select strong tier")
check(route("总结这段内容") == "mid-model", "valid classifier label was not accepted")
fake_messages.response = types.SimpleNamespace(stop_reason="max_tokens", content=[types.SimpleNamespace(type="text", text="mid")])
check(route("总结这段内容") == "manual_review_required", "truncated classifier output did not require review")
fake_messages.response = types.SimpleNamespace(stop_reason="end_turn", content=[types.SimpleNamespace(type="text", text="unknown")])
check(route("总结这段内容") == "manual_review_required", "invalid classifier label did not require review")
fake_messages.error = TimeoutError("fixture")
check(route("总结这段内容") == "manual_review_required", "classifier exception did not require review")
check(fake_messages.calls == 4, "unexpected mock call count")

print(f"llm-model-selection-review: {checks}/{checks} checks passed; 2 Python fences compiled; 1 router exercised with mock; providerCalls=0")
