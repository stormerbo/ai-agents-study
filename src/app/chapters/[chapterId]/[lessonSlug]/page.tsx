import type { Metadata } from 'next';
import Link from 'next/link';
import { notFound } from 'next/navigation';

import { CheckpointList } from '@/components/chapter/checkpoint-list';
import { LessonToggle } from '@/components/progress/lesson-toggle';
import { ResourceSidebar } from '@/components/resource/resource-sidebar';
import { InlineMd, plainText } from '@/components/ui/inline-md';
import { getAdjacentLessons, getChapters, getLesson, getResources } from '@/content/curriculum';
import { getLessonBody } from '@/lib/content/body';
import { DIFFICULTY_LABEL } from '@/lib/labels';

export function generateStaticParams() {
  return getChapters().flatMap((chapter) =>
    chapter.lessons.map((lesson) => ({
      chapterId: chapter.id,
      lessonSlug: lesson.slug,
    })),
  );
}

export async function generateMetadata(
  props: PageProps<'/chapters/[chapterId]/[lessonSlug]'>,
): Promise<Metadata> {
  const { chapterId, lessonSlug } = await props.params;
  const entry = getLesson(`${chapterId}/${lessonSlug}`);
  if (!entry) return {};
  return { title: entry.lesson.title, description: plainText(entry.lesson.summary) };
}

export default async function LessonPage(props: PageProps<'/chapters/[chapterId]/[lessonSlug]'>) {
  const { chapterId, lessonSlug } = await props.params;
  const entry = getLesson(`${chapterId}/${lessonSlug}`);
  if (!entry) notFound();

  const { lesson, chapter } = entry;
  const { prev, next } = getAdjacentLessons(lesson.id);
  const resources = getResources(lesson.resourceIds ?? []);
  const lessonIndex = chapter.lessons.findIndex((l) => l.id === lesson.id);
  // 正文可能还没写 —— 那时渲染大纲占位，而不是给一个空白页
  const Body = lesson.hasBody ? await getLessonBody(chapter.id, lesson.slug) : undefined;

  return (
    <main className="mx-auto max-w-6xl px-6 py-10">
      <div className="lg:grid lg:grid-cols-[minmax(0,1fr)_17rem] lg:items-start lg:gap-x-10">
        <div className="lg:col-start-1 lg:row-start-1">
          {/* 面包屑 */}
          <nav className="flex flex-wrap items-center gap-1.5 text-xs text-muted-foreground">
            <Link href="/chapters" className="hover:text-foreground">
              章节
            </Link>
            <span aria-hidden>/</span>
            <Link href={`/chapters/${chapter.id}`} className="hover:text-foreground">
              {chapter.title}
            </Link>
          </nav>

          <header className="mt-5">
            <div className="flex flex-wrap items-center gap-x-2.5 text-[11px] text-muted-foreground/70">
              <span>
                第 {lessonIndex + 1} 节 / 共 {chapter.lessons.length} 节
              </span>
              <span aria-hidden>·</span>
              <span>{DIFFICULTY_LABEL[lesson.difficulty]}</span>
              <span aria-hidden>·</span>
              <span>约 {lesson.estimatedMinutes} 分钟</span>
            </div>
            <h1 className="mt-3 text-2xl font-semibold tracking-tight">{lesson.title}</h1>
            {lesson.summary && (
              <p className="mt-3 leading-relaxed text-muted-foreground">
                <InlineMd text={lesson.summary} />
              </p>
            )}
          </header>
        </div>

        {/* 延伸阅读 —— 桌面端固定在右栏，默认折叠；窄屏落到正文之后 */}
        <aside className="mt-8 lg:sticky lg:top-20 lg:col-start-2 lg:row-span-2 lg:row-start-1 lg:mt-0 lg:self-start">
          <ResourceSidebar resources={resources} title="本节延伸阅读" />
        </aside>

        {/* 正文主体 —— 桌面端落在第 1 列第 2 行；窄屏排在侧栏之后（侧栏默认折叠，只有一条） */}
        <div className="lg:col-start-1 lg:row-start-2">
          {/* 正文区域 */}
          <div className="mt-8">
            {Body ? (
              <article className="prose max-w-none prose-zinc dark:prose-invert">
                <Body />
              </article>
            ) : (
              <div className="rounded-xl border border-border bg-muted/40 px-5 py-6">
                <h2 className="text-sm font-medium">这一节的正文还在撰写中</h2>
                <p className="mt-2.5 text-sm leading-relaxed text-muted-foreground">
                  不过下面这些内容现在就能用：本节要讲的核心问题、需要你自己回答的自检题、
                  以及值得读的原始资料。你可以先按标题去查，再用自检题验证自己是否真的理解了。
                </p>
                {chapter.backendMapping && (
                  <p className="mt-4 border-t border-border pt-4 text-sm leading-relaxed text-muted-foreground">
                    <span className="font-medium text-foreground">对照你的后端经验：</span>
                    {chapter.backendMapping.analogy}
                  </p>
                )}
              </div>
            )}
          </div>

          {/* 自检 */}
          {lesson.checkpoints && lesson.checkpoints.length > 0 && (
            <section className="mt-12">
              <h2 className="text-sm font-medium">自检清单</h2>
              <p className="mt-1.5 text-xs text-muted-foreground">
                先自己回答，再展开对照。直接看答案等于没做。每条答案都标注了依据类型。
              </p>
              <div className="mt-4">
                <CheckpointList
                  checkpoints={lesson.checkpoints}
                  currentLessonId={lesson.id}
                  currentChapterId={chapter.id}
                />
              </div>
            </section>
          )}

          {/* 学完标记 —— 进度存在浏览器本地，不上传（见 lib/progress/store.ts 的说明） */}
          <div className="mt-12 flex flex-wrap items-center gap-3 border-t border-border pt-6">
            <LessonToggle lessonId={lesson.id} />
            <span className="text-xs text-muted-foreground/70">
              进度只存在这台设备上。换设备或清缓存会重置。
            </span>
          </div>

          {/* 翻页 */}
          <nav className="mt-14 grid gap-3 border-t border-border pt-6 sm:grid-cols-2">
            {prev ? (
              <Link
                href={`/chapters/${prev.chapter.id}/${prev.lesson.slug}`}
                className="rounded-lg border border-border p-3.5 transition-colors hover:bg-muted/50"
              >
                <span className="block text-[11px] text-muted-foreground">上一节</span>
                <span className="mt-1 block text-sm">{prev.lesson.title}</span>
              </Link>
            ) : (
              <span />
            )}
            {next && (
              <Link
                href={`/chapters/${next.chapter.id}/${next.lesson.slug}`}
                className="rounded-lg border border-border p-3.5 text-right transition-colors hover:bg-muted/50 sm:col-start-2"
              >
                <span className="block text-[11px] text-muted-foreground">下一节</span>
                <span className="mt-1 block text-sm">{next.lesson.title}</span>
              </Link>
            )}
          </nav>
        </div>
      </div>
    </main>
  );
}
