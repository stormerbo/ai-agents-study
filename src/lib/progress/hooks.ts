'use client';

import { useSyncExternalStore } from 'react';
import type { LessonId } from '@/content/curriculum/schema';

import { getServerSnapshot, getSnapshot, subscribe, type ProgressState } from './store';

/**
 * 读取进度。
 *
 * 必须走 `useSyncExternalStore` —— 三个参数各有用处：
 *   · subscribe      进度变化时通知 React
 *   · getSnapshot    客户端读当前值
 *   · getServerSnapshot 服务端渲染时返回**同一个冻结对象**
 *
 * 第三个是关键：如果服务端每次返回新对象，React 会认为状态一直在变，
 * 触发无限重渲染。这也是本站 Playground 踩过的那个坑（§4.7）。
 */
export function useProgress(): ProgressState {
  return useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);
}

/** 这个 lesson 完成了吗。 */
export function useIsComplete(id: LessonId): boolean {
  const state = useProgress();
  return id in state.completed;
}

/** 一组 lesson 里完成了几个。 */
export function useCompletedCount(ids: readonly LessonId[]): number {
  const state = useProgress();
  let n = 0;
  for (const id of ids) if (id in state.completed) n++;
  return n;
}

/**
 * 是否已经水合完成。
 *
 * 用来避免「服务端渲染 0/117、客户端渲染 42/117」这种闪烁 ——
 * 首屏两者一致（都是空进度），水合之后再显示真实值。
 */
export function useHydrated(): boolean {
  return useSyncExternalStore(
    () => () => {},
    () => true,
    () => false,
  );
}
