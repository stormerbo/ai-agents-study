"""W6 whole-lesson checks for caching terminology and copyable-example limits."""
from __future__ import annotations

import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/cost-and-latency/03-caching.mdx"
META = ROOT / "src/content/chapters/cost-and-latency/meta.ts"
RESOURCES = ROOT / "src/content/curriculum/resources.ts"
OLD_REVIEW = ROOT / "experiments/scripts/verify_cost_caching_review_20261021.py"


class CachingBoundariesW6(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.body = LESSON.read_text(encoding="utf-8")
        cls.fences = re.findall(r"```python\n(.*?)\n```", cls.body, re.S)

    def test_ratio_is_not_labeled_as_a_provider_hit_rate(self):
        self.assertIn("候选可复用比例", self.body)
        self.assertIn("不是 cache hit 率或概率", self.body)
        self.assertNotIn("命中率    命中 token", self.body)
        self.assertNotIn("失效 token", self.body)

    def test_anthropic_request_placeholder_does_not_promise_a_cache_hit(self):
        self.assertIn("占位符不是实际可缓存内容", self.body)
        self.assertIn("当前模型和平台的最小缓存长度", self.body)
        self.assertIn("`cache_control` 只标记候选断点", self.body)

    def test_provider_sources_are_linked_and_claude_doc_was_rechecked(self):
        meta = META.read_text(encoding="utf-8")
        resources = RESOURCES.read_text(encoding="utf-8")
        for source_id in ("claude-prompt-caching", "deepseek-context-caching", "deepseek-anthropic-api", "openai-prompt-caching"):
            self.assertIn(f"'{source_id}'", meta)
            self.assertIn(f"id: '{source_id}'", resources)
        block = resources.split("'claude-prompt-caching': {", 1)[1].split("\n  },", 1)[0]
        self.assertIn("verifiedAt: '2026-10-22'", block)

    def test_python_demo_and_prior_lesson_audit_pass(self):
        self.assertEqual(len(self.fences), 1)
        compile(self.fences[0], str(LESSON), "exec")
        with tempfile.NamedTemporaryFile("w", suffix=".py", encoding="utf-8") as script:
            script.write(self.fences[0])
            script.flush()
            run = subprocess.run([sys.executable, script.name], capture_output=True, text=True, check=True)
        self.assertIn("候选前缀 token", run.stdout)
        self.assertNotIn("命中率", run.stdout)
        self.assertNotIn("失效 token", run.stdout)
        for fragment in ("第 2 段：工具定义", "9.8%", "差了 21.6 个百分点"):
            self.assertIn(fragment, run.stdout)
        prior = subprocess.run([sys.executable, str(OLD_REVIEW)], capture_output=True, text=True, check=True)
        self.assertIn("37/37 checks passed", prior.stdout)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(CachingBoundariesW6)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print(f"providerCalls=0; externalNetworkCalls=0; tests={result.testsRun}; failures={len(result.failures) + len(result.errors)}")
    raise SystemExit(not result.wasSuccessful())
