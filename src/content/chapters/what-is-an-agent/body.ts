// 编译期护栏：客户端组件导入这个模块会直接构建失败。
// 章节树 / 知识地图 / 进度组件都读 meta.ts，很容易顺手把正文也带进浏览器 bundle。
import 'server-only';

/** 章 0 的正文加载器。key 必须与 meta.ts 里 lesson 的 slug 一致。 */
export const bodies = {
  'why-now': () => import('./01-why-now.mdx'),
  'what-counts-as-agent': () => import('./02-what-counts-as-agent.mdx'),
  'mindset-shift': () => import('./03-mindset-shift.mdx'),
  'how-to-use-this-site': () => import('./04-how-to-use-this-site.mdx'),
} as const;
