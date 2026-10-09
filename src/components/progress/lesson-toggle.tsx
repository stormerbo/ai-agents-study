'use client';

import type { LessonId } from '@/content/curriculum/schema';
import { cn } from '@/lib/utils';

import { useHydrated, useIsComplete } from '@/lib/progress/hooks';
import { toggleComplete } from '@/lib/progress/store';

/** 节末尾的「标记完成」按钮。 */
export function LessonToggle({ lessonId }: { lessonId: LessonId }) {
  const done = useIsComplete(lessonId);
  const hydrated = useHydrated();

  // 水合前不渲染真实状态，避免服务端（未完成）与客户端（已完成）不一致
  if (!hydrated) {
    return <div className="h-9" aria-hidden />;
  }

  return (
    <button
      type="button"
      onClick={() => toggleComplete(lessonId)}
      aria-pressed={done}
      className={cn(
        'inline-flex items-center gap-2 rounded-md border px-3.5 py-2 text-sm transition-colors',
        done
          ? 'border-emerald-600/40 bg-emerald-600/10 text-emerald-700 dark:text-emerald-500'
          : 'border-border hover:bg-muted text-muted-foreground hover:text-foreground',
      )}
    >
      <span aria-hidden className="font-mono text-xs">
        {done ? '✓' : '○'}
      </span>
      {done ? '已学完' : '标记为已学完'}
    </button>
  );
}
