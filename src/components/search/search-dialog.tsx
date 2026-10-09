'use client';

import { useCallback, useEffect, useRef, useState } from 'react';

import { cn } from '@/lib/utils';
import { loadPagefind } from '@/lib/search/pagefind';

interface Hit {
  id: string;
  title: string;
  url: string;
  excerpt: string;
  /** 命中的小节标题，正文命中时用来提示「在哪个小节里」 */
  sub: string | null;
}

type Status = 'idle' | 'ready' | 'unavailable';

/**
 * 全文搜索。
 *
 * 三个要点：
 *   1. **索引是懒加载的** —— 只有打开搜索框才拉 pagefind.js，首屏零开销
 *   2. **索引不存在时不报错** —— 本地 `pnpm dev` 没跑过 build-search，
 *      这时给一句可读的提示，而不是让页面崩掉
 *   3. **摘录用 dangerouslySetInnerHTML** —— 内容来自 Pagefind 对本站自己页面的索引，
 *      其中的 <mark> 是它加的高亮。这是可以接受的信任边界，但不能推广到任意输入。
 */
export function SearchDialog() {
  const [open, setOpen] = useState(false);
  const [q, setQ] = useState('');
  const [hits, setHits] = useState<Hit[]>([]);
  const [status, setStatus] = useState<Status>('idle');
  const [active, setActive] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const pagefindRef = useRef<Awaited<ReturnType<typeof loadPagefind>> | null>(null);

  // ⌘K / Ctrl+K 打开
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        setOpen((v) => !v);
      }
      if (e.key === 'Escape') setOpen(false);
    }
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);

  // 打开时聚焦输入框
  useEffect(() => {
    if (open) setTimeout(() => inputRef.current?.focus(), 10);
  }, [open]);

  // 首次打开时才加载索引。
  // 注意这里不设 "loading" 状态 —— "还没好" 由 `status === "idle" && open` 推导，
  // 因为**在 effect 体里同步 setState 会触发级联渲染**（eslint react-hooks/set-state-in-effect）。
  useEffect(() => {
    if (!open || pagefindRef.current || status !== 'idle') return;
    let cancelled = false;
    loadPagefind()
      .then(async (pf) => {
        await pf.init?.();
        if (cancelled) return;
        pagefindRef.current = pf;
        setStatus('ready');
      })
      .catch(() => {
        if (!cancelled) setStatus('unavailable');
      });
    return () => {
      cancelled = true;
    };
  }, [open, status]);

  // 检索（带 120ms 防抖）
  useEffect(() => {
    const query = q.trim();
    // 清空查询时重置在 onChange 里做（事件处理器），不在这里 ——
    // effect 体里同步 setState 会触发级联渲染。
    if (!query || status !== 'ready' || !pagefindRef.current) return;

    let cancelled = false;
    const timer = setTimeout(async () => {
      const res = await pagefindRef.current!.search(query);
      const top = await Promise.all(res.results.slice(0, 8).map((r) => r.data()));
      if (cancelled) return;
      setHits(
        top.map((d, i) => ({
          id: res.results[i]!.id,
          title: d.meta.title ?? '未命名',
          url: d.url,
          excerpt: d.excerpt,
          sub: d.sub_results?.[0]?.title ?? null,
        })),
      );
      setActive(0);
    }, 120);
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [q, status]);

  const go = useCallback((url: string) => {
    setOpen(false);
    window.location.href = url;
  }, []);

  function onInputKey(e: React.KeyboardEvent) {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setActive((i) => Math.min(i + 1, hits.length - 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setActive((i) => Math.max(i - 1, 0));
    } else if (e.key === 'Enter' && hits[active]) {
      go(hits[active]!.url);
    }
  }

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="flex items-center gap-2 rounded-md border border-border px-2.5 py-1.5 text-sm text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
        aria-label="搜索"
      >
        <span aria-hidden>⌕</span>
        <span className="hidden sm:inline">搜索</span>
        <kbd className="hidden rounded border border-border bg-muted/60 px-1 font-mono text-[10px] sm:inline">
          ⌘K
        </kbd>
      </button>

      {open && (
        <div
          className="fixed inset-0 z-50 flex items-start justify-center bg-black/40 p-4 pt-[12vh]"
          onClick={() => setOpen(false)}
          role="presentation"
        >
          <div
            className="w-full max-w-xl overflow-hidden rounded-xl border border-border bg-background shadow-lg"
            onClick={(e) => e.stopPropagation()}
            role="dialog"
            aria-modal="true"
            aria-label="全文搜索"
          >
            <div className="flex items-center gap-3 border-b border-border px-4">
              <span aria-hidden className="text-muted-foreground">
                ⌕
              </span>
              <input
                ref={inputRef}
                value={q}
                onChange={(e) => {
                  const v = e.target.value;
                  setQ(v);
                  if (!v.trim()) {
                    setHits([]);
                    setActive(0);
                  }
                }}
                onKeyDown={onInputKey}
                placeholder="搜索全书正文…"
                className="h-12 flex-1 bg-transparent text-sm outline-none placeholder:text-muted-foreground/60"
              />
              <kbd className="rounded border border-border px-1 font-mono text-[10px] text-muted-foreground">
                ESC
              </kbd>
            </div>

            <div className="max-h-[55vh] overflow-y-auto">
              {status === 'unavailable' && (
                <p className="px-4 py-6 text-sm leading-relaxed text-muted-foreground">
                  搜索索引还没生成。先跑 <code className="font-mono text-xs">pnpm build</code> 再跑{' '}
                  <code className="font-mono text-xs">pnpm build-search</code>。
                </p>
              )}
              {status === 'idle' && open && (
                <p className="px-4 py-6 text-sm text-muted-foreground">加载索引…</p>
              )}
              {status === 'ready' && q.trim() && hits.length === 0 && (
                <p className="px-4 py-6 text-sm text-muted-foreground">没有匹配的内容。</p>
              )}
              {status === 'ready' && !q.trim() && (
                <p className="px-4 py-6 text-sm leading-relaxed text-muted-foreground">
                  输入关键词。索引覆盖全书正文（不含代码块内的高频词）。
                </p>
              )}
              {hits.map((h, i) => (
                <button
                  key={h.id}
                  type="button"
                  onMouseEnter={() => setActive(i)}
                  onClick={() => go(h.url)}
                  className={cn(
                    'block w-full border-b border-border/60 px-4 py-3 text-left transition-colors last:border-b-0',
                    i === active ? 'bg-muted' : 'hover:bg-muted/50',
                  )}
                >
                  <span className="block text-sm font-medium">{h.title}</span>
                  {h.sub && (
                    <span className="mt-0.5 block text-[11px] text-muted-foreground/70">
                      {h.sub}
                    </span>
                  )}
                  <span
                    className="mt-1 block text-xs leading-relaxed text-muted-foreground [&_mark]:rounded-[2px] [&_mark]:bg-amber-500/25 [&_mark]:text-foreground"
                    dangerouslySetInnerHTML={{ __html: h.excerpt }}
                  />
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
