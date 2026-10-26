import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import Ajv2020 from 'ajv/dist/2020.js';

const root = new URL('../../', import.meta.url);
const lessonPath = new URL('src/content/chapters/human-in-the-loop/04-progress-and-trust.mdx', root);
const metaPath = new URL('src/content/chapters/human-in-the-loop/meta.ts', root);
const dataPath = new URL('docs/DATA.md', root);
const lesson = readFileSync(lessonPath, 'utf8');
const meta = readFileSync(metaPath, 'utf8');
const data = readFileSync(dataPath, 'utf8');
let checks = 0;
const check = (condition, message) => {
  checks += 1;
  assert.ok(condition, message);
};

const schemaMatch = lesson.match(/```json\n([\s\S]*?)\n```/);
assert.ok(schemaMatch, 'schema JSON fence exists');
const schema = JSON.parse(schemaMatch[1]);
const ajv = new Ajv2020({ allErrors: true, strict: true });
const validate = ajv.compile(schema);
const validExamples = [
  { status: 'ok', answer: '已找到订单', evidence: ['event-1'] },
  { status: 'unknown', answer: null, evidence: [], unknown_reason: '需要订单号' },
  { status: 'need_confirmation', answer: null, evidence: [], confirmation: { proposed_action: '发送邮件', why: '发送前需要确认' } },
];
for (const example of validExamples) check(validate(example), `valid schema branch accepted: ${example.status}`);
const invalidExamples = [
  { status: 'unknown', answer: null, evidence: [] },
  { status: 'unknown', answer: 'success-looking string', evidence: [], unknown_reason: 'missing data' },
  { status: 'need_confirmation', answer: null, evidence: [], confirmation: { proposed_action: 'send' } },
  { status: 'ok', answer: 'done', evidence: [], unknown_reason: 'contradictory branch' },
  { status: 'ok', answer: 'done', evidence: [], extra: true },
];
for (const example of invalidExamples) check(!validate(example), `invalid schema branch rejected: ${JSON.stringify(example)}`);

const pythonFences = [...lesson.matchAll(/```python\n([\s\S]*?)\n```/g)].map((match) => match[1]);
check(pythonFences.length === 1, `expected one complete Python fence, found ${pythonFences.length}`);
const python = spawnSync('python3', ['-c', `${pythonFences[0]}\n`], { encoding: 'utf8' });
check(python.status === 0, `complete Python example runs: ${python.stderr}`);
check(python.stdout.includes('60%') && python.stdout.includes('后续步骤尚未确定'), 'fixed-total and dynamic-progress cases are both shown');
check(python.stdout.includes('越界进度被拒绝'), 'invalid determinate progress is rejected');

check(data.includes('11,827 token') && data.includes('不能推断模型是否察觉'), 'historical UI-agent observation stays within archived evidence');
check(data.includes('Plan-Execute **0/3**') && data.includes('不能证明答案准确率'), 'historical planner score stays bounded to its weak scorer');
check(!lesson.includes('12,269 token') && !lesson.includes('模型察觉不到自己卡住了'), 'unsupported old cost and anthropomorphic inference are removed');
check(lesson.includes('动作级状态是可选的呈现方案') && lesson.includes('字段白名单投影'), 'trace-to-UI is explicitly an authorized projection');
check(lesson.includes('取消任务的比率') && lesson.includes('不能单独诊断盲批'), 'behavior telemetry is not treated as causal trust diagnosis');
check(lesson.includes('aria-valuenow') && lesson.includes('可用性检查可让目标用户执行具体监督任务'), 'status accessibility and task-based validation are covered');
check(lesson.includes('总体准确率、模型自报信心') === false, 'lesson body does not claim aggregate accuracy grants permissions');
check(meta.includes('lee-see-trust-automation') && meta.includes('w3c-wcag-status-messages') && meta.includes('anthropic-structured-outputs'), 'lesson resources include human factors, accessibility and provider schema guidance');

console.log(`PASS ${checks}/${checks}; schema branches validated with Ajv 2020; Python example executed; providerCalls=0`);
console.log(python.stdout.trim());
