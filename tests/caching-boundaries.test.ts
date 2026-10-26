import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';

describe('cost-and-latency/caching evidence boundaries', () => {
  const lesson = readFileSync('src/content/chapters/cost-and-latency/03-caching.mdx', 'utf8');

  it('does not label a deterministic prefix ratio as a cache hit rate', () => {
    expect(lesson).toContain('候选可复用比例');
    expect(lesson).toContain('不是 cache hit 率或概率');
    expect(lesson).not.toContain('命中率    命中 token');
    expect(lesson).not.toContain('失效 token');
  });

  it('warns that the short Anthropic placeholder is not cacheable by itself', () => {
    expect(lesson).toContain('占位符不是实际可缓存内容');
    expect(lesson).toContain('当前模型和平台的最小缓存长度');
    expect(lesson).toContain('`cache_control` 只标记候选断点');
  });
});