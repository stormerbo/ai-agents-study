"""Offline audit of chat-template claims and token-count example; no provider calls."""

from __future__ import annotations

import os
import re
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/context-engineering/06-chat-template.mdx"
META = ROOT / "src/content/chapters/context-engineering/meta.ts"
DATA = ROOT / "docs/DATA.md"
text = LESSON.read_text(encoding="utf-8")
meta = META.read_text(encoding="utf-8")
data = DATA.read_text(encoding="utf-8")
checks = 0


def check(condition: bool, message: str) -> None:
    global checks
    checks += 1
    assert condition, message


fences = re.findall(r"```python\n(.*?)\n```", text, flags=re.S)
check(len(fences) == 1, f"expected one Python fence, got {len(fences)}")
for index, source in enumerate(fences, 1):
    compile(source, f"chat-template-python-fence-{index}", "exec")
    check(True, f"Python fence {index} compiles")

# Confirm that the executable example uses a fake SDK only. No real SDK/network is imported.
source = fences[0]
check("client.messages.count_tokens(" in source, "example must use token-count API")
check("response.input_tokens" in source, "example must return provider-reported input count")
check("cache_read_input_tokens" not in source, "count-token sample must not claim cache usage")
check("two distinct user turns" in source, "same-role message caveat must be visible")
check(source.index("names = [") < source.index("counts = [") < source.index("input_tokens(system, messages)"), "variant validation precedes provider calls")
check("实跑状态：未调用 provider" in text, "live execution status is disclosed")

class FakeCountResponse:
    def __init__(self, input_tokens: int) -> None:
        self.input_tokens = input_tokens


class FakeMessages:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, object]]] = []

    def count_tokens(self, **kwargs: object) -> FakeCountResponse:
        self.calls.append(("count_tokens", kwargs))
        return FakeCountResponse(17 + len(str(kwargs.get("system", ""))))


fake_messages = FakeMessages()
fake_module = types.ModuleType("anthropic")
fake_module.Anthropic = lambda **kwargs: types.SimpleNamespace(messages=fake_messages)  # type: ignore[attr-defined]
sys.modules["anthropic"] = fake_module
namespace: dict[str, object] = {"__name__": "offline_lesson_fixture"}
original_key = os.environ.get("ANTHROPIC_API_KEY")
original_token = os.environ.get("ANTHROPIC_AUTH_TOKEN")
original_model = os.environ.get("VERIFY_MODEL")
try:
    os.environ.pop("ANTHROPIC_API_KEY", None)
    os.environ.pop("ANTHROPIC_AUTH_TOKEN", None)
    try:
        exec(compile(source, "chat-template-example", "exec"), namespace)
    except RuntimeError as exc:
        check("set exactly one" in str(exc), "missing credentials fail closed")
    else:
        raise AssertionError("missing credentials should fail")

    os.environ["ANTHROPIC_API_KEY"] = "fixture-key"
    os.environ["VERIFY_MODEL"] = "fixture-model"
    exec(compile(source, "chat-template-example", "exec"), namespace)
    count_fn = namespace["input_tokens"]
    compare_fn = namespace["compare_variants"]
    check(count_fn("system", [{"role": "user", "content": "hello"}]) == 23, "count result comes from fake SDK")
    variants = [
        ("base", "a", [{"role": "user", "content": "x"}]),
        ("changed", "abc", [{"role": "user", "content": "x"}]),
    ]
    check(compare_fn(variants, "base") == [("base", 18, 0), ("changed", 20, 2)], "variant deltas use named baseline")
    check(len(fake_messages.calls) == 3, "only fake token-count calls were made")
    calls_before_invalid_baseline = len(fake_messages.calls)
    try:
        compare_fn(variants, "missing")
    except ValueError as exc:
        check("include the baseline" in str(exc), "unknown baseline is rejected")
    else:
        raise AssertionError("unknown baseline should fail")
    check(
        len(fake_messages.calls) == calls_before_invalid_baseline,
        "invalid baseline is rejected before provider calls",
    )

    duplicate_names = [variants[0], ("base", "b", [{"role": "user", "content": "y"}])]
    calls_before_duplicate_names = len(fake_messages.calls)
    try:
        compare_fn(duplicate_names, "base")
    except ValueError as exc:
        check("unique" in str(exc), "duplicate variant names are rejected")
    else:
        raise AssertionError("duplicate variant names should fail")
    check(
        len(fake_messages.calls) == calls_before_duplicate_names,
        "duplicate names are rejected before provider calls",
    )
finally:
    if original_key is None:
        os.environ.pop("ANTHROPIC_API_KEY", None)
    else:
        os.environ["ANTHROPIC_API_KEY"] = original_key
    if original_token is None:
        os.environ.pop("ANTHROPIC_AUTH_TOKEN", None)
    else:
        os.environ["ANTHROPIC_AUTH_TOKEN"] = original_token
    if original_model is None:
        os.environ.pop("VERIFY_MODEL", None)
    else:
        os.environ["VERIFY_MODEL"] = original_model
    sys.modules.pop("anthropic", None)

check("逐次请求/响应、准确 endpoint/model、usage 原文和评分材料未归档" in text, "historical provenance boundary is explicit")
check("不能把 60 token 归因给 20 个边界标记" in text, "boundary attribution is withdrawn")
check("不能推出每轮固定增加多少 token" in text, "historical token delta is not generalized")
check("'claude-token-counting'" in meta and "'openai-prompt-caching'" in meta and "'anthropic-compaction'" in meta, "official resources are linked in checkpoint metadata")
check("compare-preflight" in meta, "preflight guidance has a checkpoint")
check("同样的内容，拆成 10 轮比合并成 1 轮多 25%" not in meta, "stale lesson summary is removed")
check("不能把 60 token 差值归因于消息边界" in meta, "checkpoint reflects confounded comparison")
check("缓存全废" not in meta, "universal cache invalidation claim is removed")
check("Chat Template 历史 token 汇总（不可复核）" in data, "historical figures are listed in data register")

print(f"offline assertions passed: {checks}; providerCalls=0; pythonFencesCompiled={len(fences)}")
