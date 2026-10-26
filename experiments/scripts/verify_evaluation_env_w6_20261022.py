"""W6 whole-lesson boundary checks for evaluation/eval-env (2026-10-22)."""
from __future__ import annotations

import contextlib
import io
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LESSON_PATH = ROOT / "src/content/chapters/evaluation/05-eval-env.mdx"
META_PATH = ROOT / "src/content/chapters/evaluation/meta.ts"
LESSON = LESSON_PATH.read_text(encoding="utf-8")
FENCES = re.findall(r"```python\n(.*?)\n```", LESSON, re.DOTALL)


class EvaluationEnvironmentW6(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if len(FENCES) != 2:
            raise AssertionError(f"expected two Python fences, got {len(FENCES)}")
        cls.namespace = {"__name__": "lesson_w6_verifier"}
        exec(compile(FENCES[0], str(LESSON_PATH), "exec"), cls.namespace)

    def test_manifest_is_valid_and_versionable(self):
        json_fences = re.findall(r"```json\n(.*?)\n```", LESSON, re.DOTALL)
        self.assertEqual(len(json_fences), 1)
        manifest = __import__("json").loads(json_fences[0])
        self.assertEqual(
            manifest["isolation"], "one in-memory environment per case"
        )
        self.assertTrue(
            all(
                key in manifest
                for key in (
                    "fixture_version",
                    "tool_schema_version",
                    "grader_version",
                    "execution",
                )
            )
        )

    def test_lesson_demo_runs_all_contract_assertions(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            exec(compile(FENCES[0], str(LESSON_PATH), "exec"), {"__name__": "__main__"})
        self.assertIn(
            "PASS: fixture, execution, environment, grader, and cleanup states",
            output.getvalue(),
        )

    def test_clean_and_write_cases_are_scored(self):
        run_case = self.namespace["run_case"]
        agent = self.namespace["scripted_agent"]
        cases = {case["id"]: case for case in self.namespace["CASES"]}
        self.assertTrue(run_case(cases["clean-count"], agent)["passed"])
        self.assertTrue(run_case(cases["expected-write"], agent)["passed"])

    def test_invalid_fixture_is_not_scored(self):
        outcome = self.namespace["run_case"](
            next(c for c in self.namespace["CASES"] if c["id"] == "stale-fixture"),
            self.namespace["scripted_agent"],
        )
        self.assertEqual(outcome["status"], "invalid_fixture")
        self.assertNotIn("passed", outcome)

    def test_execution_exception_is_not_labeled_model_failure(self):
        def interrupted(*_):
            raise RuntimeError("runtime interrupted")

        outcome = self.namespace["run_case"](
            self.namespace["CASES"][0], interrupted
        )
        self.assertEqual(outcome["status"], "agent_runtime_error")
        self.assertEqual(outcome["error"], "RuntimeError")

    def test_tool_environment_error_is_separate(self):
        env = self.namespace["EvalEnv"]
        case = self.namespace["CASES"][0]

        def duplicate_id(environment, _):
            return environment.call_tool(
                "create_refund", {"refund_id": "R-001"}
            )

        outcome = self.namespace["run_case"](case, duplicate_id)
        self.assertEqual(outcome["status"], "environment_error")
        self.assertEqual(outcome["error"], "EnvironmentFailure")

    def test_grader_error_is_separate(self):
        def failed_grader(*_):
            raise AssertionError("grader parser failed")

        outcome = self.namespace["run_case"](
            self.namespace["CASES"][0],
            self.namespace["scripted_agent"],
            grader_fn=failed_grader,
        )
        self.assertEqual(outcome["status"], "grader_error")

    def test_cleanup_failure_does_not_overwrite_primary_status(self):
        base = self.namespace["EvalEnv"]

        class CleanupFailureEnv(base):
            def close(self):
                raise RuntimeError("cleanup failed")

        def interrupted(*_):
            raise RuntimeError("runtime interrupted")

        outcome = self.namespace["run_case"](
            self.namespace["CASES"][0],
            interrupted,
            env_factory=CleanupFailureEnv,
        )
        self.assertEqual(outcome["status"], "agent_runtime_error")
        self.assertEqual(outcome["cleanup"]["status"], "error")

    def test_documentation_describes_non_attribution_boundary(self):
        self.assertIn(
            "不能把它直接解释为模型能力失败或 provider 故障", LESSON
        )
        self.assertIn("清理结果单独写入", LESSON)
        self.assertIn("id: 'error-attribution'", META_PATH.read_text(encoding="utf-8"))

    def test_historical_3_of_5_claim_remains_withdrawn(self):
        data = (ROOT / "docs/DATA.md").read_text(encoding="utf-8")
        self.assertIn("数据：合成", LESSON)
        self.assertIn("无法独立复核", LESSON)
        self.assertIn("评测环境 3/5 退款记录", data)
        self.assertIn("已从实测结论撤下", data)

    def test_existing_documentation_sources_remain_attached(self):
        meta = META_PATH.read_text(encoding="utf-8")
        self.assertIn("openai-evaluation-best-practices", meta)
        self.assertIn("pytest-fixtures", meta)

    def test_negative_teardown_example_still_reproduces(self):
        namespace = {"__name__": "__main__"}
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            exec(compile(FENCES[1], str(LESSON_PATH), "exec"), namespace)
        self.assertIn(
            "Observed: AssertionError: environment did not return to initial state",
            output.getvalue(),
        )


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        EvaluationEnvironmentW6
    )
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print(
        f"providerCalls=0; externalNetworkCalls=0; tests={result.testsRun}; "
        f"failures={len(result.failures) + len(result.errors)}"
    )
    raise SystemExit(not result.wasSuccessful())
