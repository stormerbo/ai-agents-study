import type { Metadata } from 'next';
import Link from 'next/link';

import { getStats } from '@/content/curriculum';

export const metadata: Metadata = {
  title: '关于',
  description: '这个站的定位、内容生产方式、对时效性的处理原则，以及它目前做不到的事。',
};

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="mt-10">
      <h2 className="text-base font-semibold tracking-tight">{title}</h2>
      <div className="mt-3 space-y-3 text-sm leading-relaxed text-muted-foreground">{children}</div>
    </section>
  );
}

export default function AboutPage() {
  const stats = getStats();

  return (
    <main className="mx-auto max-w-3xl px-6 py-10">
      <h1 className="text-2xl font-semibold tracking-tight">关于这个站</h1>

      <Section title="它要解决什么问题">
        <p>
          市面上的 AI Agent 教程大多有两个问题：一是散，知识点之间没有依赖顺序，学完仍然不知道
          下一步该看什么；二是假设读者从零开始，把一个已有多年工程经验的后端工程师，当成刚学编程的人来教。
        </p>
        <p>
          这个站想做的是一条<strong className="font-medium text-foreground">有依赖顺序</strong>
          的路径， 并且承认你已经具备的能力：你懂并发、幂等、持久化、可观测性，这些在 agent
          开发里全都要用上。 真正需要重新学的，是那些会<em>反过来咬人</em>的直觉 ——
          比如“同样的输入应该得到同样的输出”。
        </p>
        <p>
          所以每一章都有一个固定的「后端视角对照」小节，明确列出哪些经验可以直接迁移、
          哪些直觉在这里会失效。
        </p>
      </Section>

      <Section title="内容是怎么生产出来的">
        <p>
          章节大纲与正文由 AI 辅助撰写。每条技术论断都标注了依据类型（有文档依据 / 经验判断 /
          未能核实），资源链接另有可用性巡检。即便如此，你仍需要保持正常的怀疑
          ——尤其是涉及具体版本、API 细节和数字的地方，第一手资料永远以官方文档为准。
        </p>
        <p>
          每一章的元数据里都记录了最近核实日期。资源库里的每一条都标注了核实方式：
          是实际打开过页面，还是仅来自搜索结果交叉印证。
        </p>
      </Section>

      <Section title="关于“具体数字”的处理原则">
        <p>
          凡是会过期的数字——模型价格、基准分数、token 倍率、star 数——本站的处理原则是：
          <strong className="font-medium text-foreground">要么标注来源与核实日期，要么不写</strong>
          。
        </p>
        <p>
          所以你不会在这里看到“某某模型每百万 token 多少钱”这类看起来很实用的信息。
          因为它在几周内就会变成误导。取而代之的是学会估算方法，价格到官方定价页现查。
        </p>
        <p>
          同理，资源库里没有任何硬编码的 star 数。GitHub star 数在二手资料里出入极大 ——
          首轮核实时就发现，同一个项目在不同来源里的 star 数能差出一倍。
        </p>
      </Section>

      <Section title="时效性：这类站点最大的敌人">
        <p>
          AI 领域的外链腐化速度远快于其他领域。在整理这份资源清单的首轮核实中，就修正了三处问题：
          一个被广泛推荐的仓库其实已经归档、一个仓库改了组织导致链接失效、 一个只有 2 个 star
          的仓库被二手资料描述成“知名教程”。
        </p>
        <p>
          站内有链接巡检脚本（
          <code className="font-mono text-xs text-foreground">scripts/check-links.mjs</code>）
          可以定期检查所有外链的可用性。但它只能回答“页面还在吗”，
          回答不了“内容还对吗”——后者只能靠人工复审。
        </p>
      </Section>

      <Section title="目前的状态与局限">
        <p>
          当前共 {stats.chapterCount} 章、{stats.lessonCount} 个小节的元数据与大纲已完成， 其中{' '}
          {stats.lessonsWithBody} 节有完整正文。正文正在按顺序推进。
        </p>
        <p>尚未实现、但已在规划中的部分：</p>
        <ul className="ml-4 list-disc space-y-1.5">
          <li>站内代码实验（需要自带 API Key）—— 实验的目标与任务已定义，运行组件还没接上</li>
          <li>学习进度记录（章节完成、自检项勾选）</li>
          <li>站内全文搜索</li>
        </ul>
        <p>
          未写正文的章节仍然可以打开。它们的章概览页包含学习目标、小节大纲、 精选资源与自检问题 ——
          即使没有正文，也足以支撑你自己去学。
        </p>
      </Section>

      <Section title="阅读约定">
        <p>
          技术术语保留英文原词。原因很实际：你要读的文档、论文和报错信息都是英文，
          把术语翻成中文反而会增加你搜索时的阻力。正文在术语第一次出现时会给出中文解释，
          完整的对照表在术语表中维护。
        </p>
      </Section>

      <nav className="mt-12 flex flex-wrap gap-4 border-t border-border pt-6 text-sm">
        <Link href="/map" className="text-muted-foreground hover:text-foreground">
          知识地图 →
        </Link>
        <Link href="/chapters" className="text-muted-foreground hover:text-foreground">
          全部章节 →
        </Link>
        <Link href="/resources" className="text-muted-foreground hover:text-foreground">
          资源库 →
        </Link>
      </nav>
    </main>
  );
}
