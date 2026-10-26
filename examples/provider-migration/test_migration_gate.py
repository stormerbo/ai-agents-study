import unittest

from migration_gate import Outcome, evaluate_case, migration_decision


class MigrationGateTests(unittest.TestCase):
    def test_tool_call_requires_name_and_arguments(self):
        result = evaluate_case("lookup", "tool_call", Outcome("tool_call", tool_name="lookup"))
        self.assertFalse(result["passed"])

    def test_refusal_is_not_completed_answer(self):
        result = evaluate_case("refuse", "completed", Outcome("refusal", text="I cannot help"))
        self.assertFalse(result["passed"])

    def test_truncation_remains_distinct_from_success(self):
        result = evaluate_case("long", "completed", Outcome("truncated", text="partial"))
        self.assertEqual(result["actual"], "truncated")
        self.assertFalse(result["passed"])

    def test_missing_usage_is_unknown_not_zero(self):
        result = evaluate_case("plain", "completed", Outcome("completed", text="ok"))
        self.assertIsNone(result["usage"]["input_tokens"])

    def test_missing_required_cases_blocks_a_decision(self):
        results = [evaluate_case("plain", "completed", Outcome("completed", text="ok"))]
        self.assertEqual(migration_decision(results, {"plain", "tool"}), "incomplete")

    def test_duplicate_case_ids_make_report_incomplete(self):
        result = evaluate_case("plain", "completed", Outcome("completed", text="ok"))
        self.assertEqual(migration_decision([result, result], {"plain"}), "incomplete")

    def test_empty_required_suite_is_not_a_fixture_pass(self):
        self.assertEqual(migration_decision([], set()), "incomplete")

    def test_fixture_pass_does_not_claim_live_migration(self):
        results = [evaluate_case("plain", "completed", Outcome("completed", text="ok"))]
        self.assertEqual(migration_decision(results, {"plain"}), "fixture-pass")



if __name__ == "__main__":
    unittest.main()
