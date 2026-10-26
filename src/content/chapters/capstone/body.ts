// 编译期护栏：客户端组件导入这个模块会直接构建失败。
import 'server-only';

/** 章 22（综合项目）的正文加载器。 */
export const bodies = {
  scope: () => import('./01-scope.mdx'),
  skeleton: () => import('./02-skeleton.mdx'),
  hardening: () => import('./03-hardening.mdx'),
  deliver: () => import('./04-deliver.mdx'),
  retrospective: () => import('./05-retrospective.mdx'),
  acceptance: () => import('./06-acceptance.mdx'),
} as const;
