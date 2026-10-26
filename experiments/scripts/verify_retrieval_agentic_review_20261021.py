import re
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/retrieval/05-agentic-retrieval.mdx"
META = ROOT / "src/content/chapters/retrieval/meta.ts"
source = LESSON.read_text()
meta = META.read_text()
fences = re.findall(r"^```([^\n]*)\n([\s\S]*?)^```\s*$", source, re.M)
python = [body for lang, body in fences if lang.strip() == "python"]
assert len(python) == 2, len(python)

checks = 0


def check(condition, message):
    global checks
    assert condition, message
    checks += 1


# Run the provider-independent full control-flow example.
demo_index = next(i for i, (lang, body) in enumerate(fences) if lang.strip() == "python" and "class FakePlanner" in body)
demo = fences[demo_index][1]
run = subprocess.run(
    [sys.executable, "-c", demo], capture_output=True, text=True, check=True
)
expected = (
    "可跳过检索: done_without_evidence searches= 0\n"
    "证据驱动多步: done searches= 2 evidence= ['cache', 'rerank']\n"
    "格式错误: protocol_error searches= 0\n"
)
check(
    run.stdout == expected
    and fences[demo_index + 1][0].strip() == "text"
    and run.stdout == fences[demo_index + 1][1],
    "demo output matches adjacent text fence",
)
demo_ns = {"__name__": "demo_module"}
exec(compile(demo, "retrieval_policy_demo.py", "exec"), demo_ns)

# Test strict query parsing and the retrieval-loop boundary with fakes.
outline = next(body for body in python if "def parse_queries" in body)
ns = {}
exec(outline, ns)
check(ns["parse_queries"]('["one", "two"]') == ["one", "two"], "valid array")
check(ns["parse_queries"]('{"queries": ["one"]}') == [], "object rejected")
check(ns["parse_queries"]('["one", 2]') == [], "mixed array rejected")
check(ns["parse_queries"]('["one", "two", "three", "four"]') == [], "over-limit rejected")
check(ns["merge_hits"]([(1, ["a", "b"]), (2, ["b", "c"])], 3) == ["a", "b", "c"], "dedupe order")


class FakeResponse:
    def __init__(self, text, stop_reason="end_turn"):
        self.content = [SimpleNamespace(type="text", text=text)]
        self.stop_reason = stop_reason


class FakeMessages:
    def __init__(self, response):
        self.response = response
        self.requests = []

    def create(self, **kwargs):
        self.requests.append(kwargs)
        return self.response


def fake_client(text, stop_reason="end_turn"):
    client = SimpleNamespace()
    client.messages = FakeMessages(FakeResponse(text, stop_reason))
    return client


rewrite_queries = []
client = fake_client('["q1", "q2"]')
merged = ns["arm_b"](
    client, "fixture-model", "original question",
    lambda q: rewrite_queries.append(q) or {"q1": ["a", "b"], "q2": ["b", "c"]}[q],
    k=3,
)
check(
    rewrite_queries == ["q1", "q2"] and merged == ["a", "b", "c"]
    and len(client.messages.requests) == 1,
    "one rewrite call fans out to deduplicated searches",
)

fallback_queries = []
client = fake_client("not JSON")
fallback = ns["arm_b"](
    client, "fixture-model", "original question",
    lambda q: fallback_queries.append(q) or ["original-result"],
)
check(fallback_queries == ["original question"] and fallback == ["original-result"], "invalid rewrite falls back to original query")

fallback_queries = []
client = fake_client('["rewrite"]', stop_reason="max_tokens")
fallback = ns["arm_b"](
    client, "fixture-model", "original question",
    lambda q: fallback_queries.append(q) or ["original-result"],
)
check(fallback_queries == ["original question"] and fallback == ["original-result"], "nonterminal rewrite falls back to original query")

client = fake_client("DONE")
retrieved, status = ns["arm_c"](
    client, "fixture-model", "query", lambda q: ["doc-1"],
    {"doc-1": "authoritative fixture evidence"}, max_rounds=2,
)
check(retrieved == ["doc-1"] and status == "done", "DONE after search")
check("authoritative fixture evidence" in client.messages.requests[0]["messages"][0]["content"], "body passed to planner")

client = fake_client("possibly done")
_, status = ns["arm_c"](
    client, "fixture-model", "query", lambda q: ["doc-1"],
    {"doc-1": "evidence"}, max_rounds=2,
)
check(status == "protocol_error", "malformed planner output is not DONE")

client = fake_client("DONE", stop_reason="max_tokens")
_, status = ns["arm_c"](
    client, "fixture-model", "query", lambda q: ["doc-1"],
    {"doc-1": "evidence"}, max_rounds=2,
)
check(status == "provider_nonterminal", "nonterminal response is not DONE")

try:
    ns["arm_c"](fake_client("DONE"), "fixture-model", "query", lambda q: [], {}, max_rounds=0)
except ValueError:
    check(True, "invalid max_rounds rejected")
else:
    check(False, "invalid max_rounds accepted")

budgeted = demo_ns["run_retrieval"](
    "缓存失效", demo_ns["FakePlanner"](["SEARCH: 重排候选"]),
    must_retrieve=True, max_searches=2,
)
check(
    budgeted["status"] == "search_budget_exhausted"
    and len(budgeted["events"]) == 2
    and set(budgeted["evidence"]) == {"cache", "rerank"},
    "search budget exhaustion remains distinct after another SEARCH action",
)

# Scope assertions keep old measurements and causes explicitly unverified.
check("不可独立复核的历史摘要" in source, "historical evidence label")
check("实测 3.3/10 与 6.3/10 的差距就出在这个决定上" not in source, "removed causal overclaim")
check("多轮的输入是 7.5 倍" not in source, "removed unverified ratio")
check("唯一值得开多轮" not in source, "removed universal use case")
check("不能由此说查询改写通常有效" in source, "no causal inference")
check("输入 token 比值 `5,660 / 754`" in source, "cost ratio caveat")
check("Self-RAG" in source and "Adaptive-RAG" in source, "research distinctions")
check("本轮用 fake client 核对解析与控制流边界" in source, "execution status matches local fake-client coverage")
check("自适应路由" in meta and "逐题报告" in meta, "checkpoint metrics")
check("约 20% 历史插值" in meta, "no universal 20% threshold")
check("adaptive-rag-naacl-2024" in meta and "self-rag-paper" in meta, "resources linked")

print(f"retrieval/agentic-retrieval review: {checks} local checks passed; providerCalls=0")
