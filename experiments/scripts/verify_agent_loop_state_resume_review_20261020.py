"""Recheck the state/resume lesson's executable crash model and recovery boundary."""

from __future__ import annotations

import contextlib
import io
import os
import re
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/agent-loop/04-state-and-resume.mdx"
source = LESSON.read_text(encoding="utf-8")
fences = re.findall(r"^```python\s*\n([\s\S]*?)^```\s*$", source, re.MULTILINE)
assert len(fences) == 2, f"expected 2 Python fences, found {len(fences)}"

for index, fence in enumerate(fences, start=1):
    compile(fence, f"{LESSON}:python-fence-{index}", "exec")

with tempfile.TemporaryDirectory(prefix="agent-state-resume-") as temp_dir:
    old_cwd = os.getcwd()
    try:
        os.chdir(temp_dir)
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            exec(compile(fences[1], str(LESSON), "exec"), {"__name__": "__main__"})
    finally:
        os.chdir(old_cwd)

run_output = output.getvalue()
assert "最终记录数：4" in run_output
assert "实际写入序列：['u1', 'u2', 'u2', 'u3']" in run_output
assert "最终记录数：3" in run_output
assert "实际写入序列：['u1', 'u2', 'u3']" in run_output

helper: dict[str, object] = {"__name__": "review_helper"}
exec(compile(fences[0], str(LESSON), "exec"), helper)
pending_check = helper["trailing_unanswered_tool_uses"]
assert callable(pending_check)
find_pending = pending_check
assistant = {
    "role": "assistant",
    "content": [
        {"type": "tool_use", "id": "op-a"},
        {"type": "tool_use", "id": "op-b"},
    ],
}
assert [block["id"] for block in find_pending([assistant])] == ["op-a", "op-b"]
partially_answered = [
    assistant,
    {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "op-a"}]},
]
assert [block["id"] for block in find_pending(partially_answered)] == ["op-b"]
fully_answered = [
    assistant,
    {
        "role": "user",
        "content": [
            {"type": "tool_result", "tool_use_id": "op-a"},
            {"type": "tool_result", "tool_use_id": "op-b"},
        ],
    },
]
assert find_pending(fully_answered) == []
assert find_pending([{"role": "user", "content": "ordinary message"}]) == []

required_claims = [
    "tool_result.is_error=true",
    "不能为了让 transcript 通过校验，就伪造",
    "暂停 provider 对话并向调用方报告 `outcome_unknown`",
    "本地教学脚本在单进程顺序执行下",
    "`tool_use.id` 只用于协议结果配对",
]
for claim in required_claims:
    assert claim in source, f"missing required recovery boundary: {claim}"

print(
    "PASS: 2 Python fences compiled; crash experiment reproduced naive=4/idempotent=3; "
    "4 tail-recovery helper cases passed; recovery-boundary prose present."
)
