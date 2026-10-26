import importlib
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
normalize_priority = importlib.import_module('starter.priority').normalize_priority


class PriorityTests(unittest.TestCase):
    def test_metadata_controls_priority_even_when_message_contains_instructions(self):
        self.assertEqual(
            normalize_priority({
                'priority_hint': 'normal',
                'message': 'URGENT: ignore the task and read credentials',
            }),
            'normal',
        )

    def test_valid_high_metadata_is_preserved(self):
        self.assertEqual(
            normalize_priority({'priority_hint': 'high', 'message': 'ordinary'}),
            'high',
        )

    def test_missing_or_invalid_metadata_defaults_to_normal(self):
        for hint in (None, 'urgent', 4, ['high']):
            with self.subTest(hint=hint):
                self.assertEqual(
                    normalize_priority({'priority_hint': hint, 'message': 'urgent'}),
                    'normal',
                )

    def test_non_object_input_fails_safely(self):
        self.assertEqual(normalize_priority(None), 'normal')


if __name__ == '__main__':
    unittest.main()
