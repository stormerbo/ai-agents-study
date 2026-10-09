import type { Metadata } from 'next';
import Link from 'next/link';
import { notFound } from 'next/navigation';

import { InlineMd, plainText } from '@/components/ui/inline-md';
import { Markdown } from '@/components/ui/markdown';
import { curriculum, getChapters, getResource } from '@/content/curriculum';
import { getReading, getTranslation, hasReading, hasTranslation } from '@/lib/content/reading';
import {
  DIFFICULTY_LABEL,
  RESOURCE_KIND_LABEL,
  RESOURCE_LANG_LABEL,
  RESOURCE_STATUS_LABEL,
} from '@/lib/labels';

/**
 * 站内精读页。
 *
 * 存在的理由：资源库 48 条里 42 条是英文外链，每读一条都要跳出去再过语言关。
 * 这一页把「它讲了什么、该读哪部分」用中文放在站内，原文链接保留在顶部。
 *
 * 没有精读的条目也会生成页面 —— 那样列表页的链接才是统一的，
 * 页面里会明确写「还没有站内精读」并给出原文链接，而不是 404。
 */

export function generateStaticParams() {
  return Object.keys(curriculum.resources).map((resourceId) => ({ resourceId }));
}

export async function generateMetadata(
  props: PageProps<'/resources/[resourceId]'>,
): Promise<Metadata> {
  const { resourceId } = await props.params;
  const resource = getResource(resourceId);
  if (!resource) return {};
  return {
    title: `${resource.title} —— 精读`,
    description: plainText(resource.why),
  };
}

export default async function ReadingPage(props: PageProps<'/resources/[resourceId]'>) {
  const { resourceId } = await props.params;
  const resource = getResource(resourceId);
  if (!resource) notFound();

  const Body = hasReading(resourceId) ? await getReading(resourceId) : undefined;
  const Translation = hasTranslation(resourceId) ? await getTranslation(resourceId) : undefined;

  // 哪些章引用了它 —— 读完精读之后最自然的下一步是去那一章
  const citingChapters = getChapters().filter((c) => {
    if (c.resourceIds.includes(resource.id)) return true;
    return c.lessons.some((l) => (l.resourceIds ?? []).includes(resource.id));
  });

  return (
    <main className="mx-auto max-w-3xl px-6 py-10">
      <nav className="flex flex-wrap items-center gap-1.5 text-xs text-muted-foreground">
        <Link href="/resources" className="hover:text-foreground">
          资源库
        </Link>
        <span aria-hidden>/</span>
        <span className="line-clamp-1">{resource.title}</span>
      </nav>

      <header className="mt-5">
        <div className="flex flex-wrap items-center gap-x-2.5 text-[11px] text-muted-foreground/70">
          <span>{RESOURCE_KIND_LABEL[resource.kind]}</span>
          <span aria-hidden>·</span>
          <span>{RESOURCE_LANG_LABEL[resource.lang]}</span>
          <span aria-hidden>·</span>
          <span>{DIFFICULTY_LABEL[resource.difficulty]}</span>
          {resource.estimatedMinutes && (
            <>
              <span aria-hidden>·</span>
              <span>原文约 {resource.estimatedMinutes} 分钟</span>
            </>
          )}
          {resource.status !== 'active' && (
            <>
              <span aria-hidden>·</span>
              <span className="text-amber-600 dark:text-amber-500">
                {RESOURCE_STATUS_LABEL[resource.status]}
              </span>
            </>
          )}
        </div>

        <h1 className="mt-3 text-2xl font-semibold tracking-tight">{resource.title}</h1>
        {resource.author && (
          <p className="mt-1.5 text-sm text-muted-foreground">{resource.author}</p>
        )}

        {/* 原文链接始终在顶部 —— 精读是入口，不是替代品 */}
        <a
          href={resource.url}
          target="_blank"
          rel="noopener noreferrer"
          className="mt-4 inline-flex items-center gap-1.5 rounded-md border border-border px-3 py-1.5 text-sm transition-colors hover:bg-muted"
        >
          看原文
          <span aria-hidden className="text-xs text-muted-foreground">
            ↗
          </span>
        </a>
        {resource.mirrors?.map((m) => (
          <a
            key={m}
            href={m}
            target="_blank"
            rel="noopener noreferrer"
            className="ml-2 text-xs text-muted-foreground underline-offset-2 hover:text-foreground hover:underline"
          >
            镜像
          </a>
        ))}
      </header>

      <section className="mt-8 border-y border-border py-4">
        <p className="text-sm leading-relaxed">
          <span className="text-muted-foreground">为什么值得读 —— </span>
          <InlineMd text={resource.why} />
        </p>
      </section>

      {/* 中文全文优先 —— 这是这一页的主内容 */}
      {Translation ? (
        <>
          <p className="mt-8 border-l-2 border-border/60 pl-3 text-xs leading-relaxed text-muted-foreground/70">
            <strong className="font-medium">机器翻译</strong>，仅供个人学习参考；
            版权归原作者所有，需要准确表述时请对照
            <a
              href={resource.url}
              target="_blank"
              rel="noopener noreferrer"
              className="mx-0.5 underline-offset-2 hover:underline"
            >
              原文
            </a>
            。术语与代码标识符保留英文原词。
          </p>
          <article className="prose mt-8 max-w-none prose-zinc dark:prose-invert">
            <Markdown>{Translation}</Markdown>
          </article>
        </>
      ) : Body ? (
        <article className="prose mt-10 max-w-none prose-zinc dark:prose-invert">
          <Body />
        </article>
      ) : (
        <section className="mt-10 rounded-xl border border-border bg-card p-5">
          <h2 className="text-sm font-medium">这条还没有站内内容</h2>
          <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
            中文全文还在逐步补。这条目前只有上面那段「为什么值得读」，
            需要完整内容请用顶部的「看原文」链接。
          </p>
        </section>
      )}

      {/* 导读：译文之上的判断（该读哪节、可跳哪节）。有译文时默认折叠，不抢主内容。 */}
      {Body && Translation && (
        <details className="group mt-14 overflow-hidden rounded-xl border border-border bg-card">
          <summary className="flex cursor-pointer list-none items-center gap-2 px-4 py-3 text-sm font-medium marker:hidden hover:bg-muted/50">
            <span
              aria-hidden
              className="font-mono text-xs text-muted-foreground/40 transition-transform group-open:rotate-90"
            >
              ▸
            </span>
            导读：这篇讲什么、该读哪节
          </summary>
          <div className="border-t border-border/70 px-4 py-5">
            <article className="prose prose-sm max-w-none prose-zinc dark:prose-invert">
              <Body />
            </article>
          </div>
        </details>
      )}

      {citingChapters.length > 0 && (
        <section className="mt-12">
          <h2 className="text-sm font-medium">哪些章引用了它</h2>
          <ul className="mt-3 flex flex-wrap gap-2">
            {citingChapters.map((c) => (
              <li key={c.id}>
                <Link
                  href={`/chapters/${c.id}`}
                  className="rounded-md border border-border px-2.5 py-1 text-xs text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
                >
                  第 {c.order} 章《{c.title}》
                </Link>
              </li>
            ))}
          </ul>
        </section>
      )}
    </main>
  );
}
