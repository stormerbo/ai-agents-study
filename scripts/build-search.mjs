/**
 * 构建搜索索引。
 *
 * 必须在 `next build` **之后**跑 —— Pagefind 索引的是构建出的 HTML。
 * 产物写到 `public/pagefind/`，由 Next 当静态资源提供。
 *
 * 为什么索引 `.next/server/app` 而不是 `out/`：
 * 本站目前不是静态导出（next.config 里没有 output: "export"），
 * 构建产物就在 `.next/server/app` 下的各个 HTML 文件里。
 */

import { execFileSync } from 'node:child_process';
import { existsSync, mkdirSync, rmSync } from 'node:fs';
import { join } from 'node:path';

const SITE = '.next/server/app';
const OUT = 'public/pagefind';

if (!existsSync(SITE)) {
  console.error(`✖ 找不到 ${SITE} —— 先跑 pnpm build`);
  process.exit(1);
}

// 每次重建，避免旧索引残留（Pagefind 不会自动清理多余分片）
rmSync(OUT, { recursive: true, force: true });
mkdirSync(join('public'), { recursive: true });

console.log(`索引 ${SITE} → ${OUT}`);
try {
  const out = execFileSync(
    'pnpm',
    ['exec', 'pagefind', '--site', SITE, '--output-path', OUT, '--force-language', 'zh'],
    { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] },
  );
  // Pagefind 把统计写在 stderr，这里合并展示
  process.stdout.write(out);
} catch (err) {
  // pagefind 正常输出也走 stderr，所以失败时才打印
  const msg = (err.stdout || '') + (err.stderr || '');
  console.error(msg);
  console.error(`✖ pagefind 退出码 ${err.status}`);
  process.exit(1);
}
