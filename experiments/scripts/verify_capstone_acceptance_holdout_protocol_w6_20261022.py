from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "examples/capstone-acceptance"))
sys.path.insert(0, str(ROOT / "examples/p5-agent-delivery/evaluation"))

from acceptance import OFFICIAL_HOLDOUT_RESULT_SCHEMA_V6 as ACCEPTANCE_HOLDOUT_SCHEMA, REQUIRED_HOLDOUT_STOP_CONDITIONS, _decimal_usd  # noqa: E402
from official_holdout import CandidateRuntime, HoldoutRegistry, HoldoutReservation, HoldoutRunSpec, RegistryEventSnapshot, OFFICIAL_HOLDOUT_RESULT_SCHEMA, REQUIRED_STOP_CONDITIONS  # noqa: E402

LESSON = ROOT / "src/content/chapters/capstone/06-acceptance.mdx"
TEXT = LESSON.read_text(encoding="utf-8")
PLAN = ROOT / "docs/superpowers/plans/2026-10-20-stage5-capstone.md"
PLAN_TEXT = PLAN.read_text(encoding="utf-8")


class CapstoneHoldoutProtocolW6(unittest.TestCase):
    def test_lesson_explains_the_frozen_holdout_and_role_boundary(self) -> None:
        section = TEXT.split("### 正式盲测的证据链", 1)[1].split("## 机器门禁与本地报告", 1)[0]
        for phrase in (
            "authorization_event_id",
            "reservation",
            "terminal",
            "剩余预算字符串",
            "隐藏数据 custodian",
            "可信外部 registry",
            "JSON 整数或浮点数",
            "最低通过率（整数 basis points，0–10000）",
            "quality_decision",
            "不能代替质量结论",
            "权限边界破坏",
            "对象含样本数",
            "总 token usage 和成本",
            "owner ID、executor ID 和 recovery operator ID 不含姓名",
            "检查发生在 `candidate.execute` 返回之后",
            "不能防止适配器在返回前先把超大响应读入内存",
            "`report_sha256` 是对规范化结果正文",
            "终态 registry event 必须保存同一个 digest",
            "完整验收材料包使用 `official-blind-holdout-evidence-envelope-v6`",
            "双见证路径要求每条权威事件都有独立 witness 回执",
            "当前本地 runner 尚未生成这层正式材料包",
            "`authorized → reserved → terminal` 三类事件还必须按 `previous_event_id` 首尾相连",
        ):
            self.assertIn(phrase, section)
        self.assertTrue({
            "authorization_event_id", "executor_sha256", "minimum_task_count",
            "minimum_pass_rate_bps", "require_all_tasks_pass", "stop_conditions",
            "owner_id", "executor_id", "recovery_operator_id",
        }.issubset(HoldoutRunSpec.__dataclass_fields__))
        self.assertEqual(CandidateRuntime.execute.__annotations__["remaining_budget_usd"], "str")
        self.assertIn("reconcile", HoldoutRegistry.__dict__)
        self.assertIn("recover_abort", HoldoutRegistry.__dict__)
        self.assertIn("payload", RegistryEventSnapshot.__dataclass_fields__)
        self.assertIn("registry_snapshot", HoldoutReservation.__dataclass_fields__)
        self.assertEqual(REQUIRED_STOP_CONDITIONS, REQUIRED_HOLDOUT_STOP_CONDITIONS)

    def test_acceptance_costs_use_exact_decimal_strings(self) -> None:
        self.assertIsNone(_decimal_usd(1.25))
        self.assertIsNone(_decimal_usd(1))
        self.assertEqual(str(_decimal_usd("1.25")), "1.25")
        self.assertIsNone(_decimal_usd("NaN"))

    def test_design_plan_matches_implemented_seam_and_separates_run_from_quality(self) -> None:
        self.assertIn("本地合同已实现，正式盲测未完成", PLAN_TEXT)
        self.assertNotIn("正式 blind holdout 协议（设计约束，尚未实现）", PLAN_TEXT)
        self.assertEqual(
            PLAN_TEXT.count("验收证据必须来自真实冻结候选的一次受控运行"),
            1,
        )
        self.assertIn("decision=completed", PLAN_TEXT)
        self.assertIn("quality_decision=failed", PLAN_TEXT)
        self.assertIn("最低通过率 basis points", PLAN_TEXT)
        self.assertIn("报告携带完整 frozen spec", PLAN_TEXT)
        self.assertIn("重算 canonical SHA-256", PLAN_TEXT)
        self.assertIn("规范化 frozen spec 正文", PLAN_TEXT)
        self.assertIn("authorization_event_id` 必须由 owner 在授权前生成", PLAN_TEXT)
        self.assertIn("要先知道事件 ID 才能计算 hash", PLAN_TEXT)
        self.assertIn("预先生成的 authorization event id", PLAN_TEXT)
        self.assertIn("只有快照状态为 `authorized`", PLAN_TEXT)
        self.assertIn("`not_found` 表示授权本身不存在", PLAN_TEXT)
        self.assertIn("`recover_abort`", PLAN_TEXT)
        self.assertIn("candidate 从未启动", PLAN_TEXT)
        self.assertIn("registry 从受信审计源核实证据后", PLAN_TEXT)
        self.assertIn("不能返回题面、标签、prompt、候选原始输出、凭据或 capability", PLAN_TEXT)
        self.assertIn("reserve 必须同时返回授权→预约的 allowlist 事件快照", PLAN_TEXT)
        self.assertIn("一次性门禁钥匙", PLAN_TEXT)
        self.assertIn("外部 registry 接入前的服务级合同测试", PLAN_TEXT)
        self.assertIn("两个并发 executor 竞争同一预约", TEXT)
        self.assertIn("owner 对同一 `(holdout_version, run_id)` 并发提交不同 authorization event id/spec", PLAN_TEXT)
        self.assertIn("scorer 标签释放时序", PLAN_TEXT)
        self.assertIn("executor 与 recovery operator 同时写终态", TEXT)
        self.assertIn("registry 要原子地完成“预约成功”和“给唯一 runtime session 发钥匙”", TEXT)
        self.assertIn("本地核对 owner/executor actor role", PLAN_TEXT)
        self.assertIn("owner、executor 和 recovery operator 的身份用身份系统里的稳定 subject ID 表示", PLAN_TEXT)
        self.assertIn("actor ID 应与冻结 subject ID 一致", TEXT)
        self.assertIn("reconcile(run_id) -> RegistrySnapshot", PLAN_TEXT)
        self.assertIn("RegistrySnapshot` 只是外部查询结果的数据结构", TEXT)
        self.assertIn("独立 recovery operator", TEXT)
        self.assertIn("registry 从受信运行时审计源核实证据、确认 candidate 从未启动", TEXT)
        self.assertIn("report_sha256", PLAN_TEXT)
        self.assertIn("两层须由 evidence assembler 显式组合", PLAN_TEXT)
        self.assertIn("`previous_event_id` 形成 authorized→reserved→terminal 链", PLAN_TEXT)
        self.assertIn("不能只相信 operator 自己提交的证据链接和 hash", TEXT)
        self.assertIn("返回只能是脱敏事件字段和 payload hash", TEXT)
        self.assertIn("runner 在启动 candidate 前核对 registry 返回的脱敏授权/预约两条事件", TEXT)
        self.assertIn("本地检查只能发现响应内部矛盾", TEXT)
        self.assertIn("owner 先生成 `authorization_event_id`", TEXT)
        run_record = ROOT / "docs/superpowers/templates/official-holdout-run-record.md"
        self.assertTrue(run_record.is_file())
        run_record_text = run_record.read_text(encoding="utf-8")
        self.assertIn("默认 no-go", run_record_text)
        self.assertIn("最大总费用", run_record_text)
        self.assertIn("独立 reviewer 对 preflight 的签署", run_record_text)
        self.assertIn("scorer 不得同时是候选实现者", run_record_text)
        self.assertIn("registry 终态（consumed / aborted / failed / 尚无终态事件）", run_record_text)
        self.assertIn("执行观察状态（known / unknown）", run_record_text)
        self.assertIn("not_found` 表示没有授权事件", run_record_text)
        self.assertIn("unavailable`，不能据此推断为 `not_found`", run_record_text)
        self.assertIn("授权未过期、run/spec hash 完全匹配", run_record_text)
        self.assertIn("结果 hash 已封存后，独立 scorer 才能按授权读取该 run 标签", run_record_text)
        self.assertIn("scorer 不得兼任候选实现者/executor/runtime operator", PLAN_TEXT)
        handoff_template = ROOT / "examples/p5-agent-delivery/HANDOFF-RECORD.template.json"
        handoff_template_text = handoff_template.read_text(encoding="utf-8")
        self.assertIn('"schema": "p5-independent-handoff-v3"', handoff_template_text)
        self.assertIn('"profile": "local-reference"', handoff_template_text)
        self.assertIn('"append_authority_compromise_in_scope": null', handoff_template_text)
        self.assertIn('"registry_state": "not_checked"', handoff_template_text)
        self.assertIn('"execution_observation": "not_started"', handoff_template_text)
        self.assertIn('"quality_decision": "pending"', handoff_template_text)
        self.assertIn('"runner_outcome": "not_run"', handoff_template_text)
        self.assertNotIn('"consumed": false', handoff_template_text)
        self.assertIn('"owner_subject_id"', handoff_template_text)
        self.assertIn('"holdout_reviewer_subject_id"', handoff_template_text)
        self.assertIn('"reviewer_subject_id": null', handoff_template_text)
        self.assertNotIn("name_or_id", handoff_template_text)
        handoff_schema_text = (ROOT / "examples/p5-agent-delivery/HANDOFF-RECORD.schema.json").read_text(encoding="utf-8")
        self.assertIn('"dual-witness-v1"', handoff_schema_text)
        self.assertIn('"terminal_witness_receipt_sha256"', handoff_schema_text)
        handoff_guide = (ROOT / "examples/p5-agent-delivery/HANDOFF.md").read_text(encoding="utf-8")
        self.assertIn("official-holdout-run-record.md", handoff_guide)
        self.assertIn("registry lookup failure is not `not_found`", handoff_guide)
        self.assertIn("`runner_outcome`", handoff_guide)
        self.assertEqual(OFFICIAL_HOLDOUT_RESULT_SCHEMA, "official-blind-holdout-run-result-v4")
        self.assertEqual(ACCEPTANCE_HOLDOUT_SCHEMA, "official-blind-holdout-evidence-envelope-v6")
        self.assertNotEqual(OFFICIAL_HOLDOUT_RESULT_SCHEMA, ACCEPTANCE_HOLDOUT_SCHEMA)
        acceptance_source = (ROOT / "examples/capstone-acceptance/acceptance.py").read_text(encoding="utf-8")
        acceptance_tests = (ROOT / "examples/capstone-acceptance/test_acceptance.py").read_text(encoding="utf-8")
        self.assertIn("_verify_assurance_attestations", acceptance_source)
        self.assertIn("test_v6_holdout_without_signed_governance_attestations_stays_unverified", acceptance_tests)
        self.assertIn("test_v6_invalid_governance_signature_or_handoff_binding_is_invalid", acceptance_tests)
        self.assertIn("fetch_latest_witness_chain", acceptance_source)
        self.assertIn("verify_dual_witness_receipt_chain(", acceptance_source)
        self.assertIn("test_v6_dual_witness_profile_requires_and_verifies_latest_witness_chain", acceptance_tests)

    def test_documented_offline_test_counts_match_current_suites(self) -> None:
        self.assertIn("81 项通过", TEXT)
        self.assertIn("Ran 81 tests", TEXT)
        suites = (
            ("examples/capstone-acceptance", "93"),
            ("examples/p5-agent-delivery/evaluation", "87"),
        )
        for suite, count in suites:
            result = subprocess.run(
                [
                    "uv", "run", "--frozen", "python", "-m", "unittest",
                    "discover", "-s", suite, "-q",
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
                timeout=60,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn(f"Ran {count} tests", result.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
