import type { Metadata } from 'next';
import Link from 'next/link';
import { notFound } from 'next/navigation';

import { CheckpointList } from '@/components/chapter/checkpoint-list';
import { ProgressBar } from '@/components/progress/progress-bar';
import { ResourceSidebar } from '@/components/resource/resource-sidebar';
import { InlineMd, plainText } from '@/components/ui/inline-md';
import {
  getChapter,
  getChapters,
  getLabs,
  getProjectsByStage,
  getResources,
  getStage,
} from '@/content/curriculum';
import type { Chapter } from '@/content/curriculum/schema';
import { CONTENT_STATUS_LABEL, DIFFICULTY_LABEL, formatMinutes } from '@/lib/labels';

export function generateStaticParams() {
  return getChapters().map((chapter) => ({ chapterId: chapter.id }));
}

export async function generateMetadata(
  props: PageProps<'/chapters/[chapterId]'>,
): Promise<Metadata> {
  const { chapterId } = await props.params;
  const chapter = getChapter(chapterId);
  if (!chapter) return {};
  return { title: chapter.title, description: plainText(chapter.summary) };
}

// ---------------------------------------------------------------------------

function MetaItem({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-[11px] text-muted-foreground">{label}</dt>
      <dd className="mt-0.5 text-sm">{value}</dd>
    </div>
  );
}

function BackendMappingPanel({ chapter }: { chapter: Chapter }) {
  const { backendMapping } = chapter;

  return (
    <section className="rounded-xl border border-border bg-card p-5">
      <div className="flex items-baseline gap-2">
        <h2 className="text-sm font-medium">后端视角对照</h2>
        <span className="text-[11px] text-muted-foreground">
          迁移成本：
          {backendMapping.cost === 'low' ? '低' : backendMapping.cost === 'medium' ? '中' : '高'}
        </span>
      </div>

      <p className="mt-3 text-sm leading-relaxed">
        <span className="text-muted-foreground">一句话类比 —— </span>
        <InlineMd text={backendMapping.analogy} />
      </p>

      <div className="mt-5 grid gap-5 sm:grid-cols-2">
        <div>
          <h3 className="text-[11px] tracking-wide text-muted-foreground uppercase">
            可以直接迁移
          </h3>
          <ul className="mt-2.5 space-y-2">
            {backendMapping.transferable.map((item) => (
              <li key={item} className="flex gap-2 text-sm leading-relaxed">
                <span aria-hidden className="mt-px shrink-0 text-muted-foreground/50">
                  ·
                </span>
                <InlineMd text={item} />
              </li>
            ))}
          </ul>
        </div>

        <div>
          <h3 className="text-[11px] tracking-wide text-amber-600 uppercase dark:text-amber-500">
            会失效的直觉
          </h3>
          <ul className="mt-2.5 space-y-2">
            {backendMapping.pitfalls.map((item) => (
              <li key={item} className="flex gap-2 text-sm leading-relaxed">
                <span
                  aria-hidden
                  className="mt-px shrink-0 text-amber-600/60 dark:text-amber-500/60"
                >
                  !
                </span>
                <InlineMd text={item} />
              </li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  );
}

function CheckpointSummary({ chapter }: { chapter: Chapter }) {
  const groups = chapter.lessons
    .map((lesson) => ({ lesson, checkpoints: lesson.checkpoints ?? [] }))
    .filter((group) => group.checkpoints.length > 0);

  const total = groups.reduce((sum, group) => sum + group.checkpoints.length, 0);
  if (total === 0) return null;

  return (
    <section>
      <h2 className="text-sm font-medium">自检清单</h2>
      <p className="mt-1.5 text-xs text-muted-foreground">
        共 {total} 项。答不上来不是问题 —— 说明那一节值得再看一遍。
        每条答案都标注了依据类型，便于判断该信到什么程度。
      </p>
      <div className="mt-4 space-y-6">
        {groups.map(({ lesson, checkpoints }) => (
          <div key={lesson.id}>
            <h3 className="mb-2 text-xs text-muted-foreground">
              <Link
                href={`/chapters/${chapter.id}/${lesson.slug}`}
                className="hover:text-foreground"
              >
                来自《{lesson.title}》→
              </Link>
            </h3>
            <CheckpointList
              checkpoints={checkpoints}
              currentLessonId={lesson.id}
              currentChapterId={chapter.id}
            />
          </div>
        ))}
      </div>
    </section>
  );
}

// ---------------------------------------------------------------------------

export default async function ChapterPage(props: PageProps<'/chapters/[chapterId]'>) {
  const { chapterId } = await props.params;
  const chapter = getChapter(chapterId);
  if (!chapter) notFound();

  const stage = getStage(chapter.stageId);
  const resources = getResources(chapter.resourceIds);
  const labs = getLabs(chapter.labIds ?? []);
  const projects = getProjectsByStage(chapter.stageId).filter((p) =>
    chapter.projectIds?.includes(p.id),
  );
  const prerequisites = chapter.prerequisiteIds
    .map((id) => getChapter(id))
    .filter((c) => c !== undefined);
  const chapterIndex = getChapters().findIndex((c) => c.id === chapter.id);
  const prevChapter = chapterIndex > 0 ? getChapters()[chapterIndex - 1] : undefined;
  const nextChapter = getChapters()[chapterIndex + 1];
  const hasAnyBody = chapter.lessons.some((l) => l.hasBody);

  return (
    <main className="mx-auto max-w-6xl px-6 py-10">
      <div className="lg:grid lg:grid-cols-[minmax(0,1fr)_17rem] lg:items-start lg:gap-x-10">
        <div className="lg:col-start-1 lg:row-start-1">
          {/* 面包屑 */}
          <nav className="flex items-center gap-1.5 text-xs text-muted-foreground">
            <Link href="/chapters" className="hover:text-foreground">
              章节
            </Link>
            {stage && (
              <>
                <span aria-hidden>/</span>
                <span>{stage.title}</span>
              </>
            )}
          </nav>

          {/* 标题区 */}
          <header className="mt-5">
            <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
              <span className="font-mono text-sm text-muted-foreground tabular-nums">
                {String(chapter.order).padStart(2, '0')}
              </span>
              <h1 className="text-2xl font-semibold tracking-tight">{chapter.title}</h1>
            </div>
            {chapter.subtitle && <p className="mt-2 text-muted-foreground">{chapter.subtitle}</p>}
            <p className="mt-4 leading-relaxed">
              <InlineMd text={chapter.summary} />
            </p>
          </header>
        </div>

        {/* 本章资源 —— 桌面端固定在右栏，默认折叠；窄屏落到正文之后 */}
        <aside className="mt-8 lg:sticky lg:top-20 lg:col-start-2 lg:row-span-2 lg:row-start-1 lg:mt-0 lg:self-start">
          <ResourceSidebar resources={resources} title="本章延伸阅读" />
        </aside>

        {/* 正文主体 —— 桌面端在第 1 列第 2 行；窄屏排在侧栏之后 */}
        <div className="lg:col-start-1 lg:row-start-2">
          {/* 元信息 */}
          <dl className="mt-6 grid grid-cols-2 gap-4 border-y border-border py-4 sm:grid-cols-4">
            <MetaItem label="难度" value={DIFFICULTY_LABEL[chapter.difficulty]} />
            <MetaItem label="预计用时" value={formatMinutes(chapter.estimatedMinutes)} />
            <MetaItem label="小节" value={`${chapter.lessons.length} 节`} />
            <MetaItem
              label="正文状态"
              value={hasAnyBody ? CONTENT_STATUS_LABEL[chapter.status] : '大纲完成，正文待写'}
            />
          </dl>

          {!hasAnyBody && (
            <p className="mt-6 rounded-lg border border-border bg-muted/40 px-4 py-3 text-sm leading-relaxed text-muted-foreground">
              这一章的正文还在撰写中。但下面的大纲、资源与自检问题已经是可用的 ——
              你完全可以按小节标题自己去找答案，再用自检问题验证。
            </p>
          )}

          <div className="mt-10 space-y-12">
            {/* 学习目标 */}
            <section>
              <h2 className="text-sm font-medium">学完这一章你应该能做到</h2>
              <ul className="mt-4 space-y-2.5">
                {chapter.outcomes.map((outcome) => (
                  <li key={outcome} className="flex gap-2.5 text-sm leading-relaxed">
                    <span aria-hidden className="mt-px shrink-0 text-muted-foreground/50">
                      —
                    </span>
                    <span>{outcome}</span>
                  </li>
                ))}
              </ul>
            </section>

            {/* 后端视角对照 —— 全站差异化主线，放在最显眼的位置 */}
            <BackendMappingPanel chapter={chapter} />

            {/* 前置章节 */}
            {prerequisites.length > 0 && (
              <section>
                <h2 className="text-sm font-medium">建议先读</h2>
                <ul className="mt-3 flex flex-wrap gap-2">
                  {prerequisites.map((prereq) => (
                    <li key={prereq.id}>
                      <Link
                        href={`/chapters/${prereq.id}`}
                        className="inline-block rounded-md border border-border px-3 py-1.5 text-sm transition-colors hover:bg-muted"
                      >
                        {prereq.title}
                      </Link>
                    </li>
                  ))}
                </ul>
                <p className="mt-2.5 text-xs text-muted-foreground">
                  只是建议，不是门槛。你随时可以跳到真正需要的章节。
                </p>
              </section>
            )}

            {/* 小节大纲 */}
            <section>
              <div className="flex flex-wrap items-center justify-between gap-3">
                <h2 className="text-sm font-medium">小节</h2>
                <ProgressBar lessonIds={chapter.lessons.map((l) => l.id)} className="w-40" />
              </div>
              <ol className="mt-4 divide-y divide-border overflow-hidden rounded-xl border border-border">
                {chapter.lessons.map((lesson, i) => (
                  <li key={lesson.id}>
                    <Link
                      href={`/chapters/${chapter.id}/${lesson.slug}`}
                      className="flex items-baseline gap-3 px-4 py-3.5 transition-colors hover:bg-muted/50"
                    >
                      <span className="w-5 shrink-0 font-mono text-xs text-muted-foreground/50 tabular-nums">
                        {i + 1}
                      </span>
                      <span className="min-w-0 flex-1">
                        <span className="block text-sm font-medium">{lesson.title}</span>
                        {lesson.summary && (
                          <span className="mt-1 block text-xs leading-relaxed text-muted-foreground">
                            <InlineMd text={lesson.summary} />
                          </span>
                        )}
                      </span>
                      <span className="shrink-0 font-mono text-[11px] text-muted-foreground tabular-nums">
                        {lesson.estimatedMinutes} 分
                      </span>
                    </Link>
                  </li>
                ))}
              </ol>
            </section>

            {/* 代码实验 */}
            {labs.length > 0 && (
              <section>
                <h2 className="text-sm font-medium">代码实验</h2>
                <ul className="mt-4 space-y-3">
                  {labs.map((lab) => (
                    <li key={lab.id}>
                      <Link
                        href={`/labs/${lab.id}`}
                        className="block rounded-lg border border-border bg-card p-4 transition-colors hover:border-accent/60"
                      >
                        <div className="flex flex-wrap items-baseline gap-2">
                          <span className="text-sm font-medium">{lab.title}</span>
                          <span className="ml-auto text-[11px] text-muted-foreground">
                            约 {lab.estimatedMinutes} 分钟
                          </span>
                        </div>
                        <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                          <InlineMd text={lab.goal} />
                        </p>
                      </Link>
                    </li>
                  ))}
                </ul>
                <p className="mt-2.5 text-xs text-muted-foreground">
                  实验需要你自己的 API Key。Key 只存在你的浏览器里，不会上传。
                </p>
              </section>
            )}

            {/* 自检清单 */}
            <CheckpointSummary chapter={chapter} />

            {/* 实战作业 */}
            {projects.length > 0 && (
              <section>
                <h2 className="text-sm font-medium">阶段作业</h2>
                <ul className="mt-4 space-y-3">
                  {projects.map((project) => (
                    <li key={project.id} className="rounded-lg border border-border bg-card p-4">
                      <span className="text-sm font-medium">{project.title}</span>
                      <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                        {project.brief}
                      </p>
                      <p className="mt-2 text-[11px] text-muted-foreground/70">
                        预计 {project.estimatedHours[0]}–{project.estimatedHours[1]} 小时 · 评分清单{' '}
                        {project.rubric.length} 项
                      </p>
                    </li>
                  ))}
                </ul>
              </section>
            )}
          </div>

          {/* 上一章 / 下一章 */}
          <nav className="mt-14 grid gap-3 border-t border-border pt-6 sm:grid-cols-2">
            {prevChapter ? (
              <Link
                href={`/chapters/${prevChapter.id}`}
                className="rounded-lg border border-border p-3.5 transition-colors hover:bg-muted/50"
              >
                <span className="block text-[11px] text-muted-foreground">上一章</span>
                <span className="mt-1 block text-sm">{prevChapter.title}</span>
              </Link>
            ) : (
              <span />
            )}
            {nextChapter && (
              <Link
                href={`/chapters/${nextChapter.id}`}
                className="rounded-lg border border-border p-3.5 text-right transition-colors hover:bg-muted/50 sm:col-start-2"
              >
                <span className="block text-[11px] text-muted-foreground">下一章</span>
                <span className="mt-1 block text-sm">{nextChapter.title}</span>
              </Link>
            )}
          </nav>
        </div>
      </div>
    </main>
  );
}
