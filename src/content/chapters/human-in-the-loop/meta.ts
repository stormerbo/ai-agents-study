import type { Chapter } from '@/content/curriculum/schema';

export const chapter = {
  id: 'human-in-the-loop',
  stageId: 'stage-4-production',
  order: 19,
  title: '人机协作',
  subtitle: '在哪里停下来问人',
  summary:
    '全自动与全手动之间有很多档。这一章讲怎么选档位、审批点该展示什么才算「可核对」、中断之后怎么安全恢复，以及长任务里信任是怎么一点点建立的。',
  outcomes: [
    '能为一个任务选出合适的自动化档位，并说得出依据',
    '能设计出「人能核对」的审批界面，而不是只给一个是/否按钮',
    '能实现中断与恢复，并说清恢复时为什么必须配幂等',
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
      summary: '从「每步都确认」到「只在异常时找人」，中间的每一档都有代价。',
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
            '四档，按人的介入时机划分：**逐步确认**（每个动作前都要批准）—— 最安全，但基本等于人在操作，只适合调试期；**关键点确认**（只对不可逆或有副作用的动作确认）—— 生产环境的常见默认；**异常时介入**（正常跑完全自动，只有失败或不确定时才找人）—— 效率最高，前提是你能可靠判断「异常」；**事后审计**（跑完再抽查）—— 只适合可回滚、代价低的批量任务。选择的依据是**两个变量的组合**：这个动作失败一次的代价，以及它被自动判定为成功/失败的可靠程度。后者常常被忽略 —— 如果你无法自动判断成功与否，就只能退回到更靠前的档位（第 8 章讲 Reflexion 时也提到过，没有失败判定器就没有自动化的基础）。',
        },
        {
          id: 'escalation-not-failure',
          basis: 'inferred',
          question: '为什么「找人」应当被当成一条正常路径，而不是失败？',
          answer:
            '因为把它当失败会带来两个坏结果：一是团队会想尽办法降低它的触发率，于是把阈值调松、把不确定的情况硬判成成功 —— 这恰好是在牺牲正确性换数字；二是它会被记进错误率指标，让监控噪声淹没真正的问题。正确的建模是把它当成一个**明确的结果状态**：任务的结果有三种 —— 完成、失败、**需要人介入**。第三种要能带着上下文交出去（做了什么、卡在哪、建议怎么处理），而不是一句「失败了」。这也和结构化输出那一章的思路一致：**把「不确定」显式化，而不是把它藏进一个看起来正常的默认值里。**',
        },
      ],
      resourceIds: ['twelve-factor-agents', 'ai-engineering-huyen'],
    },
    {
      id: 'human-in-the-loop/approval-design',
      chapterId: 'human-in-the-loop',
      slug: 'approval-design',
      title: '审批点怎么设计',
      summary: '一个「确认 / 取消」按钮不是审批，它只是把责任转嫁给人。',
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
            '三样：**即将执行的原始动作**（工具名 + 完整参数，不是模型的自然语言转述）、**目标对象**（对哪条记录、哪个文件、哪个地址）、以及**模型给出的理由**（它是基于什么信息决定这么做的）。第一项最关键 —— 因为自然语言转述会掩盖细节：模型说「我要更新这条订单的状态」，而原始参数里可能写着状态从「已支付」改成「已取消」。如果只让人看转述，审批就变成了走过场。第三项的价值是把审批变成一次小型复核：人能看出它是否基于了错误的前提。要避免的是**把审批做成确认弹窗**：点得越快越危险，最后所有人都无脑点确定。',
        },
        {
          id: 'approval-friction',
          basis: 'inferred',
          question: '审批太少和太多，分别会出什么问题？',
          answer:
            '**太少**：不可逆动作直接执行，出事时没有拦截点 —— 这是本章存在的理由。**太多**：人会开始无脑批准，审批就退化成形式，而且系统会显得又慢又烦，团队自然会想绕开它。所以审批点的设计原则是**稀有且高价值**：只在真正不可逆、且出错代价高的动作上设置，其余一律自动。另外要监控一个信号 —— **每个审批点的通过率**。如果某个点长期 99% 通过，说明它设错了位置（把可逆动作也拦了）；如果某个点驳回率很高，说明上游的决策逻辑有问题，该去改工具设计或提示，而不是靠人一遍遍拦。',
        },
      ],
      resourceIds: ['claude-agent-sdk', 'ai-engineering-huyen'],
    },
    {
      id: 'human-in-the-loop/interrupt-and-resume',
      chapterId: 'human-in-the-loop',
      slug: 'interrupt-and-resume',
      title: '中断与恢复',
      summary: '能暂停的 agent 才谈得上协作；而恢复的前提是幂等。',
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
            '因为人的响应时间是**分钟到小时级**，而 agent 的执行是秒级。如果状态只存在内存里，一个等待审批的 agent 要么占着进程干等（成本高且脆弱），要么只能失败重来 —— 而重来意味着前面花的钱全部作废。持久化执行（durable execution）解决的就是这件事：把执行状态落到外部，任务可以暂停、可以在另一台机器上继续、可以在进程重启后接着跑。这也让「长任务」在架构上成为可能：一个跑几小时的 agent 不可能依赖一个长连接不断。',
        },
        {
          id: 'resume-safety',
          basis: 'inferred',
          question: '恢复执行时最容易犯的错是什么？',
          answer:
            '**重复执行有副作用的步骤。** 恢复点记录的是「执行到第 N 步」，但第 N 步可能已经产生了副作用而结果没被记录 —— 重放一遍就会重复下单、重复发消息。第 4 章实测过一个反直觉的结果：模型在状态未知时反而很谨慎，主动选择不重试；**真正会造成重复的是恢复逻辑本身**。所以可恢复必须配幂等键：每个有副作用的步骤带唯一标识，服务端按标识去重，重复请求返回首次结果。可以这样理解两者的分工：**持久化让你知道该从哪继续，幂等才让你敢继续。** 只做前者，等于把重复执行的风险推迟到第一次恢复时爆发。',
        },
      ],
      resourceIds: ['twelve-factor-agents', 'claude-agent-sdk'],
    },
    {
      id: 'human-in-the-loop/progress-and-trust',
      chapterId: 'human-in-the-loop',
      slug: 'progress-and-trust',
      title: '进度、可见性与信任',
      summary: '可预测的中间状态能帮助用户理解和校准对 agent 的信任。',
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
            '报**语义进度**，而不是百分比。agent 的任务很少有可靠的完成度估计 —— 一个「已完成 60%」的假数字比没有更糟，因为它会在卡住时给出错误的稳定感。可报告的是三类真实信息：**已经做了什么**（完成了哪几步、调用了哪些工具）、**当前在做什么**、以及**还剩什么不确定的事**（比如「还需要确认三处数据源」）。这些是事实，不依赖对未来的估计。另外要允许用户**随时打断**，而且打断后能拿到当前的部分结果 —— 这既符合人对长任务的预期，也是「可中断」这个能力在产品层的体现。',
        },
        {
          id: 'trust-calibration',
          basis: 'inferred',
          question: '怎么让用户逐步信任一个 agent，而不是一次性交出全部权限？',
          answer:
            '把权限放开做成**有依据的渐进过程**，而不是一个开关。可行的路径：先只给读权限跑一段时间，把它的判断与人工判断做对照（这就是评估那一章的价值 —— 没有对照数据，放开权限只是赌博）；确认准确率稳定后，放开可逆的写操作；不可逆动作再单独评估，并且即使放开也保留审计与回滚。关键是**每一次放权都有前置的证据**，而不是「最近没出事所以应该没问题」。还有一个常被忽略的反向机制：**降权也要设计**。当准确率下降（模型更新、数据分布漂移）时，系统应该能自动退回更保守的档位，而不是等人发现。',
        },
      ],
      resourceIds: ['claude-agent-sdk', 'ai-engineering-huyen'],
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
            '协议层至少有四类：消息开始（带 usage）、内容块开始与增量（文本片段、工具参数分片）、消息增量（停止原因与累计用量）、以及消息结束。产品层该做的是**把内容块映射成不同的 UI 语义**：文本增量渲染成逐字输出；工具调用开始渲染成「正在查询 X」这样的动作提示（而不是把工具名和 JSON 直接倒给用户）；思考内容则要谨慎处理 —— 它可能很长，多数产品选择折叠或不展示。第 1 章记录过完整的 63 个事件序列，那一章解决协议解析；这一层解决的是**哪些事件值得让用户看见**。',
          sourceIds: ['claude-streaming'],
        },
        {
          id: 'control-surface',
          basis: 'inferred',
          question: '一个 agent 交互界面，最少需要哪些控制手段？',
          answer:
            '三个：**停止**（立刻中断当前生成，而不是等它跑完）、**取消任务**（终止整个任务并保留已完成的部分）、以及**纠正后继续**（不中断整个任务，只补一句修正让它接着做）。第三个最容易被漏掉，但它是「协作」和「命令」的分界线 —— 用户发现方向偏了时，最自然的反应是纠正，而不是推翻重来。要实现它，任务状态必须能接受外部注入的消息，这又回到了持久化那一条：**能暂停、能注入、能继续**，这三个能力是同一套机制支撑的。',
        },
      ],
      resourceIds: ['claude-streaming', 'claude-agent-sdk'],
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
      '审批只给自然语言转述，人看不到原始参数与目标',
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
