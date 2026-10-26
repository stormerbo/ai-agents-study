from __future__ import annotations

import hashlib
import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "examples/capstone-acceptance"))
from acceptance import REQUIRED_GATES, REQUIRED_KINDS  # noqa: E402

LESSON = ROOT / "src/content/chapters/capstone/06-acceptance.mdx"
TEXT = LESSON.read_text(encoding="utf-8")
OBSERVATION = json.loads(
    (ROOT / "experiments/results/exp-capstone-acceptance-w6-20261022/source-observation.json")
    .read_text(encoding="utf-8")
)


class CapstoneAcceptanceW6(unittest.TestCase):
    def test_gate_matrix_and_required_kinds_match_runtime(self) -> None:
        table = TEXT.split("| ID | 场景 | 通过条件 |", 1)[1].split("\n\n", 1)[0]
        gate_ids = re.findall(r"\| `([^`]+)` \|", table)
        self.assertEqual(len(gate_ids), 19)
        self.assertEqual(len(set(gate_ids)), len(gate_ids))
        self.assertEqual(set(gate_ids), REQUIRED_GATES)
        self.assertEqual(set(REQUIRED_KINDS), REQUIRED_GATES)

    def test_machine_decisions_and_gate_states_match_runtime_language(self) -> None:
        for value in (
            "ready-for-human-acceptance", "blocked", "incomplete",
            "insufficient-evidence", "invalid-report", "missing", "failed",
            "unverified", "passed", "not-evaluated",
        ):
            self.assertIn(f"`{value}`", TEXT)
        self.assertIn("authenticated: false", TEXT)
        self.assertIn("不会替团队批准上线", TEXT)

    def test_smoke_snapshot_and_terminal_state_are_not_conflated(self) -> None:
        report = OBSERVATION["sourceFiles"]["report.json"]
        terminal = OBSERVATION["sourceFiles"]["task-terminal-state.json"]
        registry = OBSERVATION["sourceFiles"]["evidence/acceptance-report.json"]
        self.assertEqual(report["taskStatusSnapshot"], "waiting_approval")
        self.assertEqual(terminal["taskStatus"], "failed")
        self.assertEqual(terminal["approvalStatus"], "cancelled")
        self.assertEqual(terminal["sendNoticeActionStatus"], "cancelled")
        self.assertEqual(registry["registryDecision"], "incomplete")
        self.assertEqual(registry["liveModelNormalEvidenceStatus"], "unverified")
        self.assertIn("task 为 `failed`、approval 与 `send_notice` action 为 `cancelled`", TEXT)
        self.assertNotIn("任务、审批和通知 action 被取消", TEXT)

    def test_no_sink_effect_claim_exceeds_available_artifacts(self) -> None:
        self.assertFalse(OBSERVATION["negativeEvidence"]["successfulSendNoticeToolResult"])
        self.assertFalse(OBSERVATION["negativeEvidence"]["deliveryReceipt"])
        self.assertFalse(OBSERVATION["negativeEvidence"]["independentSinkReceiveLog"])
        self.assertIn("不能据此断言 sink 从未收到请求", TEXT)
        self.assertIn("没有独立 sink 接收日志", TEXT)
        self.assertIn("最终输出没有生成", TEXT)
        self.assertIn("不证明 `live_model_normal` 成功", TEXT)

    def test_observation_hashes_match_ignored_inputs_when_present(self) -> None:
        base = ROOT / "verify-output/stage5-live/5f394310-aaae-4043-aac1-7cd9a3f42fd1"
        for relative, metadata in OBSERVATION["sourceFiles"].items():
            self.assertRegex(metadata["sha256"], r"^[0-9a-f]{64}$")
            source = base / relative
            if source.is_file():
                self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), metadata["sha256"])

if __name__ == "__main__":
    unittest.main(verbosity=2)
