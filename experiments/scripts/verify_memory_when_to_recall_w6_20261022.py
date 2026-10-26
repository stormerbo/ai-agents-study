#!/usr/bin/env python3
"""Verify local behavior and evidence boundaries in memory/when-to-recall."""
from __future__ import annotations

import contextlib
import io
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/memory/03-when-to-recall.mdx"
DATA = ROOT / "docs/DATA.md"
META = ROOT / "src/content/chapters/memory/meta.ts"
BODY = LESSON.read_text(encoding="utf-8")
DATA_TEXT = DATA.read_text(encoding="utf-8")
META_TEXT = META.read_text(encoding="utf-8")
PYTHON_FENCES = re.findall(r"^```python\s*\n(.*?)^```\s*$", BODY, re.MULTILINE | re.DOTALL)
TEXT_FENCES = re.findall(r"^```text\s*\n(.*?)^```\s*$", BODY, re.MULTILINE | re.DOTALL)

checks = 0


def check(condition: bool, message: str) -> None:
    global checks
    checks += 1
    if not condition:
        raise AssertionError(message)


check(len(PYTHON_FENCES) == 3, f"expected 3 Python fences, got {len(PYTHON_FENCES)}")
for index, fence in enumerate(PYTHON_FENCES):
    compile(fence, f"{LESSON}#python-fence-{index}", "exec")
    check(True, f"Python fence {index} compiles")

# Threshold fixture: boundary is inclusive; no result stays empty; calibration requires both labels.
vector_ns = {"__name__": "review_fixture"}
exec(compile(PYTHON_FENCES[0], str(LESSON), "exec"), vector_ns)
check(vector_ns["gate"]([("equal", 0.30), ("below", 0.299)], 0.30) == [("equal", 0.30)], "threshold boundary")
check(vector_ns["gate"]([("below", 0.1)], 0.3) == [], "empty gate result")
check("0.71 到 0.85" in vector_ns["summarize"]([0.91, 0.88, 0.93, 0.85], [0.62, 0.71, 0.58, 0.44]), "separated calibration")
check("边界重叠" in vector_ns["summarize"]([0.60, 0.85], [0.62, 0.71]), "overlapping calibration")
try:
    vector_ns["summarize"]([], [0.1])
except ValueError:
    check(True, "empty calibration rejected")
else:
    check(False, "empty calibration must be rejected")

vector_out = io.StringIO()
with contextlib.redirect_stdout(vector_out):
    exec(compile(PYTHON_FENCES[0], str(LESSON), "exec"), {"__name__": "__main__"})
vector_golden = next((item for item in TEXT_FENCES if item.startswith("校准样本可分")), None)
check(vector_golden is not None and vector_out.getvalue().rstrip() == vector_golden.rstrip(), "vector output matches lesson")

# Recall fixture: exact timezone-aware TTL, independent provenance and expiry gates, lexical score is candidate-only.
recall_ns = {"__name__": "review_fixture"}
exec(compile(PYTHON_FENCES[1], str(LESSON), "exec"), recall_ns)
check(recall_ns["self_test"]() == 4, "embedded recall self-tests")
memories = recall_ns["MEMORIES"]
check(recall_ns["is_expired"](memories[0]) is False, "fresh record remains active")
check(recall_ns["is_expired"](memories[4]) is True, "expired record is rejected")
boundary = {"updated_at": "2026-10-01T00:00:00+08:00", "ttl_days": 7}
check(recall_ns["is_expired"](boundary) is True, "TTL boundary expires at the configured instant")
for bad in (
    {"updated_at": "2026-10-01T00:00:00", "ttl_days": 7},
    {"updated_at": None, "ttl_days": 7},
    {"updated_at": 123, "ttl_days": 7},
    {"updated_at": "2026-10-01T00:00:00+08:00", "ttl_days": -1},
    {"updated_at": "2026-10-01T00:00:00+08:00", "ttl_days": True},
):
    try:
        recall_ns["is_expired"](bad)
    except ValueError:
        check(True, "invalid TTL timestamp/value fails closed")
    else:
        check(False, "invalid TTL timestamp/value must fail closed")
candidates, blocked = recall_ns["recall"]("帮我写一段部署脚本，把服务发到服务器上")
check([memory["id"] for memory, _ in candidates] == ["m1", "m2"], "candidate IDs")
check([memory["id"] for memory, _ in blocked] == ["m3", "m4", "m5"], "blocked IDs")
check([reason.split("：")[0] for _, reason in blocked] == ["来源闸门", "来源闸门", "时效闸门"], "provenance and TTL gates are separately exercised")
check([score for _, score in candidates] == [0.0, 0.0], "lexical zero-score candidates are explicitly exposed")
recall_out = io.StringIO()
with contextlib.redirect_stdout(recall_out):
    exec(compile(PYTHON_FENCES[1], str(LESSON), "exec"), {"__name__": "__main__"})
recall_golden = next((item for item in TEXT_FENCES if item.startswith("本地闸门测试")), None)
check(recall_golden is not None and recall_out.getvalue().rstrip() == recall_golden.rstrip(), "recall output matches lesson")

# Trace fixture: actual injected IDs and blocked IDs are captured without raw query text.
trace_ns = {"__name__": "review_fixture"}
exec(compile(PYTHON_FENCES[2], str(LESSON), "exec"), trace_ns)
row = trace_ns["record_trace"](
    "2026-10-21T15:55:08+08:00",
    "req-review-001",
    4,
    [("m1", 0.5)],
    [("m2", "below_threshold")],
)
check(row["injected_ids"] == ["m1"], "trace records injected IDs")
check([item["id"] for item in row["blocked"]] == ["m2"], "trace records blocked IDs")
check("query" not in row and "query_text" not in row, "trace omits raw query fields")
check("req-review-001" in trace_ns["trace_line"](row), "trace has correlation ID")
trace_out = io.StringIO()
with contextlib.redirect_stdout(trace_out):
    exec(compile(PYTHON_FENCES[2], str(LESSON), "exec"), {"__name__": "__main__"})
trace_golden = next((item for item in TEXT_FENCES if item.startswith('{"ts"')), None)
check(trace_golden is not None and trace_out.getvalue().rstrip() == trace_golden.rstrip(), "trace output matches lesson")

# Historical model evidence remains scoped to the surviving summary.
check("原始逐次请求、响应、评分器、模型路由与运行参数未归档" in BODY, "lesson discloses missing historical records")
check("不能证明普遍因果关系，也不能估计误召回发生率" in BODY, "lesson does not generalize historical effect")
check("不能由此估计误召回频率或普遍因果" in DATA_TEXT, "data ledger bounds historical evidence")
check("recall-gates-and-thresholds" in META_TEXT and "false-recall-cost" in META_TEXT, "checkpoint metadata updated")
check("误召回一定比漏召回更严重" in BODY and "不能把“误召回一定比漏召回更严重”当作通用规律" in BODY, "risk comparison is bounded")

print(f"memory when-to-recall review: {checks} checks passed")
