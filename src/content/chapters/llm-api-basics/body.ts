// 编译期护栏：这个模块一旦被客户端组件导入，构建会直接失败。
// 章节树、知识地图、进度组件都要读 meta.ts，很容易顺手把 body 也带进去 ——
// 那会让整棵内容树的 MDX 编译产物进入浏览器 bundle。
import 'server-only';

/**
 * 章 1 的正文加载器。
 *
 * 用**显式写死的 lazy import**，不用 `import(`./${slug}.mdx`)` 这类模板串：
 * - 模板串会生成一个覆盖整个目录的 context module，把所有 MDX 都纳入编译图
 * - 路径写错时会在 tsc 阶段就报错，而不是等到运行时才发现某一节打不开
 * - 「这一章写了哪几节」在代码里一眼可见
 *
 * key 必须与 meta.ts 里 lesson 的 slug 一致 —— tests/curriculum.test.ts
 * 会校验两边是否对齐。
 */
export const bodies = {
  'tokens-and-context': () => import('./01-tokens-and-context.mdx'),
  'sampling-params': () => import('./02-sampling-params.mdx'),
  'messages-api': () => import('./03-messages-api.mdx'),
  'model-selection': () => import('./04-model-selection.mdx'),
  'prompt-caching': () => import('./05-prompt-caching.mdx'),
} as const;
