#!/usr/bin/env node
/**
 * 内容体量统计 —— 对应 AGENTS.md §3.2 的验收标准。
 *
 * 为什么要有脚本：项目一直在用「中文 + 说明文字 + 图 + 代码块」四个指标，
 * 但一直是手工数的（§4.4 说过单看中文会误导）。既然字数进了验收标准，
 * 就不能再靠人眼估。
 *
 * 口径（用标杆 1-1 校准过：应为 中文 3922 / 说明文字 6704）：
 *   中文     = 剔除围栏代码块后的 CJK 字符数
 *   说明文字 = 剔除围栏代码块后的**非空白**字符数
 * 两者都排除 frontmatter；图与代码块单独计数。
 *
 * 用法：node scripts/content-stats.mjs [--chapter=structured-output]
 */
import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join } from 'node:path';

const ROOT = 'src/content/chapters';
const only = process.argv.find((a) => a.startsWith('--chapter='))?.split('=')[1];
const CJK = /[\u4e00-\u9fff]/g;
const FENCE = /\`\`\`[\s\S]*?\`\`\`/g;
const MWD = /<Mermaid[\s\S]*?\/>/g;

const rows = [];
for (const chapter of readdirSync(ROOT)) {
  if (!statSync(join(ROOT, chapter)).isDirectory()) continue;
  if (only && chapter !== only) continue;
  for (const file of readdirSync(join(ROOT, chapter)).filter((f) => f.endsWith('.mdx')).sort()) {
    const raw = readFileSync(join(ROOT, chapter, file), 'utf8').replace(/^---[\s\S]*?---/, '');
    const prose = raw.replace(FENCE, '');
    const cjk = (prose.match(CJK) ?? []).length;
    const text = prose.replace(/\s+/g, '').length;
    rows.push({
      key: chapter + '/' + file.replace(/\.mdx$/, ''),
      cjk, text,
      figures: (raw.match(MWD) ?? []).length,
      codes: (raw.match(FENCE) ?? []).length,
      ok: cjk >= 1500 && text >= 3000,
    });
  }
}
console.log('节'.padEnd(46), '中文'.padStart(6), '说明文字'.padStart(9), '图'.padStart(3), '码'.padStart(3), ' 达标');
console.log('-'.repeat(80));
for (const r of rows) {
  console.log(r.key.padEnd(46), String(r.cjk).padStart(6), String(r.text).padStart(9), String(r.figures).padStart(3), String(r.codes).padStart(3), r.ok ? ' ✅' : ' ❌');
}
console.log('\n共 ' + rows.length + ' 节，达标 ' + rows.filter((r) => r.ok).length + ' 节（标准：中文≥1500 且 说明文字≥3000）');
