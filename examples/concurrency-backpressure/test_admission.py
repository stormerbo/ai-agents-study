import unittest

from admission import admit, retry_delay


class AdmissionTests(unittest.TestCase):
    def test_starts_within_concurrency_cap(self):
        result = admit(now=10, deadline=20, active=2, queued=0, max_active=3,
                       max_queue=5, remaining_budget=10, reserve=2,
                       queue_wait=0, max_queue_wait=5)
        self.assertEqual((result.state, result.reserved_budget), ("started", 2))

    def test_over_capacity_queues_only_until_queue_bound(self):
        accepted = admit(now=10, deadline=20, active=3, queued=1, max_active=3,
                         max_queue=2, remaining_budget=10, reserve=1,
                         queue_wait=3, max_queue_wait=5)
        rejected = admit(now=10, deadline=20, active=3, queued=2, max_active=3,
                         max_queue=2, remaining_budget=10, reserve=1,
                         queue_wait=3, max_queue_wait=5)
        self.assertEqual((accepted.state, rejected.state), ("queued", "queue_full"))

    def test_admission_reserves_budget_before_queueing(self):
        result = admit(now=10, deadline=20, active=3, queued=0, max_active=3,
                       max_queue=2, remaining_budget=0.5, reserve=1,
                       queue_wait=1, max_queue_wait=5)
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

    def test_queue_wait_must_fit_both_queue_policy_and_deadline(self):
        policy_rejected = admit(now=10, deadline=30, active=3, queued=0, max_active=3,
                                max_queue=2, remaining_budget=10, reserve=1,
                                queue_wait=6, max_queue_wait=5)
        deadline_rejected = admit(now=10, deadline=15, active=3, queued=0, max_active=3,
                                  max_queue=2, remaining_budget=10, reserve=1,
                                  queue_wait=5, max_queue_wait=10)
        self.assertEqual((policy_rejected.state, deadline_rejected.state),
                         ("queue_wait_exceeded", "expired"))

    def test_invalid_capacity_and_non_finite_budget_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "capacity"):
            admit(now=10, deadline=20, active=0, queued=0, max_active=0,
                  max_queue=2, remaining_budget=10, reserve=1,
                  queue_wait=0, max_queue_wait=5)
        with self.assertRaisesRegex(ValueError, "values"):
            admit(now=10, deadline=20, active=0, queued=0, max_active=1,
                  max_queue=2, remaining_budget=float("nan"), reserve=1,
                  queue_wait=0, max_queue_wait=5)

    def test_capacity_counts_require_non_boolean_integers(self):
        base = dict(now=10, deadline=20, active=0, queued=0, max_active=1,
                    max_queue=2, remaining_budget=10, reserve=1,
                    queue_wait=0, max_queue_wait=5)
        for field, value in (("active", 0.5), ("queued", True),
                             ("max_active", True), ("max_queue", 2.5)):
            with self.subTest(field=field, value=value), self.assertRaisesRegex(ValueError, "capacity"):
                admit(**(base | {field: value}))

    def test_attempt_counts_require_non_boolean_integers(self):
        base = dict(error_kind="rate_limited", attempt=1, max_attempts=4,
                    now=10, deadline=60, retry_after=None)
        for field, value in (("attempt", 1.5), ("max_attempts", True)):
            with self.subTest(field=field, value=value), self.assertRaisesRegex(ValueError, "retry policy"):
                retry_delay(**(base | {field: value}))

    def test_negative_retry_after_is_not_treated_as_missing(self):
        with self.assertRaisesRegex(ValueError, "parsed non-negative"):
            retry_delay(error_kind="rate_limited", attempt=1, max_attempts=4,
                        now=10, deadline=60, retry_after=-1)

    def test_retry_jitter_is_additive_and_still_respects_server_minimum(self):
        delay = retry_delay(error_kind="rate_limited", attempt=1, max_attempts=4,
                            now=10, deadline=60, retry_after=5, jitter_seconds=0.5)
        self.assertEqual(delay, 5.5)

    def test_unknown_connection_outcome_requires_explicit_replay_safety(self):
        unsafe = retry_delay(error_kind="connection_error", attempt=1, max_attempts=4,
                             now=10, deadline=60, retry_after=None)
        safe = retry_delay(error_kind="connection_error", attempt=1, max_attempts=4,
                           now=10, deadline=60, retry_after=None,
                           request_replay_safe=True)
        self.assertIsNone(unsafe)
        self.assertEqual(safe, 1)


if __name__ == "__main__":
    unittest.main()
