"""Offline scope checks for deployment-shape claims and displayed arithmetic."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/agent-deployment/01-deployment-shape.mdx"
META = ROOT / "src/content/chapters/agent-deployment/meta.ts"
DATA = ROOT / "docs/DATA.md"


class DeploymentShapeW6Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.lesson = LESSON.read_text(encoding="utf-8")
        cls.meta = META.read_text(encoding="utf-8")
        cls.fences = re.findall(r"```python\n(.*?)\n```", cls.lesson, re.S)

    def test_historical_latency_scope_is_explicit(self) -> None:
        self.assertIn("四行历史数据只有各一条样本", self.lesson)
        self.assertIn("不能据此建立延迟分布、输出速率或固定网络开销", self.lesson)
        self.assertIn("没有足够证据把 0.6–0.9 秒归因于 TCP/TLS", self.lesson)
        self.assertIn("延迟四行历史摘要", DATA.read_text(encoding="utf-8"))
        self.assertNotIn("取决于输出长度", self.lesson)
        self.assertNotIn("0/3 —— 步数事先不知道", self.lesson)

    def test_task_attempts_and_idempotency_are_bounded(self) -> None:
        self.assertIn("这不等于应用的任务 deadline、审批、租户授权、外部副作用账本也由它管理", self.lesson)
        self.assertIn("https://developers.openai.com/api/docs/guides/conversation-state", self.lesson)
        self.assertIn("执行一次尝试", self.lesson)
        self.assertIn("崩溃、租约过期或重试可能产生后续尝试", self.lesson)
        self.assertIn("同键不同 payload 应返回冲突", self.lesson)
        self.assertIn("接收端实际执行的幂等键/fencing 契约", self.lesson)
        self.assertIn("只有在写入接收端验证 epoch 时才能拦截旧 owner", self.lesson)
        self.assertNotIn("执行唯一一次逻辑任务", self.lesson)

    def test_partial_results_and_event_cursor_are_distinct(self) -> None:
        self.assertIn("event_cursor?", self.lesson)
        self.assertIn("event_cursor` 是事件流的续读位置，不等于可直接交付的部分答案", self.lesson)
        self.assertIn("只有经过校验且对用户安全的产物才作为 `partial` 返回", self.lesson)
        self.assertNotIn("result?, partial?, cursor?", self.lesson)

    def test_provider_cache_contract_is_scoped(self) -> None:
        for url in (
            "https://platform.claude.com/docs/en/build-with-claude/prompt-caching",
            "https://developers.openai.com/api/docs/guides/prompt-caching",
            "https://api-docs.deepseek.com/guides/kv_cache/",
        ):
            self.assertIn(url, self.lesson)
        self.assertIn("不是 provider 实测命中率", self.lesson)
        self.assertIn("缓存断点、可匹配单元、TTL、usage 字段与计费规则要按提供方", self.meta)

    def test_latency_demo_compiles_and_matches_published_values(self) -> None:
        self.assertEqual(len(self.fences), 2)
        for i, fence in enumerate(self.fences):
            compile(fence, f"lesson-fence-{i}", "exec")
        result = subprocess.run(
            [sys.executable, "-c", self.fences[1]],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=True,
        )
        output = result.stdout
        for expected in (
            r"(?m)^  短任务\s+1\s+1\.9s\s+同步返回$",
            r"(?m)^  中任务\s+4\s+12\.1s\s+同步返回$",
            r"(?m)^  长任务\s+15\s+53\.7s\s+返回 task id$",
        ):
            self.assertRegex(output, expected)
        estimate_table = re.search(r"## 一个具体的情景演算.*?```text\n(.*?)\n```", self.lesson, re.S)
        self.assertIsNotNone(estimate_table)
        for expected in (
            r"(?m)^短任务\s+1\s+1\.9s\s+同步$",
            r"(?m)^中任务\s+4\s+12\.1s\s+同步（情景阈值附近）$",
            r"(?m)^长任务\s+15\s+53\.7s\s+返回任务 id$",
        ):
            self.assertRegex(estimate_table.group(1), expected)
        self.assertNotIn("49.7s", self.lesson)
        self.assertIn("不是实测基准或 ETA", self.lesson)

    def test_checkpoint_sources_exist_and_cancellation_is_scoped(self) -> None:
        self.assertNotIn("已产生的 token 仍会计费", self.meta)
        self.assertIn("取决于具体 API/SDK 与计费契约", self.meta)
        resources = (ROOT / "src/content/curriculum/resources.ts").read_text(encoding="utf-8")
        for resource_id in ("claude-prompt-caching", "openai-prompt-caching", "deepseek-context-caching"):
            self.assertIn(f"id: '{resource_id}'", resources)
            self.assertIn(f"'{resource_id}'", self.meta)


if __name__ == "__main__":
    unittest.main(verbosity=2)
