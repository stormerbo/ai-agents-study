/**
 * 站内「精读」正文的加载器。
 *
 * ## 为什么要有这个东西
 *
 * 资源库里的 48 条多半是英文外链 —— 每读一条都要跳出去、还要过语言关。
 * 这里给每条配一篇**中文精读**：讲清原文的核心结论与取舍，让读者不必跳转就能判断
 * 「这条值不值得细读、该读哪部分」。
 *
 * ## 为什么是「精读」而不是「全文翻译」
 *
 * 两个理由，第二个更重要：
 *
 * 1. **版权与 `AGENTS.md` 的既有决策** —— 项目明确写了「外部资源精确外链，不做爬虫抓取」。
 *    把整篇译文重新发布，既是版权问题，也正好是那条决策要避免的事。
 * 2. **精读比翻译更有用** —— 读者要的通常不是「逐句的中文」，而是「它说了什么、
 *    哪部分值得读、和我已知的有什么关系」。一篇 1200 字的精读能替代 8000 字的译文，
 *    而且顺带回答了「要不要读原文」这个问题。
 *
 * 原文链接始终保留在精读页顶部 —— 精读是**入口**，不是替代品。
 *
 * ## 登记方式
 *
 * 和 `src/lib/content/body.ts` 同一套：**显式逐个 import，不用 glob**。
 * 路径写错会在 `tsc` 阶段报错，而不是等运行时才发现某条精读凭空消失。
 */

import 'server-only';

type ReadingLoader = () => Promise<{ default: React.ComponentType }>;

const REGISTRY: Record<string, ReadingLoader> = {
  'ai-agents-from-zero': () => import('@/content/reading/ai-agents-from-zero.mdx'),
  'ai-engineering-huyen': () => import('@/content/reading/ai-engineering-huyen.mdx'),
  aider: () => import('@/content/reading/aider.mdx'),
  'anthropic-building-effective-agents': () =>
    import('@/content/reading/anthropic-building-effective-agents.mdx'),
  'anthropic-context-engineering': () =>
    import('@/content/reading/anthropic-context-engineering.mdx'),
  'anthropic-multi-agent-research': () =>
    import('@/content/reading/anthropic-multi-agent-research.mdx'),
  'anthropics-courses': () => import('@/content/reading/anthropics-courses.mdx'),
  'awesome-ai-agents': () => import('@/content/reading/awesome-ai-agents.mdx'),
  'chain-of-thought-paper': () => import('@/content/reading/chain-of-thought-paper.mdx'),
  'claude-academy': () => import('@/content/reading/claude-academy.mdx'),
  'claude-agent-sdk': () => import('@/content/reading/claude-agent-sdk.mdx'),
  'claude-api-docs': () => import('@/content/reading/claude-api-docs.mdx'),
  'claude-effort': () => import('@/content/reading/claude-effort.mdx'),
  'claude-messages-api': () => import('@/content/reading/claude-messages-api.mdx'),
  'claude-model-migration': () => import('@/content/reading/claude-model-migration.mdx'),
  'claude-models-overview': () => import('@/content/reading/claude-models-overview.mdx'),
  'claude-pricing': () => import('@/content/reading/claude-pricing.mdx'),
  'claude-prompt-caching': () => import('@/content/reading/claude-prompt-caching.mdx'),
  'claude-streaming': () => import('@/content/reading/claude-streaming.mdx'),
  'deeplearning-ai-courses': () => import('@/content/reading/deeplearning-ai-courses.mdx'),
  'deer-flow': () => import('@/content/reading/deer-flow.mdx'),
  dify: () => import('@/content/reading/dify.mdx'),
  'google-adk-docs': () => import('@/content/reading/google-adk-docs.mdx'),
  'hf-agents-course': () => import('@/content/reading/hf-agents-course.mdx'),
  'hf-agents-course-zh': () => import('@/content/reading/hf-agents-course-zh.mdx'),
  'langchain-academy': () => import('@/content/reading/langchain-academy.mdx'),
  'langchain-docs': () => import('@/content/reading/langchain-docs.mdx'),
  'langchain-zh': () => import('@/content/reading/langchain-zh.mdx'),
  letta: () => import('@/content/reading/letta.mdx'),
  'lost-in-the-middle': () => import('@/content/reading/lost-in-the-middle.mdx'),
  'mcp-docs': () => import('@/content/reading/mcp-docs.mdx'),
  'mcp-spec-changelog': () => import('@/content/reading/mcp-spec-changelog.mdx'),
  mem0: () => import('@/content/reading/mem0.mdx'),
  'memgpt-paper': () => import('@/content/reading/memgpt-paper.mdx'),
  'ms-generative-ai-beginners': () => import('@/content/reading/ms-generative-ai-beginners.mdx'),
  'open-deep-research': () => import('@/content/reading/open-deep-research.mdx'),
  'openai-agents-sdk-python': () => import('@/content/reading/openai-agents-sdk-python.mdx'),
  'openai-chat-api': () => import('@/content/reading/openai-chat-api.mdx'),
  'openai-cookbook': () => import('@/content/reading/openai-cookbook.mdx'),
  openhands: () => import('@/content/reading/openhands.mdx'),
  'rag-paper': () => import('@/content/reading/rag-paper.mdx'),
  ragflow: () => import('@/content/reading/ragflow.mdx'),
  'react-paper': () => import('@/content/reading/react-paper.mdx'),
  'reflexion-paper': () => import('@/content/reading/reflexion-paper.mdx'),
  'roadmap-ai-engineer': () => import('@/content/reading/roadmap-ai-engineer.mdx'),
  'self-refine-paper': () => import('@/content/reading/self-refine-paper.mdx'),
  'toolformer-paper': () => import('@/content/reading/toolformer-paper.mdx'),
  'twelve-factor-agents': () => import('@/content/reading/twelve-factor-agents.mdx'),
};

/** 这条资源有站内精读吗。列表页用它决定要不要标「站内精读」。 */
export function hasReading(resourceId: string): boolean {
  return resourceId in REGISTRY;
}

/** 有精读的资源 id 列表 —— `generateStaticParams` 用。 */
export function readingIds(): string[] {
  return Object.keys(REGISTRY);
}

/** 取某条资源的精读组件。没有时返回 undefined。 */
export async function getReading(resourceId: string) {
  const loader = REGISTRY[resourceId];
  if (!loader) return undefined;
  const mod = await loader();
  return mod.default;
}
