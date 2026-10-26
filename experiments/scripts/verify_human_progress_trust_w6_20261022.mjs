import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import Ajv2020 from 'ajv/dist/2020.js';

const root = new URL('../../', import.meta.url);
const lessonPath = new URL('src/content/chapters/human-in-the-loop/04-progress-and-trust.mdx', root);
const metaPath = new URL('src/content/chapters/human-in-the-loop/meta.ts', root);
const lesson = readFileSync(lessonPath, 'utf8');
const meta = readFileSync(metaPath, 'utf8');
let checks = 0;
const check = (condition, message) => {
  checks += 1;
  assert.ok(condition, message);
};

const prior = spawnSync(process.execPath, ['experiments/scripts/verify_human_progress_trust_review_20261021.mjs'], {
  cwd: new URL('../../', import.meta.url),
  encoding: 'utf8',
});
check(prior.status === 0 && prior.stdout.includes('PASS 20/20'), `prior verifier remains green: ${prior.stderr}`);

const jsonFences = [...lesson.matchAll(/```json\s*\n([\s\S]*?)\n```/g)].map((match) => JSON.parse(match[1]));
check(jsonFences.length === 2, `expected schema and one JSON example, found ${jsonFences.length}`);
const ajv = new Ajv2020({ allErrors: true, strict: true });
const validate = ajv.compile(jsonFences[0]);
check(validate(jsonFences[1]), `published JSON example conforms to the schema: ${JSON.stringify(validate.errors)}`);
check(
  jsonFences[1].status === 'unknown' && jsonFences[1].confirmation === undefined,
  'unknown branch contains only fields allowed by its schema branch',
);
check(
  jsonFences[1].evidence.every((id) => /^evt-[a-z0-9-]+$/.test(id)),
  'evidence values are resolvable event identifiers, not model-written explanations',
);
check(
  !JSON.stringify(jsonFences[0]).includes('minLength') && lesson.includes('不支持 `minLength`'),
  'provider-facing schema omits Claude-unsupported string-length constraints and documents host validation',
);

const pythonFences = [...lesson.matchAll(/```python\n([\s\S]*?)\n```/g)].map((match) => match[1]);
check(pythonFences.length === 1, `expected one complete Python fence, found ${pythonFences.length}`);
const python = spawnSync('python3', ['-c', `${pythonFences[0]}\n`], { encoding: 'utf8' });
check(python.status === 0, `complete Python example runs: ${python.stderr}`);
check(python.stdout.includes('60%') && python.stdout.includes('后续步骤尚未确定'), 'valid fixed and dynamic progress examples remain visible');
check(python.stdout.includes('越界进度被拒绝'), 'out-of-range determinate progress is rejected');
check(pythonFences[0].includes('local_checks()') && pythonFences[0].includes('invalid dynamic status accepted'), 'invalid determinate and dynamic status values are tested');

check(meta.includes("id: 'human-in-the-loop/progress-and-trust'"), 'lesson metadata remains registered');
console.log(`PASS ${checks}/${checks}; Ajv 2020 validates every published JSON example; Python example executed; providerCalls=0`);
console.log(python.stdout.trim());
