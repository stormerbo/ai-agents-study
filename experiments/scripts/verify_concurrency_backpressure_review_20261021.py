from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
LESSON = (ROOT / "src/content/chapters/cost-and-latency/06-concurrency-and-backpressure.mdx").read_text()
ADMISSION = (ROOT / "examples/concurrency-backpressure/admission.py").read_text()
TESTS = (ROOT / "examples/concurrency-backpressure/test_admission.py").read_text()
META = (ROOT / "src/content/chapters/cost-and-latency/meta.ts").read_text()


class ReviewContract(unittest.TestCase):
    def test_retry_after_supports_both_http_wire_forms(self):
        self.assertIn("HTTP-date", LESSON)
        self.assertIn("整数秒数", LESSON)

    def test_queue_wait_is_bounded_by_config_and_deadline(self):
        self.assertIn("max_queue_wait", ADMISSION)
        self.assertIn("deadline", ADMISSION)
        self.assertIn("queue_wait_exceeded", ADMISSION)
        self.assertIn("queue_wait", TESTS)

    def test_admission_limits_are_validated(self):
        self.assertIn("max_active", ADMISSION)
        self.assertIn("max_queue", ADMISSION)
        self.assertIn("invalid admission", ADMISSION)
        self.assertIn("nan", TESTS.lower())

    def test_retry_budget_checks_do_not_turn_invalid_hint_into_early_retry(self):
        self.assertIn("无效", LESSON)
        self.assertIn("最早重试时间", LESSON)
        self.assertIn("retry_after", ADMISSION)

    def test_ambiguous_connection_failure_is_not_replayed_by_default(self):
        self.assertIn("request_replay_safe: bool = False", ADMISSION)
        self.assertIn("request_replay_safe=True", TESTS)
        self.assertIn("结果未知时默认不重放", LESSON)

    def test_local_model_boundaries_are_explicit(self):
        self.assertIn("没有维护队列", LESSON)
        self.assertIn("原子扣减共享预算", LESSON)
        self.assertIn("分布式 worker", LESSON)

    def test_current_official_and_protocol_sources_are_registered(self):
        for source_id in ("openai-rate-limits", "anthropic-rate-limits", "anthropic-errors", "http-retry-after"):
            self.assertIn(source_id, META)


if __name__ == "__main__":
    unittest.main(verbosity=2)
