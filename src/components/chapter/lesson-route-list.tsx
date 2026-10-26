'use client';

import Link from 'next/link';

import type { ChapterId, Lesson } from '@/content/curriculum/schema';
import { getLessonBodyLabel } from '@/lib/curriculum/presentation';
import { useHydrated, useProgress } from '@/lib/progress/hooks';
import { InlineMd } from '@/components/ui/inline-md';

/** A single-column ordered chapter route with locally stored completion state. */
export function LessonRouteList({
  chapterId,
  lessons,
}: {
  chapterId: ChapterId;
  lessons: readonly Lesson[];
}) {
  const progress = useProgress();
  const hydrated = useHydrated();

  return (
    <ol className="mt-4 list-none space-y-1.5">
      {lessons.map((lesson, index) => {
        const isComplete = lesson.id in progress.completed;

        return (
          <li key={lesson.id}>
            <Link
              href={`/chapters/${chapterId}/${lesson.slug}`}
              className="group focus-visible:ring-ring flex min-h-11 items-start gap-3 rounded-lg px-3 py-2.5 transition-colors hover:bg-muted/60 focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-offset-background focus-visible:outline-none"
            >
              <span
                aria-label={`第 ${index + 1} 节`}
                className="mt-0.5 shrink-0 text-sm font-medium text-accent tabular-nums"
              >
                {index + 1}
              </span>
              <span className="min-w-0 flex-1">
                <span className="block text-sm font-medium break-words text-foreground group-hover:text-accent">
                  {lesson.title}
                </span>
                {lesson.summary && (
                  <span className="mt-1 block text-xs leading-relaxed break-words text-muted-foreground">
                    <InlineMd text={lesson.summary} />
                  </span>
                )}
                <span className="mt-2 flex flex-wrap gap-x-3 gap-y-1 text-xs text-muted-foreground">
                  <span>{lesson.estimatedMinutes} 分钟</span>
                  <span>{getLessonBodyLabel(lesson)}</span>
                  <span>{hydrated ? (isComplete ? '已完成' : '未完成') : '进度读取中'}</span>
                </span>
              </span>
            </Link>
          </li>
        );
      })}
    </ol>
  );
}
