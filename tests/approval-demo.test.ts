import { readFileSync } from 'node:fs';
import { createElement } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';

import { ApprovalDemo } from '@/components/mdx/approval-demo';

describe('ApprovalDemo static fixture', () => {
  it('renders four disabled buttons without pretending to submit an approval', () => {
    const html = renderToStaticMarkup(createElement(ApprovalDemo));
    const buttons = [...html.matchAll(/<button\b[^>]*>/g)].map(([tag]) => tag);

    expect(buttons).toHaveLength(4);
    expect(buttons.every((tag) => /\sdisabled(?:="")?(?:\s|>)/.test(tag))).toBe(true);
    expect(html).not.toContain('<form');
    expect(html).not.toContain('action=');
  });

  it('keeps fenced examples narrow enough to read without horizontal scrolling', () => {
    const lesson = readFileSync(
      new URL('../src/content/chapters/tooling/05-agent-ui.mdx', import.meta.url),
      'utf8',
    );
    const fences = [...lesson.matchAll(/^\x60{3}[^\n]*\n([\s\S]*?)^\x60{3}/gm)].map(([, body]) => body ?? '');
    const longLines = fences.flatMap((fence, fenceIndex) =>
      fence.split('\n').flatMap((line, lineIndex) =>
        line.length > 88
          ? ['fence ' + (fenceIndex + 1) + ', line ' + (lineIndex + 1) + ': ' + line.length]
          : [],
      ),
    );

    expect(longLines).toEqual([]);
  });
});
