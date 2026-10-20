import json
import unittest
from pathlib import Path

from grounded_support import PolicyIndex, Principal, evaluate_cases, evaluate_recall, load_index


class GroundedSupportTests(unittest.TestCase):
    def setUp(self):
        self.index = PolicyIndex()
        self.index.add_document(
            doc_id="return-window",
            version="2026-01",
            tenant_id="tenant-a",
            text="Return requests for unused items are accepted within 30 days of delivery.",
            allowed_principals={"member-a"},
        )
        self.index.add_document(
            doc_id="refund-window-secret",
            version="2026-01",
            tenant_id="tenant-b",
            text="Refunds are processed within 5 business days after approval.",
            allowed_principals={"member-b"},
        )

    def test_retrieval_returns_only_authorized_evidence_with_versioned_citation(self):
        result = self.index.answer(
            Principal("member-a", "tenant-a"), "return unused items days", top_k=2
        )
        self.assertEqual(result.status, "evidence_found")
        self.assertEqual([item.doc_id for item in result.evidence], ["return-window"])
        self.assertEqual(result.evidence[0].version, "2026-01")
        self.assertIn("30 days", result.evidence[0].text)

    def test_no_matching_policy_abstains_instead_of_inventing_answer(self):
        result = self.index.answer(
            Principal("member-a", "tenant-a"), "Can I exchange a damaged item?"
        )
        self.assertEqual(result.status, "insufficient_evidence")
        self.assertEqual(result.evidence, [])
        self.assertIsNone(result.answer)

    def test_a_single_common_term_is_not_sufficient_evidence(self):
        result = self.index.answer(
            Principal("member-a", "tenant-a"), "days"
        )
        self.assertEqual(result.status, "insufficient_evidence")
        self.assertEqual(result.evidence, [])

    def test_query_terms_cannot_reveal_another_tenants_policy(self):
        result = self.index.answer(
            Principal("member-a", "tenant-a"), "refunds processed approval"
        )
        self.assertEqual(result.status, "insufficient_evidence")
        self.assertEqual(result.evidence, [])

    def test_deleted_document_is_not_returned(self):
        self.index.delete_document("return-window", "2026-01")
        result = self.index.answer(
            Principal("member-a", "tenant-a"), "return within days"
        )
        self.assertEqual(result.status, "insufficient_evidence")

    def test_policy_outside_validity_window_is_not_returned(self):
        self.index.add_document(
            doc_id="holiday-returns",
            version="2025-holiday",
            tenant_id="tenant-a",
            text="Holiday returns are accepted until January 15.",
            allowed_principals={"member-a"},
            valid_from="2025-12-01",
            valid_until="2026-01-15",
        )
        result = self.index.answer(
            Principal("member-a", "tenant-a"),
            "holiday returns January",
            as_of="2026-02-01",
        )
        self.assertEqual(result.status, "insufficient_evidence")

    def test_versioned_fixture_evaluation_reports_recall_citation_and_abstention(self):
        root = Path(__file__).parent
        index = load_index(root / "data" / "policies.json")
        cases = json.loads((root / "data" / "eval_cases.json").read_text())
        report = evaluate_cases(index, cases, top_k=1)
        self.assertEqual(report["case_count"], 3)
        self.assertEqual(report["recall_at_k"], 1.0)
        self.assertEqual(report["citation_precision"], 1.0)
        self.assertEqual(report["answer_exact_match"], 1.0)
        self.assertEqual(report["correct_abstentions"], 1)

    def test_undefined_retrieval_metrics_remain_null_when_denominator_is_empty(self):
        report = evaluate_cases(
            self.index,
            [{
                "case_id": "empty",
                "subject_id": "member-a",
                "tenant_id": "tenant-a",
                "query": "unsupported question",
                "relevant_doc_ids": [],
                "expected_answer": None,
                "as_of": "2026-03-01",
            }],
        )
        self.assertIsNone(report["recall_at_k"])
        self.assertIsNone(report["citation_precision"])

    def test_recall_is_measured_against_relevant_document_ids(self):
        score = evaluate_recall(
            retrieved=["a", "b"], relevant={"b", "c"}
        )
        self.assertEqual(score, 0.5)


if __name__ == "__main__":
    unittest.main()
