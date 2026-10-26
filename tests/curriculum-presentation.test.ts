import { describe, expect, it } from 'vitest';

import type { ContentStatus, Lesson } from '@/content/curriculum/schema';
import { getChapterBodyLabel, getLessonBodyLabel } from '@/lib/curriculum/presentation';

const statuses: readonly ContentStatus[] = ['planned', 'outlined', 'drafting', 'published'];

describe('curriculum presentation body labels', () => {
  it.each(
    statuses.flatMap((status) => [
      { hasBody: true, status },
      { hasBody: false, status },
    ]),
  )('uses hasBody rather than the $status workflow status', ({ hasBody, status }) => {
    const lesson = { hasBody, status };
    expect(getLessonBodyLabel(lesson)).toBe(hasBody ? '有正文' : '仅大纲');
  });

  it('aggregates chapter body labels from lesson hasBody values only', () => {
    const lessons: readonly Pick<Lesson, 'hasBody'>[] = [
      { hasBody: true },
      { hasBody: true },
      { hasBody: false },
      { hasBody: false },
    ];

    expect(getChapterBodyLabel(lessons.slice(0, 2))).toBe('正文齐全');
    expect(getChapterBodyLabel(lessons.slice(1, 3))).toBe('部分有正文');
    expect(getChapterBodyLabel(lessons.slice(2))).toBe('仅有大纲');
    expect(getChapterBodyLabel([])).toBe('仅有大纲');
  });
});
