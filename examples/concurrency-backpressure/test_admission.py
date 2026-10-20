import unittest

from admission import admit, retry_delay


class AdmissionTests(unittest.TestCase):
    def test_starts_within_concurrency_cap(self):
        result = admit(now=10, deadline=20, active=2, queued=0, max_active=3,
                       max_queue=5, remaining_budget=10, reserve=2)
        self.assertEqual((result.state, result.reserved_budget), ("started", 2))

    def test_over_capacity_queues_only_until_queue_bound(self):
        accepted = admit(now=10, deadline=20, active=3, queued=1, max_active=3,
                         max_queue=2, remaining_budget=10, reserve=1)
        rejected = admit(now=10, deadline=20, active=3, queued=2, max_active=3,
                         max_queue=2, remaining_budget=10, reserve=1)
        self.assertEqual((accepted.state, rejected.state), ("queued", "queue_full"))

    def test_admission_reserves_budget_before_queueing(self):
        result = admit(now=10, deadline=20, active=3, queued=0, max_active=3,
                       max_queue=2, remaining_budget=0.5, reserve=1)
        self.assertEqual(result.state, "budget_exhausted")

    def test_server_retry_after_is_a_minimum(self):
        delay = retry_delay(error_kind="rate_limited", attempt=1, max_attempts=4,
                            now=10, deadline=60, retry_after=5, backoff_base=1)
        self.assertEqual(delay, 5)

    def test_permanent_quota_failure_is_not_retried(self):
        self.assertIsNone(retry_delay(error_kind="quota_exhausted", attempt=1,
                                      max_attempts=4, now=10, deadline=60,
                                      retry_after=None))

    def test_retry_is_stopped_when_deadline_would_expire(self):
        self.assertIsNone(retry_delay(error_kind="overloaded", attempt=2,
                                      max_attempts=4, now=10, deadline=12,
                                      retry_after=3))

    def test_attempt_limit_caps_transient_retries(self):
        self.assertIsNone(retry_delay(error_kind="connection_error", attempt=4,
                                      max_attempts=4, now=10, deadline=60,
                                      retry_after=None))


if __name__ == "__main__":
    unittest.main()
