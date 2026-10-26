#!/usr/bin/env node
// 修复验收：与显式 Git revision 比较，确认没有未审查的内容下降。
// 用法：node scripts/verify-depth-fixes.mjs --base=HEAD [--chapter=<id>]
import { execFileSync } from 'node:child_process';
import { readFileSync, readdirSync, statSync } from 'node:fs';
import path from 'node:path';

const CUR = 'src/content/chapters';
const args = process.argv.slice(2);
const base = args.find((arg) => arg.startsWith('--base='))?.slice('--base='.length);
const only = args.find((arg) => arg.startsWith('--chapter='))?.split('=')[1];
if (!base) {
  console.error('❌ 必须显式提供 Git 基线 revision：--base=<revision>');
  process.exit(2);
}
try {
  execFileSync('git', ['rev-parse', '--verify', `${base}^{commit}`], { stdio: 'ignore' });
} catch {
  console.error(`❌ 无法解析 Git 基线 revision：${base}`);
  process.exit(2);
}

const FENCE_RE = new RegExp(String.fromCharCode(96) + String.fromCharCode(96) + String.fromCharCode(96) + '[\\s\\S]*?' + String.fromCharCode(96) + String.fromCharCode(96) + String.fromCharCode(96), 'g');
function metrics(src) {
  const body = src.replace(/^---[\s\S]*?---/, '').replace(FENCE_RE, '');
  return { cjk: (body.match(/[\u4e00-\u9fff]/g) || []).length, text: body.replace(/\s/g, '').length };
}

const APPROVED_DEDUP = new Set([
  'human-in-the-loop/01-automation-levels.mdx',
  'human-in-the-loop/02-approval-design.mdx',
  'human-in-the-loop/03-interrupt-and-resume.mdx',
  'human-in-the-loop/05-streaming-and-control.mdx',
]);
let drops = [], approved = [], added = 0, changed = 0, same = 0, rows = [];
for (const chapter of readdirSync(CUR).sort()) {
  if (!statSync(path.join(CUR, chapter)).isDirectory()) continue;
  if (only && chapter !== only) continue;
  for (const file of readdirSync(path.join(CUR, chapter)).filter((name) => name.endsWith('.mdx')).sort()) {
    const relative = `${CUR}/${chapter}/${file}`;
    const current = readFileSync(relative, 'utf8');
    let baseline;
    try {
      baseline = execFileSync('git', ['show', `${base}:${relative}`], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] });
    } catch {
      rows.push([`${chapter}/${file}`, 'NEW']);
      continue;
    }
    const before = metrics(baseline), after = metrics(current);
    const delta = current.length - baseline.length;
    if (current !== baseline) { changed++; added += delta; } else same++;
    if ((after.cjk < before.cjk - 5 || after.text < before.text - 30) && APPROVED_DEDUP.has(`${chapter}/${file}`)) {
      approved.push(`${chapter}/${file} 中文 ${before.cjk}→${after.cjk}，说明 ${before.text}→${after.text}`);
    } else if (after.cjk < before.cjk - 5 || after.text < before.text - 30) {
      drops.push(`${chapter}/${file} 中文 ${before.cjk}→${after.cjk}，说明 ${before.text}→${after.text}`);
    }
    rows.push([`${chapter}/${file}`, delta > 0 ? `+${delta}` : String(delta), `${before.cjk}→${after.cjk}`]);
  }
}
console.log(`基线 ${base}；改动文件 ${changed} / 未改动 ${same}，净增 ${added} 字符`);
if (approved.length) { console.log('ℹ️ 已批准的删除：'); approved.forEach((drop) => console.log(`  ${drop}`)); }
if (drops.length) { console.log('❌ 字数下降的节：'); drops.forEach((drop) => console.log(`  ${drop}`)); }
else console.log('✅ 没有未批准的实质性字数下降（容差：中文 -5 / 说明 -30）');
if (args.includes('--list')) rows.filter((row) => row[1] !== '0').forEach((row) => console.log(`  ${row.join('\\t')}`));
process.exit(drops.length ? 1 : 0);
