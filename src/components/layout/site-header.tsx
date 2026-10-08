import Link from 'next/link';

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
      <div className="mx-auto flex h-14 max-w-6xl items-center gap-6 px-6">
        <Link href="/" className="text-sm font-semibold tracking-tight whitespace-nowrap">
          AI Agent 学习路径
        </Link>

        <nav className="flex items-center gap-1 text-sm text-muted-foreground">
          {NAV.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="rounded-md px-2.5 py-1.5 transition-colors hover:bg-muted hover:text-foreground"
            >
              {item.label}
            </Link>
          ))}
        </nav>

        <div className="ml-auto">
          <ThemeToggle />
        </div>
      </div>
    </header>
  );
}
