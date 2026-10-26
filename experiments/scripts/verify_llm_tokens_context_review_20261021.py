"""Offline review checks for the tokens/context lesson; no provider calls."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/llm-api-basics/01-tokens-and-context.mdx"
META = ROOT / "src/content/chapters/llm-api-basics/meta.ts"
DATA = ROOT / "docs/DATA.md"


def main() -> None:
    lesson = LESSON.read_text(encoding="utf-8")
    meta = META.read_text(encoding="utf-8")
    data = DATA.read_text(encoding="utf-8")
    checks = 0

    python_fences = re.findall(r"^```python\s*\n([\s\S]*?)^```\s*$", lesson, re.M)
    for index, fence in enumerate(python_fences):
        compile(fence, f"tokens-context-python-fence-{index}", "exec")
    assert len(python_fences) == 4, len(python_fences)
    checks += 1

    assert "每次调用都有约 30 token 的结构开销" not in lesson
    assert "每次调用都有约 30 token 的结构开销" not in data
    assert "不能用来推出固定 30 token 开销" in data
    checks += 1

    assert "JSONDecodeError`，也不能仅凭这次响应" in lesson
    assert "`output_tokens=5`" in lesson and "内容只有非文本 block" in lesson
    assert "The user wants me to reply" not in lesson
    checks += 1

    assert "Anthropic 官方 Messages token-counting endpoint" in lesson
    assert "python3 input_token_estimator.py" in lesson
    assert "sourceIds: ['claude-token-counting']" in meta
    assert "它不是跨 provider 通用实现" in lesson
    checks += 1

    assert abs((1 / 1.3) * 100 - 76.92307692307692) < 1e-10
    assert "1 / 1.3 ≈ 76.9%" in lesson and "约少 23.1%" in lesson
    checks += 1

    print(f"offline checks: {checks}/5; Python fences parsed: {len(python_fences)}; provider calls: 0")


if __name__ == "__main__":
    main()
