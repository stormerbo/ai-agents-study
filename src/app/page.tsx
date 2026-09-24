import Link from 'next/link';
import type { CSSProperties } from 'react';

import { getChaptersByStage, getStages, getStats } from '@/content/curriculum';

export default function Home() {
  const stages = getStages();
  const stats = getStats();

  const statsItems = [
    { label: '学习阶段', value: stats.stageCount },
    { label: '章节', value: stats.chapterCount },
    { label: '小节', value: stats.lessonCount },
    { label: '精选资源', value: stats.resourceCount },
    { label: '代码实验', value: stats.labCount },
    { label: '实战作业', value: stats.projectCount },
  ];

  return (
    <main className="mx-auto max-w-6xl px-6 py-14">
      {/* ---------------------------------------------------------------- */}
      <section className="max-w-3xl">
        <p className="font-mono text-xs tracking-wider text-muted-foreground uppercase">
          ai-agents-study
        </p>
        <h1 className="mt-4 text-3xl font-semibold tracking-tight text-balance sm:text-4xl">
          面向后端工程师的 AI Agent 学习路径
        </h1>
        <p className="mt-6 leading-relaxed text-muted-foreground">
          市面上的教程大多假设你从零开始。但你已经懂并发、幂等、持久化和可观测性 —— 这些在 agent
          开发里全都要用上，只是用法变了。
        </p>
        <p className="mt-3 leading-relaxed text-muted-foreground">
          这条路径按<strong className="font-medium text-foreground">依赖顺序</strong>
          组织，每一章都对照你已经掌握的后端经验，并明确标出哪些直觉在这里会反过来咬人 ——
          后者才是真正需要重新学的东西。
        </p>
      </section>

      {/* ---------------------------------------------------------------- */}
      <section className="mt-12">
        <dl className="grid grid-cols-2 gap-px overflow-hidden rounded-xl border border-border bg-border sm:grid-cols-3 lg:grid-cols-6">
          {statsItems.map((item) => (
            <div key={item.label} className="bg-background px-4 py-3.5">
              <dt className="text-xs text-muted-foreground">{item.label}</dt>
              <dd className="mt-1 text-xl font-semibold tabular-nums">{item.value}</dd>
            </div>
          ))}
        </dl>
      </section>

      {/* ---------------------------------------------------------------- */}
      <section className="mt-14">
        <div className="flex items-baseline justify-between">
          <h2 className="text-lg font-semibold">学习阶段</h2>
          <Link href="/map" className="text-sm text-muted-foreground hover:text-foreground">
            查看知识地图 →
          </Link>
        </div>

        <div className="mt-6 space-y-4">
          {stages.map((stage) => {
            const stageChapters = getChaptersByStage(stage.id);
            const stageStyle = {
              '--stage-color': `var(--color-${stage.colorToken})`,
            } as CSSProperties;

            return (
              <article
                key={stage.id}
                style={stageStyle}
                className="rounded-xl border border-border bg-card p-5"
              >
                <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
                  <span
                    className="font-mono text-xs font-medium"
                    style={{ color: 'var(--stage-color)' }}
                  >
                    阶段 {stage.order}
                  </span>
                  <h3 className="font-medium">{stage.title}</h3>
                  <span className="ml-auto text-xs text-muted-foreground">
                    {stageChapters.length > 0 ? `${stageChapters.length} 章` : '建设中'}
                  </span>
                </div>

                <p className="mt-2 text-sm text-muted-foreground">{stage.tagline}</p>

                {stageChapters.length > 0 ? (
                  <ul className="mt-4 space-y-0.5">
                    {stageChapters.map((chapter) => (
                      <li key={chapter.id}>
                        <Link
                          href={`/chapters/${chapter.id}`}
                          className="-mx-2 flex items-baseline gap-2.5 rounded-md px-2 py-1.5 transition-colors hover:bg-muted"
                        >
                          <span className="w-5 shrink-0 font-mono text-xs text-muted-foreground tabular-nums">
                            {String(chapter.order).padStart(2, '0')}
                          </span>
                          <span className="text-sm">{chapter.title}</span>
                          {chapter.flagship && (
                            <span className="shrink-0 rounded border border-border px-1.5 py-px text-[10px] text-muted-foreground">
                              重点
                            </span>
                          )}
                          <span className="ml-auto shrink-0 font-mono text-xs text-muted-foreground tabular-nums">
                            {chapter.lessons.length} 节
                          </span>
                        </Link>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="mt-4 text-xs leading-relaxed text-muted-foreground">
                    这一阶段的内容还在整理中。前六个阶段的地图已经画好，正文按顺序推进。
                  </p>
                )}
              </article>
            );
          })}
        </div>
      </section>

      {/* ---------------------------------------------------------------- */}
      <section className="mt-14 border-t border-border pt-8">
        <h2 className="text-sm font-medium">关于这份路径的现状</h2>
        <p className="mt-2 max-w-3xl text-sm leading-relaxed text-muted-foreground">
          目前共 {stats.chapterCount} 章的元数据与大纲已完成，正文正在按顺序撰写。
          未写正文的章节仍然可以打开 —— 它们的章概览页包含学习目标、小节大纲、
          精选资源与自检问题，本身就是可用的学习指南。
        </p>
        <div className="mt-4 flex flex-wrap gap-3 text-sm">
          <Link href="/chapters" className="text-muted-foreground hover:text-foreground">
            全部章节 →
          </Link>
          <Link href="/resources" className="text-muted-foreground hover:text-foreground">
            资源库 →
          </Link>
          <Link href="/about" className="text-muted-foreground hover:text-foreground">
            内容说明与局限 →
          </Link>
        </div>
      </section>
    </main>
  );
}
