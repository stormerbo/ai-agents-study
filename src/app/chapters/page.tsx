import type { Metadata } from 'next';
import Link from 'next/link';
import type { CSSProperties } from 'react';

import { getChapters, getChaptersByStage, getStages } from '@/content/curriculum';
import { InlineMd } from '@/components/ui/inline-md';
import { ProgressBar } from '@/components/progress/progress-bar';
import { getChapterBodyLabel } from '@/lib/curriculum/presentation';
import { DIFFICULTY_LABEL, formatMinutes } from '@/lib/labels';

export const metadata: Metadata = {
  title: '章节',
  description: 'AI Agent 学习路径的全部章节，按学习阶段分组。',
};

export default function ChaptersPage() {
  const stages = getStages();
  // 总体进度的分母：全书所有节
  const allLessonIds = getChapters().flatMap((c) => c.lessons.map((l) => l.id));

  return (
    <main className="mx-auto max-w-6xl px-6 py-10">
      <header className="max-w-3xl">
        <h1 className="text-2xl font-semibold tracking-tight">章节</h1>
        <p className="mt-3 leading-relaxed text-muted-foreground">
          按学习阶段分组。每个阶段都有自己的定位与出阶段时应达到的状态。
        </p>
        <div className="mt-5 max-w-md">
          <ProgressBar lessonIds={allLessonIds} />
          <p className="mt-2 text-xs text-muted-foreground/70">
            进度只存在这台设备的浏览器里，不上传、不需要账号。
          </p>
        </div>
      </header>

      <div className="mt-10 space-y-12">
        {stages.map((stage) => {
          const stageChapters = getChaptersByStage(stage.id);
          const stageStyle = {
            '--stage-color': `var(--color-${stage.colorToken})`,
          } as CSSProperties;

          return (
            <section key={stage.id} style={stageStyle}>
              <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
                <span
                  data-stage-label
                  className="text-sm font-medium"
                  style={{ color: 'var(--stage-color)' }}
                >
                  阶段 {stage.order}
                </span>
                <h2 className="text-lg font-semibold">{stage.title}</h2>
                <span className="text-sm text-muted-foreground">{stage.tagline}</span>
              </div>

              <p className="mt-2.5 max-w-3xl text-sm leading-relaxed text-muted-foreground">
                {stage.summary}
              </p>

              {stageChapters.length > 0 ? (
                <ul className="mt-5 grid gap-3 sm:grid-cols-2">
                  {stageChapters.map((chapter) => {
                    const bodyLabel = getChapterBodyLabel(chapter.lessons);
                    const checkpointCount = chapter.lessons.reduce(
                      (sum, l) => sum + (l.checkpoints?.length ?? 0),
                      0,
                    );

                    return (
                      <li key={chapter.id}>
                        <Link
                          href={`/chapters/${chapter.id}`}
                          className="focus-visible:ring-ring flex h-full min-h-11 flex-col rounded-xl border border-border bg-card p-4 break-words transition-colors hover:border-accent/60 focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-offset-background focus-visible:outline-none"
                        >
                          <div className="flex flex-wrap items-baseline gap-x-2.5 gap-y-1">
                            <span
                              data-chapter-order
                              className="shrink-0 text-sm font-medium text-accent"
                            >
                              第 {chapter.order} 章
                            </span>
                            <span className="min-w-0 text-sm font-medium break-words">
                              {chapter.title}
                            </span>
                          </div>
                          <span
                            data-chapter-body-label
                            className="mt-1 inline-flex text-xs text-muted-foreground"
                          >
                            {bodyLabel}
                          </span>

                          <p className="mt-2 flex-1 text-sm leading-relaxed break-words text-muted-foreground">
                            <InlineMd text={chapter.summary} />
                          </p>

                          <div
                            data-chapter-metadata
                            className="mt-3 flex flex-wrap items-center gap-x-3 gap-y-1 text-[11px] text-muted-foreground"
                          >
                            <span>{DIFFICULTY_LABEL[chapter.difficulty]}</span>
                            <span>{formatMinutes(chapter.estimatedMinutes)}</span>
                            <span>{chapter.lessons.length} 节</span>
                            {checkpointCount > 0 && <span>自检 {checkpointCount}</span>}
                          </div>
                        </Link>
                      </li>
                    );
                  })}
                </ul>
              ) : (
                <p className="mt-5 rounded-xl border border-dashed border-border px-4 py-6 text-center text-sm text-muted-foreground">
                  这一阶段的内容还在整理中
                </p>
              )}
            </section>
          );
        })}
      </div>
    </main>
  );
}
