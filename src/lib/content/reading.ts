/**
 * 站内「精读」与「中文全文」的加载器。
 *
 * ## 两种内容，两条管线
 *
 * | | 来源 | 存法 | 怎么渲染 |
 * |---|---|---|---|
 * | **导读** | 本站原创 | `.mdx`，显式 import | MDX（手写内容，能用组件） |
 * | **中文全文** | 机器翻译 | `.zh.md`，`fs` 读 | `react-markdown`（见 `components/ui/markdown.tsx`） |
 *
 * 为什么译文不走 MDX：机器产出的 Markdown 里有原文的 `<tag>`、JSON 的 `{`、
 * README 的 `</details>`，还有**数量不保证成对的代码围栏**。实测九篇里七篇编译不过，
 * 而围栏一乱，转义方案也失效。分开处理之后两边都简单了。
 *
 * 为什么译文用 `fs` 而不是显式 import：它们是**机器生成的、会持续增加**，
 * 手维护列表必然漂移。导读是手写的，所以仍然显式 import —— 路径写错在 tsc 阶段就报错。
 *
 * ## 版权说明
 *
 * 译文仅供个人学习。译文页顶部会显示机器翻译声明与原文链接；
 * `AGENTS.md` §2 的「不做爬虫抓取」在本项目里被用户的明确要求覆盖，
 * **若将来公开部署，这批译文需要先解决授权问题**。
 */

import 'server-only';

import { readFileSync } from 'node:fs';
import { join } from 'node:path';

type ReadingLoader = () => Promise<{ default: React.ComponentType }>;

/** 中文导读（原创）：讲清结论与取舍，并给出「该读哪节」。 */
const DIGESTS: Record<string, ReadingLoader> = {
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

const READING_DIR = join(process.cwd(), 'src/content/reading');

/** 这条资源有站内导读吗。 */
export function hasReading(resourceId: string): boolean {
  return resourceId in DIGESTS;
}

/** 这条资源有中文全文吗。 */
export function hasTranslation(resourceId: string): boolean {
  return getTranslation(resourceId) !== undefined;
}

/** 取中文导读组件。没有时返回 undefined。 */
export async function getReading(resourceId: string) {
  const loader = DIGESTS[resourceId];
  if (!loader) return undefined;
  return (await loader()).default;
}

/** 取中文全文的原始 Markdown。没有时返回 undefined。 */
export function getTranslation(resourceId: string): string | undefined {
  try {
    return readFileSync(join(READING_DIR, resourceId + '.zh.md'), 'utf8');
  } catch {
    return undefined;
  }
}
