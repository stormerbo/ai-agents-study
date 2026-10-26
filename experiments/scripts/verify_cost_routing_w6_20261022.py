"""Offline W6 whole-lesson checks for the model-routing lesson."""
from __future__ import annotations

import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LESSON = (ROOT / "src/content/chapters/cost-and-latency/04-routing.mdx").read_text()
META = (ROOT / "src/content/chapters/cost-and-latency/meta.ts").read_text()
RESOURCES = (ROOT / "src/content/curriculum/resources.ts").read_text()


class RoutingW6(unittest.TestCase):
    def test_decision_objective_keeps_quality_safety_latency_as_gates(self):
        for phrase in ("质量门槛", "安全与能力约束", "延迟约束", "每个成功完成任务的实际成本"):
            self.assertIn(phrase, LESSON)
        self.assertIn("一个更强的模型不等于安全控制", LESSON)

    def test_features_are_not_quality_labels(self):
        self.assertIn("不是质量标签", LESSON)
        self.assertIn("不能把“是否发生工具调用”当作事前路由条件", LESSON)
        self.assertIn("不以输入长度或“规划/执行”标签直接等同能力", META)

    def test_latest_benchmark_claim_is_primary_source_bound_and_scoped(self):
        self.assertIn("llmrouterbench-paper", META)
        self.assertIn("id: 'llmrouterbench-paper'", RESOURCES)
        self.assertIn("https://aclanthology.org/2026.findings-acl.1881/", RESOURCES)
        self.assertIn("Findings ACL 2026 的 [LLMRouterBench]", LESSON)
        for phrase in ("21 个数据集", "33 个模型", "10 种路由基线", "只适用于论文的候选池、数据集和指标"):
            self.assertIn(phrase, LESSON)
        self.assertIn("routing-benchmark-boundary", META)
        self.assertIn("sourceIds: ['llmrouterbench-paper']", META)

    def test_no_benchmark_result_is_generalized_to_production(self):
        self.assertIn("不能推出路由在你的流量上无效", LESSON)
        self.assertIn("不证明路由在其他工作负载上无效", META)
        self.assertIn("固定最佳候选基线", LESSON)

    def test_cascade_cost_equation_and_break_even_are_consistent(self):
        cheap, strong, judge = 2400, 18000, 300
        self.assertEqual((strong - cheap - judge) / strong, 0.85)
        self.assertIn("C_cheap + C_judge + r × C_strong", LESSON)
        self.assertIn("盈亏平衡升级率是 85%", LESSON)
        self.assertIn("级联，升级率 60%              13,500,000", LESSON)

    def test_cost_example_labels_all_rates_as_constructed_assumptions(self):
        self.assertIn("假设值，不是模型价格或线上实测", LESSON)
        self.assertIn("假设规则能完美识别这些请求", LESSON)
        self.assertIn("不表示质量相同或生产能节省同样比例", LESSON)

    def test_validation_gate_does_not_claim_semantic_correctness(self):
        self.assertIn("结构正确不等于事实正确", LESSON)
        self.assertIn("structure_valid_needs_business_check", LESSON)
        self.assertIn("business_and_semantic_acceptance_required", LESSON)

    def test_provider_status_is_not_blindly_escalated_or_retried(self):
        for phrase in ("不得盲目升级", "结果未知", "不能盲目重放", "adapter 应按供应商契约归一化"):
            self.assertIn(phrase, LESSON)

    def test_legacy_results_remain_bounded(self):
        self.assertIn("不能作为等价任务的质量/成本对比", LESSON)
        self.assertIn("删除固定 1,000 阈值", LESSON)
        self.assertIn("另一段旧材料提过", LESSON)

    def test_python_fences_compile_and_execute_offline(self):
        fences = re.findall(r"```python\n(.*?)\n```", LESSON, flags=re.DOTALL)
        self.assertEqual(len(fences), 2)
        for index, source in enumerate(fences):
            self.assertNotIn("os.environ", source)
            self.assertNotIn("requests.", source)
            with tempfile.NamedTemporaryFile("w", suffix=f"_{index}.py", encoding="utf-8") as handle:
                handle.write(source)
                handle.flush()
                compiled = subprocess.run([sys.executable, "-m", "py_compile", handle.name], capture_output=True, text=True)
                self.assertEqual(compiled.returncode, 0, compiled.stderr)
                run = subprocess.run([sys.executable, handle.name], capture_output=True, text=True, check=True)
                if index == 0:
                    self.assertIn("固定较贵模型: 18000000", run.stdout)
                    self.assertIn("盈亏平衡升级率: 85.0%", run.stdout)
                    self.assertIn("规则路由相对固定较贵模型的成本降幅: 69.3%", run.stdout)
                else:
                    for expected in ("business_and_semantic_acceptance_required", "invalid_amount_type", "invalid_json_number", "handle_status_without_blind_model_upgrade:provider_error"):
                        self.assertIn(expected, run.stdout)

    def test_official_model_guidance_is_registered(self):
        for source_id in ("openai-model-selection", "anthropic-choosing-model", "anthropic-cost-intelligence"):
            self.assertIn(source_id, META)
            self.assertIn(f"'{source_id}'", RESOURCES)


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(RoutingW6)
    )
    print(f"providerCalls=0; externalNetworkCalls=0; tests={result.testsRun}; failures={len(result.failures) + len(result.errors)}")
    raise SystemExit(not result.wasSuccessful())
