'use client';

import { ThemeProvider as NextThemesProvider } from 'next-themes';
import type { ComponentProps } from 'react';

/**
 * next-themes 的 Provider 必须放在客户端组件里（Context 在 Server Component 不可用）。
 * 包一层是为了让根布局保持为 Server Component。
 */
export function ThemeProvider({ children, ...props }: ComponentProps<typeof NextThemesProvider>) {
  return (
    <NextThemesProvider
      // attribute="class" 配合 globals.css 里的 @custom-variant dark
      attribute="class"
      defaultTheme="system"
      enableSystem
      disableTransitionOnChange
      {...props}
    >
      {children}
    </NextThemesProvider>
  );
}
