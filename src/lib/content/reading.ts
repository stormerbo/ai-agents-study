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
  'anthropic-building-effective-agents': () =>
    import('@/content/reading/anthropic-building-effective-agents.mdx'),
  'anthropic-context-engineering': () =>
    import('@/content/reading/anthropic-context-engineering.mdx'),
  'claude-api-docs': () => import('@/content/reading/claude-api-docs.mdx'),
  'claude-models-overview': () => import('@/content/reading/claude-models-overview.mdx'),
  'claude-messages-api': () => import('@/content/reading/claude-messages-api.mdx'),
  'claude-streaming': () => import('@/content/reading/claude-streaming.mdx'),
  'claude-model-migration': () => import('@/content/reading/claude-model-migration.mdx'),
  'hf-agents-course-zh': () => import('@/content/reading/hf-agents-course-zh.mdx'),
  'lost-in-the-middle': () => import('@/content/reading/lost-in-the-middle.mdx'),
  'mcp-spec-changelog': () => import('@/content/reading/mcp-spec-changelog.mdx'),
  'react-paper': () => import('@/content/reading/react-paper.mdx'),
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
