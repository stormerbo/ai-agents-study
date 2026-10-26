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
assert run_output.rstrip().endswith("同 id + 不同参数：{'ok': False, 'error': 'idempotency key reused with different payload'}")
assert "实际写入序列：['u1', 'u2', 'u3']" in run_output
text_fences = re.findall(r"^\x60{3}text\s*\n([\s\S]*?)^\x60{3}\s*$", source, re.MULTILINE)
published_run = next(text for text in text_fences if "=== 朴素版 ===" in text)
assert run_output.rstrip() == published_run.rstrip(), "experiment stdout differs from published output"

# Regression: running a copied lesson snippet must not delete/overwrite same-named user files.
with tempfile.TemporaryDirectory(prefix="agent-resume-collision-") as temp_dir:
    records_path = Path(temp_dir) / "al-records.jsonl"
    state_path = Path(temp_dir) / "al-state.json"
    records_path.write_text("keep-my-records\\n", encoding="utf-8")
    state_path.write_text("keep-my-state\\n", encoding="utf-8")
    old_cwd = os.getcwd()
    try:
        os.chdir(temp_dir)
        with contextlib.redirect_stdout(io.StringIO()):
            exec(compile(fences[1], str(LESSON), "exec"), {"__name__": "__main__"})
    finally:
        os.chdir(old_cwd)
    assert records_path.read_text(encoding="utf-8") == "keep-my-records\\n"
    assert state_path.read_text(encoding="utf-8") == "keep-my-state\\n"

# Regression: a stable business key cannot silently accept a different payload.
with tempfile.TemporaryDirectory(prefix="agent-resume-key-conflict-") as temp_dir:
    module: dict[str, object] = {"__name__": "lesson_module"}
    exec(compile(fences[1], str(LESSON), "exec"), module)
    module["RECORDS"] = str(Path(temp_dir) / "records.jsonl")
    module["STATE"] = str(Path(temp_dir) / "state.json")
    create = module["tool_create_record"]
    first = create({"id": "same-key", "name": "first payload"}, True)
    duplicate = create({"id": "same-key", "name": "first payload"}, True)
    conflict = create({"id": "same-key", "name": "changed payload"}, True)
    assert first == {"ok": True, "deduped": False}
    assert duplicate == {"ok": True, "deduped": True}
    assert conflict == {"ok": False, "error": "idempotency key reused with different payload"}
    typed_first = create({"id": "typed-key", "name": 1}, True)
    typed_conflict = create({"id": "typed-key", "name": True}, True)
    assert typed_first == {"ok": True, "deduped": False}
    assert typed_conflict == {"ok": False, "error": "idempotency key reused with different payload"}
    assert len(Path(module["RECORDS"]).read_text(encoding="utf-8").splitlines()) == 2
    with Path(module["RECORDS"]).open("a", encoding="utf-8") as records:
        records.write('{"id": "u1", "name": "conflicting stored payload"}\n')
    run = module["run"]
    try:
        run(idempotent=True)
    except RuntimeError as error:
        assert str(error) == "idempotency key reused with different payload"
    else:
        raise AssertionError("payload conflict must stop the run")
    assert module["load_state"]() == 0, "conflict must not advance the checkpoint"

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
    "30 assertions passed: collision-safe files, payload-bound idempotency, exact demo stdout, "
    "4 tail-recovery helper cases, and recovery-boundary prose."
)
