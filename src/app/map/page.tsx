import type { Metadata } from 'next';

import { KnowledgeMap } from '@/components/map/knowledge-map';
import { getChapters, getStages } from '@/content/curriculum';

export const metadata: Metadata = {
  title: '知识地图',
  description:
    'AI Agent 开发的完整学习路径：6 个阶段、按依赖顺序组织的章节，以及它们之间的前置关系。',
};

export default function MapPage() {
  const chapters = getChapters();
  const stages = getStages();
  const written = chapters.filter((c) => c.lessons.some((l) => l.hasBody)).length;

  return (
    <main className="mx-auto max-w-6xl px-6 py-10">
      <header className="max-w-3xl">
        <h1 className="text-2xl font-semibold tracking-tight">知识地图</h1>
        <p className="mt-3 leading-relaxed text-muted-foreground">
          箭头表示<strong className="font-medium text-foreground">前置关系</strong>
          ：箭头指向的章节，假设你已经理解了它的来源章节。顺序不是难度递进，而是依赖递进 ——
          跳过前置直接读后面的，通常不是读不懂，而是会踩到一些“早知道就好了”的坑。
        </p>
      </header>

      <div className="mt-8">
        <KnowledgeMap chapters={chapters} stages={stages} />
      </div>

      <div className="mt-5 flex flex-wrap items-center gap-x-6 gap-y-2 text-xs text-muted-foreground">
        <span className="flex items-center gap-2">
          <span className="inline-block h-3 w-[3px] rounded-full bg-accent" aria-hidden />
          已有正文
        </span>
        <span className="flex items-center gap-2">
          <span
            className="inline-block h-3 w-6 rounded border border-border bg-transparent"
            aria-hidden
          />
          仅大纲（正文待写）
        </span>
        <span className="ml-auto">
          共 {chapters.length} 章，其中 {written} 章已有正文
        </span>
      </div>

      <p className="mt-8 border-t border-border pt-6 text-sm leading-relaxed text-muted-foreground">
        窄屏下这张图需要横向滚动。手机上看的话，首页的阶段列表是它的等价视图 ——
        信息和链接完全一致，只是排成了纵向。
      </p>
    </main>
  );
}
