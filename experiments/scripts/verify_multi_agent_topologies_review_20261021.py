"""Offline boundary checks for the multi-agent topologies lesson; no provider calls."""
from __future__ import annotations

import json
import os
import re
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/multi-agent/01-topologies.mdx"
SOURCE = LESSON.read_text(encoding="utf-8")
PYTHON_FENCES = re.findall(r"```python\s*\n(.*?)\n```", SOURCE, re.S)
ISOLATION_LESSON = ROOT / "src/content/chapters/multi-agent/03-isolation-is-the-point.mdx"
ISOLATION_SOURCE = ISOLATION_LESSON.read_text(encoding="utf-8")
ISOLATION_FENCES = re.findall(r"```python\s*\n(.*?)\n```", ISOLATION_SOURCE, re.S)


def load_example():
    if len(PYTHON_FENCES) != 1:
        raise AssertionError(f"expected one Python fence, found {len(PYTHON_FENCES)}")
    code = PYTHON_FENCES[0]
    compiled = compile(code, str(LESSON), "exec")
    namespace = {"__name__": "topologies_lesson_example"}
    exec(compiled, namespace)
    return code, namespace


class FakeResponse:
    def __init__(self, payload):
        self.payload = json.dumps(payload).encode()

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return self.payload


def response(input_tokens=10, output_tokens=4, stop_reason="end_turn", text="ok"):
    return {"usage": {"input_tokens": input_tokens, "output_tokens": output_tokens},
            "stop_reason": stop_reason,
            "content": [{"type": "text", "text": text}]}


class TopologiesReview(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.code, cls.example = load_example()
        os.environ.update({"VERIFY_MODEL": "offline-fixture", "ANTHROPIC_BASE_URL": "https://invalid.local",
                           "ANTHROPIC_AUTH_TOKEN": "fixture-only"})

    def test_fence_compiles_and_no_semantic_keyword_scorer(self):
        self.assertIn("不能判断约束是否保留", self.code)
        self.assertNotIn('"生产库" in', self.code)
        self.assertIn("不能据此拟合成本倍率", self.code)

    def test_python_fence_lines_fit_readable_page_width(self):
        self.assertLessEqual(max(map(len, self.code.splitlines())), 88)

    def test_multi_agent_aggregates_all_four_serial_calls(self):
        calls = []

        def fake_urlopen(req, timeout):
            calls.append((req, timeout))
            return FakeResponse(response(input_tokens=10 + len(calls), output_tokens=2))

        os.environ.update({"VERIFY_MODEL": "offline-fixture", "ANTHROPIC_BASE_URL": "https://invalid.local",
                           "ANTHROPIC_AUTH_TOKEN": "fixture-only"})
        with patch("urllib.request.urlopen", fake_urlopen):
            text, usage, worker_count = self.example["arm_multi"]("fixture background")
        self.assertEqual(len(calls), 4)
        self.assertEqual(worker_count, 3)
        self.assertEqual(usage, {"input_tokens": 50, "output_tokens": 8})
        self.assertTrue(text)

    def test_single_agent_reports_separate_usage_fields(self):
        with patch("urllib.request.urlopen", lambda *_a, **_k: FakeResponse(response(23, 7))):
            text, usage = self.example["arm_single"]("fixture")
        self.assertEqual(usage, {"input_tokens": 23, "output_tokens": 7})
        self.assertTrue(text)

    def test_missing_usage_fails_closed(self):
        with patch("urllib.request.urlopen", lambda *_a, **_k: FakeResponse({"content": [{"type": "text", "text": "ok"}], "stop_reason": "end_turn"})):
            with self.assertRaisesRegex(RuntimeError, "缺少 usage"):
                self.example["call"]([], "fixture")

    def test_invalid_usage_fails_closed(self):
        with patch("urllib.request.urlopen", lambda *_a, **_k: FakeResponse(response(input_tokens=True))):
            with self.assertRaisesRegex(RuntimeError, "usage.input_tokens"):
                self.example["call"]([], "fixture")

    def test_non_end_turn_fails_closed(self):
        with patch("urllib.request.urlopen", lambda *_a, **_k: FakeResponse(response(stop_reason="max_tokens"))):
            with self.assertRaisesRegex(RuntimeError, "未以 end_turn"):
                self.example["call"]([], "fixture")

    def test_empty_text_fails_closed(self):
        with patch("urllib.request.urlopen", lambda *_a, **_k: FakeResponse(response(text="  "))):
            with self.assertRaisesRegex(RuntimeError, "没有可评分的文本"):
                self.example["call"]([], "fixture")

    def test_claim_scopes_avoid_prevalence_and_guarantees(self):
        for phrase in ("不根据案例文章或少数实现推断哪种拓扑在行业里占多数",
                       "通信边不等于模型 API 调用数",
                       "不保证等于 max", "不能单独保证主管识别所有冲突"):
            self.assertIn(phrase, SOURCE)
        self.assertIn("有两组不能混为一谈", SOURCE)

    def test_cross_lesson_experiment_summaries_are_separated(self):
        prompt = (ROOT / "src/content/chapters/prompt-engineering/05-reliability.mdx").read_text(encoding="utf-8")
        reflection = (ROOT / "src/content/chapters/agent-paradigms/04-reflection.mdx").read_text(encoding="utf-8")
        reflection_meta = (ROOT / "src/content/chapters/agent-paradigms/meta.ts").read_text(encoding="utf-8")
        self.assertIn("10 道算术/计数题", prompt)
        self.assertIn("**1/6 个不同答案**", prompt)
        self.assertNotIn("C[\"本次唯一答案样本<br/>5 次采样无分歧\"]", prompt)
        self.assertIn("温度探测的另一组历史记录", prompt)
        self.assertNotIn("失效机制是同一个", reflection)
        self.assertIn("第 2 章 self-consistency 的摘要属于另一组采样实验", reflection_meta)
        self.assertIn("不可据此认定两者有相同机制", reflection_meta)


def load_isolation_example():
    if len(ISOLATION_FENCES) != 1:
        raise AssertionError(f"expected one Python fence, found {len(ISOLATION_FENCES)}")
    code = ISOLATION_FENCES[0]
    compiled = compile(code, str(ISOLATION_LESSON), "exec")
    namespace = {"__name__": "isolation_lesson_example"}
    exec(compiled, namespace)
    return code, namespace


class IsolationReview(unittest.TestCase):
    def test_reference_card_does_not_turn_browsecomp_variance_into_causation(self):
        resources = (ROOT / "src/content/curriculum/resources.ts").read_text(encoding="utf-8")
        entry = resources.split("'anthropic-multi-agent-research': {", 1)[1].split("\n  },", 1)[0]
        self.assertIn("不是上下文隔离的因果消融", entry)
        self.assertNotIn("会改变判断的因果", entry)
        self.assertNotIn("买到的主要是", entry)

    @classmethod
    def setUpClass(cls):
        cls.code, cls.example = load_isolation_example()
        os.environ.update({"VERIFY_MODEL": "offline-fixture", "ANTHROPIC_BASE_URL": "https://invalid.local",
                           "ANTHROPIC_AUTH_TOKEN": "fixture-only"})

    def test_fence_compiles_and_scope_is_limited(self):
        self.assertIn("不评分质量或硬约束语义", self.code)
        self.assertIn("三个 worker 与一个 supervisor 顺序调用", self.code)
        self.assertNotIn('"生产库" in', self.code)
        self.assertNotIn("概率随压缩比上升", ISOLATION_SOURCE)
        self.assertNotIn("总 token 更高", ISOLATION_SOURCE)
        self.assertIn("不是上下文隔离的因果消融", ISOLATION_SOURCE)
        self.assertIn("不能独立确认各数值分别对应哪条路线", ISOLATION_SOURCE)

    def test_isolation_multi_aggregates_all_four_serial_calls(self):
        calls = []

        def fake_urlopen(req, timeout):
            calls.append((req, timeout))
            return FakeResponse(response(input_tokens=10 + len(calls), output_tokens=2))

        with patch("urllib.request.urlopen", fake_urlopen):
            text, usage = self.example["arm_multi"]("fixture background")
        self.assertEqual(len(calls), 4)
        self.assertEqual(usage, {"input_tokens": 50, "output_tokens": 8})
        self.assertTrue(text)

    def test_isolation_single_usage(self):
        with patch("urllib.request.urlopen", lambda *_a, **_k: FakeResponse(response(23, 7))):
            text, usage = self.example["arm_single"]("fixture")
        self.assertEqual(usage, {"input_tokens": 23, "output_tokens": 7})
        self.assertTrue(text)

    def test_isolation_missing_usage_fails_closed(self):
        payload = {"content": [{"type": "text", "text": "ok"}], "stop_reason": "end_turn"}
        with patch("urllib.request.urlopen", lambda *_a, **_k: FakeResponse(payload)):
            with self.assertRaisesRegex(RuntimeError, "缺少 usage"):
                self.example["call"]([], "fixture")

    def test_isolation_non_end_turn_fails_closed(self):
        with patch("urllib.request.urlopen", lambda *_a, **_k: FakeResponse(response(stop_reason="max_tokens"))):
            with self.assertRaisesRegex(RuntimeError, "未以 end_turn"):
                self.example["call"]([], "fixture")

    def test_isolation_empty_text_fails_closed(self):
        with patch("urllib.request.urlopen", lambda *_a, **_k: FakeResponse(response(text="  "))):
            with self.assertRaisesRegex(RuntimeError, "没有可用文本输出"):
                self.example["call"]([], "fixture")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ("--isolation-only", "--topologies-only"):
        case = IsolationReview if sys.argv[1] == "--isolation-only" else TopologiesReview
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(case)
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        if not result.wasSuccessful():
            raise SystemExit(1)
    else:
        result = unittest.main(verbosity=2, exit=False)
        if not result.result.wasSuccessful():
            raise SystemExit(1)
