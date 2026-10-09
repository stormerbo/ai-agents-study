// 编译期护栏：客户端组件导入这个模块会直接构建失败。
import 'server-only';

/** 章 13（框架选型）的正文加载器。 */
export const bodies = {
  'what-frameworks-give': () => import('./01-what-frameworks-give.mdx'),
  'abstraction-models': () => import('./02-abstraction-models.mdx'),
  'leaky-abstractions': () => import('./03-leaky-abstractions.mdx'),
  'build-vs-buy': () => import('./04-build-vs-buy.mdx'),
  'selection-matrix': () => import('./05-selection-matrix.mdx'),
} as const;
