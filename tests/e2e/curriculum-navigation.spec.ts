import { expect, test, type Locator, type Page } from '@playwright/test';

const startPath = '/chapters/what-is-an-agent/why-now';
const sameChapterPath = '/chapters/what-is-an-agent/what-counts-as-agent';
const crossChapterPath = '/chapters/prompt-engineering/instruction-clarity';
const crossStagePath = '/chapters/llm-api-basics/tokens-and-context';

const stageIds = [
  'stage-0-orientation',
  'stage-1-foundation',
  'stage-2-primitives',
  'stage-3-orchestration',
  'stage-4-production',
  'stage-5-practice',
];

function stageDetails(nav: Locator, stageId: string) {
  return nav.locator(`details[data-stage-id="${stageId}"]`);
}

function chapterDetails(nav: Locator, chapterId: string) {
  return nav.locator(`details[data-chapter-id="${chapterId}"]`);
}

async function expectOnlyCurrentPathExpanded(
  nav: Locator,
  currentStageId: string,
  currentChapterId: string,
) {
  for (const stageId of stageIds) {
    const stage = stageDetails(nav, stageId);
    if (stageId === currentStageId) {
      await expect(stage).toHaveAttribute('open', '');
    } else {
      await expect(stage).not.toHaveAttribute('open');
    }
  }

  const chapters = nav.locator('details[data-chapter-id]');
  for (let index = 0; index < (await chapters.count()); index += 1) {
    const chapter = chapters.nth(index);
    if ((await chapter.getAttribute('data-chapter-id')) === currentChapterId) {
      await expect(chapter).toHaveAttribute('open', '');
    } else {
      await expect(chapter).not.toHaveAttribute('open');
    }
  }
}

async function expectCurrentLesson(page: Page, title: string, path: string) {
  await expect(page).toHaveURL(new RegExp(`${path.replaceAll('/', '\\/')}$`));
  const nav = page.getByRole('navigation', { name: '课程目录' });
  await expect(nav.getByRole('link', { name: title, exact: true })).toHaveAttribute(
    'aria-current',
    'page',
  );
  return nav;
}

test('lesson navigation disclosures reset on Link and browser history transitions', async ({
  page,
}) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto(startPath);

  const nav = page.getByRole('navigation', { name: '课程目录' });
  await expect(nav).toBeVisible();
  await expectCurrentLesson(page, '为什么现在更容易把 agent 做成工程系统', startPath);
  await expectOnlyCurrentPathExpanded(nav, 'stage-0-orientation', 'what-is-an-agent');

  // Expand a non-current stage and chapter, then confirm the same route retains them.
  const orchestration = stageDetails(nav, 'stage-3-orchestration');
  await orchestration.locator(':scope > summary').click();
  const agentLoop = chapterDetails(nav, 'agent-loop');
  await agentLoop.locator(':scope > summary').click();
  await expect(orchestration).toHaveAttribute('open', '');
  await expect(agentLoop).toHaveAttribute('open', '');
  await expect(page).toHaveURL(new RegExp(`${startPath.replaceAll('/', '\\/')}$`));

  // A real Next Link transition within the current chapter resets other branches.
  await nav.getByRole('link', { name: '什么算 agent，什么不算', exact: true }).click();
  await expectCurrentLesson(page, '什么算 agent，什么不算', sameChapterPath);
  await expectOnlyCurrentPathExpanded(nav, 'stage-0-orientation', 'what-is-an-agent');

  // Navigate to a different chapter within the same stage through its lesson link.
  const foundation = stageDetails(nav, 'stage-1-foundation');
  await foundation.locator(':scope > summary').click();
  const promptChapter = chapterDetails(nav, 'prompt-engineering');
  await promptChapter.locator(':scope > summary').click();
  await nav.getByRole('link', { name: '清晰直接：把“暗示”换成“明说”', exact: true }).click();
  await expectCurrentLesson(page, '清晰直接：把“暗示”换成“明说”', crossChapterPath);
  await expectOnlyCurrentPathExpanded(nav, 'stage-1-foundation', 'prompt-engineering');

  // Expand another chapter in the current stage before crossing stages.
  const llmChapter = chapterDetails(nav, 'llm-api-basics');
  await llmChapter.locator(':scope > summary').click();
  await expect(llmChapter).toHaveAttribute('open', '');

  await nav.getByRole('link', { name: 'token 与上下文窗口：真正的稀缺资源', exact: true }).click();
  await expectCurrentLesson(page, 'token 与上下文窗口：真正的稀缺资源', crossStagePath);
  await expectOnlyCurrentPathExpanded(nav, 'stage-1-foundation', 'llm-api-basics');

  await page.goBack();
  await expectCurrentLesson(page, '清晰直接：把“暗示”换成“明说”', crossChapterPath);
  await expectOnlyCurrentPathExpanded(nav, 'stage-1-foundation', 'prompt-engineering');

  await page.goForward();
  await expectCurrentLesson(page, 'token 与上下文窗口：真正的稀缺资源', crossStagePath);
  await expectOnlyCurrentPathExpanded(nav, 'stage-1-foundation', 'llm-api-basics');
});

test('lesson pages expose the named curriculum navigation and current lesson', async ({ page }) => {
  await page.goto(startPath);

  const nav = page.getByRole('navigation', { name: '课程目录' });
  await expect(nav).toBeVisible();
  await expectCurrentLesson(page, '为什么现在更容易把 agent 做成工程系统', startPath);
});

test('desktop lesson pages place curriculum navigation left of recommendations', async ({
  page,
}) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto(startPath);

  const directory = page.locator('[data-lesson-curriculum-rail]');
  const recommendations = page.locator('[data-lesson-recommendations-rail]');
  await expect(directory.getByRole('navigation', { name: '课程目录' })).toBeVisible();
  await expect(recommendations).toBeVisible();
  await expect(recommendations.locator('details > summary')).toContainText('篇');

  const positions = await directory.evaluate((left) => {
    const right = document.querySelector('[data-lesson-recommendations-rail]')!;
    const leftRect = left.getBoundingClientRect();
    const rightRect = right.getBoundingClientRect();
    return { leftX: leftRect.x, leftRight: leftRect.right, rightX: rightRect.x };
  });
  expect(positions.leftX).toBeLessThan(positions.rightX);
  expect(positions.leftRight).toBeLessThan(positions.rightX);

  const verticalGap = await page.evaluate(() => {
    const heading = document.querySelector('h1')!;
    const article = document.querySelector('article')!;
    return article.getBoundingClientRect().top - heading.getBoundingClientRect().bottom;
  });
  expect(verticalGap).toBeLessThan(120);
});
test('curriculum navigation stays responsive and its disclosure remains keyboard-operable', async ({
  page,
}) => {
  for (const viewport of [
    { width: 1440, height: 900 },
    { width: 1024, height: 900 },
    { width: 1280, height: 640 },
    { width: 640, height: 400 },
    { width: 320, height: 640 },
    { width: 375, height: 812 },
  ]) {
    await page.setViewportSize(viewport);
    await page.goto(startPath);

    const root = page.locator('[data-curriculum-root]');
    const summary = root.locator(':scope > summary');
    const measure = async () =>
      page.evaluate(() => {
        const details = document.querySelector('[data-curriculum-root]') as HTMLDetailsElement;
        const summary = details.querySelector(':scope > summary')!;
        const auxiliary = document.querySelector('.lesson-directory-auxiliary')!;
        const recommendations = document.querySelector('[data-lesson-recommendations-rail]');
        const article = document.querySelector('article')!;
        const recommendationsRail = document.querySelector('[data-lesson-recommendations-rail]');
        const rect = (node: Element) => {
          const { x, y, width, height } = node.getBoundingClientRect();
          return { x, y, width, height };
        };
        return {
          clientWidth: document.documentElement.clientWidth,
          scrollWidth: document.documentElement.scrollWidth,
          rootOpen: details.open,
          summary: rect(summary),
          auxiliary: rect(auxiliary),
          recommendations: recommendations ? rect(recommendations) : null,
          position: getComputedStyle(auxiliary).position,
          article: rect(article),
          recommendationsAfterArticle:
            !recommendationsRail ||
            (recommendationsRail.compareDocumentPosition(article) &
              Node.DOCUMENT_POSITION_PRECEDING) !==
              0,
        };
      });
    const measurements = await measure();

    expect(measurements.scrollWidth).toBe(measurements.clientWidth);
    if (viewport.width < 1024) {
      expect(measurements.rootOpen).toBe(false);
      expect(measurements.summary.height).toBeGreaterThanOrEqual(44);
      expect(measurements.article.y).toBeGreaterThan(measurements.auxiliary.y);
    }
    if (viewport.width >= 1024 && viewport.height < 720) {
      expect(measurements.position).toBe('static');
      expect(measurements.summary.width).toBeGreaterThan(0);
    }
    if (viewport.width < 1024) {
      expect(measurements.article.y).toBeGreaterThan(
        measurements.auxiliary.y + measurements.auxiliary.height,
      );
      expect(measurements.recommendationsAfterArticle).toBe(true);
    }
    if (viewport.width >= 1024) {
      expect(measurements.recommendations).not.toBeNull();
      expect(measurements.recommendations!.x).toBeGreaterThan(
        measurements.article.x + measurements.article.width,
      );
    }
    if (viewport.width >= 1024 && viewport.height >= 720) {
      expect(measurements.position).toBe('sticky');
    }

    const target = (await summary.isVisible())
      ? summary
      : page
          .getByRole('navigation', { name: '课程目录' })
          .locator('details[data-stage-id] > summary')
          .first();
    const details = target.locator('xpath=..');
    const wasOpen = await details.evaluate((node) => (node as HTMLDetailsElement).open);
    await target.focus();
    await expect(target).toBeFocused();
    await target.press('Enter');
    expect(await details.evaluate((node) => (node as HTMLDetailsElement).open)).toBe(!wasOpen);
    const afterEnter = await details.evaluate((node) => (node as HTMLDetailsElement).open);
    await target.press('Space');
    expect(await details.evaluate((node) => (node as HTMLDetailsElement).open)).toBe(!afterEnter);
  }
});

test('chapter metadata, stage labels and chapter number meet contrast thresholds in both themes', async ({
  page,
}) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto('/chapters');

  for (const theme of ['light', 'dark']) {
    await page.evaluate((mode) => localStorage.setItem('theme', mode), theme);
    await page.reload();
    const html = page.locator('html');
    if (theme === 'dark') await expect(html).toHaveClass(/\bdark\b/);
    else await expect(html).not.toHaveClass(/\bdark\b/);

    const ratios = await page.evaluate(() => {
      function srgb(value: number) {
        const normalized = value / 255;
        return normalized <= 0.04045 ? normalized / 12.92 : ((normalized + 0.055) / 1.055) ** 2.4;
      }
      function luminance(color: string) {
        const context = document.createElement('canvas').getContext('2d')!;
        context.fillStyle = color;
        context.fillRect(0, 0, 1, 1);
        const pixel = context.getImageData(0, 0, 1, 1).data;
        return 0.2126 * srgb(pixel[0]!) + 0.7152 * srgb(pixel[1]!) + 0.0722 * srgb(pixel[2]!);
      }
      function contrast(foreground: string, background: string) {
        const first = luminance(foreground);
        const second = luminance(background);
        return (Math.max(first, second) + 0.05) / (Math.min(first, second) + 0.05);
      }
      function backgroundOf(node: Element) {
        for (let current: Element | null = node; current; current = current.parentElement) {
          const background = getComputedStyle(current).backgroundColor;
          if (background !== 'rgba(0, 0, 0, 0)' && background !== 'transparent') return background;
        }
        return getComputedStyle(document.documentElement).backgroundColor;
      }
      const ratioFor = (selector: string) => {
        const node = document.querySelector(selector)!;
        return contrast(getComputedStyle(node).color, backgroundOf(node));
      };
      return {
        metadata: ratioFor('[data-chapter-metadata]'),
        chapter: ratioFor('[data-chapter-order]'),
        stages: [...document.querySelectorAll('[data-stage-label]')].map((node) =>
          contrast(getComputedStyle(node).color, backgroundOf(node)),
        ),
      };
    });

    expect(ratios.metadata, 'metadata contrast ' + theme).toBeGreaterThanOrEqual(4.5);
    expect(ratios.chapter, 'chapter number contrast ' + theme).toBeGreaterThanOrEqual(4.5);
    for (const [index, ratio] of ratios.stages.entries()) {
      expect(ratio, 'stage ' + index + ' contrast ' + theme).toBeGreaterThanOrEqual(4.5);
    }
  }
});
