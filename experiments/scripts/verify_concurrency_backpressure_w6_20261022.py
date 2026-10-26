from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
ADMISSION = (ROOT / "examples/concurrency-backpressure/admission.py").read_text()
TESTS = (ROOT / "examples/concurrency-backpressure/test_admission.py").read_text()
LESSON = (ROOT / "src/content/chapters/cost-and-latency/06-concurrency-and-backpressure.mdx").read_text()
META = (ROOT / "src/content/chapters/cost-and-latency/meta.ts").read_text()


class IntegerCapacityReview(unittest.TestCase):
    def test_capacity_counts_are_exact_integers(self):
        self.assertIn("capacities = (active, queued, max_active, max_queue)", ADMISSION)
        self.assertIn("type(value) is not int for value in capacities", ADMISSION)

    def test_retry_attempt_counts_are_exact_integers_before_policy_branching(self):
        guard = "if type(attempt) is not int or type(max_attempts) is not int:"
        self.assertIn(guard, ADMISSION)
        self.assertLess(ADMISSION.index(guard), ADMISSION.index("if error_kind not in transient"))

    def test_regressions_cover_fractional_and_boolean_counts(self):
        for sample in (
            '("active", 0.5)',
            '("queued", True)',
            '("max_active", True)',
            '("max_queue", 2.5)',
            '("attempt", 1.5)',
            '("max_attempts", True)',
        ):
            self.assertIn(sample, TESTS)

    def test_lesson_and_checkpoint_describe_python_type_boundary(self):
        self.assertIn("14 个本地测试全部通过", LESSON)
        self.assertIn("bool` 是 `int` 子类型", LESSON)
        self.assertIn("id: 'capacity-count-types'", META)
        self.assertIn("python-built-in-types", META)

    def test_complete_local_suite_passes(self):
        result = subprocess.run(
            [sys.executable, "-m", "unittest", "discover", "-s", "examples/concurrency-backpressure", "-v"],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("Ran 14 tests", result.stdout)
        self.assertIn("OK", result.stdout)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(IntegerCapacityReview)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print("providerCalls=0; externalNetworkCalls=0; checks=%d; failures=%d" % (result.testsRun, len(result.failures) + len(result.errors)))
    raise SystemExit(0 if result.wasSuccessful() else 1)
