import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { readFileSync } from 'node:fs';

const lessonPath = 'src/content/chapters/human-in-the-loop/05-streaming-and-control.mdx';
const lesson = readFileSync(lessonPath, 'utf8');
const data = readFileSync('docs/DATA.md', 'utf8');
const metadata = readFileSync('src/content/chapters/human-in-the-loop/meta.ts', 'utf8');
let checks = 0;
const check = (condition, message) => {
  assert.ok(condition, message);
  checks += 1;
};

check(
  lesson.includes('不能证明原请求在断开后仍生成了 20 秒'),
  'historical cancellation result is bounded',
);
check(lesson.includes('不能证明账单按完整输出结算'), 'billing is not inferred');
check(data.includes('流式取消探测（未能判定）'), 'DATA ledger records inconclusive cancellation');
check(lesson.includes('没有可配对的非流式对照'), 'latency comparison is not claimed');
check(lesson.includes('不要用这四条单次记录拟合通用'), 'single samples are not an ETA model');
check(
  lesson.includes('token.check() 只有在控制流再次运行时才会执行'),
  'cooperative cancellation limitation is explicit',
);
check(
  lesson.includes('不等于已证实供应商端生成和账单停止'),
  'local close is not remote billing proof',
);
check(
  lesson.includes('message_start') &&
    lesson.includes('content_block_stop') &&
    lesson.includes('message_stop'),
  'provider event lifecycle is represented',
);
check(lesson.includes('客户端应容忍未知事件'), 'unknown events are handled');
check(
  lesson.includes('Last-Event-ID') && lesson.includes('不自动保证服务端保留或重放事件'),
  'SSE replay boundary is explicit',
);
check(
  lesson.includes('outcome_unknown') && lesson.includes('reconciling'),
  'unknown side effects enter reconciliation',
);
check(
  lesson.includes('用户体验假设也要单独验证'),
  'UX causality is not asserted from click telemetry',
);
check(metadata.includes("'whatwg-sse'"), 'SSE source is linked from chapter metadata');
check(
  lesson.includes('静默丢弃已生成内容') && lesson.includes('按任务、隐私与安全策略决定是否保留'),
  'partial-output retention follows an explicit product/privacy policy',
);
check(
  lesson.includes('中间片段通常尚未构成完整 JSON') && !lesson.includes('JSON 在流式中无效'),
  'streaming JSON fragments are not overgeneralized as invalid JSON',
);
check(
  metadata.includes("id: 'streaming-control-claims'") && metadata.includes('应与产品策略一致并向用户说明'),
  'lesson checkpoint captures streaming and partial-output boundaries',
);

const fences = [...lesson.matchAll(/^```python\s*\n([\s\S]*?)^```\s*$/gm)].map((m) => m[1]);
for (const [index, source] of fences.entries()) {
  const run = spawnSync('python3', ['-c', source], { encoding: 'utf8', timeout: 10_000 });
  check(run.status === 0, `Python fence ${index + 1} executes: ${run.stderr}`);
  if (index === 0) {
    check(run.stdout.includes('提示词要求的总分片数：1200'), 'first fixture reports its configured frame budget');
    check(
      run.stdout.includes('副作用已派发后收到取消：动作仍完成：mail_sent'),
      'a cancellation arriving after side-effect dispatch does not pretend to roll it back',
    );
  }
  if (index === fences.length - 1) {
    check(run.stdout.includes('我先核对订单状态。'), 'visible text delta is delivered');
    check(
      run.stdout.includes('"order_id": "A-1001"'),
      'tool JSON is assembled before basic validation',
    );
    check(!run.stdout.includes('thinking'), 'fixture does not expose model thinking');
    check(
      run.stdout === '展示获准文本：我先核对订单状态。\n最终可见文本：我先核对订单状态。\n完整并通过基础字段检查的工具参数：[{"tool": "lookup", "order_id": "A-1001"}]\n注意：基础字段检查不是授权；工具执行由宿主策略决定。\n',
      'event fixture stdout exactly matches the intended local output',
    );
  }
}

console.log(
  `Human streaming/control review: ${checks}/${checks} checks passed; ${fences.length} Python fences executed; no provider calls.`,
);
