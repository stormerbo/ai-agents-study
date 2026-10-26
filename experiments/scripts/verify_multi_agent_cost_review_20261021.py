from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/multi-agent/02-cost-model.mdx"
META = ROOT / "src/content/chapters/multi-agent/meta.ts"
text = LESSON.read_text(encoding="utf-8")
meta = META.read_text(encoding="utf-8")
checks: list[str] = []


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)
    checks.append(message)


fences = re.findall(r"```python\s*\n(.*?)\n```", text, re.S)
check(len(fences) == 2, f"found {len(fences)} Python fences")
for index, source in enumerate(fences):
    compile(source, f"{LESSON.name}:python-fence-{index}", "exec")
    checks.append(f"Python fence {index} compiles")

helper = subprocess.run(
    [sys.executable, "-c", fences[0]], check=True, capture_output=True, text=True
)
helper_ns: dict[str, object] = {"__name__": "offline_usage_helper"}
exec(compile(fences[0], "cost-model-usage-helper", "exec"), helper_ns)
check('"input": 320, "cache_read": 256, "cache_write": 0, "output": 81' in fences[0],
      "usage helper contains an explicit normalized fixture")
check('raise ValueError(f"usage.{field} 缺失或不是非负整数")' in fences[0],
      "usage helper fails closed for missing or invalid fields")
check("cache_read" in fences[0] and "cache_write" in fences[0],
      "input token volume and cache categories are distinct")
check('rates_per_million[category]' in fences[0],
      "weighted cost applies per-category rates")
check("math.isfinite(rate)" in fences[0],
      "cost helper rejects non-finite price inputs")
try:
    helper_ns["normalize_usage"]({"input_tokens": 1})
except ValueError:
    check(True, "usage helper rejects missing categories")
else:
    check(False, "usage helper rejects missing categories")
sample_usage = helper_ns["normalize_usage"]({
    "input_tokens": 100, "cache_read_input_tokens": 10,
    "cache_creation_input_tokens": 2, "output_tokens": 20,
})
check(helper_ns["weighted_cost"]([sample_usage], {
    "input": 1, "cache_read": 0.1, "cache_write": 1.25, "output": 5
}) == 0.0002035,
      "illustrative provider rates are applied separately by token category")
try:
    helper_ns["weighted_cost"]([sample_usage], {"input": 1})
except ValueError:
    check(True, "cost helper rejects incomplete rate tables")
else:
    check(False, "cost helper rejects incomplete rate tables")
try:
    helper_ns["weighted_cost"]([sample_usage], {
        "input": float("nan"), "cache_read": 0.1, "cache_write": 1.25, "output": 5
    })
except ValueError:
    check(True, "cost helper rejects NaN rates")
else:
    check(False, "cost helper rejects NaN rates")

# Load the provider example with dummy environment values and replace its network
# function before calling it. This exercises request accounting without a provider.
os.environ.update({
    "ANTHROPIC_BASE_URL": "https://offline.invalid/anthropic",
    "ANTHROPIC_AUTH_TOKEN": "offline-test-token",
    "VERIFY_MODEL": "offline-fixture-model",
})
namespace: dict[str, object] = {"__name__": "offline_audit"}
exec(compile(fences[1], "cost-model-provider-example", "exec"), namespace)


class FakeResponse:
    def __init__(self, payload: dict[str, object]):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self) -> bytes:
        return json.dumps(self.payload).encode()


def body(stop_reason: str = "end_turn", usage: dict[str, object] | None = None,
         content: list[dict[str, str]] | None = None) -> dict[str, object]:
    return {
        "stop_reason": stop_reason,
        "usage": usage if usage is not None else {"input_tokens": 10, "output_tokens": 4},
        "content": content if content is not None else [{"type": "text", "text": "fixture"}],
    }


import urllib.request

original_urlopen = urllib.request.urlopen
fixtures = [body(usage={"input_tokens": i, "output_tokens": i + 1}) for i in (10, 20, 30, 40)]
request_urls: list[str] = []


def fake_urlopen(request, timeout):
    request_urls.append(request.full_url)
    if not fixtures:
        raise AssertionError("unexpected extra request")
    return FakeResponse(fixtures.pop(0))


urllib.request.urlopen = fake_urlopen
try:
    _answer, calls = namespace["run_multi"]("background")
finally:
    urllib.request.urlopen = original_urlopen
check(len(calls) == 4, "three worker calls and one supervisor call are all counted")
check(namespace["totals"](calls) == {
    "calls": 4, "input_tokens": 100, "output_tokens": 104
}, "constructed multi-agent usage totals match all four calls")
check(len(request_urls) == 4 and all(url.startswith("https://offline.invalid/") for url in request_urls),
      "provider requests are intercepted by the offline fixture")
check(not fixtures, "all mocked responses were consumed")

for invalid, message in (
    (body(stop_reason="max_tokens"), "non-end_turn response rejected"),
    (body(usage={"output_tokens": 4}), "missing input usage rejected"),
    (body(content=[]), "empty end_turn response rejected"),
):
    namespace.get("observed_calls", []).clear()
    urllib.request.urlopen = lambda *_args, _body=invalid, **_kwargs: FakeResponse(_body)
    try:
        try:
            namespace["call"]([], "test")
        except RuntimeError:
            check(True, message)
        else:
            check(False, message)
        if invalid.get("usage") == {"input_tokens": 10, "output_tokens": 4}:
            check(namespace.get("observed_calls", []) == [{"input_tokens": 10, "output_tokens": 4}],
                  f"{message}; response usage is preserved before rejection")
    finally:
        urllib.request.urlopen = original_urlopen

check("两次运行分别复测过" not in text, "unsupported 1.9–2.4 range removed")
check("当前无法估计运行间波动" in text, "historical run variance limitation is stated")
check("2.37×" in text and "没有对应的原始记录" in text,
      "unsupported 2.37x entry is explicitly withdrawn")
check("不超过 10 条" not in text and "便宜的小模型" not in text,
      "arbitrary summary length and cheap-model prescription removed")
check("延迟从 sum 变成 max" not in text, "universal parallel latency equation removed")
check("拆解只有成本没有收益" not in text, "same inputs are not claimed to have no benefit")
check("claude-prompt-caching" in meta and "deepseek-anthropic-api" in meta,
      "checkpoint references provider-specific cache documentation")
check("68,548 对 8,430" in meta and "不能独立复算" in meta,
      "checkpoint bounds the separate historical 8.1x summary")

check("observed_calls.append(measured)" in fences[1] and fences[1].index("observed_calls.append(measured)") < fences[1].index('if body.get("stop_reason")') and "逐调用持久化" in text, "usage from rejected responses is retained and production durability limits are explicit")

print(f"{len(checks)} checks passed; providerCalls=0")
