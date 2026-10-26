import { describe, expect, it } from 'vitest';
import { spawnSync } from 'node:child_process';
import path from 'node:path';

const script = path.resolve('scripts/verify-depth-fixes.mjs');

describe('verify-depth-fixes CLI', () => {
  it('requires a readable Git base revision instead of silently using a local snapshot', () => {
    const result = spawnSync(process.execPath, [script, '--base=definitely-not-a-git-revision'], {
      encoding: 'utf8',
    });

    expect(result.status).not.toBe(0);
    expect(result.stderr + result.stdout).toMatch(/base revision|基线 revision/i);
  });
});
