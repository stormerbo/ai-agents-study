// 编译期护栏：客户端组件导入这个模块会直接构建失败。
import 'server-only';

/** 章 7（记忆）的正文加载器。key 必须与 meta.ts 里 lesson 的 slug 一致。 */
export const bodies = {
  'context-is-not-memory': () => import('./01-context-is-not-memory.mdx'),
  'what-to-write': () => import('./02-what-to-write.mdx'),
  'when-to-recall': () => import('./03-when-to-recall.mdx'),
  'forgetting-and-conflict': () => import('./04-forgetting-and-conflict.mdx'),
  'memory-cost-and-eval': () => import('./05-memory-cost-and-eval.mdx'),
} as const;
