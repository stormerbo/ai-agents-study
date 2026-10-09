#!/usr/bin/env node
/**
 * API 连通性与行为验证。
 *
 * 用法：node scripts/verify-api.mjs
 *
 * 它做两件事：
 * 1. 确认凭据可用（把 Key 从 .env.local 读出来，全程不打印）
 * 2. 采集后续写正文要用的**真实数据**：token 计数、流式事件序列、错误响应原文
 *
 * 这是「教科书级内容」的前提 —— 真实错误案例与对比实验数据只能这样得到，
 * 编不出来。
 *
 * 输出会被保存到 `verify-output/` 目录（已 gitignore），正文引用时从这里取。
 */

import { mkdir, writeFile } from 'node:fs/promises';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { join } from 'node:path';

const ROOT = fileURLToPath(new URL('..', import.meta.url));
const OUT_DIR = join(ROOT, 'verify-output');

// ---------------------------------------------------------------------------
// 读取 .env.local（不打印任何值）
// ---------------------------------------------------------------------------

function loadEnvLocal() {
  const path = join(ROOT, '.env.local');
  let raw;
  try {
    raw = readFileSync(path, 'utf8');
  } catch {
    fail(`找不到 ${path}\n请先创建 .env.local 并填入凭据（可参考 .env.example）。`);
  }

  const env = {};
  for (const line of raw.split('\n')) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith('#')) continue;
    const eq = trimmed.indexOf('=');
    if (eq === -1) continue;
    const key = trimmed.slice(0, eq).trim();
    const value = trimmed
      .slice(eq + 1)
      .trim()
      .replace(/^["']|["']$/g, '');
    if (value) env[key] = value;
  }
  return env;
}

function fail(message) {
  console.error('\n✗ ' + message + '\n');
  process.exit(1);
}

// ---------------------------------------------------------------------------
// 组装请求头 / 地址
// ---------------------------------------------------------------------------

const env = loadEnvLocal();
const baseUrl = (env.ANTHROPIC_BASE_URL || 'https://api.anthropic.com').replace(/\/+$/, '');
const model = env.VERIFY_MODEL || env.ANTHROPIC_MODEL || '';

/**
 * 认证方式候选。
 *
 * 两种说法在公开资料里同时存在：DeepSeek 的文档说 Anthropic 兼容端点
 * 「x-api-key 完全支持」，而 Claude Code 那套集成用的是
 * ANTHROPIC_AUTH_TOKEN（也就是 Authorization: Bearer）。
 * 与其猜哪个对，不如都试一遍，用第一个成功的。
 */
const authCandidates = [];
if (env.ANTHROPIC_API_KEY) {
  authCandidates.push({ label: 'x-api-key', headers: { 'x-api-key': env.ANTHROPIC_API_KEY } });
}
if (env.ANTHROPIC_AUTH_TOKEN) {
  authCandidates.push({
    label: 'x-api-key (取自 AUTH_TOKEN)',
    headers: { 'x-api-key': env.ANTHROPIC_AUTH_TOKEN },
  });
  authCandidates.push({
    label: 'Authorization: Bearer',
    headers: { authorization: `Bearer ${env.ANTHROPIC_AUTH_TOKEN}` },
  });
}
if (authCandidates.length === 0) {
  fail('.env.local 里既没有 ANTHROPIC_AUTH_TOKEN 也没有 ANTHROPIC_API_KEY。');
}

/** 首个验证成功的认证方式，后续检查项复用它 */
let activeAuth = null;

const headers = (auth = activeAuth ?? authCandidates[0]) => ({
  'content-type': 'application/json',
  'anthropic-version': '2023-06-01',
  ...auth.headers,
});

const maskUrl = (u) => u;

// ---------------------------------------------------------------------------
// 检查项
// ---------------------------------------------------------------------------

const results = [];

async function record(name, fn) {
  process.stdout.write(`  ${name} ... `);
  try {
    const r = await fn();
    results.push({ name, ok: true, ...r });
    console.log(r.summary ?? '✓');
  } catch (err) {
    results.push({ name, ok: false, error: String(err?.message ?? err) });
    console.log('✗ ' + String(err?.message ?? err).slice(0, 120));
  }
}

/** 1. 基本调用 —— 同时用来确定可用的认证方式与模型名 */
async function basicCall() {
  const attempts = [];

  for (const auth of authCandidates) {
    const res = await fetch(`${baseUrl}/v1/messages`, {
      method: 'POST',
      headers: headers(auth),
      body: JSON.stringify({
        model,
        max_tokens: 64,
        messages: [{ role: 'user', content: '只回复两个字：收到' }],
      }),
    });
    const text = await res.text();

    if (res.ok) {
      activeAuth = auth;
      const data = JSON.parse(text);
      return {
        data,
        authLabel: auth.label,
        summary: `✓ 认证方式「${auth.label}」· 模型 ${data.model} · 输出 ${data.usage?.output_tokens ?? '?'} token`,
      };
    }

    attempts.push(`${auth.label} → HTTP ${res.status}: ${text.slice(0, 100)}`);

    // 认证类错误才值得换下一种；其他错误（如模型名不对）换认证方式也没用
    if (res.status !== 401 && res.status !== 403) break;
  }

  throw new Error(attempts.join('  |  '));
}

/** 2. 流式 —— 采集真实的事件序列，这是正文里要展示的东西 */
async function streamingCall() {
  const res = await fetch(`${baseUrl}/v1/messages`, {
    method: 'POST',
    headers: { ...headers(), accept: 'text/event-stream' },
    body: JSON.stringify({
      model,
      max_tokens: 128,
      stream: true,
      messages: [{ role: 'user', content: '从 1 数到 5，每个数字之间用空格分隔。' }],
    }),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}: ${(await res.text()).slice(0, 200)}`);

  const raw = await res.text();
  const eventNames = [...raw.matchAll(/^event: (.+)$/gm)].map((m) => m[1]);
  const order = [...new Set(eventNames)];

  return {
    raw,
    summary: `✓ ${eventNames.length} 个事件，类型: ${order.join(', ')}`,
  };
}

/** 3. token 计数 —— 对比实验的基础数据 */
async function countTokens() {
  const samples = {
    短中文: '什么是幂等性？',
    短英文: 'What is idempotency?',
    长中文: '什么是幂等性？'.repeat(50),
    长英文: 'What is idempotency? '.repeat(50),
    代码: 'func main() { fmt.Println("hello") }',
  };

  const counts = {};
  for (const [label, text] of Object.entries(samples)) {
    const res = await fetch(`${baseUrl}/v1/messages/count_tokens`, {
      method: 'POST',
      headers: headers(),
      body: JSON.stringify({ model, messages: [{ role: 'user', content: text }] }),
    });
    if (!res.ok) {
      // 部分兼容端点没有实现这个端点，不算致命
      return { skipped: true, summary: `⚠ 该端点不支持 count_tokens（HTTP ${res.status}），跳过` };
    }
    const data = await res.json();
    counts[label] = { chars: text.length, tokens: data.input_tokens };
  }

  const detail = Object.entries(counts)
    .map(([k, v]) => `${k} ${v.chars}字符→${v.tokens}tok`)
    .join(' · ');

  return { counts, summary: `✓ ${detail}` };
}

/** 4. 错误行为 —— 采集真实的报错响应原文 */
async function errorBehaviour() {
  const cases = [
    {
      label: '空模型名',
      body: { model: '', max_tokens: 16, messages: [{ role: 'user', content: 'hi' }] },
    },
    { label: '缺 max_tokens', body: { model, messages: [{ role: 'user', content: 'hi' }] } },
    {
      label: '传 temperature',
      body: {
        model,
        max_tokens: 16,
        temperature: 0.2,
        messages: [{ role: 'user', content: 'hi' }],
      },
    },
    {
      label: '超小 max_tokens 触发截断',
      body: { model, max_tokens: 5, messages: [{ role: 'user', content: '讲一个很长的故事' }] },
    },
  ];

  const out = {};
  for (const c of cases) {
    const res = await fetch(`${baseUrl}/v1/messages`, {
      method: 'POST',
      headers: headers(),
      body: JSON.stringify(c.body),
    });
    const text = await res.text();
    out[c.label] = { status: res.status, body: text.slice(0, 400) };
  }

  const summary = Object.entries(out)
    .map(([k, v]) => `${k}=${v.status}`)
    .join(' · ');

  return { cases: out, summary: `✓ ${summary}` };
}

// ---------------------------------------------------------------------------
// 主流程
// ---------------------------------------------------------------------------

console.log(`\n验证目标: ${maskUrl(baseUrl)}`);
console.log(`模型: ${model || '（未指定，请在 .env.local 里填 VERIFY_MODEL）'}\n`);

if (!model) {
  fail('请在 .env.local 里设置 VERIFY_MODEL，或在 ANTHROPIC_MODEL 里指定一个模型名。');
}

await mkdir(OUT_DIR, { recursive: true });

console.log('检查项：');
await record('1. 基本消息调用', basicCall);
await record('2. 流式事件序列', streamingCall);
await record('3. token 计数', countTokens);
await record('4. 错误行为采集', errorBehaviour);

// ---------------------------------------------------------------------------
// 落盘
// ---------------------------------------------------------------------------

const report = { baseUrl, model, ranAt: new Date().toISOString(), results };
await writeFile(join(OUT_DIR, 'report.json'), JSON.stringify(report, null, 2));

if (results.find((r) => r.name.startsWith('2.') && r.ok)?.raw) {
  await writeFile(
    join(OUT_DIR, 'stream-raw.txt'),
    results.find((r) => r.name.startsWith('2.'))?.raw ?? '',
  );
}

console.log(`\n结果已写入 verify-output/（该目录已 gitignore）`);
console.log('正文里引用的真实数据从这里取。\n');

const failed = results.filter((r) => !r.ok);
if (failed.length > 0) {
  console.log(`✗ ${failed.length} 项失败 —— 修复后才能采集到真实数据。\n`);
  process.exit(1);
}
console.log('✓ 全部通过。可以把 verify-output/ 的内容给我，我据此写正文。\n');
