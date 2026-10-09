import Link from 'next/link';

import { SearchDialog } from '@/components/search/search-dialog';
import { ThemeToggle } from './theme-toggle';

const NAV = [
  { href: '/map', label: '知识地图' },
  { href: '/chapters', label: '章节' },
  { href: '/labs', label: '实验' },
  { href: '/resources', label: '资源库' },
  { href: '/about', label: '关于' },
] as const;

export function SiteHeader() {
  return (
    <header className="sticky top-0 z-40 border-b border-border bg-background/80 backdrop-blur-sm">
      {/* 窄屏下的两个必须：
       *   1. 站点名 `shrink-0` —— 否则它会被导航挤成两行
       *   2. 导航 `overflow-x-auto` + 项 `whitespace-nowrap` —— 否则每个中文字会被折成竖排
       *      （加了搜索按钮之后更容易触发；竖向排版的导航看起来像坏了）
       */}
      <div className="mx-auto flex h-14 max-w-6xl items-center gap-3 px-4 sm:gap-6 sm:px-6">
        <Link href="/" className="shrink-0 text-sm font-semibold tracking-tight whitespace-nowrap">
          AI Agent 学习路径
        </Link>

        <nav
          className="-mx-1 flex items-center gap-0.5 overflow-x-auto text-sm text-muted-foreground sm:gap-1"
          aria-label="主导航"
        >
          {NAV.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="rounded-md px-2 py-1.5 whitespace-nowrap transition-colors hover:bg-muted hover:text-foreground sm:px-2.5"
            >
              {item.label}
            </Link>
          ))}
        </nav>

        <div className="ml-auto flex shrink-0 items-center gap-2">
          <SearchDialog />
          <ThemeToggle />
        </div>
      </div>
    </header>
  );
}
