from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
LESSON_PATH = ROOT / "src/content/chapters/cost-and-latency/04-routing.mdx"
LESSON = LESSON_PATH.read_text()
META = (ROOT / "src/content/chapters/cost-and-latency/meta.ts").read_text()
DATA = (ROOT / "docs/DATA.md").read_text()


class RoutingReviewContract(unittest.TestCase):
    def test_policy_is_evalled_on_quality_cost_latency_and_safety(self):
        for phrase in ("离线评估集", "质量门槛", "每个成功任务的成本", "尾延迟", "安全约束"):
            self.assertIn(phrase, LESSON)

    def test_thresholds_are_derived_from_costs_not_universal_percentages(self):
        self.assertIn("(C_strong - C_cheap - C_judge) / C_strong", LESSON)
        self.assertNotIn("超过一半就", LESSON)
        self.assertNotIn("超过 50% 就比直接用强模型更贵", LESSON)
        self.assertNotIn("收益上限 = 难题占比", LESSON)
        self.assertIn("ERR-089", DATA)
        self.assertIn("盈亏平衡升级率是 85%", DATA)

    def test_routing_features_are_not_mistaken_for_reliable_quality_labels(self):
        for phrase in ("输入长度", "工具调用", "结构化输出", "稳定、可执行的分组特征", "不是质量标签"):
            self.assertIn(phrase, LESSON)
        self.assertNotIn("输入长度分流", LESSON)
        self.assertNotIn("规划步骤用强模型", LESSON)

    def test_structural_validity_is_not_semantic_correctness(self):
        for phrase in ("结构正确不等于事实正确", "provider 错误", "不得盲目升级", "服务端定义的 schema"):
            self.assertIn(phrase, LESSON)
        self.assertNotIn("结果一定不完整", LESSON)
        self.assertNotIn("不会因为内容对错而误判", LESSON)

    def test_cascade_formula_accounts_for_router_cost_and_escalation_share(self):
        for phrase in ("C_cheap + C_judge + r × C_strong", "升级阈值", "误升级", "漏升级"):
            self.assertIn(phrase, LESSON)

    def test_legacy_14x_observation_is_not_used_as_model_comparison(self):
        self.assertIn("14.4 倍", LESSON)
        self.assertIn("不能作为等价任务的质量/成本对比", LESSON)

    def test_python_fences_are_self_contained_and_offline(self):
        fences = re.findall(r"```python\n(.*?)\n```", LESSON, flags=re.DOTALL)
        self.assertGreaterEqual(len(fences), 2)
        for index, source in enumerate(fences):
            with tempfile.NamedTemporaryFile("w", suffix=f"_{index}.py", encoding="utf-8") as handle:
                handle.write(source)
                handle.flush()
                self.assertNotIn("os.environ", source)
                output = subprocess.run([sys.executable, handle.name], text=True, capture_output=True, check=True)
                self.assertTrue(output.stdout.strip())
                if index == 0:
                    self.assertIn("固定较贵模型: 18000000", output.stdout)
                    self.assertIn("盈亏平衡升级率: 85.0%", output.stdout)
                if index == 1:
                    self.assertIn("business_and_semantic_acceptance_required", output.stdout)
                    self.assertIn("invalid_amount_type", output.stdout)
                    self.assertIn("invalid_json_number", output.stdout)

    def test_offline_examples_and_documentation_sources_are_registered(self):
        for source_id in ("openai-model-selection", "anthropic-choosing-model", "anthropic-cost-intelligence", "routerbench-paper"):
            self.assertIn(source_id, META)


if __name__ == "__main__":
    unittest.main(verbosity=2)
