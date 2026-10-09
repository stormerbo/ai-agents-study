import type { MDXComponents } from 'mdx/types';

import { Mermaid } from '@/components/mdx/mermaid';
import { ApprovalDemo } from '@/components/mdx/approval-demo';

/**
 * MDX 的全局组件映射。
 *
 * 两个容易踩的点：
 * 1. 用 `src/app` 时，这个文件必须放在 `src/` 下（与 app 同级）—— 放错位置 MDX 会静默不工作。
 * 2. Next 16 里 `useMDXComponents` **不接受参数**（与旧版不同），直接返回映射即可。
 */

/** 外链自动加 target 与 rel，并补一个可感知的箭头标记 */
function Anchor({ href = '', children, ...props }: React.ComponentProps<'a'>) {
  const isExternal = /^https?:\/\//.test(href);

  return (
    <a
      href={href}
      {...(isExternal ? { target: '_blank', rel: 'noopener noreferrer' } : {})}
      {...props}
    >
      {children}
      {isExternal && (
        <span aria-hidden className="text-muted-foreground ml-0.5 text-xs">
          ↗
        </span>
      )}
    </a>
  );
}

/** 表格在窄屏下横向滚动，避免撑破正文栏 */
function Table(props: React.ComponentProps<'table'>) {
  return (
    <div className="overflow-x-auto">
      <table {...props} />
    </div>
  );
}

export function useMDXComponents(): MDXComponents {
  return {
    a: Anchor,
    table: Table,
    Mermaid,
    ApprovalDemo,
  };
}
