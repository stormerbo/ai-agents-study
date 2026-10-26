import type { Chapter } from '@/content/curriculum/schema';

export const chapter = {
  id: 'agent-frameworks',
  stageId: 'stage-3-orchestration',
  order: 13,
  title: '框架选型',
  subtitle: '在抽象与掌控之间',
  summary:
    '框架不是能力，是取舍的打包。手写完第 9 章那个循环之后，你已经知道该问什么了：它替我做哪几个零件、把哪个藏起来了、以及我需要下探时它让不让路。这一章把主流框架的抽象模型摆在一起比，并给出迁移成本的判断方法。',
  outcomes: [
    '能对照自己手写的循环，逐个确认框架覆盖了哪些部分',
    '能识别一个抽象会在什么条件下从帮助变成障碍',
    '能给出有依据的选型结论，而不是「社区大所以选它」',
  ],
  depth: 'guided',
  difficulty: 'intermediate',
  estimatedMinutes: 90,
  tags: ['framework', 'langgraph', 'agents-sdk'],
  prerequisiteIds: ['agent-loop'],
  lessons: [
    {
      id: 'agent-frameworks/what-frameworks-give',
      chapterId: 'agent-frameworks',
      slug: 'what-frameworks-give',
      title: '框架替你做了什么',
      summary: '把第 9 章那五个零件当清单，逐项对照。',
      estimatedMinutes: 18,
      difficulty: 'intermediate',
      hasBody: true,
      status: 'drafting',
      keywords: ['abstraction', 'checklist'],
      checkpoints: [
        {
          id: 'framework-checklist',
          basis: 'inferred',
          question: '评估一个 agent 框架时，该先确认哪几件事？',
          answer:
            '拿第 9 章的五个零件当清单：**循环的终止信号**（是否替你判断、依据是协议字段还是文本）、**工具调度**（schema 校验与权限放在哪层）、**预算与上限**（有没有默认值、能不能改）、**循环检测**（有没有、接不接得进去）、**状态持久化**（存在哪、能不能换）。\n\n还有一个贯穿性的问题：**出错时你能看到什么。** 一个框架如果把一次失败的中间轨迹吞掉了，你在生产里就只能靠猜 —— 这比缺少某个功能更致命。',
        },
        {
          id: 'framework-not-capability',
          basis: 'inferred',
          question: '为什么说「框架不是能力」？',
          answer:
            '因为它做的每一件事，你在第 9 章都已经手写过了 —— 无非是循环、调度、状态、预算。框架提供的是**组织方式的默认值**与**省下的胶水代码**，不是新的能力上限。\n\n这个区分在选型时很关键。如果你把框架当成能力来源，就会倾向于选功能列表最长的那个；而实际上决定成败的仍然是你怎么设计工具、怎么组织上下文、怎么设预算 —— 这些换任何框架都一样要做。\n\n现实一点的判据：**如果一个需求只有在某个框架里才做得到，先怀疑自己是不是漏掉了手写方案。**',
        },
      ],
      resourceIds: ['langchain-docs', 'openai-agents-sdk-python'],
    },
    {
      id: 'agent-frameworks/abstraction-models',
      chapterId: 'agent-frameworks',
      slug: 'abstraction-models',
      title: '三种抽象模型',
      summary: '线性序列、显式图和 agent loop —— 它们把控制流与模型决策放在不同位置。',
      estimatedMinutes: 20,
      difficulty: 'intermediate',
      hasBody: true,
      status: 'drafting',
      keywords: ['langgraph', 'agents-sdk', 'claude-agent-sdk'],
      checkpoints: [
        {
          id: 'three-models',
          basis: 'inferred',
          question: '本节用哪三种教学模型讨论控制流？它们之间是什么关系？',
          answer:
            '本节用三个便于比较的教学模型：**线性序列**把顺序写在组合表达式中；**图 / 状态机**把节点、状态和路由显式化；**agent loop**让模型输出参与下一步选择，由 host/runtime 执行并约束。它们不是完整分类或能力等级，也不互斥：图节点可以调用模型，agent loop 也可以被固定流程包围。\n\n选型时要看目标任务的决策位置、状态与恢复要求、预算、安全边界和团队维护成本，而不是按某个框架的标签直接归类。',
        },
        {
          id: 'explicit-vs-implicit-control',
          basis: 'inferred',
          question: '怎样区分应用编排与模型参与决策？',
          answer:
            '应用编排与模型决策不是互斥项。应用可以用图定义状态、步骤与路由，也可以在某个节点调用模型；模型输出参与后续选择时，host/runtime 仍负责验证、授权与执行。应明确每个决策点由谁作出，以及异常、超限、人工介入和恢复时的路径。\n\n对照候选实现时，不要假定「图一定显式且易调试」或「runner 一定隐式」。查看目标版本的实际接口、trace、停止条件和持久化配置，再用关键失败路径做原型验证。',
        },
        {
          id: 'langgraph-persistence-requires-checkpointer',
          basis: 'documented',
          question: '把流程写成 LangGraph 图，就自动获得跨进程断点恢复了吗？',
          answer: '不会。需配置 checkpointer，并在调用时提供稳定的 thread_id；需要跨线程保存的业务数据还应使用 store。检查点持久化图状态，不替外部副作用提供 exactly-once 保证；重放与幂等仍由应用设计。',
          sourceIds: ['langgraph-persistence'],
        },
      ],
      resourceIds: ['langchain-docs', 'langgraph-persistence', 'openai-agents-sdk-python', 'claude-agent-sdk'],
    },
    {
      id: 'agent-frameworks/leaky-abstractions',
      chapterId: 'agent-frameworks',
      slug: 'leaky-abstractions',
      title: '抽象在哪里泄漏',
      summary: '用 schema、重试和控制流边界识别何时需要下探，并估算本项目的维护成本。',
      estimatedMinutes: 20,
      difficulty: 'advanced',
      hasBody: true,
      status: 'drafting',
      keywords: ['leaky-abstraction', 'customization'],
      checkpoints: [
        {
          id: 'leak-points',
          basis: 'documented',
          question: '在 LangChain Core 0.3.63 中，普通 str、parse_docstring 与 Literal 分别影响什么？',
          answer:
            '`@tool` 默认从函数签名推断 schema，`parse_docstring` 默认关闭；开启后可解析 Google Style 参数说明，但说明文本本身不生成 enum。该版本的 `Literal["明天", "后天"]` 可生成字段 enum。请检查实际生成的 schema；这只说明本地 schema 生成，不证明 provider 接受所有关键字，也不保证模型输出正确。',
          sourceIds: ['langchain-core-063-tool-convert', 'langchain-core-063-tool-base'],
        },
        {
          id: 'escape-hatch-test',
          basis: 'inferred',
          question: '怎样在选型阶段评估一个抽象的扩展成本？',
          answer:
            '选一条对自己重要的需求，针对固定 SDK 版本与配置验证默认路径、扩展点、失败恢复和升级时的复核责任。记录测试覆盖范围及未验证的生产边界；可以将 fork 成本纳入比较，但“不需要 fork”不能单独证明框架安全或适合生产。',
        },
      ],
      resourceIds: ['langchain-docs', 'claude-agent-sdk', 'langchain-core-063-tool-convert', 'langchain-core-063-tool-base', 'openai-agents-sdk-python'],
    },
    {
      id: 'agent-frameworks/build-vs-buy',
      chapterId: 'agent-frameworks',
      slug: 'build-vs-buy',
      title: '反方立场：12-Factor Agents',
      summary: '「agent = 确定性软件 + 少量 LLM 决策点」—— 这个立场值得认真对待。',
      estimatedMinutes: 18,
      difficulty: 'intermediate',
      hasBody: true,
      status: 'drafting',
      keywords: ['build-vs-buy', 'determinism'],
      checkpoints: [
        {
          id: 'twelve-factor-stance',
          basis: 'documented',
          question: '12-Factor Agents 的核心主张是什么？它对框架的态度是什么？',
          answer:
            '12-Factor Agents 是 HumanLayer 作者提出的工程原则，不是框架能力的对照实验。它主张让应用能检查和掌握关键控制流、提示词、上下文与状态，同时明确表示这些原则不等于批评框架，也允许把小而模块化的 agent 概念整合进现有产品。应把它用作选型核对清单；具体框架是否满足某项原则，需要按版本、配置与目标故障路径验证。',
          sourceIds: ['twelve-factor-agents'],
        },
        {
          id: 'when-buy-wins',
          basis: 'inferred',
          question: '如何按具体需求评估采用框架、自行实现或组合使用？',
          answer:
            '不存在脱离上下文的“买一定更优”结论。先列出目标能力与故障路径，再核对候选方案在当前版本和配置下的行为、可观察性、升级责任、团队维护能力、迁移与退出成本。对关键成功路径和副作用失败路径运行可重复测试；把已验证、需配置、应用负责和未知项分别记录。选择能满足要求且责任边界可接受的方案，并保留复查条件。',
        },
      ],
      resourceIds: ['twelve-factor-agents', 'langchain-docs'],
    },
    {
      id: 'agent-frameworks/selection-matrix',
      chapterId: 'agent-frameworks',
      slug: 'selection-matrix',
      title: '选型矩阵与迁移成本',
      summary: '把选型还原成几个可回答的问题，并给迁移留出余地。',
      estimatedMinutes: 20,
      difficulty: 'intermediate',
      hasBody: true,
      status: 'drafting',
      keywords: ['selection', 'migration'],
      checkpoints: [
        {
          id: 'selection-questions',
          basis: 'inferred',
          question: '不依赖具体框架名，选型时该回答哪几个问题？',
          answer:
            '先区分不可妥协的门槛与可权衡偏好：provider/协议支持、授权与数据边界、失败与恢复语义属于常见硬门槛；团队熟悉度、集成便利、扩展方式和可观测性可按项目加权。候选方案按目标版本与配置验证关键成功路径和副作用失败路径，再记录证据、未知项与复查条件。此清单是工程判断，不是普遍排序规则。',
        },
        {
          id: 'openai-sdk-or-api-choice',
          basis: 'documented',
          question: 'OpenAI 官方文档如何说明 Agents SDK 与直接使用 Responses API 的适用选择？',
          answer:
            '官方首页将“由应用控制 loop、工具分发与状态处理”列为直接使用 Responses API 的适用方向；将希望 runtime 管理 turns、工具执行、guardrails、handoffs 或 sessions 列为使用 Agents SDK 的方向，并说明应用可以混用两者。这是 OpenAI 对自家产品路径的说明，不应外推为其他框架或 provider 的通用规律。具体能力需按当前版本与配置复核。',
          sourceIds: ['openai-agents-sdk-python'],
        },
        {
          id: 'migration-cost',
          basis: 'inferred',
          question: '怎样为将来换框架留出余地？',
          answer:
            '迁移成本不能由 import 数量直接推出。把依赖点作为定位线索，再按模型/provider 适配、工具与业务策略、持久化状态格式、trace/测试/告警以及升级/部署/退出责任拆工作项。对代表性工作流做切换演练，记录语义差异、数据转换、测试缺口和实际改动；不要将单个试点外推为全系统工时。自己的业务类型和适配层可减少部分 API 耦合，但不能保证行为或持久数据可直接迁移。',
        },
      ],
      resourceIds: ['langchain-docs', 'google-adk-docs', 'langchain-academy', 'openai-agents-sdk-python'],
    },
  ],
  resourceIds: [
    'langchain-docs',
    'langgraph-persistence',
    'openai-agents-sdk-python',
    'claude-agent-sdk',
    'twelve-factor-agents',
    'google-adk-docs',
    'langchain-academy',
  ],
  backendMapping: {
    analogy: '框架选型 ≈ 选 Web 框架：真正的差别不在功能表，而在「默认帮你做的那部分」是否合你的意',
    transferable: [
      '技术选型的通用方法：先列需求清单，再看匹配度，而不是先看热度',
      '「薄适配层」的经验：把外部依赖收口在一处，换起来才便宜',
      '评估迁移成本：盘点行为、持久化、接口和运营责任，再做代表工作流的切换演练',
    ],
    pitfalls: [
      '把框架当能力来源：功能列表最长的不一定最适合你',
      '没有目标工作流和验收契约就按功能清单选型，无法判断默认行为是否满足实际要求',
      '选型测试只跑 hello world，没有验证「默认行为不够用时能否下探」',
      '业务逻辑与编排逻辑混写，导致换框架等于重写',
    ],
    cost: 'low',
  },
  status: 'published',
  updatedAt: '2026-10-08',
  verifiedAt: '2026-10-08',
} satisfies Chapter;
