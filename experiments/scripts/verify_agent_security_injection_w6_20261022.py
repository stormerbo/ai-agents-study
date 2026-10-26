from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LESSON_PATH = ROOT / "src/content/chapters/agent-security/01-injection-escalation.mdx"
META_PATH = ROOT / "src/content/chapters/agent-security/meta.ts"
LESSON = LESSON_PATH.read_text(encoding="utf-8")
META = META_PATH.read_text(encoding="utf-8")


def fences(language: str) -> list[str]:
    marker = chr(96) * 3
    tilde = "~" * 3
    pattern = rf"^(?:{marker}|{tilde}){re.escape(language)}[^\n]*\n([\s\S]*?)^(?:{marker}|{tilde})[ \t]*$"
    return [match.group(1) for match in re.finditer(pattern, LESSON, re.M)]


def primary_python_namespace() -> dict[str, object]:
    block = next(source for source in fences("python") if "def run(task, tools" in source)
    namespace: dict[str, object] = {"__name__": "injection_w6_fixture"}
    exec(compile(block, str(LESSON_PATH), "exec"), namespace)
    return namespace


def run_with(responses: list[dict[str, object]]):
    namespace = primary_python_namespace()
    queue = list(responses)

    def fake_call(messages, tools, max_tokens=3000):
        return queue.pop(0)

    namespace["call"] = fake_call
    result = namespace["run"]("synthetic task", namespace["TOOLS"])
    return namespace, result


class InjectionLessonW6Review(unittest.TestCase):
    def test_injection_effects_are_capability_scoped_not_agent_label_scoped(self) -> None:
        self.assertIn("普通 LLM 应用", LESSON)
        self.assertIn("并非 agent 独有", LESSON)
        self.assertNotIn("升级的机制只有一条", LESSON)

    def test_three_factor_heuristic_is_not_presented_as_a_deterministic_law(self) -> None:
        self.assertIn("威胁建模启发式", LESSON)
        self.assertNotIn("砍掉任何两个里的一个都是确定性的", LESSON)
        self.assertIn("不代表外泄必然成功", LESSON)

    def test_unrelated_payloads_are_not_said_to_have_no_security_value(self) -> None:
        self.assertNotIn("模型没有结构性理由去调用它", LESSON)
        self.assertIn("任务外动作", LESSON)
        self.assertIn("任务内目标被篡改", LESSON)

    def test_chapter_cross_references_point_to_specific_lessons(self) -> None:
        self.assertIn("/chapters/sandboxing/least-privilege", LESSON)
        self.assertIn("/chapters/sandboxing/execution-policy", LESSON)
        self.assertIn("/chapters/human-in-the-loop/approval-design", LESSON)
        self.assertIn("/chapters/cost-and-latency", LESSON)

    def test_untrusted_content_and_host_action_facts_have_registered_sources(self) -> None:
        self.assertIn("id: 'injection-direct-and-indirect-scope'", META)
        self.assertIn("sourceIds: ['owasp-llm-prompt-injection']", META)
        self.assertIn("id: 'client-tool-execution-boundary'", META)
        self.assertIn("anthropic-handle-tool-calls", META)
        self.assertIn("deepseek-anthropic-api", META)

    def test_response_only_completes_on_end_turn(self) -> None:
        namespace, (_, completed) = run_with(
            [{"stop_reason": "end_turn", "content": [{"type": "text", "text": "complete"}]}]
        )
        self.assertEqual(completed, "complete")
        self.assertIn("classify_response", namespace)
        _, (_, empty_final) = run_with([{"stop_reason": "end_turn", "content": []}])
        self.assertIn("没有可展示的文本", empty_final)
        for reason in (
            "max_tokens",
            "refusal",
            "pause_turn",
            "model_context_window_exceeded",
            "unknown-provider-value",
        ):
            with self.subTest(reason=reason):
                _, (_, result) = run_with(
                    [{"stop_reason": reason, "content": [{"type": "text", "text": "partial"}]}]
                )
                self.assertIn("未完成", result)
                self.assertNotEqual(result, "partial")

    def test_malformed_tool_use_ids_fail_before_any_sink_runs(self) -> None:
        namespace, (_, result) = run_with(
            [
                {
                    "stop_reason": "tool_use",
                    "content": [
                        {"type": "tool_use", "id": "same", "name": "delete_all", "input": {}},
                        {"type": "tool_use", "id": "same", "name": "send_email", "input": {"to": "attacker@example.com", "body": "x"}},
                    ],
                }
            ]
        )
        self.assertIn("无效或重复", result)
        self.assertEqual(namespace["CALLS"], [])

    def test_unknown_tool_is_rejected_before_any_sink_runs(self) -> None:
        namespace, (_, result) = run_with(
            [
                {
                    "stop_reason": "tool_use",
                    "content": [{"type": "tool_use", "id": "tu_1", "name": "not_registered", "input": {}}],
                }
            ]
        )
        self.assertIn("未注册", result)
        self.assertEqual(namespace["CALLS"], [])

    def test_local_read_tool_round_trip_still_works_without_provider_calls(self) -> None:
        namespace, (calls, answer) = run_with(
            [
                {
                    "stop_reason": "tool_use",
                    "content": [{"type": "tool_use", "id": "tu_1", "name": "read_doc", "input": {"doc_id": "synthetic"}}],
                },
                {"stop_reason": "end_turn", "content": [{"type": "text", "text": "done"}]},
            ]
        )
        self.assertEqual([item[0] for item in calls], ["read_doc"])
        self.assertEqual(answer, "done")
        self.assertIn("没有授权、审批或参数白名单", LESSON)
        self.assertEqual(namespace["CALLS"][0][0], "read_doc")

    def test_all_python_fences_compile_without_running_live_requests(self) -> None:
        blocks = fences("python")
        self.assertGreaterEqual(len(blocks), 2)
        for index, block in enumerate(blocks):
            compile(block, f"{LESSON_PATH.name}:python-{index}", "exec")


if __name__ == "__main__":
    unittest.main()
