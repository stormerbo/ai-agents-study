// 编译期护栏：客户端组件导入这个模块会直接构建失败。
import 'server-only';

/** 章 3（上下文工程）的正文加载器。 */
export const bodies = {
  'context-is-finite': () => import('./01-context-is-finite.mdx'),
  'system-prompt-altitude': () => import('./02-system-prompt-altitude.mdx'),
  'just-in-time': () => import('./03-just-in-time.mdx'),
  compaction: () => import('./04-compaction.mdx'),
  'subagent-isolation': () => import('./05-subagent-isolation.mdx'),
  'chat-template': () => import('./06-chat-template.mdx'),
  'kv-cache': () => import('./07-kv-cache.mdx'),
  'agent-skills': () => import('./08-agent-skills.mdx'),
} as const;
