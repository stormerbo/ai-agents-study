import Link from 'next/link';
import { getChapters, getResources, getLesson } from '@/content/curriculum';
import type { Checkpoint, ClaimBasis } from '@/content/curriculum/schema';
import { InlineMd } from '@/components/ui/inline-md';
import { cn } from '@/lib/utils';

/**
 * 自检清单。
 *
 * 每条答案都会显式标注它的**依据类型** —— 这是本站准确性机制在界面上的出口。
 * 如果不说清楚，读者无法分辨「这是官方文档写着的」和「这是作者的经验判断」，
 * 而两者被误认的代价完全不同。
 */

const BASIS_LABEL: Record<ClaimBasis, string> = {
  documented: '有文档依据',
  inferred: '经验判断',
  unverified: '未能核实',
};

function BasisTag({ basis }: { basis: ClaimBasis }) {
  return (
    <span
      className={cn(
        'shrink-0 rounded border px-1.5 py-px text-[10px] leading-4',
        basis === 'documented' && 'border-emerald-600/40 text-emerald-700 dark:text-emerald-500',
        basis === 'inferred' && 'border-border text-muted-foreground',
        basis === 'unverified' && 'border-amber-500/50 text-amber-700 dark:text-amber-500',
      )}
    >
      {basis === 'unverified' && '⚠ '}
      {BASIS_LABEL[basis]}
    </span>
  );
}

/** 章号 → 章。用来把答案里写的「第 N 章」变成可点链接。 */
const CHAPTERS_BY_ORDER = getChapters()
  .slice()
  .sort((a, b) => a.order - b.order);

export function CheckpointList({
  checkpoints,
  currentLessonId,
  currentChapterId,
}: {
  checkpoints: Checkpoint[];
  /** 没填 reviewLessonId 时，回看目标默认是本节 */
  currentLessonId?: string;
  /** 当前节所属的章 —— 用来滤掉「第 N 章」里指向自己的那一条 */
  currentChapterId?: string;
}) {
  if (checkpoints.length === 0) return null;

  return (
    <ul className="space-y-2">
      {checkpoints.map((cp) => {
        const sources = getResources(cp.sourceIds ?? []);
        // 回看目标：优先用显式指定的那一节，否则退回本节。
        // 这样每条自检项都有一个「答不出来看哪里」的出口 —— 而答案本身就在本节的情况是多数。
        const reviewId = cp.reviewLessonId ?? currentLessonId;
        const review = reviewId ? getLesson(reviewId) : undefined;

        // 答案里写到「第 N 章」时，把那个引用变成可点的链接。
        //
        // 为什么这么做，而不是给每条自检项手填 reviewLessonId：
        // 我试过按关键词自动匹配目标**节**，但抽出来是错的（长标题会赢），
        // 而答案里点名节标题的情况在全书是 0 条 —— 也就是说没有任何可靠信号。
        // 猜一个错的复习目标比不给更糟。但「第 N 章」是作者自己写在答案里的，
        // 它一定是对的，所以把它变成链接既准确又有用。
        const cited = CHAPTERS_BY_ORDER.filter(
          (c) => c.id !== currentChapterId && cp.answer.includes(`第 ${c.order} 章`),
        );

        return (
          <li key={cp.id}>
            {/* 用原生 details 折叠，不需要任何客户端 JS */}
            <details className="group rounded-lg border border-border bg-card">
              <summary className="cursor-pointer list-none px-4 py-3 text-sm marker:hidden">
                <span className="flex items-baseline gap-2.5">
                  <span
                    aria-hidden
                    className="shrink-0 font-mono text-xs text-muted-foreground/40 transition-transform group-open:rotate-90"
                  >
                    ▸
                  </span>
                  <InlineMd text={cp.question} />
                </span>
              </summary>

              <div className="border-t border-border px-4 py-3 pl-10">
                <p className="text-sm leading-relaxed text-muted-foreground">
                  <InlineMd text={cp.answer} />
                </p>

                <div className="mt-3 flex flex-wrap items-center gap-x-2 gap-y-1">
                  <BasisTag basis={cp.basis} />

                  {sources.map((source) => (
                    <a
                      key={source.id}
                      href={source.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="rounded border border-border px-1.5 py-px text-[10px] leading-4 text-muted-foreground underline-offset-2 hover:text-accent hover:underline"
                    >
                      {source.title}
                      <span aria-hidden className="ml-0.5">
                        ↗
                      </span>
                    </a>
                  ))}
                </div>

                {cited.length > 0 && (
                  <p className="mt-2 text-xs text-muted-foreground/70">
                    <span>答案涉及：</span>
                    {cited.map((c, i) => (
                      <span key={c.id}>
                        {i > 0 && <span className="mx-1">·</span>}
                        <Link
                          href={`/chapters/${c.id}`}
                          className="text-accent underline-offset-2 hover:underline"
                        >
                          第 {c.order} 章《{c.title}》
                        </Link>
                      </span>
                    ))}
                  </p>
                )}

                {review && (
                  <p className="mt-3 text-xs">
                    <span className="text-muted-foreground/70">答不出来？回看</span>{' '}
                    <Link
                      href={`/chapters/${review.chapter.id}/${review.lesson.slug}`}
                      className="text-accent underline-offset-2 hover:underline"
                    >
                      {review.lesson.title}
                    </Link>
                  </p>
                )}

                {cp.note && (
                  <p className="mt-2.5 border-l-2 border-border/60 pl-3 text-xs leading-relaxed text-muted-foreground/70">
                    {cp.note}
                  </p>
                )}
              </div>
            </details>
          </li>
        );
      })}
    </ul>
  );
}
