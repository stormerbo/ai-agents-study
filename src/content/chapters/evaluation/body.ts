// 编译期护栏：客户端组件导入这个模块会直接构建失败。
import 'server-only';

/** 章 15（评估与可观测性）的正文加载器。 */
export const bodies = {
  'define-good': () => import('./01-define-good.mdx'),
  dataset: () => import('./02-dataset.mdx'),
  'llm-as-judge': () => import('./03-llm-as-judge.mdx'),
  traces: () => import('./04-traces.mdx'),
  regression: () => import('./05-regression.mdx'),
} as const;
