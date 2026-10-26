"""Offline whole-lesson scope checks; no provider or external network calls."""
from __future__ import annotations
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/llm-api-basics/01-tokens-and-context.mdx"
META = ROOT / "src/content/chapters/llm-api-basics/meta.ts"
DATA = ROOT / "docs/DATA.md"

def main() -> None:
    lesson, meta, data = (p.read_text(encoding="utf-8") for p in (LESSON, META, DATA))
    checks = 0
    fences = re.findall(r"^```python\s*\n([\s\S]*?)^```\s*$", lesson, re.M)
    assert len(fences) == 4
    for i, code in enumerate(fences): compile(code, f"lesson-fence-{i}", "exec")
    checks += 1
    assert "Fable 5.1、Mythos 5.1、Fable 5 与 Mythos 5" in lesson
    assert "所有 4.7 及之后的 Claude 型号" in lesson
    assert "Mythos Preview" in lesson
    assert "约高 30%" in lesson and "核对日期：2026-10-22" in lesson
    checks += 1
    assert "server tools、MCP connector" in lesson
    assert "URL/file source 的 image/document block" in lesson
    assert "使用 base64 source" in lesson
    checks += 1
    assert "不能用来推出固定 30 token 开销" in data
    assert "固定请求开销" in lesson and "不能推广到其他 provider" in lesson
    assert "The user wants me to reply" not in lesson
    checks += 1
    assert "sourceIds: ['claude-token-counting']" in meta
    assert "Anthropic 官方 Messages token-counting endpoint" in lesson
    assert "python3 input_token_estimator.py" in lesson
    checks += 1
    assert "1 / 1.3 ≈ 76.9%" in lesson and "约少 23.1%" in lesson
    assert abs(1 / 1.3 - 0.7692307692307692) < 1e-12
    checks += 1
    print(f"whole-lesson offline checks: {checks}/6; Python fences compiled: {len(fences)}; providerCalls=0; externalNetworkCalls=0")

if __name__ == "__main__": main()
