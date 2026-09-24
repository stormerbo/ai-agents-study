'use client';

import { useTheme } from 'next-themes';
import { useSyncExternalStore } from 'react';

const OPTIONS = [
  { value: 'light', label: '浅色', icon: '☀' },
  { value: 'system', label: '跟随系统', icon: '◐' },
  { value: 'dark', label: '深色', icon: '☾' },
] as const;

/** 永不触发的订阅源 —— 我们只关心"是否已到客户端"，不关心后续变化 */
const subscribe = () => () => {};

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();

  /**
   * 判断当前是否已经挂载到客户端。
   *
   * 服务端并不知道用户选了什么主题，unmounted 时直接渲染"选中项"会造成
   * hydration mismatch。这里用 useSyncExternalStore 而非
   * useEffect + setState —— 后者在 effect 体内同步 setState 会触发级联渲染，
   * React 19 的 react-hooks/set-state-in-effect 规则会直接报错。
   * getServerSnapshot 返回 false、客户端返回 true，正是这个场景的标准解法。
   */
  const mounted = useSyncExternalStore(
    subscribe,
    () => true,
    () => false,
  );

  return (
    <div
      role="radiogroup"
      aria-label="主题"
      className="inline-flex items-center gap-0.5 rounded-full border border-border bg-muted/40 p-0.5"
    >
      {OPTIONS.map((opt) => {
        const active = mounted && theme === opt.value;
        return (
          <button
            key={opt.value}
            type="button"
            role="radio"
            aria-checked={active}
            aria-label={opt.label}
            title={opt.label}
            onClick={() => setTheme(opt.value)}
            className={`rounded-full px-2 py-1 text-xs leading-none transition-colors ${
              active
                ? 'bg-background text-foreground shadow-sm'
                : 'text-muted-foreground hover:text-foreground'
            }`}
          >
            <span aria-hidden>{opt.icon}</span>
          </button>
        );
      })}
    </div>
  );
}
