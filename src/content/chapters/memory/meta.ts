import type { Chapter } from '@/content/curriculum/schema';

export const chapter = {
  id: 'memory',
  stageId: 'stage-2-primitives',
  order: 7,
  title: '记忆',
  subtitle: '跨会话的状态，以及遗忘',
  summary:
    '上下文是工作记忆，不是记忆系统。这一章讲清什么信息值得写进外部存储、什么时候该召回、记错了怎么收回，以及为什么绝大多数记忆系统的失败不在于「记不住」，而在于「记了不该记的」。',
  outcomes: [
    '能区分工作记忆与长期记忆，并说出各自的失效方式',
    '能设计写入规则：什么该记、什么绝对不能记',
    '能处理记忆的过期与冲突，而不是让它们互相矛盾地堆在库里',
  ],
  depth: 'deep',
  difficulty: 'advanced',
  estimatedMinutes: 100,
  tags: ['memory', 'state', 'persistence'],
  prerequisiteIds: ['retrieval', 'context-engineering'],
  lessons: [
    {
      id: 'memory/context-is-not-memory',
      chapterId: 'memory',
      slug: 'context-is-not-memory',
      title: '上下文不是记忆',
      summary: '单次调用的上下文输入不自动构成记忆系统；持久化与编辑行为由应用或 API 决定，记忆还需要选择性写入、检索与冲突裁决。',
      estimatedMinutes: 18,
      difficulty: 'intermediate',
      hasBody: true,
      status: 'drafting',
      keywords: ['working-memory', 'long-term-memory'],
      checkpoints: [
        {
          id: 'why-context-isnt-memory',
          basis: 'inferred',
          question: '为什么「把对话历史全部留着」不能算记忆？',
          answer:
            '单次调用的上下文是交给模型处理的输入，不会自动决定哪些事实应长期保留、何时召回、如何更新或解决冲突。应用可以保存和编辑自己的对话状态，供应商 API 也可能提供托管会话；具体生命周期与编辑能力应按所用产品/API 合约确认。外部记忆的价值在于把选择性写入、来源、有效期、检索与冲突裁决做成明确的系统语义，而不是因为上下文必然会在请求后消失或不能修改。',
          note: '这里的“记忆”是工程设计术语，不是所有模型/API 都共享的标准分类。',
        },
        {
          id: 'provider-conversation-state',
          basis: 'documented',
          question: '下一轮上下文是否必然由客户端重发，且服务端不会保留对话状态？',
          answer:
            '不是。OpenAI 文档区分客户端手动传递历史的无状态请求、通过 \x60previous_response_id\x60 续接 Responses，以及跨会话复用的 Conversations 对象。续接不等于省去历史输入计量：OpenAI 文档说明，Responses 链中先前的输入 token 仍按输入 token 计费。服务端状态能力不等于应用已经实现长期记忆治理；仍需检查留存、删除和授权契约。',
          sourceIds: ['openai-conversation-state'],
        },
        {
          id: 'current-deepseek-context-window',
          basis: 'documented',
          question: 'DeepSeek 当前模型目录对 V4.1-Flash 与 V4-Pro 列出的上下文长度是多少？',
          answer:
            '截至 2026-10-22，官方模型列表 API 对当前 `deepseek-flash`（显示名 DeepSeek-V4.1-Flash）与 `deepseek-v4-pro` 返回 `context_window: 1048576`，约为 1M。该目录只描述查询时的可用模型，不证明 2026-10-08 的兼容请求对应同一后端版本或路由。',
          sourceIds: ['deepseek-model-list-api', 'deepseek-models-pricing'],
        },
        {
          id: 'historical-long-context-observations',
          basis: 'unverified',
          question: '旧记录中的 1,040,038-token 与 13 万 token 海捞针结果可以独立复核或推广吗？',
          answer:
            '不能。它们只能作为日期、端点和模型标识有限定的历史摘要；缺少逐次请求/响应、模型后端指纹和评分记录，不能复算、估计位置效应概率或证明当前模型规格。',
          note: '2026-10-08 原始记录未归档；新运行只能构成另一场实验，不能替代旧数据。',
        },
        {
          id: 'three-kinds-of-memory',
          basis: 'inferred',
          question: '把「记忆」笼统当成一件事，会漏掉什么区别？',
          answer:
            '为设计方便，可区分三类状态；这是本教程的工作分类，不是通用协议：\n\n1. **会话状态** —— 为同一会话后续轮提供的历史或 checkpoint；保留多久由应用/API 与数据策略决定，任务结束不自动意味着必须立即删除。\n2. **事实记忆** —— 用户偏好、项目约束或已有配置；记录来源、适用范围和失效条件，跨会话使用前仍要校验。\n3. **程序性知识** —— 工具说明、流程和成功路径；它可能属于版本化的产品配置或知识库，不一定与用户个人记忆放在同一存储。\n\n把不同来源和生命周期的状态混在一起，会让一次性上下文被误当成稳定偏好，也会让删除、更新和授权边界变得难以验证。',
          note: '分类用于建立 schema 和治理问题；实际系统可采用不同分层，重点是明确来源、生命周期、权限和删除行为。',
        },
      ],
      resourceIds: [
        'memgpt-paper',
        'anthropic-context-engineering',
        'openai-conversation-state',
        'deepseek-models-pricing',
        'deepseek-model-list-api',
        'lost-in-the-middle',
      ],
    },
    {
      id: 'memory/what-to-write',
      chapterId: 'memory',
      slug: 'what-to-write',
      title: '写入：什么该记，什么绝对不能记',
      summary: '记忆系统的第一道关口是写入规则，而不是检索算法。',
      estimatedMinutes: 22,
      difficulty: 'advanced',
      hasBody: true,
      status: 'drafting',
      keywords: ['write-policy', 'privacy'],
      checkpoints: [
        {
          id: 'write-criteria',
          basis: 'inferred',
          question: '一条信息要满足什么条件才值得写进长期记忆？',
          answer:
            '这三项是个人偏好/项目事实记忆的初筛启发式，不是通用充分条件：未来会话中的预期用途、存储维护价值、来源可追溯性。短期但有明确用途的信息可设置 scope 与 valid_until；长期偏好也会过期。是否写入还取决于产品的记忆开关、用户控制、敏感级别、租户范围与删除策略。模型自报来源不等于可信证据；应保存受控 source_ref，并把推断与用户明说区分。',
        },
        {
          id: 'why-store-everything-fails',
          basis: 'inferred',
          question: '「把用户说的每句话都存下来」为什么会在长期变成灾难？',
          answer:
            '无差别写入会增加检索噪声、保留冲突或过期陈述，并扩大敏感数据暴露面；是否发生及其任务影响要用系统自己的轨迹评估。它们并非必然不可删除：可追溯 ID、索引映射、删除传播和保留策略能支持治理；写入时控制仍可减少后续清理成本。',
        },
      ],
      resourceIds: ['mem0', 'letta', 'anthropic-stop-reasons'],
    },
    {
      id: 'memory/when-to-recall',
      chapterId: 'memory',
      slug: 'when-to-recall',
      title: '读取：什么时候召回，以及误召回的代价',
      summary: '检索候选不等于注入许可；来源、TTL 与相关性策略应分开判定，并按任务后果评估误召回与漏召回。',
      estimatedMinutes: 20,
      difficulty: 'advanced',
      hasBody: true,
      status: 'drafting',
      keywords: ['recall', 'injection'],
      checkpoints: [
        {
          id: 'inject-vs-tool',
          basis: 'inferred',
          question: '记忆是「每轮自动注入」好，还是「做成工具让模型自己查」好？',
          answer:
            '取决于记忆是**普遍相关**还是**条件相关**，并要用目标任务验证。\n\n回复语言或格式偏好可能值得常驻，但条数应按请求形态、实际使用率、token 成本和错误影响决定；不要把固定条数或账单倍率当作通则。\n\n项目部署环境通常只在相关任务中需要，可按需查询。检索到的候选仍须通过来源、时效和相关性策略；把无关候选当成可信事实注入，可能影响输出，但是否发生、是否静默都需在目标工作流中评估。',
        },
        {
          id: 'recall-gates-and-thresholds',
          basis: 'inferred',
          question: '来源、有效期和相关性筛选能否共用一个阈值？',
          answer:
            '不能把它们合并为同一分数判断。来源策略按 provenance 类型执行，时效按记录的 updated_at 与 ttl_days 比较，相关性阈值则须在目标“问题—记忆”标注集上校准并用独立数据验证。检索分数形成候选，不自动授予注入许可；记录实际注入项与被拦截项时，避免默认写入完整查询正文。',
        },
        {
          id: 'false-recall-cost',
          basis: 'inferred',
          question: '误召回与漏召回的风险应如何比较？',
          answer:
            '两者都可能损害任务：漏召回可能让模型缺少事实并用先验补全；误召回可能把无关内容作为可信前提。哪一种更严重取决于任务、安全后果、模型行为和检测机制，不能假设模型一定采纳或一定承认不知道。\n\n2026-10-08 的历史摘要记录过 Python 2.7 部署输出差异，但原始请求、响应和评分器未保存，不能证明普遍因果或估计发生率。应在目标任务上对比错误类型、任务成功和可发现性，再决定召回门槛。',
        },
      ],
      resourceIds: ['letta', 'anthropic-context-engineering'],
    },
    {
      id: 'memory/forgetting-and-conflict',
      chapterId: 'memory',
      slug: 'forgetting-and-conflict',
      title: '遗忘、更新与冲突',
      summary: '通过明确版本关系、有效期与删除状态，管理记忆更新、过期和冲突；自动裁决须限定适用范围。',
      estimatedMinutes: 22,
      difficulty: 'expert',
      hasBody: true,
      status: 'drafting',
      keywords: ['conflict', 'ttl', 'provenance'],
      checkpoints: [
        {
          id: 'conflicting-memories',
          basis: 'inferred',
          question: '两条互相矛盾的记忆同时被召回，系统该怎么办？',
          answer:
            '先确认记录属于同一主体、scope 和事实键，并保留来源、带时区时间、确认状态与版本关系。来源类型不构成跨场景通用的真值排序；较新时间也不能单独证明事实更新。只有明确的更新关系、可验证的用户/审核者确认及产品策略允许时才自动切换版本；`supersession_confirmed` 这样的证据字段只能由可信写入流程生成，不能信任模型提供的布尔值。同键多值、来源不可比或关系缺失/未确认时，阻止自动注入并进入待审/用户确认流程。模型可生成冲突解释或澄清问题，不能替用户选边。',
        },
        {
          id: 'why-forgetting-is-a-feature',
          basis: 'inferred',
          question: '为什么「遗忘」应该是记忆系统的显式功能，而不是可以一直拖延的事？',
          answer:
            '数据增长不必然降低检索精确率，但缺少过期过滤和删除路径可能让陈旧内容再次进入提示。明确区分有效期、版本失效与用户删除：有效期依数据波动、误用风险、确认成本制定；失效记录在召回时过滤；删除先在权威库写入 tombstone 并阻止注入，再通过可重试流程清理索引和副本。跨库清理需做身份/scope 校验、revision 防护与结果监测；实际保留义务依产品和部署要求核实。',
        },
      ],
      resourceIds: ['mem0', 'letta', 'ai-engineering-huyen'],
    },
    {
      id: 'memory/memory-cost-and-eval',
      chapterId: 'memory',
      slug: 'memory-cost-and-eval',
      title: '记忆的成本与评估',
      summary: '记忆读写都要钱，而它到底改善了哪个指标，必须能被说清楚。',
      estimatedMinutes: 18,
      difficulty: 'advanced',
      hasBody: true,
      status: 'drafting',
      keywords: ['cost', 'evaluation'],
      checkpoints: [
        {
          id: 'memory-cost-model',
          basis: 'inferred',
          question: '记忆系统的成本由哪几部分组成？',
          answer:
            '先按单位分账：模型调用（输入/输出 token、缓存与调用数）、存储、检索基础设施、人工复核和运营。不可把 token 与存储费用直接相加。注入记忆会在它进入的后续请求中增加输入；增量取决于注入频率、上下文、缓存与供应商计价。写入成本也随提取策略变化；需用目标部署的 usage 与账单核实。',
        },
        {
          id: 'memory-eval',
          basis: 'inferred',
          question: '怎么判断一套记忆系统值不值得？',
          answer:
            '先定义目标任务、可复核的评分规则和错误代价，再用相同任务与配置比较开/关记忆的逐题结果。可观测指标包括任务成功、重复澄清、误用、漏用和用户纠正，但纠正率会漏掉静默错误；活动指标只用于诊断。二元配对结果应按不一致任务分析，pilot 不自动证明普遍收益。',
        },
      ],
      resourceIds: ['mem0', 'ai-engineering-huyen', 'nist-mcnemar-test', 'paired-binomial-tests-intervals-fagerland', 'nist-proportion-confidence-intervals'],
    },
  ],
  resourceIds: [
    'memgpt-paper',
    'mem0',
    'letta',
    'anthropic-context-engineering',
    'ai-engineering-huyen',
  ],
  labIds: ['lab-memory-write'],
  backendMapping: {
    analogy: '记忆 ≈ 给一个无状态服务加持久化层，但写进去的是「模型得出的结论」而不是「事实」',
    transferable: [
      '缓存失效、TTL、最终一致性这些你熟悉的机制在这里全都用得上',
      '审计日志的思路：每条记忆都要能追到来源',
      '写入侧做减法（限流、脱敏、去重）比读侧优化更有效',
    ],
    pitfalls: [
      '把记忆当成「上下文不够用时的溢出容器」：它会变成噪声库',
      '无差别写入：把一次性陈述、无关信息、模型的推断一起存进去',
      '没有冲突解决策略，让互相矛盾的记忆长期共存',
      '只统计召回次数这类活动指标，而不是对照实验里的效果差异',
      '忽略「注入进上下文的内容每轮都要重新计费」',
    ],
    cost: 'high',
  },
  status: 'published',
  updatedAt: '2026-10-08',
  verifiedAt: '2026-10-08',
} satisfies Chapter;
