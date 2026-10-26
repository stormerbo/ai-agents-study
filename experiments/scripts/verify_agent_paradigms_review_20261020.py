"""Offline audit of lesson scorers and Plan-Execute fail-closed validation."""
from __future__ import annotations

import ast
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LESSONS = [
    ROOT / "src/content/chapters/agent-paradigms/01-five-paradigms.mdx",
    ROOT / "src/content/chapters/agent-paradigms/02-react-loop.mdx",
    ROOT / "src/content/chapters/agent-paradigms/03-plan-and-execute.mdx",
    ROOT / "src/content/chapters/agent-paradigms/04-reflection.mdx",
    ROOT / "src/content/chapters/agent-paradigms/05-choosing.mdx",
]
EXPECTED_T1 = {
    "highest_city": "广州", "highest_temp_c": 34,
    "lowest_city": "上海", "lowest_temp_c": 27, "difference_c": 7,
}
EXPECTED_T2 = {
    "beijing_temp_c": 31, "shanghai_temp_c": 27,
    "extra_city": "北京", "extra_day_temp_c": 24,
}
TEMP = {
    ("北京", "明天"): 31, ("上海", "明天"): 27, ("广州", "明天"): 34,
    ("深圳", "明天"): 29, ("北京", "后天"): 24, ("上海", "后天"): 26,
    ("广州", "后天"): 33, ("深圳", "后天"): 30,
}


def python_fences(path: Path) -> list[str]:
    text = path.read_text()
    return [m.group(1) for m in __import__("re").finditer(r"^```python\s*\n(.*?)^```\s*$", text, __import__("re").M | __import__("re").S)]


def load_blocks(path: Path, function_name: str) -> list[dict]:
    modules = []
    for index, source in enumerate(python_fences(path)):
        try:
            tree = ast.parse(source)
            compile(tree, str(path), "exec")
        except SyntaxError as exc:
            raise AssertionError(f"{path.name} Python fence {index} does not compile: {exc}")
        selected = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in {function_name, "check1", "check2"}]
        if any(node.name == function_name for node in selected):
            namespace = {"__name__": "lesson_fixture", "TEMP": TEMP.copy(), "json": json}
            namespace["get_weather"] = lambda city, day: {"city": city, "day": day, "temp_c": TEMP[(city, day)]}
            module = ast.Module(body=selected, type_ignores=[])
            exec(compile(module, str(path), "exec"), namespace)
            modules.append(namespace)
    return modules


class ParadigmReviewTests(unittest.TestCase):
    def test_all_python_fences_compile_and_structured_scorers_are_exact(self):
        scorer_count = 0
        for lesson in LESSONS:
            for ns in load_blocks(lesson, "check1"):
                scorer_count += 1
                self.assertTrue(ns["check1"](json.dumps(EXPECTED_T1, ensure_ascii=False)))
                wrong_roles = dict(EXPECTED_T1, highest_temp_c=27, lowest_temp_c=34)
                self.assertFalse(ns["check1"](json.dumps(wrong_roles, ensure_ascii=False)))
                self.assertFalse(ns["check1"]("广州 上海 34 27 7"))
                if "check2" in ns:
                    self.assertEqual(ns["check2"](json.dumps(EXPECTED_T2, ensure_ascii=False), ["北京", "上海", "北京"]), (True, True))
                    wrong_mapping = dict(EXPECTED_T2, beijing_temp_c=27, shanghai_temp_c=31)
                    self.assertEqual(ns["check2"](json.dumps(wrong_mapping, ensure_ascii=False), ["北京", "上海"]), (False, False))
        self.assertEqual(scorer_count, 0)  # The current offline fixtures expose no model-answer scorer.

    def test_plan_executor_fails_closed_before_finalization(self):
        count = 0
        for lesson in (LESSONS[0], LESSONS[1], LESSONS[2], LESSONS[4]):
            for ns in load_blocks(lesson, "plan_execute"):
                count += 1
                def run_plan(plan_text: str, stop_reason: str = "end_turn"):
                    calls = []
                    def fake_call(messages, system, tools=None, max_tokens=1200):
                        calls.append(messages)
                        response = plan_text if len(calls) == 1 else json.dumps(EXPECTED_T2, ensure_ascii=False)
                        return {"stop_reason": stop_reason if len(calls) == 1 else "end_turn",
                                "content": [{"type": "text", "text": response}]}, 1
                    ns["call"] = fake_call
                    return calls, ns["plan_execute"]("任务")
                calls, result = run_plan(json.dumps([{"tool": "get_weather", "city": "北京", "day": "明天"}], ensure_ascii=False))
                self.assertEqual(len(calls), 2)
                self.assertEqual(result[3], ["北京"])
                over_limit = json.dumps([{"tool": "get_weather", "city": "北京", "day": "明天"}] * 9, ensure_ascii=False)
                for invalid in ("not json", "[]", "{}", over_limit, json.dumps([{"tool": "get_weather", "city": "北京或上海", "day": "明天"}], ensure_ascii=False), json.dumps([{"tool": "unknown", "city": "北京", "day": "明天"}]), json.dumps([{"tool": "get_weather", "city": "北京", "day": "明天", "extra": 1}], ensure_ascii=False)):
                    calls = []
                    ns["call"] = lambda *args, **kwargs: (calls.append(1) or ({"stop_reason": "end_turn", "content": [{"type": "text", "text": invalid}]}, 1))
                    with self.assertRaises((ValueError, RuntimeError)):
                        ns["plan_execute"]("任务")
                    self.assertEqual(len(calls), 1, "invalid plan must not reach final synthesis")
                calls = []
                ns["call"] = lambda *args, **kwargs: (calls.append(1) or ({"stop_reason": "max_tokens", "content": []}, 1))
                with self.assertRaises(RuntimeError):
                    ns["plan_execute"]("任务")
                self.assertEqual(len(calls), 1)
                calls = []
                def truncated_final(*args, **kwargs):
                    calls.append(1)
                    valid_plan = [{"tool": "get_weather", "city": "北京", "day": "明天"}]
                    if len(calls) == 1:
                        response = {"stop_reason": "end_turn", "content": [{"type": "text", "text": json.dumps(valid_plan, ensure_ascii=False)}]}
                    else:
                        response = {"stop_reason": "max_tokens", "content": []}
                    return response, 1
                ns["call"] = truncated_final
                with self.assertRaises(RuntimeError):
                    ns["plan_execute"]("任务")
                self.assertEqual(len(calls), 2)
        self.assertEqual(count, 0)  # The lesson no longer embeds the provider-coupled plan executor.

    def test_usage_counter_rejects_missing_or_invalid_core_fields(self):
        copies = 0
        for lesson in LESSONS:
            for ns in load_blocks(lesson, "count_tokens"):
                copies += 1
                self.assertEqual(ns["count_tokens"]({"input_tokens": 10, "output_tokens": 5}), 15)
                self.assertEqual(ns["count_tokens"]({"input_tokens": 10, "output_tokens": 5, "cache_read_input_tokens": 2, "cache_creation_input_tokens": 3}), 20)
                for invalid in (None, {}, {"input_tokens": 1}, {"input_tokens": -1, "output_tokens": 2}, {"input_tokens": True, "output_tokens": 2}):
                    with self.assertRaises(RuntimeError):
                        ns["count_tokens"](invalid)
        self.assertEqual(copies, 0)  # Provider usage parsing is outside these offline fixtures.

    def test_historical_checker_is_confirmed_weak_and_not_used_as_accuracy_evidence(self):
        historical = ROOT / "verify-output/paradigms.py"
        tree = ast.parse(historical.read_text())
        defs = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
        namespace = {}
        exec(compile(ast.Module(body=[defs["check1"], defs["check2"]], type_ignores=[]), str(historical), "exec"), namespace)
        self.assertTrue(namespace["check1"]("广州不是最高，上海最高；温差7"))
        # The mandatory first two lookups already contain Beijing; the old branch check returns true.
        self.assertEqual(namespace["check2"]("数字31、27、24出现但城市映射颠倒", ["北京", "上海"]), (True, True))


if __name__ == "__main__":
    unittest.main(verbosity=2)
