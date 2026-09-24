import type { Metadata } from 'next';

import { ResourceCard } from '@/components/resource/resource-card';
import { getChapters, getResources } from '@/content/curriculum';
import type { ResourcePriority } from '@/content/curriculum/schema';
import { RESOURCE_KIND_LABEL, RESOURCE_PRIORITY_LABEL } from '@/lib/labels';

export const metadata: Metadata = {
  title: '资源库',
  description:
    '按「读它的理由」组织的外部资源清单：官方文档、论文、书籍、开源项目与中文资料，每条都写明为什么值得读。',
};

const PRIORITY_ORDER: Record<ResourcePriority, number> = {
  must: 0,
  recommended: 1,
  optional: 2,
};

export default function ResourcesPage() {
  const all = getResources(getChapters().flatMap((c) => c.resourceIds));
  const resources = [...new Map(all.map((r) => [r.id, r])).values()].sort(
    (a, b) => PRIORITY_ORDER[a.priority] - PRIORITY_ORDER[b.priority],
  );

  const byPriority = {
    must: resources.filter((r) => r.priority === 'must'),
    recommended: resources.filter((r) => r.priority === 'recommended'),
    optional: resources.filter((r) => r.priority === 'optional'),
  };

  return (
    <main className="mx-auto max-w-4xl px-6 py-10">
      <header className="max-w-3xl">
        <h1 className="text-2xl font-semibold tracking-tight">资源库</h1>
        <p className="mt-3 leading-relaxed text-muted-foreground">
          每条资源都写明了<strong className="font-medium text-foreground">为什么值得读</strong>、
          该读哪一部分、以及它是什么语言和难度。没有说明的链接不会出现在这里 ——
          一份没有判断依据的链接列表，价值约等于零。
        </p>
      </header>

      <div className="mt-6 rounded-lg border border-border bg-muted/40 px-4 py-3">
        <p className="text-xs leading-relaxed text-muted-foreground">
          <span className="font-medium text-foreground">关于时效性：</span>
          每条都标注了最近核实日期。标着「未逐页打开」的条目来自搜索结果的交叉印证，
          用之前请自行确认。AI 领域的外链腐化很快 —— 仓库归档、模型下线、
          课程过期都很常见（这份清单首轮核实时就修正了三处这类错误）。
          站内有巡检脚本定期检查链接可用性，但它只能验证页面还在，验证不了内容还对。
        </p>
      </div>

      {(['must', 'recommended', 'optional'] as const).map((priority) => {
        const items = byPriority[priority];
        if (items.length === 0) return null;

        return (
          <section key={priority} className="mt-10">
            <div className="flex items-baseline gap-3">
              <h2 className="text-sm font-medium">{RESOURCE_PRIORITY_LABEL[priority]}</h2>
              <span className="text-xs text-muted-foreground">{items.length} 条</span>
            </div>
            <ul className="mt-4 space-y-3">
              {items.map((resource) => (
                <ResourceCard key={resource.id} resource={resource} />
              ))}
            </ul>
          </section>
        );
      })}

      <p className="mt-12 border-t border-border pt-6 text-xs leading-relaxed text-muted-foreground">
        资源类型覆盖：{Object.values(RESOURCE_KIND_LABEL).join(' / ')}。
        完整清单（含未在章节中引用的条目）会随后续章节的撰写继续补充。
      </p>
    </main>
  );
}
