// 编译期护栏：客户端组件导入这个模块会直接构建失败。
import 'server-only';

/** 章 14（MCP）的正文加载器。 */
export const bodies = {
  'why-protocol': () => import('./01-why-protocol.mdx'),
  'roles-and-capabilities': () => import('./02-roles-and-capabilities.mdx'),
  'stateless-2026': () => import('./03-stateless-2026.mdx'),
  'build-a-server': () => import('./04-build-a-server.mdx'),
  'security-boundary': () => import('./05-security-boundary.mdx'),
  'remote-authorization': () => import('./06-remote-authorization.mdx'),
} as const;
