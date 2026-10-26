#!/usr/bin/env python3
"""Offline review checks for the provider-specific caching lesson."""

from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/cost-and-latency/03-caching.mdx"
META = ROOT / "src/content/chapters/cost-and-latency/meta.ts"
RESOURCES = ROOT / "src/content/curriculum/resources.ts"
text = LESSON.read_text(encoding="utf-8")
meta = META.read_text(encoding="utf-8")
resources = RESOURCES.read_text(encoding="utf-8")
checks = 0


def check(condition: bool, label: str) -> None:
    global checks
    checks += 1
    if not condition:
        raise AssertionError(label)


# Historical observations are clearly bounded and aren't presented as a replay.
check("原始逐次响应没有归档" in text, "missing missing-raw-response caveat")
check("不能单独证明因果" in text, "historical latency comparison overclaims causality")
check("历史 usage 表（原始响应缺失，无法独立复算）" in text, "table title implies a fresh run")
check("cache_read` 记为 4480" in text, "historical cache-read record disappeared")
check("不能据此报告通用的“缓存节省量”" in text, "historical usage promoted to a universal saving")
check("不能把这个解释当成已独立确认的因果结论" in text, "historical cost explanation overclaims")
check("cache_control` 是必要或有效条件" in text, "historical test is still attributed to cache_control")

# Provider contracts are kept distinct.
check('"model": "claude-opus-5-5"' in text, "explicit-breakpoint JSON is not scoped to Anthropic")
check("当前 DeepSeek Anthropic API 文档明确把 `cache_control` 列为 ignored" in text, "DeepSeek ignored field caveat missing")
check("prompt_cache_hit_tokens" in text and "prompt_cache_miss_tokens" in text, "DeepSeek Chat usage fields missing")
check("Anthropic Messages API 的总输入" in text, "Anthropic-specific usage formula missing")
check("这不是通用公式" in text and "不能跨 provider 直接相加字段" in text, "usage formula is not provider-scoped")
check("OpenAI 在输入 token details 下报告 cached tokens" in text, "OpenAI usage distinction missing")
check("缓存相关 usage 字段并没有跨 provider 的统一名称或含义" in text, "provider usage warning missing")
check("按 provider 文档核对字段，再按账单费率计算" in text, "cost accounting lacks provider-specific rates")

# Avoid absolutes about request protocol and caching behavior.
check("不要把“每一轮都重发全部历史”当作所有 agent runtime 的定律" in text, "agent request-state generalization remains")
check("server-side conversation state" in text, "server-side state caveat missing")
check("仅在第 1 节那个 stateless" in text, "quadratic model not scoped to its assumptions")
check("不能把“前缀不同”直接推成“全部缓存必然失效”" in text, "cache invalidation behavior is overstated")
check("不保证后续请求一定命中" in text, "cache hit guarantee missing")
check("应分别测量传输量、端到端时延和总费用" in text, "latency/network/cost dimensions not separated")

# Application-level caches must preserve freshness and authorization boundaries.
check("缓存键不是授权凭证" in text, "cache key is treated as authorization")
check("每次读取时按可信身份验证租户与对象权限" in text, "read-time object authorization missing")
check("过期时间" in text, "tool-result cache freshness boundary missing")

# Checkpoint sources are registered and cite the provider docs being described.
for source_id in (
    "claude-prompt-caching",
    "deepseek-context-caching",
    "deepseek-anthropic-api",
    "openai-prompt-caching",
):
    check(f"'{source_id}'" in meta, f"metadata missing source id: {source_id}")
    check(f"id: '{source_id}'" in resources, f"unregistered resource id: {source_id}")

# The complete local Python example compiles and runs; compare computed values to prose.
python_fences = re.findall(r"```python\s*\n(.*?)\n```", text, re.DOTALL)
check(len(python_fences) == 1, f"expected one Python fence, found {len(python_fences)}")
code = python_fences[0]
compile(code, str(LESSON), "exec")
with tempfile.NamedTemporaryFile("w", suffix=".py", encoding="utf-8") as script:
    script.write(code)
    script.flush()
    run = subprocess.run([sys.executable, script.name], capture_output=True, text=True, check=True)
check(re.search(r"第 2 段：工具定义\s+9\.8%", run.stdout) is not None, "displayed 9.8% does not match runnable code")
check(re.search(r"第 3 段：历史消息\s+21\.6%", run.stdout) is not None, "displayed 21.6% does not match runnable code")
check(re.search(r"第 4 段：本轮输入\s+95\.1%", run.stdout) is not None, "displayed 95.1% does not match runnable code")
check("差了 21.6 个百分点" in run.stdout, "model's stated difference does not match runnable code")

print(f"cost-caching-review: {checks}/{checks} checks passed; Python example executed; providerCalls=0")
