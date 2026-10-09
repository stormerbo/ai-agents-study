// 编译期护栏：客户端组件导入这个模块会直接构建失败。
import 'server-only';

/** 章 2（Prompt 工程）的正文加载器。key 必须与 meta.ts 里 lesson 的 slug 一致。 */
export const bodies = {
  'instruction-clarity': () => import('./01-instruction-clarity.mdx'),
  'structure-and-separation': () => import('./02-structure-and-separation.mdx'),
  'few-shot': () => import('./03-few-shot.mdx'),
  'chain-of-thought': () => import('./04-chain-of-thought.mdx'),
  reliability: () => import('./05-reliability.mdx'),
} as const;
