import unittest

from comparison import run_multi, run_single


class ComparisonTests(unittest.TestCase):
    def test_both_modes_use_same_frozen_cases_and_report_separate_metrics(self):
        single = run_single()
        multi = run_multi()
        self.assertEqual(single['case_ids'], multi['case_ids'])
        self.assertEqual(single['cases'], multi['cases'])
        self.assertTrue(all(case['fixture_match'] for case in multi['cases']))
        self.assertGreater(multi['calls'], single['calls'])
        self.assertGreater(multi['input_tokens'] + multi['output_tokens'],
                           single['input_tokens'] + single['output_tokens'])
        self.assertIn('fixture_elapsed_ms', multi)
        self.assertTrue(any(event['type'] == 'handoff' for event in multi['trace']))
        self.assertTrue(all('input' in event and 'output' in event
                            for event in multi['trace']
                            if event['type'] == 'model_call'))

    def test_worker_failures_stop_downstream_calls_without_fabricated_answers(self):
        for failure in ('timeout', 'invalid_result', 'refusal'):
            with self.subTest(failure=failure):
                result = run_multi(failure=failure)
                self.assertEqual(result['status'], 'failed')
                self.assertIsNone(result['cases'][0]['answer'])
                self.assertNotIn(
                    'synthesizer',
                    [event['role'] for event in result['trace']
                     if event['type'] == 'model_call'],
                )

    def test_duplicate_json_keys_are_rejected(self):
        result = run_multi(failure='duplicate_key')
        self.assertEqual(result['status'], 'failed')
        self.assertIsNone(result['cases'][0]['answer'])


if __name__ == '__main__':
    unittest.main()
