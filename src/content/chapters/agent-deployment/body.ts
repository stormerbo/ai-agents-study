// 编译期护栏：客户端组件导入这个模块会直接构建失败。
import 'server-only';

/** 章 20（部署与交付）的正文加载器。 */
export const bodies = {
  'deployment-shape': () => import('./01-deployment-shape.mdx'),
  versioning: () => import('./02-versioning.mdx'),
  'incident-response': () => import('./03-incident-response.mdx'),
  'ops-loop': () => import('./04-ops-loop.mdx'),
  'recovery-drills': () => import('./05-recovery-drills.mdx'),
} as const;
