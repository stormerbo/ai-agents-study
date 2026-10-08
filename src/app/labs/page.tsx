import type { Metadata } from 'next';
import Link from 'next/link';

import { curriculum, getChapter } from '@/content/curriculum';
import { InlineMd } from '@/components/ui/inline-md';

export const metadata: Metadata = {
  title: '代码实验',
  description: '可以在站内直接运行的实验：填入自己的 API Key，观察模型的完整响应过程与轨迹。',
};

export default function LabsPage() {
  const labs = Object.values(curriculum.labs);
  const byChapter = new Map<string, typeof labs>();
  for (const lab of labs) {
    const list = byChapter.get(lab.chapterId) ?? [];
    list.push(lab);
    byChapter.set(lab.chapterId, list);
  }

  return (
    <main className="mx-auto max-w-4xl px-6 py-10">
      <header className="max-w-3xl">
        <h1 className="text-2xl font-semibold tracking-tight">代码实验</h1>
        <p className="text-muted-foreground mt-3 leading-relaxed">
          这些实验可以直接在页面里跑。填入你自己的 API Key，然后观察模型返回的
          <strong className="text-foreground font-medium">完整事件轨迹</strong>
          ——不只是最终文本，还有思考过程、token 用量、以及厂商实际发出的原始数据。
        </p>
        <p className="text-muted-foreground mt-3 text-sm leading-relaxed">
          Key 只存在你的浏览器里，运行时经本站服务器转发给模型厂商，服务端不存储、不记录日志。
          建议用一把限额的、专用的 Key。
        </p>
      </header>

      <div className="mt-10 space-y-8">
        {[...byChapter.entries()].map(([chapterId, chapterLabs]) => {
          const chapter = getChapter(chapterId);
          return (
            <section key={chapterId}>
              <h2 className="text-sm font-medium">
                {chapter ? (
                  <Link href={`/chapters/${chapter.id}`} className="hover:underline">
                    {chapter.title}
                  </Link>
                ) : (
                  chapterId
                )}
              </h2>
              <ul className="mt-3 grid gap-3 sm:grid-cols-2">
                {chapterLabs.map((lab) => (
                  <li key={lab.id}>
                    <Link
                      href={`/labs/${lab.id}`}
                      className="border-border bg-card hover:border-accent/60 flex h-full flex-col rounded-xl border p-4 transition-colors"
                    >
                      <span className="text-sm font-medium">{lab.title}</span>
                      <span className="text-muted-foreground mt-2 flex-1 text-xs leading-relaxed">
                        <InlineMd text={lab.goal} />
                      </span>
                      <span className="text-muted-foreground/70 mt-3 text-[11px]">
                        约 {lab.estimatedMinutes} 分钟
                        {lab.capabilities?.length ? ` · ${lab.capabilities.join(' / ')}` : ''}
                      </span>
                    </Link>
                  </li>
                ))}
              </ul>
            </section>
          );
        })}
      </div>

      <p className="text-muted-foreground border-border mt-12 border-t pt-6 text-xs leading-relaxed">
        实验需要联网并消耗你自己的 token 额度。每个实验页都列出了「你应该观察到什么」
        与常见问题的排查方向 —— 跑之前先看一眼，否则容易跑完却不知道学到了什么。
      </p>
    </main>
  );
}
