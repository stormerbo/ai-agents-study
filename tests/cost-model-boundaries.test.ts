import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';

describe('cost-and-latency/cost-model displayed local output', () => {
  const lesson = readFileSync('src/content/chapters/cost-and-latency/01-cost-model.mdx', 'utf8');

  it('labels the percentile block as an excerpt and keeps its schema line verbatim', () => {
    expect(lesson).toContain('程序输出摘录（关键结果）');
    expect(lesson).toContain('工具定义情景估算 ≈ 240 token，占输入侧 1999 的 12.0%。');
    expect(lesson).not.toContain('上述本地程序输出：');
  });

  it('links current provider usage and pricing claims to official resources', () => {
    const meta = readFileSync('src/content/chapters/cost-and-latency/meta.ts', 'utf8');
    const resources = readFileSync('src/content/curriculum/resources.ts', 'utf8');
    for (const sourceId of ['claude-pricing', 'deepseek-models-pricing', 'openai-api-pricing']) {
      expect(meta).toContain(`'${sourceId}'`);
      expect(resources).toContain(`id: '${sourceId}'`);
      expect(resources).toContain(`verifiedAt: '2026-10-22'`);
    }
  });
});