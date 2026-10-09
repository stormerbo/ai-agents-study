import type { Metadata } from 'next';
import Link from 'next/link';
import { notFound } from 'next/navigation';

import { Playground } from '@/components/lab/playground';
import { InlineMd, plainText } from '@/components/ui/inline-md';
import { curriculum, getChapter, getLab } from '@/content/curriculum';
import { getPublicProviderList } from '@/lib/llm/registry';
import { isCustomBaseUrlAllowed } from '@/lib/llm/url-guard';

export function generateStaticParams() {
  return Object.keys(curriculum.labs).map((labId) => ({ labId }));
}

export async function generateMetadata(props: PageProps<'/labs/[labId]'>): Promise<Metadata> {
  const { labId } = await props.params;
  const lab = getLab(labId);
  if (!lab) return {};
  return { title: lab.title, description: plainText(lab.goal) };
}

export default async function LabPage(props: PageProps<'/labs/[labId]'>) {
  const { labId } = await props.params;
  const lab = getLab(labId);
  if (!lab) notFound();

  const chapter = getChapter(lab.chapterId);
  // provider 清单在服务端算好再传给客户端组件 —— 它读环境变量，
  // 不能让客户端自己去读
  const providers = getPublicProviderList();

  return (
    <main className="mx-auto max-w-3xl px-6 py-10">
      <nav className="flex flex-wrap items-center gap-1.5 text-xs text-muted-foreground">
        <Link href="/labs" className="hover:text-foreground">
          实验
        </Link>
        {chapter && (
          <>
            <span aria-hidden>/</span>
            <Link href={`/chapters/${chapter.id}`} className="hover:text-foreground">
              {chapter.title}
            </Link>
          </>
        )}
      </nav>

      <header className="mt-5">
        <h1 className="text-2xl font-semibold tracking-tight">{lab.title}</h1>
        <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
          <InlineMd text={lab.goal} />
        </p>
        <p className="mt-2 text-xs text-muted-foreground/70">
          约 {lab.estimatedMinutes} 分钟 · 需要你自己的 API Key
        </p>
      </header>

      <div className="mt-6">
        <Playground
          lab={lab}
          providers={providers}
          allowCustomEndpoint={isCustomBaseUrlAllowed()}
        />
      </div>

      {lab.troubleshooting && lab.troubleshooting.length > 0 && (
        <section className="mt-10">
          <h2 className="text-sm font-medium">遇到问题时</h2>
          <ul className="mt-3 space-y-2">
            {lab.troubleshooting.map((t) => (
              <li key={t.symptom} className="rounded-lg border border-border bg-card p-3 text-xs">
                <p className="font-medium">{t.symptom}</p>
                <p className="mt-1.5 text-muted-foreground">
                  <span className="text-foreground/70">可能原因：</span>
                  {t.cause}
                </p>
                <p className="mt-1 text-muted-foreground">
                  <span className="text-foreground/70">怎么办：</span>
                  {t.fix}
                </p>
              </li>
            ))}
          </ul>
        </section>
      )}
    </main>
  );
}
