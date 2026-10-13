#!/usr/bin/env node
// 深度门禁：机器可判的「能读懂」检查。标准见 docs/CONTENT-DEPTH.md
// 用法：node scripts/depth-check.mjs [--errors-only] [--chapter=<id>]
import { readFileSync, readdirSync, statSync } from 'node:fs';
import path from 'node:path';

const BT = String.fromCharCode(96);
const FENCE = BT + BT + BT;
const root = 'src/content/chapters';
const args = process.argv.slice(2);
const errorsOnly = args.includes('--errors-only');
const only = (args.find((a) => a.startsWith('--chapter=')) || '').split('=')[1];

const dirs = readdirSync(root).filter((d) => statSync(path.join(root, d)).isDirectory());
const chapters = dirs
  .map((d) => ({ d, order: +(readFileSync(path.join(root, d, 'meta.ts'), 'utf8').match(/order: *(\d+)/) || [])[1] }))
  .filter((c) => !only || c.d === only)
  .sort((a, b) => a.order - b.order);

const TERMS = ['RAG','embedding','嵌入模型','stop_reason','max_tokens','pass@k','Pass^k','few-shot','prefill','Jaccard','poka-yoke','MRTR','TTFE','SSE','TTFT','logits','BPE','水合','感知哈希','思考链'];
const CUE = /(指的是|也就是说|指的是|定义为|相当于|所谓|类比|可以理解为|:.*即|是[^，。]{0,40}(单位|片段|机制|层|函数|协议|字段|过程|结构))/;

const flagged = [];

for (const c of chapters) {
  const dir = path.join(root, c.d);
  const files = readdirSync(dir).filter((f) => f.endsWith('.mdx')).sort();
  const rows = [];
  for (const f of files) {
    const rel = c.d + '/' + f.replace('.mdx', '');
    const src = readFileSync(path.join(dir, f), 'utf8');
    const body = src.replace(/^---[\s\S]*?---/, '');
    const errs = [], warns = [];

    // 逐行解析围栏
    const lines = body.split('\n');
    let inFence = false, lang = '', code = [], noLang = 0, blockCount = 0;
    for (const line of lines) {
      if (line.startsWith(FENCE)) {
        if (!inFence) { inFence = true; blockCount++; lang = line.slice(3).trim(); if (!lang) noLang++; }
        else { inFence = false; }
      } else if (inFence) code.push(line);
    }
    const codeText = code.join('\n');
    const hasArtifact = /\{|\[|</.test(codeText);

    // E1 占位符
    const placeholder = body.split('\n').find((l) => l.trim() === BT + 'CODE' + BT || /@@CODE@@|\bTODO\b|待补/.test(l));
    if (placeholder) errs.push('E1 占位符: ' + placeholder.trim().slice(0, 40));
    // E2 import os
    if (/os\.environ/.test(codeText) && !/import os/.test(codeText)) errs.push('E2 用了 os.environ 但没有 import os');
    // E3 非自包含脚本
    if (/verify-output\//.test(codeText)) errs.push('E3 代码引用了 verify-output/ 下的脚本，读者拿不到');
    // E4 缺 Mermaid
    if (!/<Mermaid/.test(src)) errs.push('E4 缺 Mermaid 图');
    // W1 无产物示例
    const talksArtifact = /(字段|schema|Schema|记录|笔记|轨迹|报文|结构体|manifest)/.test(body);
    if (talksArtifact && !hasArtifact) warns.push('W1 讨论字段/记录/报文但没有产物示例');
    // W2 无错误形态
    if (!/(Error|error|报错|400|401|429|500|Traceback|失败)/.test(body)) warns.push('W2 没有失败形态');
    // W3 无实跑状态
    if (!/(实跑状态|实跑过|已跑通|实测数据|实跑数据)/.test(body)) warns.push('W3 没有实跑标注');
    // W4 代码块无语言
    if (noLang > 0) warns.push('W4 有 ' + noLang + ' 个围栏没标语言（共 ' + blockCount + ' 块）');

    if (errs.length || warns.length) rows.push({ rel, errs, warns });
  }
  const nE = rows.reduce((s, r) => s + r.errs.length, 0);
  const nW = rows.reduce((s, r) => s + r.warns.length, 0);
  if (rows.length) {
    console.log('## ' + c.d + '  (E=' + nE + ' W=' + nW + ')');
    for (const r of rows) {
      if (errorsOnly && !r.errs.length) continue;
      console.log('  ' + r.rel);
      r.errs.forEach((x) => console.log('    ❌ ' + x));
      if (!errorsOnly) r.warns.forEach((x) => console.log('    ⚠️  ' + x));
    }
  }
  flagged.push({ ch: c.d, nE, nW });
}

// 术语首现检查（按章序）
const termFirst = {};
for (const c of chapters) {
  const dir = path.join(root, c.d);
  for (const f of readdirSync(dir).filter((x) => x.endsWith('.mdx')).sort()) {
    const body = readFileSync(path.join(dir, f), 'utf8').replace(/^---[\s\S]*?---/, '');
    for (const t of TERMS) {
      const i = body.indexOf(t);
      if (i >= 0 && !termFirst[t]) termFirst[t] = { rel: c.d + '/' + f.replace('.mdx', ''), term: t, body: body };
    }
  }
}
const noDef = Object.entries(termFirst).filter(([, v]) => !CUE.test(v.body) && v.body.indexOf(v.term + '（') < 0 && v.body.indexOf('**' + v.term + '**') < 0);
console.log('\n## 术语首现无解释（' + noDef.length + '/' + Object.keys(termFirst).length + '）');
for (const [t, v] of noDef) console.log('  ' + t + '  @ ' + v.rel);

const totE = flagged.reduce((s, x) => s + x.nE, 0);
const totW = flagged.reduce((s, x) => s + x.nW, 0);
console.log('\n汇总：硬错误 ' + totE + ' 条，建议项 ' + totW + ' 条');
process.exit(totE ? 1 : 0);
