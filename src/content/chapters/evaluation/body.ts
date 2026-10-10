// 编译期护栏：客户端组件导入这个模块会直接构建失败。
import 'server-only';

/** 章 15（评估与可观测性）的正文加载器。 */
export const bodies = {
  'define-good': () => import('./01-define-good.mdx'),
  'pass-k': () => import('./02-pass-k.mdx'),
  dataset: () => import('./03-dataset.mdx'),
  contamination: () => import('./04-contamination.mdx'),
  'llm-as-judge': () => import('./05-llm-as-judge.mdx'),
  traces: () => import('./06-traces.mdx'),
  regression: () => import('./07-regression.mdx'),
} as const;
