// 编译期护栏：客户端组件导入这个模块会直接构建失败。
import 'server-only';

/** 章 21（工具与上手）的正文加载器。 */
export const bodies = {
  'retrieval-stack': () => import('./01-retrieval-stack.mdx'),
  'orchestration-stack': () => import('./02-orchestration-stack.mdx'),
  'local-models': () => import('./03-local-models.mdx'),
  'first-agent': () => import('./04-first-agent.mdx'),
  'agent-ui': () => import('./05-agent-ui.mdx'),
} as const;
