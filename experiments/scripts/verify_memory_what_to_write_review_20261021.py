"""Offline regression checks for the memory write-policy lesson review."""

from __future__ import annotations

import ast
import contextlib
import io
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/memory/02-what-to-write.mdx"
DATA = (ROOT / "docs/DATA.md").read_text()
text = LESSON.read_text()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


require("保留下来的对话脚本有 7 句" in text, "dialogue must be counted from the retained seven user turns")
require("模型推断 2 条" not in text and "推断 1 句" in text, "one inference must not be counted as two candidates")
require("无法独立复核" in text, "historical provider result must carry its evidence limit")
require("敏感信息" in text and "用户控制" in text, "persistent-write policy must cover sensitive data and user control")
require("50 轮是 25.5 倍" in text, "50-round repeated-history ratio must match the stated triangular-growth model")
require("hashlib.sha256" in text, "record IDs must not collide on a shared key prefix")
require("max_tokens" in text and "跳过评分" in text, "truncated provider outputs must be rejected")
require('if stop != "end_turn" or not text.strip():' in text and "continue\n        audit(label, text)" in text, "provider loop must skip incomplete output before scoring")
require("逐次原始请求/响应" in DATA and "未归档" in DATA, "data ledger must disclose missing historical traces")

fences = re.findall(r"```python\s*\n(.*?)\n```", text, re.S)
require(len(fences) >= 2, "expected standalone policy and experiment Python examples")
for index, source in enumerate(fences, 1):
    ast.parse(source, filename=f"lesson-python-fence-{index}")

text_outputs = re.findall(r"```text\s*\n(.*?)\n```", text, re.S)
require(bool(text_outputs), "the local policy output must be shown")
script_fence = next((source for source in fences if "def to_record(" in source), None)
require(script_fence is not None, "the standalone write-policy fence must define to_record")
module: dict[str, object] = {"__name__": "lesson_write_policy"}
exec(compile(script_fence, "lesson-write-policy.py", "exec"), module)
rendered = io.StringIO()
with contextlib.redirect_stdout(rendered):
    exec(compile(script_fence, "lesson-write-policy.py", "exec"), {"__name__": "__main__"})
require(rendered.getvalue().strip() == text_outputs[0].strip(), "captured Python output must match the published output fence")
to_record = module["to_record"]
should_write = module["should_write"]
record_a = to_record("PostgreSQL", "用户明说", "tech_stack.postgresql", scope="tenant:a", source_ref="conversation:turn-1")
record_b = to_record("MySQL", "user_stated", "tech_stack.mysql", scope="tenant:a", source_ref="conversation:turn-1")
require(record_a["id"] != record_b["id"], "different dedup keys sharing a prefix must get different record IDs")
record_other_scope = to_record("PostgreSQL", "user_stated", "tech_stack.postgresql", scope="tenant:b", source_ref="conversation:turn-1")
require(record_a["id"] != record_other_scope["id"], "the same key in different scopes must not share an ID")
require(record_a["source"] == "user_stated", "display labels must be normalized before storage")
require(should_write("以后用 PostgreSQL", "用户明说", memory_enabled=True)[0], "recognized display source should pass the toy policy")
require(not should_write("可保存", "user_stated", memory_enabled=False)[0], "disabled memory must reject persistence")
require(not should_write("医疗记录", "user_stated", memory_enabled=True, sensitivity="restricted")[0], "restricted data must be rejected by the default policy")
try:
    to_record("x", "user_stated", "key", scope="tenant:a", source_ref="conversation:turn-1", ttl_days=True)
except ValueError:
    pass
else:
    raise AssertionError("boolean ttl_days must be rejected")
require(should_write("用户可能对价格敏感", "推理得到", memory_enabled=True)[0] is False, "model inference must not be silently stored as user fact")

print("memory what-to-write review: checks passed")
