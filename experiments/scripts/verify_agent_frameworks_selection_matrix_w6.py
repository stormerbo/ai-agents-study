from __future__ import annotations

import ast
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/agent-frameworks/05-selection-matrix.mdx"
META = ROOT / "src/content/chapters/agent-frameworks/meta.ts"
RESOURCES = ROOT / "src/content/curriculum/resources.ts"
EXPECTED = """框架符号（从框架包 import 进来的）：['AgentExecutor', 'ChatMessage']
签名里出现框架类型的函数：
  <sample>:11  def handle_payment(...)  注解 'ChatMessage' 引用了 ChatMessage
合计：1 处，涉及 1 个函数
"""


def main() -> None:
    lesson = LESSON.read_text()
    meta = META.read_text()
    resources = RESOURCES.read_text()
    checks = 0

    def require(condition: bool, message: str) -> None:
        nonlocal checks
        if not condition:
            raise AssertionError(message)
        checks += 1

    require("硬性门槛" in lesson and "可权衡的偏好" in lesson,
            "matrix must separate gates from weighted preferences")
    require("不能靠其它维度的高分抵消" in lesson, "hard gates must not be score-compensated")
    require("有图 API 不代表默认就能跨重启恢复" in lesson,
            "graph API must not imply persistence guarantees")
    require("turn/step 限制不一定是你的金额或业务预算" in lesson,
            "runtime turn limits must not be equated with business budgets")
    require("历史 0/3 对 3/3 结果不可独立复核" in lesson,
            "historical model comparison must remain unverified")
    require("不等于全系统 benchmark" in lesson, "pilot evidence must be scoped")
    require("直接当成迁移工时" in lesson, "reference counts must not be migration estimate")
    require("不能按命中数量直接乘“每处成本”" in lesson,
            "migration cost must not be derived by linear count formula")
    require("两三百行" not in lesson and "30 个工具" not in lesson,
            "unsupported universal size/tool-count threshold remains")
    require("往往是最优解" not in lesson and "就是不能用" not in lesson,
            "unsupported universal recommendation remains")
    require("trace、提示与工具输入输出的数据去向" in lesson,
            "data/trace destinations must be checked")
    require("字符串形式的前向引用" in lesson, "AST scanner false-negative boundary missing")
    require("ast.AsyncFunctionDef" in lesson and "fw & names" in lesson,
            "AST scanner should handle async functions and exact imported identifiers")
    require("agent-frameworks/leaky-abstractions" in lesson,
            "schema comparison should link to its dedicated reviewed lesson")
    require("https://openai.github.io/openai-agents-python/" in lesson,
            "official product path example needs a direct primary-source link")
    require("openai-agents-sdk-python" in meta and "openai-agents-sdk-python" in resources,
            "documented checkpoint must resolve to the source catalog")
    require("有条件满足" in lesson and "unknown" not in lesson.lower(),
            "decision matrix needs explicit evidence status, not certainty inflation")

    code_fences = re.findall(r"```python\n(.*?)\n```", lesson, re.S)
    require(len(code_fences) == 1, f"expected one Python code fence, got {len(code_fences)}")
    code = code_fences[0]
    ast.parse(code)
    tree = ast.parse(code)
    root_imports = [node for node in tree.body if isinstance(node, (ast.Import, ast.ImportFrom))]
    require(len(root_imports) == 1 and isinstance(root_imports[0], ast.Import)
            and root_imports[0].names[0].name == "ast",
            "static example must not import frameworks or external libraries")
    with tempfile.TemporaryDirectory(prefix="selection-matrix-") as tmp:
        path = Path(tmp) / "example.py"
        path.write_text(code)
        result = subprocess.run([sys.executable, str(path)], check=True, text=True,
                                capture_output=True, timeout=10)
    require(result.stdout == EXPECTED, "AST demo stdout must exactly match the displayed fence")
    require(result.stderr == "", "AST demo should not emit stderr")

    print(f"PASS {checks}/{checks}; Python fence executed; providerCalls=0; networkCalls=0")


if __name__ == "__main__":
    main()
