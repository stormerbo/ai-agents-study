import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from score import ScoreError, score_pair


DATASET = {
    'version': 'support-fixtures-v1',
    'fields': ['order_id', 'intent', 'evidence'],
    'cases': [
        {'id': 'case-1', 'expected': {
            'order_id': 'A-1', 'intent': 'refund', 'evidence': 'late delivery'}},
        {'id': 'case-2', 'expected': {
            'order_id': 'B-2', 'intent': 'tracking', 'evidence': 'package delayed'}},
        {'id': 'case-3', 'expected': {
            'order_id': 'C-3', 'intent': 'cancel', 'evidence': 'duplicate order'}},
    ],
}

BEFORE = {
    'dataset_version': 'support-fixtures-v1',
    'prompt_version': 'prompt-1',
    'results': [
        {'case_id': 'case-1', 'status': 'ok', 'output': {
            'order_id': 'A-1', 'intent': 'refund', 'evidence': 'late delivery'}},
        {'case_id': 'case-2', 'status': 'ok', 'output': {
            'order_id': 'B-2', 'intent': 'tracking', 'evidence': 'late package'}},
        {'case_id': 'case-3', 'status': 'error', 'error': 'timeout'},
    ],
}

AFTER = {
    'dataset_version': 'support-fixtures-v1',
    'prompt_version': 'prompt-2',
    'results': [
        {'case_id': 'case-1', 'status': 'ok', 'output': {
            'order_id': 'A-1', 'intent': 'refund', 'evidence': 'late delivery'}},
        {'case_id': 'case-2', 'status': 'ok', 'output': {
            'order_id': 'B-3', 'intent': 'tracking', 'evidence': 'package delayed'}},
        {'case_id': 'case-3', 'status': 'ok', 'output': {
            'order_id': 'C-3', 'intent': 'cancel', 'evidence': 'duplicate order'}},
    ],
}


class PromptRegressionTests(unittest.TestCase):
    def test_scores_both_versions_on_same_denominator_and_surfaces_regression(self):
        report = score_pair(DATASET, BEFORE, AFTER)
        self.assertEqual(report['cases'], 3)
        self.assertEqual(report['before']['exact_match'], 1 / 3)
        self.assertEqual(report['after']['exact_match'], 2 / 3)
        self.assertEqual(report['before']['field_accuracy']['evidence'], 1 / 3)
        self.assertEqual(report['after']['field_accuracy']['evidence'], 1.0)
        self.assertEqual(report['regressed_cases'], [])
        self.assertEqual(report['field_regressions']['order_id'], ['case-2'])
        self.assertEqual(report['before']['failed_runs'], 1)

    def test_refuses_dataset_version_or_case_set_drift(self):
        drifted = {**AFTER, 'dataset_version': 'other'}
        with self.assertRaises(ScoreError):
            score_pair(DATASET, BEFORE, drifted)

    def test_refuses_duplicate_or_missing_case_results(self):
        duplicate = {**AFTER, 'results': AFTER['results'] + [AFTER['results'][0]]}
        missing = {**AFTER, 'results': AFTER['results'][:-1]}
        for candidate in (duplicate, missing):
            with self.subTest(candidate=len(candidate['results'])):
                with self.assertRaises(ScoreError):
                    score_pair(DATASET, BEFORE, candidate)


if __name__ == '__main__':
    unittest.main()
