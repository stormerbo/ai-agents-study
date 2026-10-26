import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/what-is-an-agent/04-how-to-use-this-site.mdx"
META = ROOT / "src/content/chapters/what-is-an-agent/meta.ts"
ROUTE = ROOT / "src/app/api/chat/route.ts"
BYOK = ROOT / "src/lib/byok/storage.ts"
FIRST_LOOP = ROOT / "examples/first-loop/readonly_support.py"
FIRST_LOOP_TEST = ROOT / "tests/first-loop-path.test.ts"
source = LESSON.read_text()
meta = META.read_text()
route = ROUTE.read_text()
byok = BYOK.read_text()
first_loop = FIRST_LOOP.read_text()
first_loop_test = FIRST_LOOP_TEST.read_text()
chapter_meta = list((ROOT / "src/content/chapters").glob("*/meta.ts"))
checks = 0


def check(condition, message):
    global checks
    assert condition, message
    checks += 1


check(len(chapter_meta) == 26, f"expected 26 chapter metadata files, got {len(chapter_meta)}")
check(all(f"阶段 {number}" in source for number in range(6)), "the map must describe all six stages")
check("不代表每章都以前面所有章节为前置" in source, "stage order must not imply strict prerequisites")
check("具体先修关系以每章自检页和[知识地图](/map)中的连线为准" in source, "the curriculum graph is the prerequisite authority")
check("第一轮动手路径" in source and "examples/first-loop/readonly_support.py" in source, "the first hands-on path must point to the local read-only fixture")
check("只读订单 fixture" in source and "不连接真实订单系统" in source, "the first path must disclose fixture and side-effect scope")
check("最多进行 4 轮模型请求" in source and "512 token" in source, "the example's explicit limits must be documented")
check("第 1 章（LLM API）" in source and "第 20 章（生产部署）" in source, "chapter references should match current order")
check("不是对所有读者的收益排名" in source, "the short path must remain a course suggestion")
check("不构成生产可用 agent 的验收清单" in source, "a minimal loop must not be presented as production readiness")
check("basis" in source and "sourceIds" in source and "未能核实" in source, "the example must accurately explain evidence labels")
check("持久模式使用 `localStorage`" in source and "只在当前会话内存保存" in source, "credential storage modes must be distinguished")
check("Key 会经过本站服务并在请求处理中可见" in source, "must disclose the server proxy path")
check("不等于部署平台没有日志" in source and "错误内容绝不会回显" in source, "avoid an absolute no-logging/no-echo promise")
check("账号同步或服务端凭据库" in source, "be clear that browser storage is not account synchronization")
check("可取得的 token 用量" in source and "不是保证精确复现的唯一依据" in source, "traces must be scoped to observable fields")
check("不能证明工具副作用或业务结果成功" in source, "a trace must not be equated with business completion")
check("链接巡检只能说明页面可访问" in source and "不能证明页面内容" in source, "link checks must not be presented as accuracy review")
check("尚未完成逐条、独立的领域专家审阅" in source, "disclose the actual expert-review scope")
check("开户、账单与免费额度随地区和时间变化" in source, "billing terms must be treated as dynamic")
check("deepseek-flash / claude-sonnet-5" not in source and "通常需要绑卡/预充值" not in source, "remove stale model and billing claims")
check("按控制台当前要求" in source and "endpoint 当前支持的 model ID" in source, "provider credentials and model IDs must be checked at source")
check("身份认证方式" not in source and "API 格式" in source, "authentication instructions should defer to the selected endpoint contract")
check("模型提出调用后，仍由宿主执行工具并回填结果" in source, "the first-loop path must distinguish proposal from host execution")
check("id: 'stage-order'" in meta and "阶段顺序是硬性先修要求吗" in meta, "self-check answer must match the clarified stage model")
check("不表示后续阶段的每一章都以前面所有章节为先修" in meta, "metadata should not reintroduce a strict stage dependency")
check("x-byok-key" in route and "creds: { apiKey" in route, "the key must be described as entering the app server and being forwarded upstream")
check("localStorage.setItem" in byok and "session" in byok, "browser persistence and memory-only mode must match implementation")
check("return err.message" in route and "不保证错误内容绝不会回显" in source, "do not promise raw upstream errors can never contain a secret")
check("MAX_OUTPUT_TOKENS = 512" in first_loop and "MAX_ROUNDS = 4" in first_loop, "documented first-loop limits must match the implementation")
check("MAX_OUTPUT_TOKENS = 512" in first_loop_test and "MAX_ROUNDS = 4" in first_loop_test, "the tracked test must cover the displayed limits")

check('completed_without_text' in source and '整批 `tool_use.id` 都是非空且唯一' in source, 'document the empty-final-text and complete-batch ID boundaries')
check('最后一轮才收到工具提议' in source and '拒绝 HTTP 重定向' in source, 'document final-round no-dispatch and redirect credential boundary')
check("id: 'redirect-credential-boundary'" in meta and "sourceIds: ['python-urllib-request']" in meta, 'the redirect behavior checkpoint must be source-bound')

# Execute the actual local example with scripted model responses. These tests never call a provider.
import importlib.util
import urllib.request

spec = importlib.util.spec_from_file_location("readonly_support_w6", FIRST_LOOP)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def response(reason, *blocks):
    return {"stop_reason": reason, "content": list(blocks)}


def tool_call(call_id="call-1"):
    return {"type": "tool_use", "id": call_id, "name": "lookup_order", "input": {"order_id": "A-1001"}}


lookups = []
original_lookup = module.lookup_order
module.lookup_order = lambda args: (lookups.append(args) or original_lookup(args))
last_round = module.run_agent(
    "A-1001 到哪了？",
    model_call=lambda *_args, **_kwargs: response("tool_use", tool_call()),
    max_rounds=1,
)
check(last_round["status"] == "max_rounds" and not lookups, "the last available model round must not dispatch an unusable tool batch")

lookups.clear()
missing_id = module.run_agent(
    "A-1001 到哪了？",
    model_call=lambda *_args, **_kwargs: response("tool_use", tool_call("")),
)
check(missing_id["status"] == "protocol_error" and not lookups, "missing tool-use IDs must fail before dispatch")

lookups.clear()
duplicate_ids = module.run_agent(
    "A-1001 到哪了？",
    model_call=lambda *_args, **_kwargs: response("tool_use", tool_call("same"), tool_call("same")),
)
check(duplicate_ids["status"] == "protocol_error" and not lookups, "duplicate tool-use IDs must fail before dispatch")

empty_final = module.run_agent(
    "你好",
    model_call=lambda *_args, **_kwargs: response("end_turn", {"type": "text", "text": "  "}),
)
check(empty_final["status"] == "completed_without_text", "an empty end_turn must not be reported as completed")

lookups.clear()
scripts = iter([
    response("tool_use", tool_call("valid-1")),
    response("end_turn", {"type": "text", "text": "订单 A-1001 已发货。"}),
])
normal = module.run_agent("A-1001 到哪了？", model_call=lambda *_args, **_kwargs: next(scripts))
check(normal["status"] == "completed" and normal["rounds"] == 2 and len(lookups) == 1, "a valid tool cycle should execute once and complete on a later response")

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread

forwarded_keys = []
target_server = None


class RedirectEndpoint(BaseHTTPRequestHandler):
    def do_POST(self):
        self.send_response(302)
        self.send_header("Location", f"http://127.0.0.1:{target_server.server_port}/capture")
        self.end_headers()

    def log_message(self, *_args):
        pass


class CredentialSink(BaseHTTPRequestHandler):
    def do_POST(self):
        forwarded_keys.append(self.headers.get("x-api-key"))
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'{"content": [], "stop_reason": "end_turn"}')

    def log_message(self, *_args):
        pass


target_server = ThreadingHTTPServer(("127.0.0.1", 0), CredentialSink)
source_server = ThreadingHTTPServer(("127.0.0.1", 0), RedirectEndpoint)
threads = [Thread(target=server.serve_forever, daemon=True) for server in (target_server, source_server)]
for thread in threads:
    thread.start()
old_base_url, old_model = module.BASE_URL, module.MODEL
old_token = os.environ.get("ANTHROPIC_AUTH_TOKEN")
try:
    module.BASE_URL = f"http://127.0.0.1:{source_server.server_port}"
    module.MODEL = "offline-test"
    os.environ["ANTHROPIC_AUTH_TOKEN"] = "dummy-test-credential"
    try:
        module.call_model([])
        redirect_error = ""
    except RuntimeError as exc:
        redirect_error = str(exc)
    check(redirect_error == "模型端点返回 HTTP 302", "the real API call path must stop on an HTTP redirect")
    check(forwarded_keys == [], "a redirect target must never receive the dummy API key")
finally:
    module.BASE_URL, module.MODEL = old_base_url, old_model
    if old_token is None:
        os.environ.pop("ANTHROPIC_AUTH_TOKEN", None)
    else:
        os.environ["ANTHROPIC_AUTH_TOKEN"] = old_token
    for server in (source_server, target_server):
        server.shutdown()
        server.server_close()
    for thread in threads:
        thread.join(timeout=1)

redirect_handler = module.RejectRedirects()
redirect = redirect_handler.redirect_request(
    urllib.request.Request("https://trusted.example/v1/messages", headers={"x-api-key": "dummy"}),
    object(), 302, "Found", {}, "https://attacker.example/collect",
)
check(redirect is None, "the API opener must reject redirects so credentials are not forwarded to a new host")
check("build_opener(RejectRedirects()).open(request" in first_loop, "call_model must use the redirect-rejecting opener")
check("urlopen(request" not in first_loop, "call_model must not use the default redirect-following urlopen path")

print(json.dumps({"checks": checks, "passed": checks, "chapterCount": len(chapter_meta), "providerCalls": 0, "firstLoopExecuted": True}, ensure_ascii=False))
