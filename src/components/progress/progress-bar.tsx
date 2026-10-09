'use client';

import type { LessonId } from '@/content/curriculum/schema';
import { cn } from '@/lib/utils';

import { useCompletedCount, useHydrated } from '@/lib/progress/hooks';

/**
 * 细进度条。**水合前渲染成 0 宽**，避免服务端与客户端宽度不一致。
 */
export function ProgressBar({
  lessonIds,
  className,
  showLabel = true,
}: {
  lessonIds: readonly LessonId[];
  className?: string;
  showLabel?: boolean;
}) {
  const done = useCompletedCount(lessonIds);
  const hydrated = useHydrated();
  const total = lessonIds.length;
  const shown = hydrated ? done : 0;
  const pct = total === 0 ? 0 : Math.round((shown / total) * 100);

  return (
    <div className={cn('flex items-center gap-2.5', className)}>
      <div
        className="bg-muted h-1.5 w-full min-w-16 overflow-hidden rounded-full"
        role="progressbar"
        aria-valuenow={pct}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label="学习进度"
      >
        <div
          className={cn(
            'h-full rounded-full transition-[width] duration-300',
            pct === 100 ? 'bg-emerald-600' : 'bg-accent',
          )}
          style={{ width: `${pct}%` }}
        />
      </div>
      {showLabel && (
        <span className="text-muted-foreground shrink-0 font-mono text-xs tabular-nums">
          {shown}/{total}
        </span>
      )}
    </div>
  );
}
