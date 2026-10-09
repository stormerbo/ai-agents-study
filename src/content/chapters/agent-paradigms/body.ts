// 编译期护栏：客户端组件导入这个模块会直接构建失败。
import 'server-only';

/** 章 10（Agent 范式）的正文加载器。key 必须与 meta.ts 里 lesson 的 slug 一致。 */
export const bodies = {
  'five-paradigms': () => import('./01-five-paradigms.mdx'),
  'react-loop': () => import('./02-react-loop.mdx'),
  'plan-and-execute': () => import('./03-plan-and-execute.mdx'),
  reflection: () => import('./04-reflection.mdx'),
  choosing: () => import('./05-choosing.mdx'),
} as const;
