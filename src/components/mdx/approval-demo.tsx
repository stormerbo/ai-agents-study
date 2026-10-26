/**'
 * 审批界面 + 进度展示的最小实现（第 19 章结论的落地）。
 *
 * 两个设计决定：
 * 这是静态界面示意：审批按钮不提交，进度不代表任务成功率。
 * 按动作显示示例进展；动态流程的总量未知时不伪造精确百分比。
 */

const APPROVAL = {
  action: '发送回复',
  target: 'zhangsan@example.com',
  targetKind: '外部地址',
  scope: '1 个外部收件人可见',
  reversible: '发出后无法撤回',
  body: '订单 A-1001 已发货，物流显示派送中。若超过 7 天未更新，可发起售后。',
};

const OPTIONS = [
  { label: '同意', hint: '就这么发', tone: 'primary' },
  { label: '拒绝', hint: '不要发这封', tone: 'plain' },
  { label: '修改后同意', hint: '方向对，改收件人或措辞', tone: 'plain' },
  { label: '换个方式', hint: '目标对，做法不对', tone: 'plain' },
];

const STEPS = [
  { text: '读取订单 A-1001', state: 'done' },
  { text: '检索退款政策', state: 'done' },
  { text: '整理要点', state: 'done' },
  { text: '等待确认发送给 zhangsan@example.com', state: 'waiting' },
];

export function ApprovalDemo() {
  return (
    <div className="not-prose my-6 space-y-4">
      {/* 进度：按动作，不按百分比 */}
      <div className="rounded-lg border border-border bg-card p-4">
        <p className="mb-3 text-xs font-medium text-muted-foreground">进度</p>
        <ol className="space-y-1.5">
          {STEPS.map((s) => (
            <li key={s.text} className="flex items-baseline gap-2 text-sm">
              <span aria-hidden className="shrink-0 font-mono text-xs">
                {s.state === 'done' ? '✓' : s.state === 'waiting' ? '⏸' : '·'}
              </span>
              <span className={s.state === 'waiting' ? 'text-accent' : 'text-muted-foreground'}>
                {s.text}
              </span>
            </li>
          ))}
        </ol>
        <p className="mt-3 text-xs text-muted-foreground/70">
          这里展示已发生的动作；动态任务总量未知时，不给出精确百分比。
        </p>
      </div>

      {/* 审批：三样信息 + 四个选项 */}
      <div className="rounded-lg border border-amber-500/40 bg-amber-500/5 p-4">
        <p className="mb-3 text-xs font-medium text-amber-700 dark:text-amber-500">
          ⏸ 需要你确认：这个动作不可逆
        </p>

        <dl className="space-y-2 text-sm">
          <div className="flex gap-3">
            <dt className="w-20 shrink-0 text-xs leading-6 text-muted-foreground">动作与目标</dt>
            <dd className="leading-6">
              {APPROVAL.action} → <span className="font-mono text-xs">{APPROVAL.target}</span>
              <span className="ml-1.5 text-xs text-muted-foreground">
                （{APPROVAL.targetKind}）
              </span>
            </dd>
          </div>
          <div className="flex gap-3">
            <dt className="w-20 shrink-0 text-xs leading-6 text-muted-foreground">影响范围</dt>
            <dd className="leading-6">{APPROVAL.scope}</dd>
          </div>
          <div className="flex gap-3">
            <dt className="w-20 shrink-0 text-xs leading-6 text-muted-foreground">可逆性</dt>
            <dd className="leading-6 text-amber-700 dark:text-amber-500">{APPROVAL.reversible}</dd>
          </div>
        </dl>

        <details className="mt-3 text-sm">
          <summary className="cursor-pointer text-xs text-muted-foreground">查看正文</summary>
          <p className="mt-2 text-xs leading-relaxed text-muted-foreground">{APPROVAL.body}</p>
        </details>

        <div className="mt-4 flex flex-wrap gap-2">
          {OPTIONS.map((o, i) => (
            <button
              key={o.label}
              type="button"
              disabled
              title={o.hint}
              className={
                i === 0
                  ? 'rounded bg-foreground px-3 py-1.5 text-xs font-medium text-background'
                  : 'rounded border border-border px-3 py-1.5 text-xs hover:bg-muted'
              }
            >
              {o.label}
              <span className="sr-only">：{o.hint}</span>
            </button>
          ))}
        </div>

        <p className="mt-3 text-xs leading-relaxed text-muted-foreground/70">
          选项应由任务决定；修改参数或提出替代方案后，新提案仍需用户核对。
        </p>
      </div>
    </div>
  );
}
