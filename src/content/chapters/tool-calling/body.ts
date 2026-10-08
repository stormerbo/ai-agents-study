// 编译期护栏：客户端组件导入这个模块会直接构建失败。
import 'server-only';

/** 章 4（Tool / Function Calling）的正文加载器。key 必须与 meta.ts 里 lesson 的 slug 一致。 */
export const bodies = {
  'what-really-happens': () => import('./01-what-really-happens.mdx'),
  'schema-design': () => import('./02-schema-design.mdx'),
  'poka-yoke': () => import('./03-poka-yoke.mdx'),
} as const;
