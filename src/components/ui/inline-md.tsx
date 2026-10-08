import type { ReactNode } from 'react';

/**
 * 把带行内标记的文本降级为纯文本。
 *
 * 用于 **不能放 JSX** 的位置：`<meta name="description">`、SVG 的 `<title>`、
 * 传给 `String.prototype` 的地方。不做这一步，`**强调**` 会原样出现在
 * 页面描述与悬浮提示里。
 */
export function plainText(text?: string | null): string {
  if (!text) return '';
  return text.replace(/\*\*([^*]+)\*\*/g, '$1').replace(/`([^`]+)`/g, '$1');
}

/**
 * 行内 Markdown 渲染器：只支持 `**粗体**` 与 `` `代码` ``。
 *
 * 为什么需要它：`meta.ts` 里的纯文本字段（章节摘要、自检项、资源推荐理由、
 * 实验目标、后端对照等）不走 MDX 管线，是直接插进 JSX 的字符串。但内容是
 * 按 Markdown 写的 —— `**强调**` 会原样显示成星号。
 *
 * 这是个**静默失效**：构建通过、页面正常、内容完整，只有肉眼能看出来。
 * 与 AGENTS.md §4.1 的代码块配色问题是同一类 —— 关掉了某个默认行为，
 * 却没有补上自己的实现。纯文本字段里要写强调，就用这个组件渲染。
 */
export function InlineMd({ text }: { text?: string | null }): ReactNode {
  if (!text) return null;

  // 必须返回**单个**元素，不能返回 Fragment：调用方的父容器常常是 flex/grid
  // （例如章节日里的「可以直接迁移」列表用 flex 排版）。Fragment 的多个子节点
  // 会各自成为一个 flex item，把一句完整的话拆成并排的几列。
  // 这是 §4.8 的同一个静默失效家族 —— 构建通过、页面不报错，只有肉眼能看出。
  return (
    <span>
      {text.split(/(\*\*[^*]+\*\*|`[^`]+`)/g).map((token, i) => {
        if (token.length > 4 && token.startsWith('**') && token.endsWith('**')) {
          return (
            <strong key={i} className="text-foreground font-semibold">
              {token.slice(2, -2)}
            </strong>
          );
        }
        if (token.length > 2 && token.startsWith('`') && token.endsWith('`')) {
          return (
            <code
              key={i}
              className="bg-muted rounded px-1 py-0.5 font-mono text-[0.85em] whitespace-nowrap"
            >
              {token.slice(1, -1)}
            </code>
          );
        }
        return token;
      })}
    </span>
  );
}
