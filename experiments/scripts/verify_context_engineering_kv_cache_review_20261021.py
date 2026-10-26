from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
lesson = (ROOT / "src/content/chapters/context-engineering/07-kv-cache.mdx").read_text(encoding="utf-8")
meta = (ROOT / "src/content/chapters/context-engineering/meta.ts").read_text(encoding="utf-8")
resources = (ROOT / "src/content/curriculum/resources.ts").read_text(encoding="utf-8")

checks = {
    "DeepSeek Context Caching source is registered with current URL":
        "'deepseek-context-caching'" in resources
        and "https://api-docs.deepseek.com/guides/kv_cache/" in resources,
    "current docs separate unsupported Responses API controls from automatic cache support":
        "`prompt_cache_key` / `prompt_cache_retention`" in lesson
        and "不表示没有缓存能力" in lesson,
    "current DeepSeek cache behavior is bounded to documented prefix units, intervals and best-effort":
        "完整持久化单元匹配" in lesson
        and "固定 token 间隔" in lesson
        and "尽力而为" in lesson
        and "不保证每次都命中" in lesson,
    "current DeepSeek usage fields are distinct from historical Anthropic-compatible usage fields":
        "`prompt_cache_hit_tokens` / `prompt_cache_miss_tokens`" in lesson
        and "历史的 `cache_read` 字段" in lesson,
    "current docs are not used to backfill the unrecoverable 2026-10-08 observation":
        "不能据此反推 2026-10-08" in lesson
        and "原始逐次响应未归档" in lesson,
    "lesson checkpoint and resource IDs identify both current provider contracts":
        "deepseek-context-caching" in meta
        and "deepseek-responses-api" in meta
        and "claude-prompt-caching" in meta,
}

for name, passed in checks.items():
    print(("PASS" if passed else "FAIL") + ": " + name)

if not all(checks.values()):
    sys.exit(1)
