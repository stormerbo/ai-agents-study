import { describe, expect, it } from 'vitest';

import { estimateImageTokens } from '@/components/lab/image-attach';

/**
 * 第 8 章的实测阶梯（deepseek-flash，2026-10-08，方形图，单次调用）：
 *   512² → 186（下限）  640² → 276  768² → 384  896² → 510
 *   1024² → 654        1280² → 996（上限）  2048² → 996  3000² → 996
 *
 * `estimateImageTokens` 是照着这条阶梯拟合出来的估算函数，用在实际发送前的
 * UI 提示上。这里只锚定两件**结构上确定**的事（下限与上限），中间段给 2% 容差 ——
 * 它是估算，不该被当成精确公式（第 8 章也记录过文档里那条公式在本端点上对不上）。
 */
describe('estimateImageTokens', () => {
  it('≤512px 一律取下限 186（实测 64²/256²/512² 完全相同）', () => {
    expect(estimateImageTokens(64, 64)).toBe(186);
    expect(estimateImageTokens(256, 256)).toBe(186);
    expect(estimateImageTokens(512, 512)).toBe(186);
    expect(estimateImageTokens(10, 4000)).toBe(186);
  });

  it('≥1280px 一律取上限 996（实测 1280/1568/2048/3000 完全相同，服务端会缩）', () => {
    expect(estimateImageTokens(1280, 1280)).toBe(996);
    expect(estimateImageTokens(2048, 2048)).toBe(996);
    expect(estimateImageTokens(3000, 3000)).toBe(996);
  });

  it('中间段与实测阶梯的误差在 2% 以内', () => {
    const measured: [number, number, number][] = [
      [640, 640, 276],
      [768, 768, 384],
      [896, 896, 510],
      [1024, 1024, 654],
    ];
    for (const [w, h, want] of measured) {
      const got = estimateImageTokens(w, h);
      expect(Math.abs(got - want) / want).toBeLessThan(0.02);
    }
  });

  it('单调不减，且永远落在 [186, 996] 内', () => {
    let prev = 0;
    for (let edge = 8; edge <= 4096; edge += 8) {
      const tok = estimateImageTokens(edge, edge);
      expect(tok).toBeGreaterThanOrEqual(186);
      expect(tok).toBeLessThanOrEqual(996);
      expect(tok).toBeGreaterThanOrEqual(prev);
      prev = tok;
    }
  });
});
