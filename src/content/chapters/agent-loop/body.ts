// 编译期护栏：客户端组件导入这个模块会直接构建失败。
import 'server-only';

/** 章 11（手写一个 Agent 循环）的正文加载器。 */
export const bodies = {
  'minimal-loop': () => import('./01-minimal-loop.mdx'),
  'tool-registry': () => import('./02-tool-registry.mdx'),
  'budgets-and-guards': () => import('./03-budgets-and-guards.mdx'),
  'state-and-resume': () => import('./04-state-and-resume.mdx'),
  'what-frameworks-do': () => import('./05-what-frameworks-do.mdx'),
} as const;
