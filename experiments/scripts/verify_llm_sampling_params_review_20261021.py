"""Offline content checks for sampling parameter migration guidance."""

from __future__ import annotations

import ast
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/llm-api-basics/02-sampling-params.mdx"
body = LESSON.read_text(encoding="utf-8")


checks = 0


def check(condition: bool, label: str) -> None:
    global checks
    checks += 1
    if not condition:
        raise AssertionError(label)
    print(f"PASS {label}")


fences = re.findall(r"```python\n(.*?)\n```", body, flags=re.S)
check(len(fences) == 3, "the lesson contains three Python examples")
for index, source in enumerate(fences, 1):
    ast.parse(source, filename=f"sampling-params-{index}.py")
check(True, "all Python fences parse without provider calls")

check("Python SDK 1.x" in body and "TypeError" in body, "SDK signature failure is separated from API rejection")
check("Claude 4.7+ / Mythos Preview" in body, "API parameter behavior is model-scoped")
check("DeepSeek Anthropic-compatible endpoint" in body, "compatible endpoint behavior is provider-scoped")
check("effort` 是另一类控制" in body, "effort is not presented as a sampling equivalent")
check("不是输出 token 硬上限" in body, "effort is distinguished from max_tokens")
check("historical" in body.lower() or "历史摘要" in body, "historical provider samples are labeled")
check("不能证明温度造成了这组差异" in body, "the small temperature sample is not used as causal evidence")
check("结论是**未知**" in body, "the unarchived thinking comparison is reported as unknown")
check("显式值等于目标模型默认值时，行为与省略字段相同" in body, "default-effort equivalence is documented")
check("per-message effort 标为 beta" in body, "per-message effort is scoped as beta")
check("VERIFY_MODEL" in fences[0] and "os.environ" in fences[0], "SDK example uses a configured model id")
check('response.stop_reason != "end_turn"' in fences[2], "migration example fails closed on non-end_turn")
check("json.loads(text)" in fences[2], "migration example parses returned JSON")
check("response.content[0].text" not in body, "migration example does not assume its first block is text")

withdrawn = (
    "temperature / top_p / top_k 被移除后，控制模型",
    "temperature=1` 三次全不同",
    "准确率没有任何变化（三次都是",
    "至少需要上百次",
    "OpenRouter",
    "参数从来不是稳定性的来源",
    "Haiku 4.5 不支持 effort",
)
for phrase in withdrawn:
    check(phrase not in body, f"withdrawn overclaim absent: {phrase}")

print(f"offline review passed: {checks}/{checks}; providerCalls=0")
