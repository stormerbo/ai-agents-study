import math
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/retrieval/04-evaluating-retrieval.mdx"
source = LESSON.read_text()
fences = re.findall(r"^```([^\n]*)\n([\s\S]*?)^```\s*$", source, re.M)
assert len(fences) == 4
python_fences = [body for lang, body in fences if lang.strip() == "python"]
assert len(python_fences) == 2

# Execute every runnable Python fence and require the immediately following
# text fence to show its exact stdout, preventing code/output drift.
for index, (language, body) in enumerate(fences):
    if language.strip() != "python":
        continue
    run_all = subprocess.run([sys.executable, "-c", body], check=True, capture_output=True, text=True)
    output_language, expected_output = fences[index + 1]
    assert output_language.strip() == "text"
    assert run_all.stdout == expected_output, (index, run_all.stdout, expected_output)

run = subprocess.run(
    [sys.executable, "-c", python_fences[1]],
    check=True,
    capture_output=True,
    text=True,
)
expected = """k=1  hit@1 = 0.75   MRR = 0.88
k=2  hit@2 = 1.00   MRR = 0.88
k=3  hit@3 = 1.00   MRR = 0.88
"""
assert run.stdout.startswith(expected), run.stdout
assert "排名=2" in run.stdout
assert "k=1  hit@1 = 0.75   MRR = 0.75" not in source
assert "k=1  hit@1 = 0.75   MRR = 0.88" in source
assert "context-engineering/compaction#历史样本二：摘要记录中遗漏一条硬约束" in source
assert "memory/forgetting-and-conflict#有效期如何设定" in source
assert "retrieval/chunking#历史摘要：评测粒度会改变“命中”的含义" in source
assert "multi-agent/cost-model#实测：两次不同背景规模下的倍数" in source

# The first Python fence only assembles a local context; it must not be called
# a model run or evidence that the generator reached an upper bound.
assert "没有调用模型，也没有实现检索或证明生成层上界" in source
assert "不可独立复核的历史摘要" in source
assert "旧报告曾按文件级与章节级口径汇总同一组 15 条查询" in source
assert "perfect retrieval proves" not in source.lower()
assert "同一批 query 的配对设计" in source
assert "百分点" in source
assert "Stanford" in source

# Check the displayed normal-approximation standard errors from the stated
# plug-in formula. These are standard errors, not confidence intervals.
for p, n, displayed in [
    (0.5, 15, 12.9), (0.5, 30, 9.1), (0.5, 100, 5.0), (0.5, 400, 2.5),
    (0.6, 15, 12.6), (0.6, 30, 8.9), (0.6, 100, 4.9), (0.6, 400, 2.4),
    (0.9, 15, 7.7), (0.9, 30, 5.5), (0.9, 100, 3.0), (0.9, 400, 1.5),
]:
    assert math.isclose(math.sqrt(p * (1 - p) / n) * 100, displayed, abs_tol=0.06)

print("retrieval/evaluating-retrieval review: 33/33 checks passed; all runnable code stdout matches; providerCalls=0")
