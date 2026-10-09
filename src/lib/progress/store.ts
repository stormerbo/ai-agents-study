/**
 * 学习进度的浏览器端存储。
 *
 * ## 承诺与兑现
 *
 * 第 0-4 章告诉读者「本站会记住你的进度」。这个模块是那句话的实现。
 *
 * ## 为什么留一层 adapter
 *
 * AGENTS.md 里写过「进度存储预留服务端扩展接口」。这不是为了好看 ——
 * 它的实际作用是：**以后要加账号时，只需要换一个 adapter，UI 一行都不用改。**
 * 所以 UI 只依赖 `ProgressAdapter` 这个接口，不认识 localStorage。
 *
 * ## 三个必须处理对的点
 *
 * **1. getServerSnapshot 必须返回稳定引用。** 每次调用都返回新对象会让
 *    React 认为状态一直在变，触发无限重渲染。下面用一个冻结的模块级常量。
 *
 * **2. 服务端没有 localStorage。** 所有读取都要能安全降级，且首屏渲染
 *    必须与客户端首次渲染一致 —— 否则水合报错（§4.7 记录过本站踩的坑）。
 *
 * **3. 写入要能容错。** 隐私模式、配额满、被禁用 —— 任何一次写入失败
 *    都不该让页面崩掉。进度是可丢的，页面不是。
 */

import type { LessonId } from '@/content/curriculum/schema';

const STORAGE_KEY = 'aas.progress.v1';

export interface ProgressState {
  version: 1;
  /** lessonId → 标记完成的时间（ISO 8601）。用对象而不是数组，查询是 O(1)。 */
  completed: Record<string, string>;
}

/** 冻结的空状态 —— 服务端快照必须返回同一个引用，否则会无限重渲染。 */
export const EMPTY_PROGRESS: ProgressState = Object.freeze({
  version: 1 as const,
  completed: Object.freeze({}) as Record<string, string>,
});

export interface ProgressAdapter {
  load(): ProgressState;
  save(state: ProgressState): void;
}

/** localStorage 实现。以后换服务端实现时，替换这个对象即可。 */
export const localAdapter: ProgressAdapter = {
  load() {
    if (typeof window === "undefined") return EMPTY_PROGRESS;
    try {
      const raw = window.localStorage.getItem(STORAGE_KEY);
      if (!raw) return EMPTY_PROGRESS;
      const parsed = JSON.parse(raw) as Partial<ProgressState>;
      if (parsed?.version !== 1 || typeof parsed.completed !== "object" || parsed.completed === null) {
        return EMPTY_PROGRESS;
      }
      return { version: 1, completed: parsed.completed as Record<string, string> };
    } catch {
      // 解析失败（数据被别的脚本写坏、或存储被禁用）—— 当作空进度，不抛
      return EMPTY_PROGRESS;
    }
  },
  save(state) {
    if (typeof window === "undefined") return;
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    } catch {
      // 配额满 / 隐私模式 —— 静默失败。进度可丢，页面不能崩。
    }
  },
};

let adapter: ProgressAdapter = localAdapter;

/** 换用别的存储实现（供将来接服务端时使用）。 */
export function setProgressAdapter(next: ProgressAdapter): void {
  adapter = next;
  snapshot = next.load();
  listeners.forEach((fn) => fn());
}

let snapshot: ProgressState = EMPTY_PROGRESS;
const listeners = new Set<() => void>();

export function subscribe(fn: () => void): () => void {
  if (listeners.size === 0 && typeof window !== "undefined") {
    snapshot = adapter.load();      // 首次订阅时才真正读存储
  }
  listeners.add(fn);
  return () => {
    listeners.delete(fn);
  };
}

export function getSnapshot(): ProgressState {
  return snapshot;
}

/** 服务端渲染用：恒定返回冻结的空状态，保证首屏与服务端一致。 */
export function getServerSnapshot(): ProgressState {
  return EMPTY_PROGRESS;
}

function commit(next: ProgressState): void {
  snapshot = next;
  adapter.save(next);
  listeners.forEach((fn) => fn());
}

export function isComplete(id: LessonId): boolean {
  return id in snapshot.completed;
}

export function markComplete(id: LessonId): void {
  if (id in snapshot.completed) return;
  commit({
    version: 1,
    completed: { ...snapshot.completed, [id]: new Date().toISOString() },
  });
}

export function unmarkComplete(id: LessonId): void {
  if (!(id in snapshot.completed)) return;
  const { [id]: _removed, ...rest } = snapshot.completed;
  commit({ version: 1, completed: rest });
}

export function toggleComplete(id: LessonId): void {
  if (isComplete(id)) unmarkComplete(id);
  else markComplete(id);
}

/** 清空全部进度（设置页用）。 */
export function clearProgress(): void {
  commit({ version: 1, completed: {} });
}

export function countCompleted(ids: readonly LessonId[]): number {
  let n = 0;
  for (const id of ids) if (id in snapshot.completed) n++;
  return n;
}

/** 最近完成的若干节（用于「继续学习」）。 */
export function recentCompleted(limit = 5): { id: string; at: string }[] {
  return Object.entries(snapshot.completed)
    .sort((a, b) => (a[1] < b[1] ? 1 : -1))
    .slice(0, limit)
    .map(([id, at]) => ({ id, at }));
}
