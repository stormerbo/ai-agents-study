import { readFileSync } from 'node:fs';
import { renderToStaticMarkup } from 'react-dom/server';
import { createElement } from 'react';

import { describe, expect, it } from 'vitest';

import { ProjectDetails } from '@/components/chapter/project-details';
import { curriculum } from '@/content/curriculum';

describe('stage project visibility', () => {
  it('renders full project acceptance criteria and independent hard gates on chapter pages', () => {
    const markup = renderToStaticMarkup(
      createElement(ProjectDetails, { project: curriculum.projects['p4-durable-support']! }),
    );
    expect(markup).toContain('跨租户读取或检索必须全部被拒绝');
    expect(markup).toContain('交付要求');
    expect(markup).toContain('里程碑');
    expect(markup).toContain('独立硬性门槛');
    expect(markup).toContain('自评 rubric');
  });

  it('shows a runnable reference implementation when a project has one', () => {
    const markup = renderToStaticMarkup(
      createElement(ProjectDetails, { project: curriculum.projects['p2-grounded-support']! }),
    );
    expect(markup).toContain('参考实现');
    expect(markup).toContain('examples/p2-grounded-support');
    expect(markup).toContain('离线');
    expect(markup).toContain('grounded_support.py --evaluate');
  });

  it('mounts the detailed project specification inside the chapter-stage project card', () => {
    const source = readFileSync('src/app/chapters/[chapterId]/page.tsx', 'utf8');
    expect(source).toContain('<ProjectDetails project={project} />');
  });
});
