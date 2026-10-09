// 编译期护栏：客户端组件导入这个模块会直接构建失败。
import 'server-only';

/** 章 18（成本与延迟）的正文加载器。 */
export const bodies = {
  'cost-model': () => import('./01-cost-model.mdx'),
  'latency-sources': () => import('./02-latency-sources.mdx'),
  'caching': () => import('./03-caching.mdx'),
  'routing': () => import('./04-routing.mdx'),
  'budget-guardrails': () => import('./05-budget-guardrails.mdx'),
} as const;
