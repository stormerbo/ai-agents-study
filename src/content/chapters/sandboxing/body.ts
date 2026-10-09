// 编译期护栏：客户端组件导入这个模块会直接构建失败。
import 'server-only';

/** 章 16（沙箱与权限）的正文加载器。 */
export const bodies = {
  'why-isolate': () => import('./01-why-isolate.mdx'),
  'isolation-levels': () => import('./02-isolation-levels.mdx'),
  'least-privilege': () => import('./03-least-privilege.mdx'),
  'secrets': () => import('./04-secrets.mdx'),
  'execution-policy': () => import('./05-execution-policy.mdx'),
} as const;
