import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';

describe('cost-and-latency/budget-guardrails input-budget scope', () => {
  it('labels the historical replay as input-only and exposes excluded output usage', () => {
    const lesson = readFileSync('src/content/chapters/cost-and-latency/05-budget-guardrails.mdx', 'utf8');
    expect(lesson).toContain('INPUT_BUDGET');
    expect(lesson).toContain('归一化输入预算');
    expect(lesson).toContain('`output_tokens` 不计入这条输入预算');
    expect(lesson).toContain('不是总 token、费用或完整任务预算');
    expect(lesson).toContain('输出 token 与美元费用需分别纳入任务预算');
    expect(lesson).not.toContain('\nBUDGET = 2000');
  });
});