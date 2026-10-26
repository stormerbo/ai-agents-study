#!/usr/bin/env python3
"""Verify the bounded, local claims in the context-versus-memory lesson."""
from __future__ import annotations

import contextlib
import io
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/memory/01-context-is-not-memory.mdx"
META = ROOT / "src/content/chapters/memory/meta.ts"
BODY = LESSON.read_text(encoding="utf-8")
META_TEXT = META.read_text(encoding="utf-8")
FENCES = re.findall(r"^```python\s*\n(.*?)^```\s*$", BODY, re.MULTILINE | re.DOTALL)

assert len(FENCES) == 2, f"expected 2 Python fences, got {len(FENCES)}"
for fence in FENCES:
    compile(fence, str(LESSON), "exec")

recall_output = io.StringIO()
recall_ns = {"__name__": "__main__"}
with contextlib.redirect_stdout(recall_output):
    exec(compile(FENCES[0], str(LESSON), "exec"), recall_ns)
assert "recall checks: 5 passed" in recall_output.getvalue()
assert "已知的长期偏好与事实：\n（无）" in recall_output.getvalue()
assert recall_ns["recall"]("没有任何重合的天气查询") == []
assert recall_ns["recall"]("部署") == ["部署"]

cost_output = io.StringIO()
with contextlib.redirect_stdout(cost_output):
    cost_ns = {"__name__": "review_fixture"}
    exec(compile(FENCES[1], str(LESSON), "exec"), cost_ns)
assert cost_ns["history_cost"](12, 740)[-1][1:] == (9380, 63720)
assert cost_ns["memory_cost"](12, 300) == 9600
assert cost_ns["history_cost"](50, 740)[-1][2] == 968500
assert cost_ns["memory_cost"](50, 300) == 40000

assert "不能估计位置效应发生率" in BODY
assert "词数不等于 token 数" in BODY
assert "一个词约等于一个 token" not in BODY
assert "不能据此说已把否定结论的证据边界" in BODY
assert "openai-conversation-state" in META_TEXT
assert "deepseek-models-pricing" in META_TEXT
assert "id: 'historical-long-context-observations'" in META_TEXT

assert "previous_response_id" in BODY
assert "先前的输入 token 仍按输入 token 计费" in BODY
assert "12 × 740 = 8,880" in BODY
assert "6.51" in BODY
assert "deepseek-model-list-api" in META_TEXT
assert "context_window: 1048576" in META_TEXT
print("memory context W6 review: 23 checks passed")
