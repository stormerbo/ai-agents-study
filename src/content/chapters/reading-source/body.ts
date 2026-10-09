// 编译期护栏：客户端组件导入这个模块会直接构建失败。
import 'server-only';

/** 章 21（源码研读）的正文加载器。 */
export const bodies = {
  'why-and-how': () => import('./01-why-and-how.mdx'),
  'picking-projects': () => import('./02-picking-projects.mdx'),
  'trace-one-task': () => import('./03-trace-one-task.mdx'),
  'compare': () => import('./04-compare.mdx'),
  'outputs': () => import('./05-outputs.mdx'),
} as const;
