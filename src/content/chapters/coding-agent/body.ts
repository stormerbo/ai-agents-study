// 编译期护栏：客户端组件导入这个模块会直接构建失败。
import 'server-only';

/** 章 23（Coding Agent）的正文加载器。 */
export const bodies = {
  'why-coding-agent': () => import('./01-why-coding-agent.mdx'),
  'search-strategy': () => import('./02-search-strategy.mdx'),
  'file-editing': () => import('./03-file-editing.mdx'),
  'error-recovery': () => import('./04-error-recovery.mdx'),
  safety: () => import('./05-safety.mdx'),
} as const;
