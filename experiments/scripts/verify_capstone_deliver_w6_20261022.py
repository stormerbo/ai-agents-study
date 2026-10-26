from __future__ import annotations

import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/capstone/04-deliver.mdx"
META = ROOT / "src/content/chapters/capstone/meta.ts"
text = LESSON.read_text(encoding="utf-8")
meta = META.read_text(encoding="utf-8")
fences = re.findall(r"^```python\s*\n(.*?)^```\s*$", text, re.M | re.S)


class CapstoneDeliverW6(unittest.TestCase):
    def test_python_fences_compile_and_template_executes(self) -> None:
        self.assertEqual(len(fences), 1)
        for index, source in enumerate(fences, 1):
            compile(source, f"capstone-deliver-fence-{index}", "exec")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "handoff.py"
            path.write_text(fences[0], encoding="utf-8")
            run = subprocess.run([sys.executable, str(path)], check=True, capture_output=True, text=True)
        self.assertTrue(all(f"## {name}" in run.stdout for name in (
            "1 怎么跑", "2 不做什么", "3 怎么验", "4 出事怎么查", "5 已知缺口", "6 判断依据",
        )))
        self.assertIn("静态空白提纲", text)
        self.assertIn("不会读取项目的范围表", text)

    def test_six_block_order_is_presented_as_adaptable_not_universal(self) -> None:
        self.assertIn("交付文档要有的六块", text)
        self.assertIn("不是所有项目通用的优先级", text)
        self.assertIn("高风险交付可以把权限、安全和已知缺口提前", text)

    def test_observations_and_approval_policy_are_scoped(self) -> None:
        self.assertIn("特定 7 步合成任务", text)
        self.assertIn("不证明可逆性单独就能决定生产审批策略", text)
        self.assertIn("按数据分级选择性记录、脱敏或省略", text)
        self.assertIn("OWASP Logging Cheat Sheet", text)
        self.assertIn("安排一个未参与实现的人", meta)
        self.assertIn("不等于独立交接", meta)
        self.assertIn("不预设为半天", meta)

    def test_clean_run_path_failure_is_not_misreported_as_total_handoff_cost(self) -> None:
        self.assertIn("0.03 秒", text)
        self.assertIn("没有单独计量找路径耗时", text)
        self.assertIn("不能据此说交接的全部成本都出在这一步", text)
        self.assertIn("工作目录未写清而找不到文件", text)
        self.assertNotIn("全部成本都出在「找路径」那一步", text)
        self.assertIn("不是实测出来的故障阈值", text)

    def test_historical_timing_is_only_the_script_process_time(self) -> None:
        self.assertIn("只测到该次脚本进程的执行时间", text)
        self.assertIn("不能代表完整交接成本", text)
        self.assertIn("一次有限的本地清理检查", text)
        self.assertIn("不等价于从干净 checkout、全新机器或隔离环境完成交接", text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
