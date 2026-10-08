// 编译期护栏：客户端组件导入这个模块会直接构建失败。
import 'server-only';

/** 章 5（结构化输出）的正文加载器。key 必须与 meta.ts 里 lesson 的 slug 一致。 */
export const bodies = {
  'why-not-prompt-only': () => import('./01-why-not-prompt-only.mdx'),
  'json-schema-strict': () => import('./02-json-schema-strict.mdx'),
  'validation-retry': () => import('./03-validation-retry.mdx'),
  'beyond-json': () => import('./04-beyond-json.mdx'),
} as const;
