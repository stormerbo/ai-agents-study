// 编译期护栏：客户端组件导入这个模块会直接构建失败。
import 'server-only';

/** 章 17（安全与信任边界）的正文加载器。 */
export const bodies = {
  'injection-escalation': () => import('./01-injection-escalation.mdx'),
  'tools-as-untrusted-input': () => import('./02-tools-as-untrusted-input.mdx'),
  'supply-chain': () => import('./03-supply-chain.mdx'),
  exfiltration: () => import('./04-exfiltration.mdx'),
  'defense-in-depth': () => import('./05-defense-in-depth.mdx'),
} as const;
