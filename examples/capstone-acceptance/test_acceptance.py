import unittest

from acceptance import Evidence, REQUIRED_GATES, REQUIRED_KINDS, decide


def all_evidence(kind="integration"):
    return [Evidence(gate, "passed", REQUIRED_KINDS.get(gate, kind), f"artifact://{gate}") for gate in REQUIRED_GATES]


class AcceptanceTests(unittest.TestCase):
    def test_missing_gate_makes_report_incomplete(self):
        self.assertEqual(decide(all_evidence()[:-1])["decision"], "incomplete")

    def test_failed_invariant_blocks_even_if_other_gates_pass(self):
        items = all_evidence("live")
        items[0] = Evidence(items[0].gate_id, "failed", "live", "trace://failed")
        self.assertEqual(decide(items)["decision"], "blocked")

    def test_fixture_only_model_result_cannot_satisfy_live_gate(self):
        items = all_evidence()
        gate = next(i for i, item in enumerate(items) if item.gate_id == "live_model_normal")
        items[gate] = Evidence("live_model_normal", "passed", "fixture", "artifact://fixture")
        self.assertEqual(decide(items)["decision"], "insufficient-evidence")

    def test_integration_fixture_cannot_replace_receiver_reconciliation(self):
        items = all_evidence()
        gate = next(i for i, item in enumerate(items) if item.gate_id == "receiver_without_idempotency")
        items[gate] = Evidence("receiver_without_idempotency", "passed", "fixture", "artifact://fixture")
        self.assertEqual(decide(items)["decision"], "insufficient-evidence")

    def test_unverified_gate_cannot_be_approved(self):
        items = all_evidence("live")
        gate = items[-1]
        items[-1] = Evidence(gate.gate_id, "unverified", "manual", "")
        self.assertEqual(decide(items)["decision"], "invalid-report")

    def test_complete_evidence_requests_human_acceptance_not_auto_release(self):
        self.assertEqual(decide(all_evidence("live"))["decision"], "ready-for-human-acceptance")

    def test_duplicate_gate_is_invalid(self):
        items = all_evidence("live")
        items.append(items[0])
        self.assertEqual(decide(items)["decision"], "invalid-report")


if __name__ == "__main__":
    unittest.main()
