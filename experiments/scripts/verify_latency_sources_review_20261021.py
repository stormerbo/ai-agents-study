from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
LESSON_PATH = ROOT / "src/content/chapters/cost-and-latency/02-latency-sources.mdx"
LESSON = LESSON_PATH.read_text()
DATA = (ROOT / "docs/DATA.md").read_text()
META = (ROOT / "src/content/chapters/cost-and-latency/meta.ts").read_text()


class LatencyReviewContract(unittest.TestCase):
    def test_historical_four_rows_are_not_generalized_to_fixed_rates(self):
        self.assertIn("无法独立复现", LESSON)
        self.assertIn("不能推断", LESSON)
        self.assertNotIn("生成时间完全由输出长度决定", LESSON)
        self.assertNotIn("180 token/秒，基本是个常数", LESSON)
        self.assertIn("原始逐次请求", DATA)

    def test_metrics_separate_provider_ttft_from_user_visible_and_agent_latency(self):
        for phrase in ("TTFT", "首个可见文本", "任务端到端延迟", "关键路径", "TPOT"):
            self.assertIn(phrase, LESSON)

    def test_latency_model_accounts_for_serial_parallel_work_and_overhead(self):
        for phrase in ("串行阶段求和", "并行分支取最长", "排队", "工具耗时", "重试"):
            self.assertIn(phrase, LESSON)

    def test_text_delta_is_the_user_visible_measurement_boundary(self):
        self.assertIn('delta.get("type") == "text_delta"', LESSON)
        self.assertIn("thinking", LESSON)
        self.assertIn("工具输入", LESSON)

    def test_no_provider_credentials_or_calls_are_required_for_the_runnable_fence(self):
        fences = re.findall(r"```python\n(.*?)\n```", LESSON, flags=re.DOTALL)
        self.assertGreaterEqual(len(fences), 1)
        for index, source in enumerate(fences):
            with tempfile.NamedTemporaryFile("w", suffix=f"_{index}.py", encoding="utf-8") as handle:
                handle.write(source)
                handle.flush()
                self.assertNotIn("os.environ", source)
                output = subprocess.run([sys.executable, handle.name], text=True, capture_output=True, check=True)
                self.assertTrue(output.stdout.strip())

    def test_current_sources_are_registered_and_used_by_checkpoints(self):
        for source_id in ("openai-latency-optimization", "anthropic-reduce-latency", "pd-serve-paper"):
            self.assertIn(source_id, META)


if __name__ == "__main__":
    unittest.main(verbosity=2)
