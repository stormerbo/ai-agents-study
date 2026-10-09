import 'server-only';

import type { ComponentType } from 'react';

import { bodies as contextEngineeringBodies } from '@/content/chapters/context-engineering/body';
import { bodies as llmApiBasicsBodies } from '@/content/chapters/llm-api-basics/body';
import { bodies as memoryBodies } from '@/content/chapters/memory/body';
import { bodies as multimodalBodies } from '@/content/chapters/multimodal/body';
import { bodies as computerUseBodies } from '@/content/chapters/computer-use/body';
import { bodies as agentParadigmsBodies } from '@/content/chapters/agent-paradigms/body';
import { bodies as agentLoopBodies } from '@/content/chapters/agent-loop/body';
import { bodies as multiAgentBodies } from '@/content/chapters/multi-agent/body';
import { bodies as agentFrameworksBodies } from '@/content/chapters/agent-frameworks/body';
import { bodies as mcpBodies } from '@/content/chapters/mcp/body';
import { bodies as evaluationBodies } from '@/content/chapters/evaluation/body';
import { bodies as sandboxingBodies } from '@/content/chapters/sandboxing/body';
import { bodies as agentSecurityBodies } from '@/content/chapters/agent-security/body';
import { bodies as costAndLatencyBodies } from '@/content/chapters/cost-and-latency/body';
import { bodies as humanInTheLoopBodies } from '@/content/chapters/human-in-the-loop/body';
import { bodies as agentDeploymentBodies } from '@/content/chapters/agent-deployment/body';
import { bodies as readingSourceBodies } from '@/content/chapters/reading-source/body';
import { bodies as capstoneBodies } from '@/content/chapters/capstone/body';
import { bodies as toolingBodies } from '@/content/chapters/tooling/body';
import { bodies as promptEngineeringBodies } from '@/content/chapters/prompt-engineering/body';
import { bodies as retrievalBodies } from '@/content/chapters/retrieval/body';
import { bodies as structuredOutputBodies } from '@/content/chapters/structured-output/body';
import { bodies as toolCallingBodies } from '@/content/chapters/tool-calling/body';
import { bodies as whatIsAnAgentBodies } from '@/content/chapters/what-is-an-agent/body';

/**
 * 正文加载器。
 *
 * 各章的 body.ts 单独存在、这里集中注册，是为了让**没有正文的章节**
 * 也能正常存在 —— 章节元数据（meta.ts）与正文（*.mdx）在物理上是分离的，
 * 知识地图与章节页可以完整呈现一章的大纲，即使它的正文还没写。
 *
 * 新增一章时：写 meta.ts → 写 body.ts → 在这里注册一行。
 */
type BodyLoader = () => Promise<{ default: ComponentType }>;

const REGISTRY: Record<string, Record<string, BodyLoader>> = {
  'what-is-an-agent': whatIsAnAgentBodies,
  'llm-api-basics': llmApiBasicsBodies,
  'prompt-engineering': promptEngineeringBodies,
  'context-engineering': contextEngineeringBodies,
  'tool-calling': toolCallingBodies,
  'structured-output': structuredOutputBodies,
  'retrieval': retrievalBodies,
  'memory': memoryBodies,
  'multimodal': multimodalBodies,
  'computer-use': computerUseBodies,
  'agent-paradigms': agentParadigmsBodies,
  'agent-loop': agentLoopBodies,
  'multi-agent': multiAgentBodies,
  'agent-frameworks': agentFrameworksBodies,
  'mcp': mcpBodies,
  'evaluation': evaluationBodies,
  'sandboxing': sandboxingBodies,
  'agent-security': agentSecurityBodies,
  'cost-and-latency': costAndLatencyBodies,
  'human-in-the-loop': humanInTheLoopBodies,
  'agent-deployment': agentDeploymentBodies,
  'reading-source': readingSourceBodies,
  'capstone': capstoneBodies,
  'tooling': toolingBodies,
};

/** 取某一节的正文组件。没写正文时返回 undefined（页面会渲染大纲占位）。 */
export async function getLessonBody(
  chapterId: string,
  lessonSlug: string,
): Promise<ComponentType | undefined> {
  const loader = REGISTRY[chapterId]?.[lessonSlug];
  if (!loader) return undefined;
  const mod = await loader();
  return mod.default;
}

/** 该章是否已经接了正文（用于一致性检查） */
export function hasBodyRegistry(chapterId: string): boolean {
  return chapterId in REGISTRY;
}
