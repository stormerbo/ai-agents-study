import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

/**
 * 渲染**原始 Markdown**（机器生成或外部抓取的内容）。
 *
 * ## 为什么不能用 MDX 管线
 *
 * 手写正文走 MDX 是对的 —— 它能用组件、能语法高亮。但 MDX 不是 Markdown：
 * 它把 `<tag>` 当 JSX、把 `{` 当 JS 表达式。
 *
 * 机器翻译出来的文本里什么都有：原文的 `<instructions>`、JSON 示例的 `{`、README 的
 * `</details>`、以及**数量不保证成对的代码围栏**。这些会让 MDX 构建直接失败 ——
 * 实测时九篇里有七篇编译不过，而且围栏奇偶一乱，转义方案也跟着失效。
 *
 * 所以：**手写内容走 MDX，机器内容走这个组件。** 边界清楚，两边都不用迁就对方。
 */
export function Markdown({ children }: { children: string }) {
  return <ReactMarkdown remarkPlugins={[remarkGfm]}>{children}</ReactMarkdown>;
}
