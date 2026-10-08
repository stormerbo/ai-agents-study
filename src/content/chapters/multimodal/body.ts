// 编译期护栏：客户端组件导入这个模块会直接构建失败。
import 'server-only';

/** 章 8（多模态输入）的正文加载器。key 必须与 meta.ts 里 lesson 的 slug 一致。 */
export const bodies = {
  'how-images-enter-context': () => import('./01-how-images-enter-context.mdx'),
  'document-routes': () => import('./02-document-routes.mdx'),
  'resolution-and-cost': () => import('./03-resolution-and-cost.mdx'),
  'when-vision-fails': () => import('./04-when-vision-fails.mdx'),
  'vision-in-the-loop': () => import('./05-vision-in-the-loop.mdx'),
} as const;
