"""Offline contract checks for the compaction lesson; no provider calls."""

from __future__ import annotations

import re
from pathlib import Path

LESSON = Path("src/content/chapters/context-engineering/04-compaction.mdx")
text = LESSON.read_text(encoding="utf-8")
fences = re.findall(r"```python\n(.*?)\n```", text, flags=re.S)
assert len(fences) == 2, f"expected 2 Python fences, got {len(fences)}"
for index, source in enumerate(fences, 1):
    compile(source, f"lesson-python-fence-{index}", "exec")

helper_source = next(source for source in fences if "def validate_notes" in source)
scope: dict[str, object] = {}
exec(helper_source, scope)
validate_notes = scope["validate_notes"]
merge_notes = scope["merge_notes"]

sample = {
    "identifiers": [], "amounts": [], "dates": [], "rejected_proposals": [],
    "constraints": [], "error_codes": [], "contacts": [],
}
assert validate_notes(sample) == []
assert validate_notes({})  # missing schema fields fail
bad_source = {**sample, "constraints": [{"text": "no prod"}]}
assert any("missing fact_id or source" in e for e in validate_notes(bad_source))

one = {**sample, "amounts": [{"fact_id": "amount:v1", "value": 4820, "unit": "CNY", "what": "退款金额", "source": "turn-1"}]}
new = {"category": "amounts", "fact_id": "amount:v2", "value": 4800, "unit": "CNY", "what": "退款金额", "source": "turn-2"}
merged = merge_notes(one, [new])
assert len(merged["amounts"]) == 2  # a changed fact does not silently erase its predecessor
assert merge_notes(merged, [new]) == merged  # stable fact_id is idempotent
conflicting = {**new, "value": 4700}
try:
    merge_notes(merged, [conflicting])
except ValueError as exc:
    assert "conflicting contents" in str(exc)
else:
    raise AssertionError("same fact_id with a different value must be rejected")
assert merged["amounts"][-1]["value"] == 4800
try:
    merge_notes(sample, [{"category": "unknown", "fact_id": "x"}])
except ValueError:
    pass
else:
    raise AssertionError("unknown category must fail")

checks = [
    "逐次原始请求/响应、准确 endpoint/model、完整 usage 与 scorer 未归档",
    "不能把“先读全量历史”当成所有压缩 API 的统一实现细节",
    "字段由你定义，缺字段和格式错误更容易由程序检查",
    "它不保证模型填对、填全",
    "不能保证模型不补全",
    "不能把 70%/50% 当通用阈值",
    "server-side compaction / context editing",
    "Responses API 也提供 compaction 接口",
    "exactly one of ANTHROPIC_API_KEY or ANTHROPIC_AUTH_TOKEN",
    "resp.stop_reason != \"end_turn\"",
]
for marker in checks:
    assert marker in text, f"missing lesson boundary: {marker}"

print("offline assertions passed: 21")
