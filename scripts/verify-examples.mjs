import { createHash } from 'node:crypto';
import { mkdtempSync, readFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const manifest = JSON.parse(readFileSync(join(root, 'examples/manifest.json'), 'utf8'));
const ids = new Set();
let failures = 0;

for (const example of manifest.examples) {
  if (ids.has(example.id)) throw new Error(`Duplicate example id: ${example.id}`);
  ids.add(example.id);
  if (!['python', 'uv-project'].includes(example.runtime)) throw new Error(`Unsupported example runtime for ${example.id}`);
  if (!Number.isInteger(example.timeoutMs) || example.timeoutMs < 1 || example.timeoutMs > 30000)
    throw new Error(`Invalid timeout for ${example.id}`);
  const entryPath = resolve(root, example.entry);
  if (!entryPath.startsWith(`${root}/`)) throw new Error(`Example path escapes workspace: ${example.entry}`);
  const digest = createHash('sha256').update(readFileSync(entryPath)).digest('hex');
  if (digest !== example.sha256) throw new Error(`Entry hash changed for ${example.id}; review and update the manifest.`);

  let command;
  let args;
  let cwd = root;
  if (example.runtime === 'uv-project') {
    if (!example.projectDir || !example.dependencyLockPath || !example.dependencyLockSha256)
      throw new Error(`uv-project example ${example.id} must pin its project and lockfile`);
    const projectDir = resolve(root, example.projectDir);
    const lockPath = resolve(root, example.dependencyLockPath);
    if (!projectDir.startsWith(`${root}/`) || !lockPath.startsWith(`${root}/`))
      throw new Error(`uv-project paths escape workspace: ${example.id}`);
    const lockDigest = createHash('sha256').update(readFileSync(lockPath)).digest('hex');
    if (lockDigest !== example.dependencyLockSha256)
      throw new Error(`Lockfile hash changed for ${example.id}; review and update the manifest.`);
    command = 'uv';
    args = ['run', '--offline', '--frozen', '--no-sync', '--project', projectDir, ...example.args];
    cwd = projectDir;
  } else {
    command = process.env.PYTHON ?? 'python3';
    args = example.args;
  }

  const temp = mkdtempSync(join(tmpdir(), 'agent-study-example-'));
  try {
    const result = spawnSync(command, args, {
      cwd,
      encoding: 'utf8',
      timeout: example.timeoutMs,
      maxBuffer: 1024 * 1024,
      env: { PATH: process.env.PATH ?? '', HOME: temp, TMPDIR: temp, TMP: temp, TEMP: temp, UV_OFFLINE: '1', PYTHONDONTWRITEBYTECODE: '1' },
    });
    process.stdout.write(result.stdout ?? '');
    process.stderr.write(result.stderr ?? '');
    if (result.error) throw result.error;
    if (result.status !== 0) {
      failures += 1;
      process.stderr.write(`FAIL ${example.id}: exit ${result.status}\n`);
    } else {
      process.stdout.write(`PASS ${example.id}\n`);
    }
  } finally {
    rmSync(temp, { recursive: true, force: true });
  }
}

if (failures) process.exitCode = 1;
