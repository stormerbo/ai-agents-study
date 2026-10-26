from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/human-in-the-loop/03-interrupt-and-resume.mdx"
META = ROOT / "src/content/chapters/human-in-the-loop/meta.ts"
text = LESSON.read_text(encoding="utf-8")
meta = META.read_text(encoding="utf-8")
checks = 0


def check(condition: bool, message: str) -> None:
    global checks
    checks += 1
    if not condition:
        raise AssertionError(message)


fences = re.findall(r"```python\n(.*?)\n```", text, re.S)
check(len(fences) == 1, f"expected 1 runnable Python fence, got {len(fences)}")
for index, source in enumerate(fences, 1):
    compile(source, f"interrupt-resume-fence-{index}", "exec")

with tempfile.TemporaryDirectory() as tmp:
    code_path = Path(tmp) / "lesson.py"
    code_path.write_text(fences[0], encoding="utf-8")
    run = subprocess.run([sys.executable, str(code_path)], check=True, capture_output=True, text=True)
output = run.stdout
check("PASS: unauthorized actor rejected" in output, "local state model must reject an unauthorized actor")
check("expired approval rejected" in output, "local state model must reject an expired approval")
check("reconciled with one fake receiver effect" in output and "now=103" in fences[0], "unknown effects must be reconciled even after approval expiry, without resending")
check("one fake receiver effect" in output, "lost receipt retry must deduplicate in the fake receiver")
check("fx.approvals[old][\"status\"] == \"invalidated\"" in fences[0], "editing must invalidate the old proposal")
check("fx.approvals[new][\"version\"] == 2" in fences[0], "edited proposal must receive a new version")
check("hashlib.sha256" in fences[0] and "sort_keys=True" in fences[0], "digest fixture must use canonical serialization and a cryptographic hash")
check("tenant_id" in fences[0] and "actor_id" in fences[0], "decision path must model tenant and actor checks")
check("expires_at" in fences[0] and "now >= rec[\"expires_at\"]" in fences[0], "approval expiry must gate execution")
check("idempotency_key_conflict" in fences[0], "same receiver key with changed payload must conflict")
check("not a persistence" not in text.lower() and "不是持久化、并发或跨服务事务的证明" in text,
      "fixture limitations must be explicit")
check("不能据此断言它的重复概率高于崩溃" in text, "the unsupported comparative probability must be explicitly rejected")
check("不能仅按时长比较重复概率" in text, "duration must not be used as a proxy for duplicate probability")
check("执行修改后的版本，不重新规划" not in text, "edits cannot inherit the old approval")
check("不能把重新规划变成绕过否决" in text, "replanning must not evade refusal")
check("免费信号" not in text, "approval metrics must not be framed as self-explanatory or cost-free diagnosis")
check("客户端" not in text or "不应信任浏览器传回的摘要" in text, "browser-provided digest must not become the trust source")
check("本地数据库事务本身不提供跨服务 exactly-once" in text, "external side effect guarantees must be bounded")
check("接收方必须以稳定幂等键去重" in text, "external deduplication must be receiver-backed")
check("status=unknown" in text or "`unknown`" in text, "unknown external outcomes must be represented")
check("人的响应时间是**分钟到小时级**" not in meta, "metadata must not assert a universal wait-time ratio")
check("postgres-row-locking-18" in meta and "stripe-idempotency-keys" in meta,
      "metadata must cite the sources used for row-locking and receiver idempotency boundaries")
check("owasp-transaction-authorization" in meta and "owasp-authorization-cheat-sheet" in meta,
      "metadata must include approval binding and authorization sources")

check("postgres-date-time-functions-18" in meta, "metadata must cite the PostgreSQL clock semantics used in the SQL example")
check("tenant_id = :authenticated_tenant" in text and "status = 'pending'" in text, "SQL sketch must constrain the tenant and current state")
check("expires_at > clock_timestamp()" in text and "必须恰好返回一行" in text, "SQL sketch must enforce expiry at execution and fail closed on a lost state race")

check('"0" * 64' in fences[0] and 'proposal_hash' in fences[0], "the example must reject a stale or mismatched proposal digest without consuming the pending approval")
check("id: 'approval-single-use-before-execution'" in meta and "sourceIds: ['owasp-ai-agent-security']" in meta,
      "approval consumption checkpoint must be bound to OWASP AI Agent Security")
check("原子状态转换" in text and "紧邻受保护动作前" in text and "原子消费 approval" in text,
      "approval must be atomically consumed immediately before the protected effect")
check("异步执行" in text and "执行 claim 的截止时间" in text,
      "queued effects must define the expiry boundary for their execution claim")
check('approved_then_late' in fences[0] and 'len(fx.effects) == effects_before_late_claim' in fences[0],
      "the fixture must prove that an approval expiring after the human decision cannot start a delayed effect")
check('remote_committed_local_stale' in fences[0] and 'len(fx.effects) == effects_before_reconcile' in fences[0],
      "the fixture must reconcile a receiver commit after a crash before the local receipt is persisted")
check('本地记录仍显示 `approved`' in text and '接收端的权威幂等账本' in text,
      "the prose must cover the remote-commit/local-stale crash window and require authoritative receiver evidence")

print(f"PASS {checks}/{checks}; Python fences compiled={len(fences)}; state fixture executed; providerCalls=0")
print(output)
