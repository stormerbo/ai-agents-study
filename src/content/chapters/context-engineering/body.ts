// 编译期护栏：客户端组件导入这个模块会直接构建失败。
import 'server-only';

/** 章 3（上下文工程）的正文加载器。key 必须与 meta.ts 里 lesson 的 slug 一致。 */
export const bodies = {
  'context-is-finite': () => import('./01-context-is-finite.mdx'),
} as const;
