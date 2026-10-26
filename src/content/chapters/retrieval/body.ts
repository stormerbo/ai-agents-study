// 编译期护栏：客户端组件导入这个模块会直接构建失败。
import 'server-only';

/** 章 6（检索）的正文加载器。key 必须与 meta.ts 里 lesson 的 slug 一致。 */
export const bodies = {
  'why-retrieval': () => import('./01-why-retrieval.mdx'),
  chunking: () => import('./02-chunking.mdx'),
  'vector-limits': () => import('./03-vector-limits.mdx'),
  'evaluating-retrieval': () => import('./04-evaluating-retrieval.mdx'),
  'agentic-retrieval': () => import('./05-agentic-retrieval.mdx'),
  'index-lifecycle': () => import('./06-index-lifecycle.mdx'),
  'permission-filtering': () => import('./07-permission-filtering.mdx'),
} as const;
