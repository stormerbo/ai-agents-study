import json
import math
import os
import re
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/retrieval/03-vector-limits.mdx"
text = LESSON.read_text()
fences = re.findall(r"^```[^\n]*\n([\s\S]*?)^```\s*$", text, re.M)
assert len(fences) == 7

toy = {"__name__": "toy_embed_module"}
exec(compile(fences[0], "hybrid_recall.py", "exec"), toy)
assert toy["embed"]("same input") == toy["embed"]("same input")
assert len(toy["embed"]("same input")) == 64
assert math.isclose(toy["cosine"](toy["embed"]("a b"), toy["embed"]("a b")), 1.0)
try:
    toy["cosine"]([1.0, 0.0], [1.0])
except ValueError:
    dimension_mismatch_rejected = True
else:
    dimension_mismatch_rejected = False
assert dimension_mismatch_rejected
assert toy["rrf"](["a", "b"], ["b", "a"])[0] == "a"

module = {"__name__": "rerank_module"}
old_environ = os.environ.copy()
try:
    os.environ.pop("ANTHROPIC_AUTH_TOKEN", None)
    os.environ["ANTHROPIC_BASE_URL"] = "https://fixture.invalid"
    os.environ["VERIFY_MODEL"] = "fixture-model"
    exec(compile(fences[4], "two_stage_rerank.py", "exec"), module)
finally:
    os.environ.clear()
    os.environ.update(old_environ)

parse = module["parse_rerank_response"]
assert parse("[1]", "end_turn", 3) == [1]
assert parse("[1]", "max_tokens", 3) is None
assert parse("not json", "end_turn", 3) is None
assert parse("answer: [1]", "end_turn", 3) is None
assert parse("[0]", "end_turn", 3) is None
assert parse("[4]", "end_turn", 3) is None
assert parse("[1, 1]", "end_turn", 3) is None

calls = []
handlers = []
class FakeResponse:
    def __enter__(self): return self
    def __exit__(self, *_): return False
    def read(self):
        return json.dumps({
            "content": [{"type": "text", "text": "[1]"}],
            "usage": {"input_tokens": 12, "cache_read_input_tokens": 4, "output_tokens": 3},
            "stop_reason": "end_turn",
        }).encode()

class FakeOpener:
    def open(self, request, timeout):
        calls.append((request.full_url, timeout))
        return FakeResponse()

def fake_build_opener(handler):
    handlers.append(handler)
    return FakeOpener()

original_build_opener = urllib.request.build_opener
urllib.request.build_opener = fake_build_opener
os.environ["ANTHROPIC_BASE_URL"] = "https://fixture.invalid"
os.environ["ANTHROPIC_AUTH_TOKEN"] = "offline-fixture-token"
os.environ["VERIFY_MODEL"] = "fixture-model"
try:
    result = module["rerank"]("q", ["a", "b"])
finally:
    os.environ.pop("ANTHROPIC_BASE_URL", None)
    os.environ.pop("ANTHROPIC_AUTH_TOKEN", None)
    os.environ.update(old_environ)
    urllib.request.build_opener = original_build_opener
assert calls == [("https://fixture.invalid/v1/messages", 180)]
assert result[1] == {"input_tokens": 12, "cache_read_input_tokens": 4, "output_tokens": 3}
assert result[2] == "end_turn"
assert len(handlers) == 1 and isinstance(handlers[0], module["RejectRedirects"])

redirect_guard = module["RejectRedirects"]()
real_opener = urllib.request.build_opener(module["RejectRedirects"]())
redirect_handlers = [h for h in real_opener.handlers if isinstance(h, urllib.request.HTTPRedirectHandler)]
assert len(redirect_handlers) == 1 and isinstance(redirect_handlers[0], module["RejectRedirects"])
request = urllib.request.Request(
    "https://provider.invalid/v1/messages", data=b"{}", headers={"x-api-key": "dummy-test-token"}
)
assert redirect_guard.redirect_request(request, None, 302, "Found", {}, "https://attacker.invalid/collect") is None

assert "0.012 到 0.041" in text
assert "不是通用中文分词器，也不是 BM25 分数" in text
assert "本节没有真实 embedding 端点或可复算的向量实验" in text
assert "API embeddings 默认做 L2 归一化" in text
assert "不能推广到其他 embedding provider" in text
assert "先用精确搜索做基线" in text
assert "RRF 不需要跨路分数校准" in text
assert "k₀=60" in text and "不是普遍最优值" in text
assert "天然免疫量纲差异" not in text
assert "不要把“十万条”当作通用切换阈值" in text
assert "几十上百个候选" not in text
assert "向量空间兼容性" in text

print("retrieval/vector-limits offline checks: 30/30 passed; providerCalls=0")
