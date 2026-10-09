// 编译期护栏：客户端组件导入这个模块会直接构建失败。
import 'server-only';

/** 章 19（人机协作）的正文加载器。 */
export const bodies = {
  'automation-levels': () => import('./01-automation-levels.mdx'),
  'approval-design': () => import('./02-approval-design.mdx'),
  'interrupt-and-resume': () => import('./03-interrupt-and-resume.mdx'),
  'progress-and-trust': () => import('./04-progress-and-trust.mdx'),
  'streaming-and-control': () => import('./05-streaming-and-control.mdx'),
} as const;
