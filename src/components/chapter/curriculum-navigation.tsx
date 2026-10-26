import Link from 'next/link';

import { CurriculumNavigationShell } from './curriculum-navigation-shell';

import { getChapters, getChaptersByStage, getStages } from '@/content/curriculum';
import type { Chapter, Stage } from '@/content/curriculum/schema';

type CurriculumData = {
  stages: Stage[];
  chapters: Chapter[];
};

type CurriculumNavigationProps = {
  currentStageId: string;
  currentChapterId: string;
  currentLessonId: string;
  /** Injectable registry-shaped fixture for the synchronous SSR contract tests. */
  curriculum?: CurriculumData;
};

export function CurriculumNavigation({
  currentStageId,
  currentChapterId,
  currentLessonId,
  curriculum,
}: CurriculumNavigationProps) {
  const stages = curriculum?.stages ?? getStages();
  const chapters = curriculum?.chapters ?? getChapters();

  return (
    <CurriculumNavigationShell>
      <nav aria-label="课程目录" className="text-sm">
        <ul className="space-y-1">
          {stages.map((stage) => {
            const stageChapters = curriculum
              ? chapters.filter((chapter) => chapter.stageId === stage.id)
              : getChaptersByStage(stage.id);

            return (
              <li key={stage.id}>
                <details
                  data-stage-id={stage.id}
                  open={stage.id === currentStageId}
                  className="group border-l-2 pl-2"
                  style={{ borderInlineStartColor: 'var(--color-' + stage.colorToken + ')' }}
                >
                  <summary className="min-h-11 cursor-pointer list-none rounded-sm px-2 py-2 leading-7 font-medium marker:hidden focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent">
                    <span>{stage.title}</span>
                    <span className="ml-2 text-xs font-normal text-muted-foreground">
                      {stage.tagline}
                    </span>
                  </summary>
                  <ul className="space-y-1 pl-2">
                    {stageChapters.map((chapter) => (
                      <li key={chapter.id} className="border-l border-border/70 pl-2">
                        <Link
                          href={'/chapters/' + chapter.id}
                          data-chapter-link
                          className="flex min-h-11 items-center rounded-sm px-2 py-2 leading-5 text-foreground underline-offset-4 hover:text-accent hover:underline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
                        >
                          第 {chapter.order} 章 · {chapter.title}
                        </Link>
                        <details
                          data-chapter-id={chapter.id}
                          open={chapter.id === currentChapterId}
                        >
                          <summary className="min-h-11 cursor-pointer list-none rounded-sm px-2 py-2 text-muted-foreground marker:hidden hover:text-foreground focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent">
                            <span className="sr-only">展开《{chapter.title}》小节</span>
                            <span aria-hidden>小节</span>
                            <span className="ml-1 text-xs">({chapter.lessons.length})</span>
                          </summary>
                          <ul className="space-y-1 border-l border-border/70 pl-3">
                            {chapter.lessons.map((lesson) => {
                              const isCurrent = lesson.id === currentLessonId;
                              return (
                                <li key={lesson.id}>
                                  <Link
                                    href={'/chapters/' + chapter.id + '/' + lesson.slug}
                                    data-lesson-link
                                    aria-current={isCurrent ? 'page' : undefined}
                                    className="flex min-h-11 items-center rounded-sm px-2 py-2 leading-5 text-muted-foreground underline-offset-4 hover:text-foreground hover:underline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent aria-[current=page]:font-medium aria-[current=page]:text-accent"
                                  >
                                    {lesson.title}
                                  </Link>
                                </li>
                              );
                            })}
                          </ul>
                        </details>
                      </li>
                    ))}
                  </ul>
                </details>
              </li>
            );
          })}
        </ul>
      </nav>
    </CurriculumNavigationShell>
  );
}
