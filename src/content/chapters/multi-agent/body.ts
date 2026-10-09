// 编译期护栏：客户端组件导入这个模块会直接构建失败。
import 'server-only';

/** 章 12（多智能体）的正文加载器。 */
export const bodies = {
  'topologies': () => import('./01-topologies.mdx'),
  'cost-model': () => import('./02-cost-model.mdx'),
  'isolation-is-the-point': () => import('./03-isolation-is-the-point.mdx'),
  'failure-modes': () => import('./04-failure-modes.mdx'),
  'alternatives': () => import('./05-alternatives.mdx'),
} as const;
