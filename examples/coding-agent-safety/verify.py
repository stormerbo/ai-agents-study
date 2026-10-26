"""Run acceptance tests against the published reference implementation."""

import importlib
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.modules['starter.priority'] = importlib.import_module('reference.priority')

suite = unittest.defaultTestLoader.discover(
    str(ROOT / 'tests'), pattern='test_*.py'
)
result = unittest.TextTestRunner(verbosity=2).run(suite)
raise SystemExit(0 if result.wasSuccessful() else 1)
