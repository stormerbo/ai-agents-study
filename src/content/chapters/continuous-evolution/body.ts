// 编译期护栏：客户端组件导入这个模块会直接构建失败。
import 'server-only';

/** 章 24（持续进化）的正文加载器。 */
export const bodies = {
  'from-traces': () => import('./01-from-traces.mdx'),
  'distill-and-test': () => import('./02-distill-and-test.mdx'),
} as const;
