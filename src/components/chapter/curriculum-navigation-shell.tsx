'use client';

import { useEffect, useRef, type ReactNode } from 'react';

const DESKTOP_QUERY = '(min-width: 64rem)';

/**
 * The server-rendered tree stays in the parent Server Component. Only this one
 * disclosure root needs client state so its initial value can follow the viewport.
 */
export function CurriculumNavigationShell({ children }: { children: ReactNode }) {
  const detailsRef = useRef<HTMLDetailsElement>(null);

  useEffect(() => {
    const media = window.matchMedia(DESKTOP_QUERY);
    const syncOpenState = (matches: boolean) => {
      if (detailsRef.current) detailsRef.current.open = matches;
    };

    syncOpenState(media.matches);
    const handleChange = (event: MediaQueryListEvent) => syncOpenState(event.matches);
    media.addEventListener('change', handleChange);

    return () => media.removeEventListener('change', handleChange);
  }, []);

  return (
    <details ref={detailsRef} data-curriculum-root className="curriculum-navigation-root">
      <summary className="curriculum-navigation-root-summary min-h-11 cursor-pointer list-none rounded-sm px-3 py-2 font-medium marker:hidden focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent">
        <span className="curriculum-navigation-root-collapsed-label">展开课程目录</span>
        <span className="curriculum-navigation-root-expanded-label">收起课程目录</span>
      </summary>
      {children}
    </details>
  );
}
