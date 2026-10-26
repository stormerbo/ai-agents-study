"""Offline audit of trace-learning taxonomy, evidence boundaries, and trust controls."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/continuous-evolution/01-from-traces.mdx"
META = ROOT / "src/content/chapters/continuous-evolution/meta.ts"
RESOURCES = ROOT / "src/content/curriculum/resources.ts"
lesson = LESSON.read_text(encoding="utf-8")
meta = META.read_text(encoding="utf-8")
resources = RESOURCES.read_text(encoding="utf-8")
checks = 0


def check(condition: bool, message: str) -> None:
    global checks
    checks += 1
    assert condition, message


check("不把它们排成普适的成本序列" in lesson, "taxonomy is no longer presented as universal cost order")
check("没有验证和发布门禁，收集轨迹不会让系统自行变好" in lesson, "trace collection is not conflated with autonomous learning")
check("不必等到积累「大量」线上轨迹才开始" in lesson, "the workflow does not require a large online corpus to begin")
check("不能据此推断「大多数团队」的采用比例" in lesson, "unsupported adoption frequency removed")
check("不存在通用的分钟级／周级周期" in lesson, "provider-independent timing removed")
check("访问控制 + 来源/时效校验" in lesson, "diagram includes provenance and access checks")
check("CRM 记录 crm-88213，版本 18" in lesson, "example identifies an authoritative descriptive source")
check('"退款可以免审批"' not in lesson, "memory example no longer encodes an authorization decision")
check('"tenant_id": "tenant-7"' in lesson, "example is tenant-scoped")
check("不能代替授权" in lesson, "similarity search is not treated as authorization")
check("模型生成的过滤条件" in lesson, "server-side filtering does not trust model-generated scope")
check("都不天然等于已确认事实" in lesson, "model/tool/user input is not implicitly authoritative")
check("不可信数据" in lesson and "不要把外部文本直接提升为 system 指令" in lesson, "retrieved content is not elevated to system instruction")
check("这个提示不能形成可靠隔离" in lesson, "prompt wording is not presented as security isolation")
check("在副作用前检查" in lesson, "business policy is enforced before side effects")
check("模型参数更新也不是表达困难时的默认兜底" in lesson, "taxonomy avoids training-only fallback")
check("不单独证明样本处在能力边界" in lesson, "pass-k instability is not mislabeled as capability-boundary proof")
check("不说明优化它的收益最高" in lesson, "instability is not equated with highest ROI")
check("不能估算过期比例" in lesson, "unsupported stale-memory prevalence removed")
check("不能说规则一多就必然矛盾" in lesson, "rule conflict is not claimed as inevitable")
check("historical" not in lesson, "lesson body remains Chinese prose")
check("retrieval-trust-boundary" in meta, "documented security checkpoint exists")
check("basis: 'documented'" in meta and "sourceIds: ['owasp-authorization-cheat-sheet', 'owasp-llm-prompt-injection']" in meta, "checkpoint cites registered authoritative sources")
check("OWASP Authorization Cheat Sheet" in resources, "authorization reference is registered")
check("OWASP GenAI LLM01:2025 Prompt Injection" in resources, "prompt-injection reference is registered")
check("四种形态是分类，不是通用成本序列" in meta, "metadata checkpoint matches lesson taxonomy")
check("不单独证明它位于能力边界" in meta, "metadata checkpoint matches instability limitation")
check(not re.search(r"分钟级生效|周级生效|大多数团队只做前两种|比稳定失败的任务更有价值|规则一多必然", lesson), "unsupported universal claims are absent")

# Check the illustrative JSON object remains parseable and contains tenant scope.
json_block = re.search(r"```json\s*(\{.*?\})\s*```", lesson, re.S)
check(json_block is not None, "knowledge record example exists")
record = json.loads(json_block.group(1)) if json_block else {}
check(record.get("scope") == {"tenant_id": "tenant-7", "customer_id": "88213"}, "knowledge example scope parses")
check(record.get("source") and record.get("written_at") and record.get("expires_at"), "knowledge example retains provenance and lifecycle fields")

python_blocks = re.findall(r"```python\s*(.*?)```", lesson, re.S)
check(len(python_blocks) == 2, "the lesson has classifier plus failure-case Python examples")
run = subprocess.run([sys.executable, "-c", python_blocks[0]], capture_output=True, text=True, timeout=10, check=True)
check("金额超 100 才退款" in run.stdout and "-> 程序" in run.stdout, "rule example executes as documented")
check("这个客户是 VIP" in run.stdout and "-> 知识" in run.stdout, "fact example executes as documented")
check("什么样的回答算得体" in run.stdout and "-> 参数" in run.stdout, "classifier fallback is shown as a candidate, not a mandate")

print(f"offline assertions passed: {checks}; providerCalls=0; historicalRunsReplayed=0")
