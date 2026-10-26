"""Verify the local disagreement example and scope boundaries in the lesson.

This checks deterministic teaching code only; it makes no provider-quality claim.
"""
from __future__ import annotations

import contextlib
import io
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/multimodal/05-vision-in-the-loop.mdx"
text = LESSON.read_text(encoding="utf-8")

checks = 0


def check(condition: bool, message: str) -> None:
    global checks
    checks += 1
    if not condition:
        raise AssertionError(message)


check("历史摘要" in text and "不能独立复算或代表当前模型" in text,
      "historical vision metrics must remain explicitly unverified")
check("不能证明策略在其他图像上也有 100% 精确率" in text,
      "historical precision must not be generalized")
check("没有一个通用的 5% 比例能保证发现某类错误" in text,
      "sampling must not use an unsupported universal threshold")
check("实跑状态：** 2026-10-21" in text, "the local run scope/date must be explicit")
check("不再把该汇总呈现为可复核结果" in text,
      "unarchived aggregate-validation outputs must not be presented as reproducible")
meta = (ROOT / "src/content/chapters/multimodal/meta.ts").read_text(encoding="utf-8")
openai_checkpoint = meta.split("id: 'openai-response-chain-input-billing'", 1)[1].split("id: ", 1)[0]
check("basis: 'documented'" in openai_checkpoint,
      "OpenAI conversation-chain token accounting must be source-backed")
check("sourceIds: ['openai-conversation-state']" in openai_checkpoint,
      "OpenAI conversation-chain checkpoint must reference its official source")
check("previous_response_id" in openai_checkpoint and "input tokens" in openai_checkpoint,
      "checkpoint must state the documented previous-input billing boundary")
python_fences_all = re.findall(r"```python\s*\n([\s\S]*?)\n```", text)
check(all(max(map(len, fence.splitlines()), default=0) <= 88 for fence in python_fences_all),
      "Python examples must fit the production code-block width")

section = text.split("## 完整可运行代码", 1)[1].split("## 常见坑", 1)[0]
fences = re.findall(r"```python\s*([\s\S]*?)\s*```", section)
check(len(fences) == 1, "lesson should contain one isolated offline Python fence")
namespace: dict[str, object] = {}
output = io.StringIO()
with contextlib.redirect_stdout(output):
    exec(compile(fences[0], str(LESSON), "exec"), namespace)
check(output.getvalue().splitlines() == [
    "需复核: ['B']",
    "稳定错误需复核: []",
], "offline example output changed")

validation_section = text.split("## 组合校验策略", 1)[1].split("**三，跑多次", 1)[0]
validation_fences = re.findall(r"```python\s*([\s\S]*?)\s*```", validation_section)
check(len(validation_fences) == 1, "validation function fence is missing")
validation_namespace: dict[str, object] = {}
exec(compile(validation_fences[0], str(LESSON), "exec"), validation_namespace)
rows = [("ITM-101", "1", "0.10"), ("ITM-102", "2", "0.20")]
check(validation_namespace["check_consistency"](
    rows, expect_rows=2, total_qty=3, total_amount="0.30"
) == [], "Decimal total should pass the matching independent totals")
check(validation_namespace["check_consistency"](
    rows, expect_rows=2, total_qty=3, total_amount="0.31"
) == ["amount 合计 0.30 != 0.31"], "mismatched Decimal total should fail")
check(validation_namespace["check_consistency"](
    [("ITM-101", "1", "0.10")], expect_rows=1,
    total_qty=True, total_amount="0.10"
) == ["total_qty 必须是非负整数"], "boolean must not pass as a quantity total")
check(validation_namespace["check_consistency"](
    [("ITM-101", "1")], expect_rows=1
) == ["第 1 行必须包含 3 个字段"], "malformed rows should fail closed without IndexError")
check(validation_namespace["check_consistency"](
    [("ITM-101", "1", "NaN")], expect_rows=1
) == ["第 1 行 amount 必须是有限十进制数"], "non-finite amounts must be rejected")
check(validation_namespace["check_consistency"](
    [("ITM-101", "1", "0.001")], expect_rows=1
) == ["第 1 行 amount 最多保留两位小数"], "currency input must not be silently rounded")

print(f"PASS {checks}/{checks}; providerCalls=0; historical model metrics not tested")
