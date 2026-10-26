"""W6 scope audit of Agent Skills claims, provider roles, and historical evidence."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "src/content/chapters/context-engineering/08-agent-skills.mdx"
META = ROOT / "src/content/chapters/context-engineering/meta.ts"
RESOURCES = ROOT / "src/content/curriculum/resources.ts"
DATA = ROOT / "docs/DATA.md"
lesson = LESSON.read_text(encoding="utf-8")
meta = META.read_text(encoding="utf-8")
resources = RESOURCES.read_text(encoding="utf-8")
data = DATA.read_text(encoding="utf-8")
checks = 0


def check(condition: bool, message: str) -> None:
    global checks
    checks += 1
    assert condition, message


check("历史摘要：三种组织方式" in lesson, "old model results are marked historical")
check("实跑状态：本节未调用真实模型或平台 runtime" in lesson, "live execution status is disclosed")
check("逐次请求/响应、精确 endpoint 与模型版本、usage 原文、题目映射、评分器和聚合口径均未归档" in lesson, "missing provenance is explicit")
check("A/B 的分母是 5，C 的分母是 3" in lesson, "different denominators are disclosed")
check("不能证明“省 61% 且正确率不掉”" in lesson, "old quality-equivalence conclusion is withdrawn")
check("不是可迁移的节省预期" in lesson, "old savings percentages are not generalized")
check("旧解释把原因归结为" in lesson and "无法确认模型确实按字面处理" in lesson, "old dedupe attribution is qualified")
check("按需读取是一种可选设计" in lesson, "two-stage path is no longer universal")
check("不是 Agent Skills 的必需协议" in lesson, "runtime-specific choices are explicit")
check("Anthropic 的 Agent Skills 文档明确采用三级渐进披露" in lesson, "Anthropic behavior is scoped to its docs")
check("Responses API 的 shell skills 和 Agents API capability directories" in lesson, "OpenAI integration variants are mentioned")
check("OpenAI Responses API hosted shell 则把 `name`、`description` 和 `path` 放进 user prompt" in lesson, "OpenAI shell skill instruction role is distinguished from Anthropic system prompt metadata")
check("优先级与其他 user 提供的指令相同" in lesson, "OpenAI skill instructions are not mistaken for system-level authority")
check("skill 的指令会影响模型规划或工具使用" in lesson, "skill instructions are distinguished from pure metadata")
check("不等于授权策略或工作流引擎" in lesson, "skill is not presented as an authorization boundary")
check("Skill 不只是无害的提示词文本" in lesson, "security implications are covered")
check("来源、版本、所有文件、脚本行为、外部依赖与网络访问" in lesson, "supply-chain review scope is concrete")
check("真正执行边界重新授权" in lesson, "host-side authorization is required")
check("工具数实验直接外推成 skill 选择规律" in lesson, "tool-count results are not conflated with skill retrieval")
check("token 节省、时延和安全性都需要实测" in lesson, "quality/cost claims require target-system evaluation")
check("anthropic-agent-skills" in meta and "openai-agent-skills" in meta, "lesson metadata cites both providers")
check("https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview" in resources, "Anthropic official source is registered")
check("https://developers.openai.com/api/docs/guides/tools-skills" in resources, "OpenAI official source is registered")
check("Agent Skills 组织方式的历史对照（不可复核）" in data, "historical evidence register is updated")
check(not re.search(r"必须两阶段|模型没有这条规则，就退回了通用直觉", lesson), "unsupported universal and causal language is absent")

print(f"offline assertions passed: {checks}; providerCalls=0; historicalRunsReplayed=0")
