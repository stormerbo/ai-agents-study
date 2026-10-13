#!/usr/bin/env node
// 修复验收：对比 HEAD 基线，确认没有删改既有内容、字数不下降，并汇总改动量。
// 用法：node verify-output/verify-depth-fixes.mjs [--chapter=<id>]
import { readFileSync, readdirSync, statSync, existsSync } from 'node:fs';
import path from 'node:path';

const CUR = 'src/content/chapters';
const BASE = 'verify-output/baseline/src/content/chapters';
const only = (process.argv.find((a) => a.startsWith('--chapter=')) || '').split('=')[1];

// FENCE 展开
const FENCE_RE = new RegExp(String.fromCharCode(96) + String.fromCharCode(96) + String.fromCharCode(96) + '[\\s\\S]*?' + String.fromCharCode(96) + String.fromCharCode(96) + String.fromCharCode(96), 'g');
function m(src) {
  const body = src.replace(/^---[\s\S]*?---/, '').replace(FENCE_RE, '');
  return { cjk: (body.match(/[\u4e00-\u9fff]/g) || []).length, text: body.replace(/\s/g, '').length };
}

// 已批准的「跨章重复内容删除」：第 19 章里混入的第 13 章段落被删掉并改为一行指引
const APPROVED_DEDUP = new Set([
  'human-in-the-loop/01-automation-levels.mdx',
  'human-in-the-loop/02-approval-design.mdx',
  'human-in-the-loop/03-interrupt-and-resume.mdx',
  'human-in-the-loop/05-streaming-and-control.mdx',
]);
let drops = [], approved = [], added = 0, changed = 0, same = 0, rows = [];
for (const ch of readdirSync(CUR).sort()) {
  if (!statSync(path.join(CUR, ch)).isDirectory()) continue;
  if (only && ch !== only) continue;
  for (const f of readdirSync(path.join(CUR, ch)).filter((x) => x.endsWith('.mdx')).sort()) {
    const cur = readFileSync(path.join(CUR, ch, f), 'utf8');
    const bp = path.join(BASE, ch, f);
    if (!existsSync(bp)) { rows.push([ch + '/' + f, 'NEW']); continue; }
    const base = readFileSync(bp, 'utf8');
    const a = m(base), b = m(cur);
    const delta = cur.length - base.length;
    if (cur !== base) { changed++; added += delta; } else same++;
    if ((b.cjk < a.cjk - 5 || b.text < a.text - 30) && APPROVED_DEDUP.has(ch + '/' + f)) approved.push(ch + '/' + f + ' 中文 ' + a.cjk + '→' + b.cjk + '，说明 ' + a.text + '→' + b.text);
    else if (b.cjk < a.cjk - 5 || b.text < a.text - 30) drops.push(ch + '/' + f + ' 中文 ' + a.cjk + '→' + b.cjk + '，说明 ' + a.text + '→' + b.text);
    rows.push([ch + '/' + f, delta > 0 ? '+' + delta : String(delta), a.cjk + '→' + b.cjk]);
  }
}
console.log('改动文件 ' + changed + ' / 未改动 ' + same + '，净增 ' + added + ' 字符');
if (approved.length) { console.log('ℹ️ 已批准的删除（跨章重复内容，已改为指向第 13 章的指引）：'); approved.forEach((d) => console.log('  ' + d)); }
if (drops.length) { console.log('❌ 字数下降的节：'); drops.forEach((d) => console.log('  ' + d)); }
else console.log('✅ 没有实质性的字数下降（容差：中文 -5 / 说明 -30，用于占位符与路径替换）');
if (process.argv.includes('--list')) rows.filter((r) => r[1] !== '0').forEach((r) => console.log('  ' + r.join('\t')));
process.exit(drops.length ? 1 : 0);
