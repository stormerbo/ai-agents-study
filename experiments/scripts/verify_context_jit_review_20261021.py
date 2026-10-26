from __future__ import annotations

import ast
import re
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/context-engineering/03-just-in-time.mdx"
META = ROOT / "src/content/chapters/context-engineering/meta.ts"
DATA = ROOT / "docs/DATA.md"


def check(condition: bool, label: str) -> None:
    if not condition:
        raise AssertionError(label)
    print(f"PASS {label}")


text = LESSON.read_text()
meta = META.read_text()
data = DATA.read_text()
python_fences = re.findall(r"```python\s*\n(.*?)\n```", text, re.S)
check(len(python_fences) == 1, "one complete Python sample is registered in this lesson")
sample = python_fences[0]
compile(sample, str(LESSON), "exec")
check(True, "complete Python sample compiles")

check("历史单次观测摘要" in text, "historical comparisons are labeled as single-run summaries")
check("逐次请求/响应" in text and "无法独立重放" in text, "missing raw traces and replay limit are disclosed")
check("不是可迁移阈值" in text, "the 20 percent crossover is not generalized")
check("不验证两条路线是否给出同等正确答案" in text, "token-only script does not imply answer equivalence")
check("resp.stop_reason != \"end_turn\"" in sample, "preload rejects non-completed responses")
check('resp.stop_reason == "end_turn"' in sample, "on-demand only returns a completed turn")
check("达到工具轮次上限" in sample, "tool-loop exhaustion is an explicit incomplete result")
check("if not results:" in sample, "empty client tool-use result batches fail closed")
check("Anthropic Messages usage 字段语义" in sample, "usage calculation is scoped to Anthropic semantics")
check("prompt_cache_hit_tokens" in meta and "cache_read_input_tokens" in meta, "provider cache usage schemas are separated in the checkpoint")
check("20% 交叉点只是稀疏单次样本的插值" in data, "data ledger carries the non-generalization caveat")
check("宿主校验" in text and "每次读取" in text, "authorization is assigned to the host on catalogue and read paths")

tree = ast.parse(sample)
function = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "total_tokens")
namespace: dict[str, object] = {}
exec(compile(ast.Module(body=[function], type_ignores=[]), str(LESSON), "exec"), namespace)
counter = namespace["total_tokens"]
usage = SimpleNamespace(input_tokens=10, cache_read_input_tokens=20, cache_creation_input_tokens=3, output_tokens=7)
check(counter(usage) == 40, "Anthropic-style total input plus output usage arithmetic")
usage_without_cache = SimpleNamespace(input_tokens=10, output_tokens=7)
check(counter(usage_without_cache) == 17, "usage counter tolerates absent optional cache fields")

print("RESULT 16/16 PASS")
