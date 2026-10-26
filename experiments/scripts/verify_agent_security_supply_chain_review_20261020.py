from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/agent-security/03-supply-chain.mdx"
TEXT = LESSON.read_text(encoding="utf-8")


def python_fences() -> list[str]:
    marker = chr(96) * 3
    pattern = rf"^{marker}python[^\n]*\n([\s\S]*?)^{marker}[ \t]*$"
    return [match.group(1) for match in re.finditer(pattern, TEXT, re.M)]


class SupplyChainReview(unittest.TestCase):
    def test_historical_provider_claim_is_explicitly_unverified(self) -> None:
        self.assertIn("历史实验", TEXT)
        self.assertIn("不能将其当成已核实实验结果、模型能力结论或防护效果", TEXT)
        self.assertIn("本轮只做了静态编译和本地合成响应检查，没有调用模型", TEXT)
        self.assertIn("历史汇总缺少可复算逐次记录，见 ERR-052", TEXT)

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

    def test_synthetic_tool_request_reaches_fake_sink_without_policy_gate(self) -> None:
        namespace: dict[str, object] = {"__name__": "supply_chain_review"}
        exec(compile(python_fences()[0], str(LESSON), "exec"), namespace)
        responses = iter(
            [
                {
                    "stop_reason": "tool_use",
                    "content": [
                        {
                            "type": "tool_use",
                            "id": "synthetic-delete-1",
                            "name": "delete_all",
                            "input": {},
                        }
                    ],
                },
                {"stop_reason": "end_turn", "content": [{"type": "text", "text": "synthetic"}]},
            ]
        )
        namespace["call"] = lambda _messages, _tools: next(responses)
        run = namespace["run"]
        build_tools = namespace["build_tools"]
        calls, output = run("synthetic task", build_tools())  # type: ignore[operator]
        self.assertEqual(calls, ["delete_all"])
        self.assertEqual(output, "synthetic")
        self.assertIn("没有授权、审批、参数 allowlist、租户检查或 sandbox", TEXT)


if __name__ == "__main__":
    unittest.main()
