import { describe, expect, it } from 'vitest';
import { execFileSync } from 'node:child_process';
import { readFileSync, readdirSync, statSync } from 'node:fs';
import path from 'node:path';

// 深度门禁：docs/CONTENT-DEPTH.md 里「机器可判」的那一半。
// 五要素中的定义/产物质量仍需人工判断，这里只拦会一眼毁掉可读性的硬错误：
// 占位符、代码块不自包含、用了 os.environ 却没 import os、缺 Mermaid。
describe('深度门禁（docs/CONTENT-DEPTH.md）', () => {
  it('scripts/depth-check.mjs 无硬错误', () => {
    let out = '';
    let status = 0;
    try {
      out = execFileSync('node', ['scripts/depth-check.mjs', '--errors-only'], { encoding: 'utf8' });
    } catch (err) {
      const e = err as { stdout?: string; status?: number };
      out = e.stdout ?? '';
      status = e.status ?? 1;
    }
    expect(out).not.toContain('❌');
    expect(status).toBe(0);
  });

  it('每一节都有 Mermaid 图，且没有裸占位符', () => {
    const root = 'src/content/chapters';
    const sections: string[] = [];
    for (const ch of readdirSync(root)) {
      const dir = path.join(root, ch);
      if (!statSync(dir).isDirectory()) continue;
      for (const f of readdirSync(dir).filter((x) => x.endsWith('.mdx'))) sections.push(path.join(dir, f));
    }
    expect(sections.length).toBe(134);
    for (const p of sections) {
      const src = readFileSync(p, 'utf8');
      expect(src, p + ' 缺 Mermaid').toContain('<Mermaid');
      expect(src, p + ' 有裸占位符').not.toMatch(/@@CODE@@|^\s*CODE\s*$/m);
    }
  });
});
