'use client';

import { useTheme } from 'next-themes';
import { useEffect, useId, useState } from 'react';

/**
 * Mermaid 图表。
 *
 * 几个刻意的设计：
 *
 * 1. **动态 import** —— mermaid 是个约 1MB 的依赖，不能让它进首屏 bundle。
 *    只有在页面上真的出现图表时才会被加载。
 * 2. **主题变化时重绘** —— mermaid 在渲染时就固定了配色，切换深浅色必须重新
 *    渲染一次，否则会得到一张白底图贴在深色背景上。
 * 3. **骨架屏而非空白** —— 渲染是异步的，先占住高度的位置，避免内容跳动。
 */

export function Mermaid({ chart }: { chart: string }) {
  const [svg, setSvg] = useState('');
  const [error, setError] = useState<string | null>(null);
  const { resolvedTheme } = useTheme();
  // useId 生成的值含冒号，不能直接用作 DOM id
  const rawId = useId();
  const id = `mermaid-${rawId.replace(/[^a-zA-Z0-9]/g, '')}`;

  useEffect(() => {
    let cancelled = false;

    void (async () => {
      try {
        const mermaid = (await import('mermaid')).default;

        mermaid.initialize({
          startOnLoad: false,
          theme: resolvedTheme === 'dark' ? 'dark' : 'neutral',
          // 图表里的字体跟随正文，否则会和周围排版割裂
          fontFamily: 'inherit',
          securityLevel: 'strict',
        });

        const result = await mermaid.render(id, chart.trim());
        if (!cancelled) {
          setSvg(result.svg);
          setError(null);
        }
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : String(err));
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [chart, id, resolvedTheme]);

  // 图表语法写错时不要把整页搞崩，而是显示原文 + 错误信息
  if (error) {
    return (
      <div className="not-prose my-6 rounded-lg border border-dashed border-border p-4">
        <p className="text-xs text-muted-foreground">
          图表渲染失败（这通常意味着 Mermaid 语法有误）：
        </p>
        <p className="mt-1 font-mono text-xs text-amber-600 dark:text-amber-500">{error}</p>
        <pre className="mt-3 overflow-x-auto text-xs text-muted-foreground">{chart}</pre>
      </div>
    );
  }

  if (!svg) {
    return (
      <div
        aria-hidden
        className="not-prose my-6 h-40 animate-pulse rounded-lg border border-dashed"
      />
    );
  }

  return (
    <div
      className="not-prose my-6 flex justify-center overflow-x-auto"
      // mermaid 产出的是 SVG 字符串。securityLevel: 'strict' 已禁用
      // 图表内的脚本与外部链接，输入来源是本仓库的正文而非用户内容。
      dangerouslySetInnerHTML={{ __html: svg }}
    />
  );
}
