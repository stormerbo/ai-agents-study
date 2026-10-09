import type { Resource } from '@/content/curriculum/schema';
import { InlineMd } from '@/components/ui/inline-md';
import {
  DIFFICULTY_LABEL,
  RESOURCE_KIND_LABEL,
  RESOURCE_LANG_LABEL,
  RESOURCE_STATUS_LABEL,
} from '@/lib/labels';
import { cn } from '@/lib/utils';

/**
 * 窄栏里的一条资源。
 *
 * 为什么不用 ResourceCard：那个是**宽栏**版 —— 标题与徽章同一行、徽章靠右（`ml-auto`）。
 * 放进 17rem 的侧栏里会被挤成两三行、且换行位置随机。窄栏需要的是**竖向堆叠**：
 * 标题一行、徽章一行、说明一行。同一份数据，两种版式，各自适配自己的宽度。
 */
function CompactBadge({
  children,
  tone = 'default',
}: {
  children: React.ReactNode;
  tone?: 'default' | 'warning';
}) {
  return (
    <span
      className={cn(
        'shrink-0 rounded border px-1 py-px text-[10px] leading-4 whitespace-nowrap',
        tone === 'warning'
          ? 'border-amber-500/40 text-amber-600 dark:text-amber-500'
          : 'border-border text-muted-foreground',
      )}
    >
      {children}
    </span>
  );
}

export function ResourceCardCompact({ resource }: { resource: Resource }) {
  const notActive = resource.status !== 'active';

  return (
    <li className="border-t border-border/70 px-3.5 py-3 first:border-t-0">
      <a
        href={resource.url}
        target="_blank"
        rel="noopener noreferrer"
        className="text-sm leading-snug font-medium underline-offset-4 hover:text-accent hover:underline"
      >
        {resource.title}
        <span aria-hidden className="ml-1 text-[11px] text-muted-foreground">
          ↗
        </span>
      </a>

      <div className="mt-1.5 flex flex-wrap items-center gap-1 text-muted-foreground">
        {resource.priority === 'must' && <CompactBadge>必读</CompactBadge>}
        <CompactBadge>{RESOURCE_KIND_LABEL[resource.kind]}</CompactBadge>
        <CompactBadge>{RESOURCE_LANG_LABEL[resource.lang]}</CompactBadge>
        <CompactBadge>{DIFFICULTY_LABEL[resource.difficulty]}</CompactBadge>
        {notActive && (
          <CompactBadge tone="warning">{RESOURCE_STATUS_LABEL[resource.status]}</CompactBadge>
        )}
      </div>

      {/* why 是本站与「链接堆砌」的核心区别，窄栏里也不能省 */}
      <p className="mt-2 text-xs leading-relaxed text-muted-foreground">
        <InlineMd text={resource.why} />
      </p>

      <p className="mt-1.5 text-[10px] text-muted-foreground/60">
        {resource.author && <span>{resource.author} · </span>}
        {resource.estimatedMinutes && <span>约 {resource.estimatedMinutes} 分钟 · </span>}
        <span>核实于 {resource.verifiedAt}</span>
      </p>
    </li>
  );
}

/**
 * 右侧的延伸阅读栏。**默认折叠**，展开才显示内容。
 *
 * 用原生 `<details>` 而不是 useState —— 和第 21 章第 5 节那份审批界面同一个判断：
 * 折叠状态不需要进 React，交给浏览器就少一份状态、少一次水合、也少一类 hydration 不一致。
 * 而且它天然支持键盘（Enter/Space 展开，Tab 聚焦），不用自己补 aria。
 */
export function ResourceSidebar({
  resources,
  title = '延伸阅读',
}: {
  resources: Resource[];
  title?: string;
}) {
  if (resources.length === 0) return null;

  return (
    <details className="group overflow-hidden rounded-xl border border-border bg-card">
      <summary
        className={cn(
          'flex cursor-pointer list-none items-center gap-2 px-3.5 py-3 marker:hidden hover:bg-muted/50',
          // 折叠时只有这一条；展开后它变成栏头，下面接内容
          'transition-colors',
        )}
      >
        <span
          aria-hidden
          className="shrink-0 font-mono text-xs text-muted-foreground/40 transition-transform group-open:rotate-90"
        >
          ▸
        </span>
        <span className="text-sm font-medium">{title}</span>
        <span className="ml-auto font-mono text-[11px] text-muted-foreground/70">
          {resources.length} 篇
        </span>
      </summary>

      <ul className="max-h-[60vh] overflow-y-auto border-t border-border/70">
        {resources.map((r) => (
          <ResourceCardCompact key={r.id} resource={r} />
        ))}
      </ul>
    </details>
  );
}
