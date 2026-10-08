import type { Resource } from '@/content/curriculum/schema';
import { InlineMd } from '@/components/ui/inline-md';
import {
  DIFFICULTY_LABEL,
  RESOURCE_KIND_LABEL,
  RESOURCE_LANG_LABEL,
  RESOURCE_STATUS_LABEL,
} from '@/lib/labels';
import { cn } from '@/lib/utils';

function Badge({
  children,
  tone = 'default',
}: {
  children: React.ReactNode;
  tone?: 'default' | 'warning' | 'muted';
}) {
  return (
    <span
      className={cn(
        'shrink-0 rounded border px-1.5 py-px text-[10px] leading-4 whitespace-nowrap',
        tone === 'default' && 'border-border text-muted-foreground',
        tone === 'warning' && 'border-amber-500/40 text-amber-600 dark:text-amber-500',
        tone === 'muted' && 'border-border text-muted-foreground/60',
      )}
    >
      {children}
    </span>
  );
}

export function ResourceCard({ resource }: { resource: Resource }) {
  const notActive = resource.status !== 'active';

  return (
    <li className="rounded-lg border border-border bg-card p-4">
      <div className="flex flex-wrap items-baseline gap-x-2 gap-y-1.5">
        <a
          href={resource.url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-sm font-medium underline-offset-4 hover:text-accent hover:underline"
        >
          {resource.title}
          <span aria-hidden className="ml-1 text-xs text-muted-foreground">
            ↗
          </span>
        </a>

        <span className="ml-auto flex flex-wrap items-center gap-1.5 text-muted-foreground">
          {resource.priority === 'must' && <Badge>必读</Badge>}
          <Badge>{RESOURCE_KIND_LABEL[resource.kind]}</Badge>
          <Badge>{RESOURCE_LANG_LABEL[resource.lang]}</Badge>
          <Badge>{DIFFICULTY_LABEL[resource.difficulty]}</Badge>
          {notActive && <Badge tone="warning">{RESOURCE_STATUS_LABEL[resource.status]}</Badge>}
        </span>
      </div>

      {/* why 是本站与"链接堆砌"的核心区别，所以给它正文级的视觉权重 */}
      <p className="mt-2.5 text-sm leading-relaxed text-muted-foreground">
        <InlineMd text={resource.why} />
      </p>

      <div className="mt-2.5 flex flex-wrap items-center gap-x-3 gap-y-1 text-[11px] text-muted-foreground/70">
        {resource.author && <span>{resource.author}</span>}
        {resource.estimatedMinutes && <span>约 {resource.estimatedMinutes} 分钟</span>}
        <span className="ml-auto">
          核实于 {resource.verifiedAt}
          {resource.verificationLevel === 'search-only' && '（未逐页打开）'}
        </span>
      </div>
    </li>
  );
}

/** 资源列表。空列表时不渲染任何东西，避免页面上出现空标题。 */
export function ResourceList({
  resources,
  title = '延伸阅读',
}: {
  resources: Resource[];
  title?: string;
}) {
  if (resources.length === 0) return null;

  return (
    <section>
      <h2 className="text-sm font-medium">{title}</h2>
      <ul className="mt-4 space-y-3">
        {resources.map((resource) => (
          <ResourceCard key={resource.id} resource={resource} />
        ))}
      </ul>
    </section>
  );
}
