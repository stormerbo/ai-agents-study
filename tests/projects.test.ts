import { describe, expect, it } from 'vitest';

import { curriculum } from '@/content/curriculum';

describe('stage projects', () => {
  it('registers one after-sales support project for stages 1 through 5', () => {
    const expected = [
      'p1-reliable-extraction',
      'p2-grounded-support',
      'p3-controlled-agent',
      'p4-durable-support',
      'p5-agent-delivery',
    ];
    expect(Object.keys(curriculum.projects).sort()).toEqual(expected.sort());
    for (const project of Object.values(curriculum.projects)) {
      expect(`${project.brief} ${project.requirements.join(' ')}`).toContain('售后订单');
    }
  });

  it('keeps production security invariants outside the compensating rubric score', () => {
    for (const id of ['p4-durable-support', 'p5-agent-delivery']) {
      expect(curriculum.projects[id]?.hardGates?.length).toBeGreaterThan(0);
    }
  });

  it('keeps the first three stage projects independently scoped', () => {
    expect(curriculum.projects['p1-reliable-extraction']?.constraints).toContain(
      '不得使用厂商强制 Schema；本阶段练习提示设计与代码校验。',
    );
    expect(curriculum.projects['p2-grounded-support']?.constraints.join(' ')).toContain(
      '哈希向量仅用于验证管线控制流，不可报告成真实语义检索效果。',
    );
    expect(curriculum.projects['p3-controlled-agent']?.requirements).toContain(
      '至少完成一次真实模型工具往返；离线 fixture 结果单独标为控制流验证。',
    );
  });
});

describe('grounded support reference project', () => {
  it('links the stage-2 project to a runnable offline implementation and evidence limits', () => {
    const project = curriculum.projects['p2-grounded-support'];
    expect(project?.referenceImpl?.repo).toBe('examples/p2-grounded-support');
    expect(project?.referenceImpl?.notes).toContain('离线');
    expect(project?.referenceImpl?.notes).toContain('embedding');
  });
});
