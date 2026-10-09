// 编译期护栏：客户端组件导入这个模块会直接构建失败。
import 'server-only';

/** 章 9（计算机使用）的正文加载器。key 必须与 meta.ts 里 lesson 的 slug 一致。 */
export const bodies = {
  'what-differs': () => import('./01-what-differs.mdx'),
  'observe-act-loop': () => import('./02-observe-act-loop.mdx'),
  'failure-modes': () => import('./03-failure-modes.mdx'),
  'safety-and-scope': () => import('./04-safety-and-scope.mdx'),
  'when-not-to-use': () => import('./05-when-not-to-use.mdx'),
} as const;
