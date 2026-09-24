import type { Metadata } from 'next';

import { SiteHeader } from '@/components/layout/site-header';
import { ThemeProvider } from '@/components/layout/theme-provider';

import './globals.css';

export const metadata: Metadata = {
  title: {
    default: 'AI Agent 学习路径',
    template: '%s · AI Agent 学习路径',
  },
  description:
    '面向后端工程师的 AI Agent 开发学习路径。从 LLM API 调用到生产化部署，按依赖顺序组织，每个知识点都对照你已经掌握的后端经验。',
};

export default function RootLayout({ children }: LayoutProps<'/'>) {
  return (
    // suppressHydrationWarning 是 next-themes 要求的：它在客户端脚本里改
    // <html> 的 class，服务端渲染的结果必然与之不同。
    <html lang="zh-CN" suppressHydrationWarning>
      <body className="min-h-dvh bg-background font-sans text-foreground antialiased">
        <ThemeProvider>
          <SiteHeader />
          {children}
        </ThemeProvider>
      </body>
    </html>
  );
}
