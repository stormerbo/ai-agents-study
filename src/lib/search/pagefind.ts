/**
 * Pagefind 的懒加载封装。
 *
 * ## 为什么要绕一下
 *
 * Pagefind 的索引是在 `next build` **之后**生成的，产物放在 `public/pagefind/`。
 * 所以 `pagefind.js` 在构建期**并不存在** —— 如果用静态字符串写 `import("/pagefind/pagefind.js")`，
 * 打包器会在构建时报 "Module not found"。
 *
 * 解法是把路径放进变量，并标记 `webpackIgnore` —— 让打包器跳过解析，
 * 把这个 import 原样留给浏览器。**这也是为什么它必须是懒加载**：
 * 只有用户真的打开搜索框时才去拉那份 JS（约几十 KB），首屏不受影响。
 */

export interface PagefindResultData {
  url: string;
  content: string;
  word_count: number;
  filters: Record<string, string[]>;
  meta: Record<string, string>;
  /** 带高亮标记的摘录 HTML，由 Pagefind 生成 */
  excerpt: string;
  raw_url?: string;
  sub_results?: PagefindSubResult[];
}

export interface PagefindSubResult {
  title: string;
  url: string;
  excerpt: string;
}

export interface PagefindSearchResult {
  id: string;
  score: number;
  words: string[];
  data: () => Promise<PagefindResultData>;
}

interface PagefindModule {
  search: (query: string) => Promise<{ results: PagefindSearchResult[] }>;
  options?: (opts: Record<string, unknown>) => Promise<void>;
  init?: () => Promise<void>;
}

const PAGEFIND_PATH = "/pagefind/pagefind.js";

let cached: Promise<PagefindModule> | null = null;

export function loadPagefind(): Promise<PagefindModule> {
  if (!cached) {
    // 路径在变量里、并且标了 webpackIgnore —— 打包器不解析，浏览器直接 import
    cached = import(/* webpackIgnore: true */ PAGEFIND_PATH) as Promise<PagefindModule>;
  }
  return cached;
}

/** 索引还没生成时（比如本地 `pnpm dev` 且没跑过 build-search），给出可读的提示。 */
export function isSearchAvailable(): boolean {
  return typeof window !== "undefined";
}
