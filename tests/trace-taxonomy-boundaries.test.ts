import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

const lesson = readFileSync(
  resolve(process.cwd(), 'src/content/chapters/continuous-evolution/01-from-traces.mdx'),
  'utf8',
);

describe('轨迹学习分类边界', () => {
  it('区分参数版本回退与对单条行为变化的精确解释', () => {
    expect(lesson).toContain('回滚到已保存的模型版本');
    expect(lesson).toContain('不等于精确撤销某一类行为变化');
    expect(lesson).not.toContain('也无法精确回滚');
  });

  it('不把低知识命中数当作自动淘汰依据', () => {
    expect(lesson).toContain('低命中不等于无价值');
    expect(lesson).toContain('候选复核');
    expect(lesson).toContain('低频高风险');
    expect(lesson).not.toContain('→ 候选淘汰');
  });

  it('把代码方案的运行优势与实现成本分开评估', () => {
    expect(lesson).toContain('减少每次把相同判断交给模型');
    expect(lesson).toContain('实现成本取决于现有架构');
    expect(lesson).not.toContain('写成代码更便宜');
  });
});
