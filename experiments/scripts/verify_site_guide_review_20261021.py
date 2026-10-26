import json
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

print(json.dumps({"checks": checks, "passed": checks, "chapterCount": len(chapter_meta), "providerCalls": 0, "firstLoopExecuted": False}, ensure_ascii=False))
