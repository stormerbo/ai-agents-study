"""Offline checks for the memory conflict, expiry, and deletion lesson."""

from __future__ import annotations

import ast
import contextlib
import io
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/memory/04-forgetting-and-conflict.mdx"
text = LESSON.read_text()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


require("逐次请求、响应、提示快照、评分器与精确模型路由未归档" in text,
        "historical conflict runs need an evidence boundary")
require("不能证明时间戳导致稳定" in text, "do not claim causal timestamp effect")
require("仅凭较新时间不能证明用户想覆盖旧规则" in text, "timestamps do not prove user intent")
require("明确、可验证的更新关系" in text and "阻止自动注入" in text,
        "ambiguous conflicts must fail closed")
require("不能跨场景固定排成一个通用真值顺序" in text,
        "source types must not be treated as a universal ranking")
require("没有适用于所有产品的固定 TTL" in text,
        "TTL durations must remain workload-specific")
require("tombstone" in text and "outbox" in text and "revision" in text,
        "deletion sketch must fence and retry cross-store cleanup")
require("检索命中后、注入前仍需向权威库校验" in text,
        "stale index entries must not be injectable")
require("不覆盖副本、缓存、备份和法律保留策略" in text,
        "deletion sketch limitations must be explicit")
require("超阈值时示例代码只打上待审标记" in text,
        "topic limits must not be treated as truth or auto-overwrite")

fences = re.findall(r"```python\s*\n(.*?)\n```", text, re.S)
require(len(fences) == 3, "expected resolver, deletion protocol, and topic gate fences")
for index, source in enumerate(fences, 1):
    ast.parse(source, filename=f"memory-forgetting-fence-{index}")

resolver = {"__name__": "lesson_resolver"}
exec(compile(fences[0], "resolver.py", "exec"), resolver)
resolve = resolver["resolve"]
args = {"scope": "project:demo", "key": "reply_language",
        "now": "2026-10-21T00:00:00+08:00"}
captured = io.StringIO()
with contextlib.redirect_stdout(captured):
    exec(compile(fences[0], "resolver.py", "exec"), {"__name__": "__main__"})
require(captured.getvalue().strip() == "有明确版本链: m2\n没有版本链: needs_review",
        "resolver output must match the lesson golden")
require(resolve(resolver["MEMORIES"], **args)["record"]["id"] == "m2",
        "explicit supersession chain should produce its unique tip")
fork = [dict(r, supersedes_id=None) for r in resolver["MEMORIES"]]
require(resolve(fork, **args)["status"] == "needs_review",
        "unrelated conflicting values must go to review")
mixed_source = [dict(resolver["MEMORIES"][0]), dict(resolver["MEMORIES"][1], source="observed")]
require(resolve(mixed_source, **args)["status"] == "needs_review",
        "different evidence classes must not be ordered automatically")
cycle = [dict(resolver["MEMORIES"][0], supersedes_id="m2"),
         dict(resolver["MEMORIES"][1], supersedes_id="m1")]
require(resolve(cycle, **args)["status"] == "needs_review", "version cycles must fail closed")
other_scope = [dict(r, scope="project:other") for r in resolver["MEMORIES"]]
require(resolve(other_scope, **args)["status"] == "none",
        "records from another scope must not conflict")
expired = [dict(resolver["MEMORIES"][1], valid_until="2026-10-20T00:00:00+08:00")]
require(resolve(expired, **args)["status"] == "none", "expired records must not be selected")
try:
    resolve([dict(resolver["MEMORIES"][0], event_at="2026-03-01T09:00:00")], **args)
except ValueError:
    pass
else:
    raise AssertionError("naive timestamps must be rejected")

require(fences[1].index("tombstone_and_clear_payload") < fences[1].index("enqueue_outbox"),
        "deletion must tombstone the authoritative record before queuing cleanup")
topic_gate = {"__name__": "lesson_topic_gate"}
exec(compile(fences[2], "topic-gate.py", "exec"), topic_gate)
topic_output = io.StringIO()
with contextlib.redirect_stdout(topic_output):
    exec(compile(fences[2], "topic-gate.py", "exec"), {"__name__": "__main__"})
require(topic_output.getvalue().strip().splitlines() == [
    "待审组: [{'scope': 'project:demo', 'topic': 'reply_language', 'ids': ['m1', 'm2'], 'count_over_limit': 1}]",
    "标记后: [('m1', True), ('m2', True), ('m3', False)]",
], "topic gate output must match the published golden")
groups, pending = topic_gate["classify"]([
    {"id": "a", "scope": "tenant:a", "topic": "reply_language", "status": "active"},
    {"id": "b", "scope": "tenant:a", "topic": "reply_language", "status": "active"},
    {"id": "c", "scope": "tenant:b", "topic": "reply_language", "status": "active"},
])
require(len(pending) == 1 and pending[0]["scope"] == "tenant:a",
        "review thresholds must be partitioned by scope")
records = [{"id": "a", "scope": "tenant:a", "pending_review": "old"}]
topic_gate["mark_pending"](records, [])
require("pending_review" not in records[0], "resolved candidates must clear stale review markers")

print("memory forgetting/conflict review: checks passed")
