#!/usr/bin/env node
/**
 * 资源链接巡检。
 *
 * 用法：
 *   node scripts/check-links.mjs
 *   node scripts/check-links.mjs --timeout 20000 --concurrency 8
 *
 * 它只回答一个问题：**这个 URL 现在还打得开吗**。
 *
 * 两个方向的误判都要防：
 * - 打不开 ≠ 内容失效（可能只是反爬、地区封锁或临时故障）
 * - 打得开 ≠ 内容还对（页面还在，但可能已经过时或被换掉）
 *
 * 所以本脚本的定位是**发现线索、辅助人工复审**，不做自动修复。
 * 「内容还对」只能靠人工，这正是 Resource 保留 verifiedAt 字段的原因。
 *
 * 退出码：发现 ≥1 个确认失效的链接时为 1，便于挂进 CI。
 */

import { readdir, readFile } from 'node:fs/promises';
import { join, extname, relative } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = fileURLToPath(new URL('..', import.meta.url));
const SCAN_DIRS = ['src/content'];
const SCAN_EXT = new Set(['.ts', '.tsx', '.mdx', '.md']);

const UA =
  'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 ' +
  '(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36';

/** 示例 / 占位 / 本地域名，不参与巡检 */
const IGNORE_PATTERNS = [
  /^https?:\/\/localhost/,
  /^https?:\/\/127\.0\.0\.1/,
  /example\.com/,
  /acme\.com/,
  /\.local\b/,
];

// ---------------------------------------------------------------------------
// 参数
// ---------------------------------------------------------------------------
const args = process.argv.slice(2);
const readFlag = (name, fallback) => {
  const i = args.indexOf(`--${name}`);
  return i >= 0 && args[i + 1] ? Number(args[i + 1]) : fallback;
};
const TIMEOUT_MS = readFlag('timeout', 20000);
const CONCURRENCY = readFlag('concurrency', 6);

// ---------------------------------------------------------------------------
// 收集
// ---------------------------------------------------------------------------
async function walk(dir) {
  const out = [];
  let entries;
  try {
    entries = await readdir(dir, { withFileTypes: true });
  } catch {
    return out;
  }
  for (const e of entries) {
    const full = join(dir, e.name);
    if (e.isDirectory()) out.push(...(await walk(full)));
    else if (SCAN_EXT.has(extname(e.name))) out.push(full);
  }
  return out;
}

/** 返回 Map<url, Set<相对文件路径>>，用于报告时定位来源 */
async function collectUrls() {
  const found = new Map();
  for (const dir of SCAN_DIRS) {
    for (const file of await walk(join(ROOT, dir))) {
      const text = await readFile(file, 'utf8');
      for (const raw of text.match(/https:\/\/[^\s'"`)\]<>},]+/g) ?? []) {
        // 去掉结尾可能被粘上的标点
        const url = raw.replace(/[.,;:]+$/, '');
        if (IGNORE_PATTERNS.some((re) => re.test(url))) continue;
        if (!found.has(url)) found.set(url, new Set());
        found.get(url).add(relative(ROOT, file));
      }
    }
  }
  return found;
}

// ---------------------------------------------------------------------------
// 检查
// ---------------------------------------------------------------------------

/**
 * 用 GET 而非 HEAD：相当一部分站点（含 GitHub 的部分路径）对 HEAD
 * 返回 405/403，会造成假阳性。拿到响应头后立刻取消 body，避免真下载页面。
 */
async function check(url) {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), TIMEOUT_MS);
  try {
    const res = await fetch(url, {
      method: 'GET',
      redirect: 'follow',
      signal: ctrl.signal,
      headers: {
        'user-agent': UA,
        accept: 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'accept-language': 'en-US,en;q=0.9,zh-CN;q=0.8',
      },
    });
    // 不读 body，直接取消
    if (res.body) await res.body.cancel().catch(() => {});
    return { status: res.status, finalUrl: res.url };
  } catch (err) {
    const aborted = err?.name === 'AbortError';
    return {
      status: 0,
      error: aborted ? `timeout(${TIMEOUT_MS}ms)` : (err?.message ?? String(err)),
    };
  } finally {
    clearTimeout(timer);
  }
}

/** 按并发上限批量执行 */
async function runPool(items, limit, worker) {
  const results = new Array(items.length);
  let cursor = 0;
  const runners = Array.from({ length: Math.min(limit, items.length) }, async () => {
    while (true) {
      const i = cursor++;
      if (i >= items.length) return;
      results[i] = await worker(items[i], i);
    }
  });
  await Promise.all(runners);
  return results;
}

// ---------------------------------------------------------------------------
// 主流程
// ---------------------------------------------------------------------------
const C = {
  reset: '\x1b[0m',
  dim: '\x1b[2m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  bold: '\x1b[1m',
};

const urls = await collectUrls();
const list = [...urls.keys()].sort();
console.log(
  `${C.bold}链接巡检${C.reset} ${C.dim}共 ${list.length} 个唯一 URL，` +
    `超时 ${TIMEOUT_MS}ms，并发 ${CONCURRENCY}${C.reset}\n`,
);

let done = 0;
const results = await runPool(list, CONCURRENCY, async (url) => {
  const r = await check(url);
  done += 1;
  const mark =
    r.status >= 200 && r.status < 400
      ? `${C.green}✓${C.reset}`
      : r.status === 403 || r.status === 429
        ? `${C.yellow}!${C.reset}`
        : `${C.red}✗${C.reset}`;
  process.stdout.write(
    `  ${mark} ${String(r.status || r.error).padEnd(12)} ${url}  ${C.dim}[${done}/${list.length}]${C.reset}\n`,
  );
  return { url, ...r };
});

// ---------------------------------------------------------------------------
// 报告
// ---------------------------------------------------------------------------
const ok = results.filter((r) => r.status >= 200 && r.status < 400);
const blocked = results.filter((r) => r.status === 403 || r.status === 429);
const broken = results.filter(
  (r) => !(r.status >= 200 && r.status < 400) && !(r.status === 403 || r.status === 429),
);

console.log(`\n${C.bold}汇总${C.reset}`);
console.log(`  ${C.green}可达${C.reset}     ${ok.length}`);

if (blocked.length) {
  console.log(
    `  ${C.yellow}被拦截${C.reset}   ${blocked.length}  ${C.dim}(403/429：多半是反爬，需人工打开确认)${C.reset}`,
  );
  for (const r of blocked) {
    console.log(`    ${C.dim}${r.url}${C.reset}  ← ${[...urls.get(r.url)].join(', ')}`);
  }
}

if (broken.length) {
  console.log(`  ${C.red}失效${C.reset}     ${broken.length}  ${C.dim}(优先处理这些)${C.reset}`);
  for (const r of broken) {
    console.log(`    ${C.red}${r.status || r.error}${C.reset}  ${r.url}`);
    console.log(`      ${C.dim}来源: ${[...urls.get(r.url)].join(', ')}${C.reset}`);
  }
}

if (broken.length) {
  console.log(`\n${C.red}有 ${broken.length} 个链接需要处理。${C.reset}`);
  process.exit(1);
}
console.log(`\n${C.green}没有发现确认失效的链接。${C.reset}`);
console.log(`${C.dim}注意：可达不等于内容正确。仍建议按 verifiedAt 定期人工复审。${C.reset}\n`);
