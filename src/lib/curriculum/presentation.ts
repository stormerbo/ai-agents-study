import type { Lesson } from '@/content/curriculum/schema';

export function getLessonBodyLabel(lesson: Readonly<Pick<Lesson, 'hasBody'>>): '有正文' | '仅大纲' {
  return lesson.hasBody ? '有正文' : '仅大纲';
}

export function getChapterBodyLabel(
  lessons: readonly Readonly<Pick<Lesson, 'hasBody'>>[],
): '正文齐全' | '部分有正文' | '仅有大纲' {
  const bodyCount = lessons.filter((lesson) => lesson.hasBody).length;

  if (bodyCount === lessons.length && lessons.length > 0) return '正文齐全';
  if (bodyCount > 0) return '部分有正文';
  return '仅有大纲';
}
