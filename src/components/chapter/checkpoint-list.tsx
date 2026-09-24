import { getResources } from '@/content/curriculum';
import type { Checkpoint, ClaimBasis } from '@/content/curriculum/schema';
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

export function CheckpointList({ checkpoints }: { checkpoints: Checkpoint[] }) {
  if (checkpoints.length === 0) return null;

  return (
    <ul className="space-y-2">
      {checkpoints.map((cp) => {
        const sources = getResources(cp.sourceIds ?? []);

        return (
          <li key={cp.id}>
            {/* 用原生 details 折叠，不需要任何客户端 JS */}
            <details className="border-border bg-card group rounded-lg border">
              <summary className="cursor-pointer list-none px-4 py-3 text-sm marker:hidden">
                <span className="flex items-baseline gap-2.5">
                  <span
                    aria-hidden
                    className="text-muted-foreground/40 shrink-0 font-mono text-xs transition-transform group-open:rotate-90"
                  >
                    ▸
                  </span>
                  <span>{cp.question}</span>
                </span>
              </summary>

              <div className="border-border border-t px-4 py-3 pl-10">
                <p className="text-muted-foreground text-sm leading-relaxed">{cp.answer}</p>

                <div className="mt-3 flex flex-wrap items-center gap-x-2 gap-y-1">
                  <BasisTag basis={cp.basis} />

                  {sources.map((source) => (
                    <a
                      key={source.id}
                      href={source.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-muted-foreground hover:text-accent border-border rounded border px-1.5 py-px text-[10px] leading-4 underline-offset-2 hover:underline"
                    >
                      {source.title}
                      <span aria-hidden className="ml-0.5">
                        ↗
                      </span>
                    </a>
                  ))}
                </div>

                {cp.note && (
                  <p className="text-muted-foreground/70 border-border/60 mt-2.5 border-l-2 pl-3 text-xs leading-relaxed">
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
