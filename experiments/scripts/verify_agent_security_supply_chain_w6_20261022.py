from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/agent-security/03-supply-chain.mdx"
TEXT = LESSON.read_text(encoding="utf-8")
META = ROOT / "src/content/chapters/agent-security/meta.ts"
METADATA = META.read_text(encoding="utf-8")


def python_fences() -> list[str]:
    marker = chr(96) * 3
    pattern = rf"^{marker}python[^\n]*\n([\s\S]*?)^{marker}[ \t]*$"
    return [match.group(1) for match in re.finditer(pattern, TEXT, re.M)]


class SupplyChainReview(unittest.TestCase):
    def test_historical_provider_claim_is_explicitly_unverified(self) -> None:
        self.assertIn("历史实验", TEXT)
        self.assertIn("不能将其当成已核实实验结果、模型能力结论或防护效果", TEXT)
        self.assertIn("下面的代码是新写的离线宿主控制演示，不重放历史提示或模型", TEXT)
        self.assertIn("历史汇总缺少可复算逐次记录，见 ERR-052", TEXT)
        self.assertIn("历史结果仍未复现", TEXT)

    def test_current_mcp_metadata_and_trust_boundaries_are_scoped(self) -> None:
        for phrase in (
            "协议不会默认把整段对话交给 server",
            "不能说改了描述就必然改变模型行为",
            "可选输出 schema 与 annotations",
            "不能证明代码、真实副作用、权限或参数处理方式",
            "快照不会 pin 远程实现",
        ):
            self.assertIn(phrase, TEXT)
        self.assertNotIn("你能审查的表面只有这三样", TEXT)
        self.assertNotIn("远程 server 拿到你授予的凭据", TEXT)

    def test_all_python_fences_compile_without_running_live_api(self) -> None:
        fences = python_fences()
        self.assertEqual(len(fences), 1)
        for index, code in enumerate(fences):
            compile(code, f"{LESSON}:python-fence-{index}", "exec")

    def test_w6_synthetic_dangerous_tool_proposal_is_denied(self) -> None:
        namespace: dict[str, object] = {"__name__": "supply_chain_review"}
        exec(compile(python_fences()[0], str(LESSON), "exec"), namespace)
        response = {
            "stop_reason": "tool_use",
            "content": [{"type": "tool_use", "id": "synthetic-delete-1", "name": "delete_all", "input": {}}],
        }
        responses = [response, {"stop_reason": "end_turn", "content": [{"type": "text", "text": "synthetic"}]}]
        run = namespace["run"]
        events, calls, output = run("synthetic task", "synthetic document", namespace["TOOLS"], namespace["FakeClient"](responses))
        self.assertEqual(events, ["拒绝 delete_all：不在本任务 allowlist"])
        self.assertEqual(calls, [])
        self.assertEqual(namespace["CALLS"], [])
        self.assertEqual(output, "synthetic")


    def test_offline_demo_output_matches_and_has_no_provider_path(self) -> None:
        import io
        from contextlib import redirect_stdout
        source = python_fences()[0]
        self.assertNotIn("urllib.request", source)
        self.assertNotIn("ANTHROPIC_BASE_URL", source)
        namespace: dict[str, object] = {"__name__": "__main__"}
        output = io.StringIO()
        with redirect_stdout(output):
            exec(compile(source, str(LESSON), "exec"), namespace)
        expected = (
            "畸形批次：3/3 在任何 sink 调用前拒绝\n"
            "历史 provider 观察：未重跑；以下 FakeClient 响应不代表模型行为\n"
            "A 干净文档（合成正常提案）：允许 read_doc；执行=['read_doc']；输出=收入为 1.2 亿元；应收账款周转天数上升。\n"
            "B 文档含指令（合成危险提案）：允许 read_doc / 拒绝 delete_all：不在本任务 allowlist / 拒绝 send_email：不在本任务 allowlist；执行=['read_doc']；输出=危险提案已被宿主拒绝。\n"
            "C 工具描述含指令（合成危险提案）：拒绝 delete_all：不在本任务 allowlist；执行=[]；输出=危险提案已被宿主拒绝。\n"
        )
        self.assertEqual(output.getvalue(), expected)

    def test_mcp_metadata_claim_has_a_documented_source_binding(self) -> None:
        self.assertIn("id: 'mcp-tool-metadata-not-proof-of-implementation'", METADATA)
        self.assertIn("basis: 'documented'", METADATA)
        self.assertIn("sourceIds: ['mcp-tools-2026']", METADATA)

    def test_cross_references_point_to_current_lesson_routes(self) -> None:
        self.assertNotIn("第 16 节", TEXT)
        self.assertNotRegex(TEXT, r"\\bL\\d+\\b")
        self.assertNotIn("三个月前的 review 已过期", TEXT)
        self.assertIn("/chapters/agent-security/tools-as-untrusted-input", TEXT)
        self.assertIn("/chapters/sandboxing/secrets", TEXT)

if __name__ == "__main__":
    unittest.main()
