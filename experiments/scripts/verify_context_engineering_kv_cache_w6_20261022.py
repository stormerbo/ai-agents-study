from __future__ import annotations

import contextlib
import hashlib
import io
import re
import types
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/context-engineering/07-kv-cache.mdx"
SOURCE = LESSON.read_text(encoding="utf-8")
FENCES = re.findall(r"```python\s*\n(.*?)```", SOURCE, re.DOTALL)
PROGRAM = next(fence for fence in FENCES if "def request_fingerprint" in fence)
NAMESPACE: dict[str, object] = {"__name__": "kv_cache_lesson"}
exec(compile(PROGRAM, str(LESSON), "exec"), NAMESPACE)


class KvCacheW6(unittest.TestCase):
    def test_historical_numbers_are_scoped_as_unverified_summary(self):
        self.assertIn("下表只转录旧摘要", SOURCE)
        self.assertIn("`cache_creation=0`", SOURCE)
        self.assertIn("不能据此确认发生了真实缓存命中", SOURCE)
        self.assertIn("不能证明此前缓存被清除", SOURCE)
        self.assertNotIn("一组实测数据", SOURCE)
        self.assertIn("### 一个历史排查假设", SOURCE)
        self.assertIn("无法核实该问题是否实际发生", SOURCE)
        self.assertNotIn("缓存命中率接近零", SOURCE)
        self.assertIn("不能确认这是一次真实未命中", SOURCE)
        self.assertNotIn("首次，冷启动", SOURCE)
        self.assertNotIn("这组请求中观察到了自动命中", SOURCE)

    def test_missing_historical_artifacts_are_in_data_ledger(self):
        data = (ROOT / "docs/DATA.md").read_text(encoding="utf-8")
        self.assertIn("KV cache 课程的历史缓存摘要", data)
        self.assertIn("(1205,0,0)", data)
        self.assertIn("原始 prompt、计数结果、逐次请求/响应、usage 对象、模型快照均未归档", data)
        self.assertIn("工具定义顺序导致缓存未命中的历史解释", data)
        self.assertIn("它只能作为排查假设", data)
        self.assertIn("见 ERR-237", data)

    def test_documented_checkpoint_links_to_the_exact_responses_guide(self):
        meta = (ROOT / "src/content/chapters/context-engineering/meta.ts").read_text(encoding="utf-8")
        resources = (ROOT / "src/content/curriculum/resources.ts").read_text(encoding="utf-8")
        self.assertIn("sourceIds: ['claude-prompt-caching', 'deepseek-context-caching', 'deepseek-responses-guide']", meta)
        self.assertIn("'deepseek-responses-guide':", resources)
        self.assertIn("https://api-docs.deepseek.com/guides/responses_api/", resources)
        self.assertIn("verifiedAt: '2026-10-22'", resources[resources.index("'deepseek-responses-guide':"):resources.index("'deepseek-tool-calls':")])

    def test_request_fingerprint_uses_unambiguous_complete_payload(self):
        fingerprint = NAMESPACE["request_fingerprint"]
        first = {"system": 'Policy\n{"content":"ask"}'}
        second = {"system": "Policy", "messages": [{"content": "ask"}]}
        self.assertNotEqual(fingerprint(first), fingerprint(second))

    def test_request_fingerprint_is_stable_but_detects_field_and_array_changes(self):
        fingerprint = NAMESPACE["request_fingerprint"]
        first = {"model": "model-a", "tools": [{"name": "one"}, {"name": "two"}]}
        reordered_keys = {"tools": [{"name": "one"}, {"name": "two"}], "model": "model-a"}
        reordered_tools = {"model": "model-a", "tools": [{"name": "two"}, {"name": "one"}]}
        changed_model = {"model": "model-b", "tools": [{"name": "one"}, {"name": "two"}]}
        self.assertEqual(fingerprint(first), fingerprint(reordered_keys))
        self.assertNotEqual(fingerprint(first), fingerprint(reordered_tools))
        self.assertNotEqual(fingerprint(first), fingerprint(changed_model))

    def test_request_fingerprint_does_not_return_request_text(self):
        fingerprint = NAMESPACE["request_fingerprint"]({"system": "private marker"})
        self.assertRegex(fingerprint, r"^[0-9a-f]{64}$")
        self.assertEqual(fingerprint, hashlib.sha256(b'{"system":"private marker"}').hexdigest())

    def test_hit_rate_uses_provider_reported_input_and_cache_counts(self):
        usage = types.SimpleNamespace(
            input_tokens=181,
            cache_read_input_tokens=1024,
            cache_creation_input_tokens=0,
        )
        self.assertAlmostEqual(NAMESPACE["hit_rate"](usage), 1024 / 1205)

    def test_hit_rate_rejects_usage_without_cache_fields(self):
        for usage in (
            types.SimpleNamespace(input_tokens=100),
            types.SimpleNamespace(input_tokens=100, cache_read_input_tokens=0),
        ):
            with self.subTest(usage=usage), self.assertRaises(ValueError):
                NAMESPACE["hit_rate"](usage)

    def test_hit_rate_rejects_missing_or_invalid_required_input_count(self):
        for usage in (
            types.SimpleNamespace(),
            types.SimpleNamespace(input_tokens=None),
            types.SimpleNamespace(input_tokens=True),
            types.SimpleNamespace(input_tokens=-1),
            types.SimpleNamespace(input_tokens=1.5),
        ):
            with self.subTest(usage=usage), self.assertRaises(ValueError):
                NAMESPACE["hit_rate"](usage)

    def test_cache_counts_reject_invalid_values(self):
        for usage in (
            types.SimpleNamespace(input_tokens=10, cache_read_input_tokens=-1, cache_creation_input_tokens=0),
            types.SimpleNamespace(input_tokens=10, cache_read_input_tokens=0, cache_creation_input_tokens=True),
            types.SimpleNamespace(input_tokens=10, cache_read_input_tokens=1.5, cache_creation_input_tokens=0),
            types.SimpleNamespace(input_tokens=10, cache_read_input_tokens=None, cache_creation_input_tokens=0),
        ):
            with self.subTest(usage=usage), self.assertRaises(ValueError):
                NAMESPACE["hit_rate"](usage)

    def test_embedded_demo_matches_its_displayed_stdout(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            exec(compile(PROGRAM, str(LESSON), "exec"), {"__name__": "__main__"})
        expected = next(
            fence
            for fence in re.findall(r"```text\s*\n(.*?)```", SOURCE, re.DOTALL)
            if "cache hit rate" in fence
        )
        self.assertEqual(output.getvalue(), expected)


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(KvCacheW6)
    )
    print(
        f"providerCalls=0; externalNetworkCalls=0; tests={result.testsRun}; "
        f"failures={len(result.failures) + len(result.errors)}"
    )
    raise SystemExit(not result.wasSuccessful())
