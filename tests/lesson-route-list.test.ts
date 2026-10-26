import { createElement } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';

import type { Lesson } from '@/content/curriculum/schema';
import { LessonRouteList } from '@/components/chapter/lesson-route-list';

const lessons: Lesson[] = [
  {
    id: 'chapter-alpha/first',
    chapterId: 'chapter-alpha',
    slug: 'first',
    title: '先建立请求边界',
    summary: '明确模型调用的输入和返回边界。',
    estimatedMinutes: 18,
    difficulty: 'beginner',
    hasBody: true,
    status: 'drafting',
  },
  {
    id: 'chapter-alpha/second',
    chapterId: 'chapter-alpha',
    slug: 'second',
    title: '再处理重试语义',
    summary: '区分可以安全重试与不能重试的失败。',
    estimatedMinutes: 24,
    difficulty: 'intermediate',
    hasBody: false,
    status: 'published',
  },
  {
    id: 'chapter-alpha/third',
    chapterId: 'chapter-alpha',
    slug: 'third',
    title: '最后验证完整链路',
    summary: '用一次端到端演练检验前两节。',
    estimatedMinutes: 32,
    difficulty: 'advanced',
    hasBody: true,
    status: 'planned',
  },
];

const renderRoute = () =>
  renderToStaticMarkup(createElement(LessonRouteList, { chapterId: 'chapter-alpha', lessons }));

describe('LessonRouteList SSR contract', () => {
  it('renders the ordered lesson route with content, body labels, and direct links', () => {
    const html = renderRoute();

    expect(html).toContain('<ol');
    expect(html).toContain('先建立请求边界');
    expect(html).toContain('明确模型调用的输入和返回边界。');
    expect(html).toContain('18 分钟');
    expect(html).toContain('有正文');
    expect(html).toContain('再处理重试语义');
    expect(html).toContain('区分可以安全重试与不能重试的失败。');
    expect(html).toContain('24 分钟');
    expect(html).toContain('仅大纲');
    expect(html).toContain('最后验证完整链路');
    expect(html).toContain('32 分钟');
    expect(html).toContain('href="/chapters/chapter-alpha/first"');
    expect(html).toContain('href="/chapters/chapter-alpha/second"');
    expect(html).toContain('href="/chapters/chapter-alpha/third"');
    expect(html.indexOf('href="/chapters/chapter-alpha/first"')).toBeLessThan(
      html.indexOf('href="/chapters/chapter-alpha/second"'),
    );
    expect(html.indexOf('href="/chapters/chapter-alpha/second"')).toBeLessThan(
      html.indexOf('href="/chapters/chapter-alpha/third"'),
    );
  });

  it('keeps body availability independent from workflow status', () => {
    const html = renderRoute();
    const sameBodyDifferentStatus = lessons.map((lesson, index) => ({
      ...lesson,
      status: (['published', 'planned', 'drafting'] as const)[index]!,
    }));
    const comparison = renderToStaticMarkup(
      createElement(LessonRouteList, {
        chapterId: 'chapter-alpha',
        lessons: sameBodyDifferentStatus,
      }),
    );

    expect(comparison).toBe(html);
    expect(html.match(/有正文/g)).toHaveLength(2);
    expect(html.match(/仅大纲/g)).toHaveLength(1);
    expect(html).not.toContain('drafting');
    expect(html).not.toContain('published');
    expect(html).not.toContain('planned');
  });
});
