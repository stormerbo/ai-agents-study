import { createElement } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';

import { getChapters, getChaptersByStage, getStages } from '@/content/curriculum';
import type { Chapter, Lesson, Stage } from '@/content/curriculum/schema';
import { CurriculumNavigation } from '@/components/chapter/curriculum-navigation';

function renderNavigation(props: Parameters<typeof CurriculumNavigation>[0]) {
  return renderToStaticMarkup(createElement(CurriculumNavigation, props));
}

function hasAttribute(attributes: string, name: string) {
  return new RegExp('(?:^|\\s)' + name + '(?:\\s|=|$)').test(attributes);
}

function detailsAttributes(html: string) {
  return [...html.matchAll(/<details([^>]*)>/g)].map((match) => match[1] ?? '');
}

const syntheticStage = {
  id: 'stage-sample',
  order: 1,
  title: '示例阶段',
  tagline: '按顺序学习',
  summary: '用于验证树的语义和顺序。',
  assumedKnowledge: [],
  capstone: '完成示例',
  colorToken: 'stage-1',
} satisfies Stage;

const makeLesson = (chapterId: string, slug: string, title: string, hasBody = true): Lesson => ({
  id: chapterId + '/' + slug,
  chapterId,
  slug,
  title,
  estimatedMinutes: 10,
  difficulty: 'beginner',
  hasBody,
  status: 'published',
});

const syntheticChapters: Chapter[] = [
  {
    id: 'sample-first',
    stageId: syntheticStage.id,
    order: 1,
    title: '第一章',
    summary: '第一章摘要',
    outcomes: [],
    depth: 'deep',
    difficulty: 'beginner',
    estimatedMinutes: 20,
    tags: [],
    prerequisiteIds: [],
    lessons: [
      makeLesson('sample-first', 'opening', '首节'),
      makeLesson('sample-first', 'closing', '末节'),
    ],
    resourceIds: [],
    backendMapping: { analogy: '', transferable: [], pitfalls: [], cost: 'low' },
    status: 'planned',
    updatedAt: '2026-10-26',
    verifiedAt: '2026-10-26',
  },
  {
    id: 'sample-second',
    stageId: syntheticStage.id,
    order: 2,
    title: '第二章',
    summary: '第二章摘要',
    outcomes: [],
    depth: 'guided',
    difficulty: 'intermediate',
    estimatedMinutes: 30,
    tags: [],
    prerequisiteIds: [],
    lessons: [makeLesson('sample-second', 'outline-only', '无正文课', false)],
    resourceIds: [],
    backendMapping: { analogy: '', transferable: [], pitfalls: [], cost: 'medium' },
    status: 'outlined',
    updatedAt: '2026-10-26',
    verifiedAt: '2026-10-26',
  },
];

const syntheticCurriculum = { stages: [syntheticStage], chapters: syntheticChapters };

describe('CurriculumNavigation SSR contract', () => {
  it('renders the entire curriculum tree in registry order with exact route URLs', () => {
    const stages = getStages();
    const chapters = getChapters();
    const allLessons = chapters.flatMap((chapter) => chapter.lessons);
    const currentChapter = chapters[0]!;
    const currentLesson = currentChapter.lessons[0]!;
    const html = renderNavigation({
      currentStageId: currentChapter.stageId,
      currentChapterId: currentChapter.id,
      currentLessonId: currentLesson.id,
    });

    expect(html.match(/<nav\b/g)).toHaveLength(1);
    expect(html).toMatch(
      /<details[^>]*data-curriculum-root[^>]*><summary[^>]*>.*展开课程目录.*收起课程目录.*<\/summary>/,
    );
    expect(html).toMatch(/<nav aria-label="课程目录"/);
    expect(html.match(/<ul\b/g)).toHaveLength(1 + stages.length + chapters.length);
    expect(html.match(/<li\b/g)).toHaveLength(stages.length + chapters.length + allLessons.length);
    expect(html.match(/<summary\b/g)).toHaveLength(1 + stages.length + chapters.length);
    expect(detailsAttributes(html)[0]).not.toMatch(/(?:^|\s)open(?:=|\s|$)/);
    expect(html).toContain('data-curriculum-root');

    const stageIds = [...html.matchAll(/data-stage-id="([^"]+)"/g)].map((match) => match[1]);
    expect(stageIds).toEqual(stages.map((stage) => stage.id));
    const renderedChapterIds = [...html.matchAll(/data-chapter-id="([^"]+)"/g)].map(
      (match) => match[1],
    );
    expect(renderedChapterIds).toEqual(chapters.map((chapter) => chapter.id));

    const chapterHrefs = [...html.matchAll(/<a[^>]*data-chapter-link[^>]*href="([^"]+)"/g)].map(
      (match) => match[1],
    );
    expect(chapterHrefs).toEqual(chapters.map((chapter) => '/chapters/' + chapter.id));
    const lessonHrefs = [...html.matchAll(/<a[^>]*data-lesson-link[^>]*href="([^"]+)"/g)].map(
      (match) => match[1],
    );
    expect(lessonHrefs).toEqual(
      allLessons.map((lesson) => '/chapters/' + lesson.chapterId + '/' + lesson.slug),
    );
    expect(html.match(/aria-current="page"/g)).toHaveLength(1);
    expect(html).toContain('href="/chapters/' + currentChapter.id + '/' + currentLesson.slug + '"');

    const openDetails = detailsAttributes(html).filter((attributes) =>
      hasAttribute(attributes, 'open'),
    );
    expect(openDetails).toHaveLength(2);
    expect(
      openDetails.some((attributes) =>
        attributes.includes('data-stage-id="' + currentChapter.stageId + '"'),
      ),
    ).toBe(true);
    expect(
      openDetails.some((attributes) =>
        attributes.includes('data-chapter-id="' + currentChapter.id + '"'),
      ),
    ).toBe(true);

    for (const stage of stages) {
      const stageStart = html.indexOf('data-stage-id="' + stage.id + '"');
      const summaryStart = html.indexOf('<summary', stageStart);
      const summaryEnd = html.indexOf('</summary>', summaryStart);
      expect(html.slice(summaryStart, summaryEnd)).not.toContain('<a ');
      expect(html.slice(summaryStart, summaryEnd)).toContain(stage.title);
      for (const chapter of getChaptersByStage(stage.id)) {
        expect(html).toContain(chapter.title);
        for (const lesson of chapter.lessons) expect(html).toContain(lesson.title);
      }
    }
  });

  it('keeps each chapter link beside its disclosure and opens only the current path', () => {
    const html = renderNavigation({
      currentStageId: syntheticStage.id,
      currentChapterId: 'sample-second',
      currentLessonId: 'sample-second/outline-only',
      curriculum: syntheticCurriculum,
    });

    expect(html).toMatch(/<nav aria-label="课程目录"/);
    expect(html).toMatch(
      /<a[^>]*data-chapter-link[^>]*href="\/chapters\/sample-first"[^>]*>第 1 章 · 第一章<\/a><details[^>]*data-chapter-id="sample-first"[^>]*><summary[^>]*>/,
    );
    expect(html).toMatch(
      /<a[^>]*data-chapter-link[^>]*href="\/chapters\/sample-second"[^>]*>第 2 章 · 第二章<\/a><details[^>]*data-chapter-id="sample-second"[^>]*open[^>]*><summary[^>]*>/,
    );
    expect(html).toContain('aria-current="page"');
    expect(html).toContain('href="/chapters/sample-first/opening"');
    expect(html).toContain('href="/chapters/sample-first/closing"');
    expect(html).toContain('href="/chapters/sample-second/outline-only"');

    const openDetails = detailsAttributes(html).filter((attributes) =>
      hasAttribute(attributes, 'open'),
    );
    expect(openDetails).toHaveLength(2);
    expect(
      openDetails.some((attributes) =>
        attributes.includes('data-stage-id="' + syntheticStage.id + '"'),
      ),
    ).toBe(true);
    expect(
      openDetails.some((attributes) => attributes.includes('data-chapter-id="sample-second"')),
    ).toBe(true);
    expect(
      openDetails.some((attributes) => attributes.includes('data-chapter-id="sample-first"')),
    ).toBe(false);
  });
});
