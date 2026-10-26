import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

const lesson = readFileSync(
  resolve(process.cwd(), 'src/content/chapters/continuous-evolution/02-distill-and-test.mdx'),
  'utf8',
);

describe('规则提炼发布门禁', () => {
  it('要求候选规则先通过离线评测，再审批并受控发布', () => {
    const workflow = lesson.match(/一条规则从候选到受控发布[\s\S]*?\n\n\*\*四、回滚/)?.[0];
    expect(workflow).toBeDefined();

    const steps = [...workflow!.matchAll(/^\d+\.\s+([^\n]+)/gm)].map((match) => match[1]);
    const offlineEvaluation = steps.findIndex((step) => step?.includes('离线评测'));
    const approval = steps.findIndex((step) => step?.includes('人工审批'));
    const rollout = steps.findIndex((step) => step?.includes('受控发布'));

    expect(offlineEvaluation).toBeGreaterThanOrEqual(0);
    expect(approval).toBeGreaterThan(offlineEvaluation);
    expect(rollout).toBeGreaterThan(approval);
    expect(workflow).toContain('回归');
    expect(workflow).toContain('回滚');
    expect(workflow).toContain('预先写明通过标准');
  });

  it('区分整体指标稀释与是否具备回滚能力', () => {
    expect(lesson).toContain('总体指标的影响可能被稀释');
    expect(lesson).toContain('能否回滚取决于是否保留版本、开关和责任流程');
    expect(lesson).not.toContain('你既看不出有没有用，也无法回滚');
  });

  it('准确描述留出集覆盖范围并定义日期解析契约', () => {
    expect(lesson).toContain('留出输入');
    expect(lesson).toContain('不是 4 个全新的格式族');
    expect(lesson).toContain('18/10/2026` 与训练样本 `15.10.2026`');
    expect(lesson).toContain('20261021` 与 `20261014` 是同一紧凑格式');
    expect(lesson).toContain('DD-MM-YYYY');
    expect(lesson).toContain('UTC 日历日期');
  });
});
