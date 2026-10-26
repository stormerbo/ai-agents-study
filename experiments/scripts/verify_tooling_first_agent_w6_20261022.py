"""W6 full-lesson boundary checks for the LangGraph first-agent lesson."""

from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/tooling/04-first-agent.mdx"
TEXT = LESSON.read_text(encoding="utf-8")


class FirstAgentBoundaries(unittest.TestCase):
    def test_distinguishes_caller_reinvoke_from_automatic_retry(self):
        self.assertIn("调用方捕获异常后再次调用 `invoke`", TEXT)
        self.assertIn("不是配置 LangGraph 的自动 retry policy", TEXT)

    def test_retry_heading_names_the_observed_path(self):
        self.assertIn("同一 thread 再次调用可能重复副作用", TEXT)
        self.assertNotIn("故障注入：节点重试会重复副作用", TEXT)

    def test_measured_console_lines_are_labeled_as_an_excerpt(self):
        self.assertIn("关键输出摘录（对应完整 stdout）", TEXT)
        for phrase in ("第 1 次执行后", "第 2 次 invoke 抛出异常", "再次 invoke 后", "work 节点被执行 3 次"):
            self.assertIn(phrase, TEXT)

    def test_graph_streaming_does_not_claim_to_provide_browser_transport(self):
        self.assertIn("浏览器传输仍由应用实现", TEXT)
        self.assertIn("LangGraph Graph API 提供图事件流", TEXT)

    def test_thread_and_side_effect_limits_remain_explicit(self):
        for phrase in (
            "thread_id` 不是用户身份凭证",
            "InMemorySaver` 只在当前进程内存中保存状态",
            "不等同于真实进程崩溃",
            "外部副作用的 exactly-once 保证",
        ):
            self.assertIn(phrase, TEXT)


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(FirstAgentBoundaries)
    )
    raise SystemExit(not result.wasSuccessful())
