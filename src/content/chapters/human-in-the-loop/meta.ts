import type { Chapter } from '@/content/curriculum/schema';

export const chapter = {
  id: 'human-in-the-loop',
  stageId: 'stage-4-production',
  order: 19,
  title: '人机协作',
  subtitle: '在哪里停下来问人',
  summary:
    '全自动与全手动之间有很多档。这一章讲怎么选档位、审批点该展示什么才算「可核对」、中断之后怎么安全恢复，以及长任务里如何帮助用户监督并校准对 agent 的信任。',
  outcomes: [
    '能为一个任务选出合适的自动化档位，并说得出依据',
    '能设计出「人能核对」的审批界面，而不是只给一个是/否按钮',
    '能设计持久化的审批等待/恢复流程，并区分本地原子提交、接收端去重与未知结果对账',
  ],
  depth: 'deep',
  difficulty: 'advanced',
  estimatedMinutes: 90,
  tags: ['human-in-the-loop', 'approval', 'interrupt'],
  prerequisiteIds: ['agent-loop'],
  lessons: [
    {
      id: 'human-in-the-loop/automation-levels',
      chapterId: 'human-in-the-loop',
      slug: 'automation-levels',
      title: '自动化档位',
      summary: '用五类人工介入方式组织策略选择；它们是实用分类，不是行业统一标准。',
      estimatedMinutes: 18,
      difficulty: 'intermediate',
      hasBody: true,
      status: 'drafting',
      keywords: ['automation', 'levels'],
      checkpoints: [
        {
          id: 'levels',
          basis: 'inferred',
          question: '自动化程度大致有哪几档？怎么选？',
          answer:
            '本节把人工介入分为五类：**全自动**（主体授权和自动额度内执行）、**事后复核**（先执行后按策略检查结果）、**关键点确认**（特定动作执行前暂停）、**逐步确认**（每步都需复核）、**人做主**（agent 只提供建议）。这是便于讨论的工程分类，不是统一标准，系统也可组合多类控制。选型需结合主体/对象授权、影响范围、可恢复性、失败代价、检测能力、复核容量与组织策略；风险信号不自动等于审批，无权限动作必须拒绝。新模型/工具变更可触发评测或临时收紧，但放宽控制应有证据和回滚路径，而不能按时间或“最近没出事”自动决定。',
        },
        {
          id: 'policy-inputs-fail-closed',
          basis: 'inferred',
          question: '策略门禁遇到缺失金额或畸形风险元数据时，应如何处理？',
          answer:
            '对要求金额的动作，缺失金额不能默认成 0；主体授权、风险标签或自动阈值缺失/格式错误时应拒绝，而不是继续套用默认策略。此示例只覆盖金额字段与有限元数据检查，仍不能替代完整参数 schema、对象级授权或执行时重验。',
        },
        {
          id: 'escalation-not-failure',
          basis: 'inferred',
          question: '为什么「找人」应当被当成一条正常路径，而不是失败？',
          answer:
            '把「需要人介入」建模为明确状态，可以让宿主与运营流程区分任务已完成、执行失败和等待决策，并保存交接所需的任务状态、已完成动作与待处理问题。它是状态模型建议，不证明团队一定会降低阈值或减少误判；指标如何统计也应区分待审批任务与失败任务，并按业务目标校验。把不确定状态显式化，可避免将未决动作误报为成功，但仍需由执行层和业务状态机落实。',
        },
      ],
      resourceIds: [
        'twelve-factor-agents',
        'ai-engineering-huyen',
        'owasp-llm06-excessive-agency',
        'owasp-authorization-cheat-sheet',
      ],
    },
    {
      id: 'human-in-the-loop/approval-design',
      chapterId: 'human-in-the-loop',
      slug: 'approval-design',
      title: '审批点怎么设计',
      summary: '让复核者看到具体交易内容，并把批准绑定到服务端验证的冻结提案。',
      estimatedMinutes: 20,
      difficulty: 'advanced',
      hasBody: true,
      status: 'drafting',
      keywords: ['approval', 'ux'],
      checkpoints: [
        {
          id: 'what-approval-must-show',
          basis: 'inferred',
          question: '一个可核对的审批请求，至少要展示什么？',
          answer:
            '展示足够让审批者核对**这次具体交易会改变什么**的信息：动作、目标对象、关键参数或状态差异、影响范围和撤销边界；按动作把技术数据整理成可读预览，不能只显示工具名，也不应只倒出未经整理的 JSON。预览必须对应服务端冻结的提案，批准后执行的就是同一组数据。模型给出的理由可以作为上下文，但不是权限或正确性的证据。审批页面应保护敏感信息，并说明批准实际授权的动作。',
        },
        {
          id: 'approval-friction',
          basis: 'inferred',
          question: '审批太少和太多，分别会出什么问题？',
          answer:
            '**太少**会让需要独立复核的高影响动作未经确认；**太多**会增加人的时间成本，但不能仅凭频率就断言出现了盲批或疲劳。审批判据应由主体/对象授权、业务影响、敏感度、规模、可逆性和可用补救路径共同决定，越权动作必须拒绝，不能让确认按钮补权。可按动作风险分层观察审批量、修改/拒绝、误批与后续更正，并结合抽样复核和用户研究；通过率或响应时间没有通用阈值，单项指标也不能证明审批有效。',
        },
        {
          id: 'trace-data-minimization',
          basis: 'documented',
          sourceIds: ['opentelemetry-genai-semconv'],
          question: '为什么不能默认把完整模型与工具内容写入普通轨迹？',
          answer:
            'OpenTelemetry GenAI 语义约定将消息、工具参数和结果等内容属性标为 opt-in，并提示这些内容可能敏感；该约定当前处于 Development 状态，是遥测字段约定而非通用隐私法规。实际采集仍需按用途、数据分类和适用规则决定字段白名单、脱敏、权限与保留策略。',
        },
      ],
      resourceIds: [
        'claude-agent-sdk',
        'ai-engineering-huyen',
        'owasp-transaction-authorization',
        'owasp-llm06-excessive-agency',
        'owasp-authorization-cheat-sheet',
        'opentelemetry-genai-semconv',
      ],
    },
    {
      id: 'human-in-the-loop/interrupt-and-resume',
      chapterId: 'human-in-the-loop',
      slug: 'interrupt-and-resume',
      title: '中断与恢复',
      summary: '持久化检查点使等待中的任务可恢复；副作用需要接收端去重或对账。',
      estimatedMinutes: 22,
      difficulty: 'expert',
      hasBody: true,
      status: 'drafting',
      keywords: ['durable-execution', 'resume', 'idempotency'],
      checkpoints: [
        {
          id: 'why-durable',
          basis: 'inferred',
          question: '为什么「能中断、能恢复」是长任务 agent 的前提？',
          answer:
            '把可恢复状态保存在耐久存储中，可让服务在请求/worker 结束后，于后续进程中恢复，而不必在等待期间占用同一执行资源。具体等待时长、资源模型和是否需要长连接取决于系统设计，并非所有 agent 都必须采用 durable execution。恢复状态至少要区分 checkpoint、已 claim 的动作、已确认副作用与 outcome unknown；持久化本身不保证恢复正确，也不保证外部操作不会重放。',
        },
        {
          id: 'resume-safety',
          basis: 'inferred',
          question: '恢复执行时最容易犯的错是什么？',
          answer:
            '**把“从哪里继续”误当作“之前效果一定发生/没发生”。** 本地 checkpoint 与外部效果可能跨越不同提交边界。先恢复 operation ledger 并对账：确认成功后复用真实结果；确认未执行后才可按同一稳定键和参数重试；无法判定时停在 `unknown` 并进入对账。下游幂等键必须由接收端契约支持，且其保留期覆盖重试周期；单有本地 key 或模型一次“不重试”的响应都不是防重控制。',
        },
        {
          id: 'approval-single-use-before-execution',
          basis: 'documented',
          sourceIds: ['owasp-ai-agent-security'],
          question: '为什么待审批不应只靠 UI 确认状态来允许执行？',
          answer:
            'OWASP AI Agent Security 指引建议执行组件在副作用前验证 approval 是否绑定当前 actor 与精确工具调用、是否仍有效且未消费，并在同一原子步骤检查和消费，以防并发或重放复用；参数或目标变化应取得新批准。这是安全指导而不是形式化协议，具体存储、事务与外部效果边界仍需按系统实现和测试。',
        },
      ],
      resourceIds: [
        'twelve-factor-agents',
        'claude-agent-sdk',
        'postgres-row-locking-18',
        'postgres-date-time-functions-18',
        'stripe-idempotency-keys',
        'owasp-transaction-authorization',
        'owasp-authorization-cheat-sheet',
        'owasp-ai-agent-security',
      ],
    },
    {
      id: 'human-in-the-loop/progress-and-trust',
      chapterId: 'human-in-the-loop',
      slug: 'progress-and-trust',
      title: '进度、可见性与信任',
      summary: '中间状态可为用户监督 agent 提供信息；呈现效果需按任务和用户验证。',
      estimatedMinutes: 18,
      difficulty: 'intermediate',
      hasBody: true,
      status: 'drafting',
      keywords: ['progress', 'trust', 'observability'],
      checkpoints: [
        {
          id: 'progress-reporting',
          basis: 'inferred',
          question: '长任务里，进度反馈该报什么？',
          answer:
            '反馈应围绕用户需要监督的决策：已完成/正在进行/等待谁或什么，以及是否需要用户行动。动态计划的步数不能直接冒充完成百分比；固定且可测量的工作量（如已上传字节/总字节）可以显示确定进度。ETA 只在该工作流有校准数据时呈现，并说明不确定性。状态消息还应考虑可访问性、更新频率、隐私和当前用户权限；具体展示效果需用目标用户任务验证。',
        },
        {
          id: 'trust-calibration',
          basis: 'inferred',
          question: '用户对系统的信任校准与权限授权是什么关系？',
          answer:
            '信任校准（用户如何理解并依赖系统）与授权（某主体能否对某对象执行某动作）是不同问题。评测结果可用于限定任务范围、灰度和监控策略，但总体准确率、模型自报信心或“最近没出事”都不能单独授予权限。授权应在执行时依据可信身份、对象范围、策略和当前状态检查；放宽或收紧控制需要明确的风险依据、负责人和回滚路径，不能由 UI 信任指标自动决定。',
        },
      ],
      resourceIds: [
        'claude-agent-sdk',
        'ai-engineering-huyen',
        'lee-see-trust-automation',
        'w3c-wcag-status-messages',
        'w3c-aria-range-properties',
        'json-schema-validation-2020-12',
        'anthropic-structured-outputs',
      ],
    },
    {
      id: 'human-in-the-loop/streaming-and-control',
      chapterId: 'human-in-the-loop',
      slug: 'streaming-and-control',
      title: '流式与控制感',
      summary: '同一份流式数据，组织方式决定了它是「看得见的进展」还是「刷屏」。',
      estimatedMinutes: 18,
      difficulty: 'intermediate',
      hasBody: true,
      status: 'drafting',
      keywords: ['streaming', 'ux'],
      checkpoints: [
        {
          id: 'what-to-stream',
          basis: 'documented',
          question: '流式响应里有哪些事件类型，它们分别该用来做什么？',
          answer:
            'Claude Messages API 的流包含 message_start、content block start/delta/stop、一个或多个 message_delta 与 message_stop，也可能出现 ping、error；协议允许未来增加事件，客户端应安全处理未知类型。tool_use 的 JSON delta 可能不完整，应按 block index 累积到 content_block_stop 后再解析和校验。产品层只展示经产品策略批准的用户可见文本与状态；工具参数不是展示内容或授权依据，thinking 属独立内容块，不能默认当作用户说明。',
          sourceIds: ['claude-streaming'],
        },
        {
          id: 'streaming-control-claims',
          basis: 'inferred',
          question: '结构化分片和停止后的部分结果应该如何处理？',
          answer:
            '流式结构化数据的中间分片通常不构成完整 JSON，应缓冲到协议定义的块完成后再解析和校验。停止后是否保留部分结果取决于任务、隐私与安全策略；无论保留或丢弃都应与产品策略一致并向用户说明，保留时标注不完整。费用或上游状态只能依据宿主和供应商可用证据核实，不能从客户端断连推断。',
        },
        {
          id: 'control-surface',
          basis: 'inferred',
          question: '一个 agent 交互界面，最少需要哪些控制手段？',
          answer:
            '控制面应按任务能力、风险与持久化语义设计，而不存在适用于所有 agent 的最小三按钮集合。停止生成、取消整个任务、暂停并恢复、纠正后续指令是不同操作；取消通常是尽力而为，客户端断开或接受取消请求都不能证明上游生成或副作用已终止。只有在运行宿主确认状态后才报告终态；继续执行需检查点、上下文恢复、权限复核与业务策略支持。',
        },
      ],
      resourceIds: ['claude-streaming', 'claude-agent-sdk', 'whatwg-sse'],
    },
  ],
  resourceIds: [
    'twelve-factor-agents',
    'claude-agent-sdk',
    'ai-engineering-huyen',
    'claude-streaming',
  ],
  backendMapping: {
    analogy:
      '人机协作 ≈ 给自动化流程加审批节点：和你在 CI/CD 里加人工放行、在工单系统里加审批流是同一件事',
    transferable: [
      '审批流设计：谁批、批什么、驳回后回哪去',
      '持久化执行与断点恢复：和你写过的任务队列是同一类问题',
      '权限渐进放开：灰度、审计、回滚这一套',
    ],
    pitfalls: [
      '把「需要人工介入」当成失败，逼团队去调松阈值',
      '审批界面没有展示足够核对具体动作、目标和影响的信息',
      '审批点设得太密，导致所有人无脑点通过',
      '恢复执行时直接重放，重复执行有副作用的步骤',
      '用假的百分比进度代替真实的状态描述',
      '只设计放权、不设计降权，准确率下降时无法自动退回保守档',
    ],
    cost: 'medium',
  },
  status: 'published',
  updatedAt: '2026-10-08',
  verifiedAt: '2026-10-08',
} satisfies Chapter;
