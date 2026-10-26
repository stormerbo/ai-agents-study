from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/multi-agent/06-failure-modes-collaboration.mdx"
META = ROOT / "src/content/chapters/multi-agent/meta.ts"
text = LESSON.read_text(encoding="utf-8")
meta = META.read_text(encoding="utf-8")
checks: list[str] = []


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)
    checks.append(message)


fences = re.findall(r"```python\s*\n(.*?)\n```", text, re.S)
check(len(fences) == 2, f"found {len(fences)} Python fences")
for index, source in enumerate(fences):
    compile(source, f"{LESSON.name}:python-fence-{index}", "exec")
    checks.append(f"Python fence {index} compiles")
    check(
        max(map(len, source.splitlines())) <= 88,
        f"Python fence {index} has no line longer than 88 characters",
    )

thread_run = subprocess.run([sys.executable, "-c", fences[0]], check=True, capture_output=True, text=True)
check("无保护的读-改-写：期望 8，实际 1，丢失 7 次更新" in thread_run.stdout, "barrier fixture deterministically reproduces a lost update")
check("锁罩住「读-改-写」：期望 8，实际 8，丢失 0 次更新" in thread_run.stdout, "in-process lock protects the whole fixture operation")
check("threading.Barrier" in fences[0] and "time.sleep" not in fences[0], "race fixture uses a deterministic barrier rather than timing assumptions")
check("expected = WORKERS if use_lock else 1" in fences[0], "thread outcomes have executable assertions")

lineage = subprocess.run([sys.executable, "-c", fences[1]], check=True, capture_output=True, text=True)
check("valid source and derivation graph: accepted" in lineage.stdout, "valid constructed lineage graph is accepted")
check("missing parent fixture: detected" in lineage.stdout, "missing lineage edge is detected")
check("duplicate ID and cycle fixtures: detected" in lineage.stdout, "duplicate IDs and cycles are detected")
check("source truth, freshness, semantic correctness and authorization: not evaluated" in lineage.stdout, "lineage code discloses its evidence boundary")

check("屏障刻意让所有线程先读再写" in text, "thread result is scoped to a constructed interleaving")
check("不代表所有 agent 并发都会发生相同结果" in text, "concurrency behavior is not treated as agent-specific or universal")
check("进程内 mutex 不能保护其他进程或服务" in text, "local lock is not described as distributed protection")
check("应避免把慢速模型调用放在需要保护的事务临界区内" in text, "slow model calls are not prescribed inside a protected transaction")
check("Jaccard 相似度对两个 token 集合 A、B 定义为 `|A ∩ B| / |A ∪ B|`" in text, "lexical metric definition is explicit")
check("原始请求、五份完整响应、分词细节、结论标签和评分过程未归档" in text, "historical diversity result is not independently reproducible")
check("构造例子，不是该次模型原文" in text, "constructed output paraphrases are distinguished from historical responses")
check("不证明真实 agent 一定趋同" in text, "synthetic example is not generalized to model behavior")
check("Tevet 与 Berant" in text and "不提供本例历史数字的复核" in text, "research source is limited to its task and does not validate the old sample")
check("不同的目标或反方约束" in text and "不保证模型能力专门化或结论互补" in text, "task steering is treated as a candidate lever, not a guarantee")
check("上游未经验证的主张被下游当成已验证事实" in text, "cascade is described as a risk scenario rather than an invariant")
check("不能单独判断原始来源可信、仍然新鲜、解释正确或动作已获授权" in text, "lineage is separated from truth, freshness, semantics and authorization")
check("OpenTelemetry 的 GenAI spans 规范目前标注为 development" in text, "trace standard status is time-scoped")
check("这些问题可能静默发生，也可能伴随冲突异常、拒绝、超时或预算耗尽" in text, "failure modes are not all claimed to be silent")
check("不套用固定两轮阈值" in text and "没有通用阈值" in text, "loop thresholds are task-specific")
check("不能假定人工判断必然可靠" in text, "human review is not treated as infallible")

check("sourceIds: ['postgres-row-locking-18', 'postgres-insert-18']" in meta, "metadata anchors database claims to PostgreSQL documentation")
check("sourceIds: ['eacl-evaluating-diversity-metrics']" in meta, "metadata anchors metric claims to the primary ACL paper")
check("opentelemetry-genai-semconv" in meta, "metadata registers trace conventions for the trace/lineage distinction")
check("每次都出问题" not in meta and "几百毫秒到几秒" not in meta, "metadata removes unsupported latency and failure-frequency claims")

print(f"{len(checks)} checks passed; providerCalls=0")
