import type { Chapter } from '@/content/curriculum/schema';

export const chapter = {
  id: 'agent-frameworks',
  stageId: 'stage-3-orchestration',
  order: 11,
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
      hasBody: false,
      status: 'outlined',
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
      summary: '图、agent-runner、session-hooks —— 它们对「一个 agent 是什么」的回答不同。',
      estimatedMinutes: 20,
      difficulty: 'intermediate',
      hasBody: false,
      status: 'outlined',
      keywords: ['langgraph', 'agents-sdk', 'claude-agent-sdk'],
      checkpoints: [
        {
          id: 'three-models',
          basis: 'inferred',
          question: '主流框架对「一个 agent」的抽象，大致有哪几种形态？',
          answer:
            '三种，差别在**你把流程写成什么形状**：\n\n1. **图 / 状态机** —— 节点是步骤、边是转移条件（LangGraph 这一类）。控制流是显式的，适合步骤清晰、需要人工介入与分支的任务。代价是你要把流程想清楚才能写。\n2. **agent + runner + handoff** —— 你定义一个 agent（指令 + 工具），runner 负责循环，多个 agent 之间用转交连接（OpenAI Agents SDK 这一类）。最少的样板代码，代价是循环内部的细节默认由框架决定。\n3. **session + 钩子** —— 以会话为中心，通过权限、钩子、子 agent、技能来定制行为（Claude Agent SDK 这一类）。它假设你要的是一个能干活的编码/操作型 agent，而不是自己拼一套流程。\n\n选哪种，先看你**更愿意把复杂度写在哪里**：写在流程里（图）、写在配置里（runner）、还是写在钩子里（session）。',
        },
        {
          id: 'explicit-vs-implicit-control',
          basis: 'inferred',
          question: '「控制流显式」和「控制流隐式」分别适合什么情况？',
          answer:
            '**显式**（图）适合流程需要被审计、被干预、被复用的场景 —— 你能指着图说「这一步之后必须人工确认」。它也更容易做可视化与断点调试。代价是灵活性：流程要改就得改图。\n\n**隐式**（runner 循环）适合流程本身就是「模型自己决定下一步」的场景 —— 硬写成图反而是自欺欺人，因为你并不知道它下一步会做什么。代价是可观测性与可控性都要另外补。\n\n一个实用的折中：**外层用显式流程，内层用隐式循环。** 把「必须按顺序发生的几件事」写成图或普通代码，把「每件事内部怎么探索」交给 agent 循环。',
        },
      ],
      resourceIds: ['langchain-docs', 'openai-agents-sdk-python', 'claude-agent-sdk'],
    },
    {
      id: 'agent-frameworks/leaky-abstractions',
      chapterId: 'agent-frameworks',
      slug: 'leaky-abstractions',
      title: '抽象在哪里泄漏',
      summary: '四个最常见的下探触发点，选型时就该问清楚。',
      estimatedMinutes: 20,
      difficulty: 'advanced',
      hasBody: false,
      status: 'outlined',
      keywords: ['leaky-abstraction', 'customization'],
      checkpoints: [
        {
          id: 'leak-points',
          basis: 'inferred',
          question: '实际项目里，最常被迫下探到框架内部的是哪几种需求？',
          answer:
            '四个：**自定义重试与预算策略**（默认策略与你的成本模型不匹配）、**替换状态存储**（默认存在内存或某个你不想要的数据库里）、**插入人工确认点**（高风险动作前必须停下来等人）、以及**拿到完整的执行轨迹**（用于成本归因与故障复盘）。\n\n这四个的共同点是：**它们都发生在「默认行为不够用」的时刻，而那正是生产与 demo 的分界线。** 所以选型测试不该是「跑通一个 hello world」，而该是「把其中一项需求实现一遍」。',
        },
        {
          id: 'escape-hatch-test',
          basis: 'inferred',
          question: '怎么在选型阶段就判断一个框架让不让路？',
          answer:
            '做一次**逃逸测试**：挑上面四项里你最需要的一项，在**不改框架源码**的前提下实现它。允许的话，抽象就是安全的；要 fork 才能做，就说明这个抽象在你的场景里迟早会成为负债。\n\n两项补充证据也很有用：**错误信息的可读性**（出问题时它告诉你的是「第几步、哪个工具、什么参数」，还是一句泛泛的异常），以及**能否导出完整调用轨迹**（第 4 阶段做成本归因时会直接依赖它）。\n\n这两项都不需要写代码就能验证 —— 看文档和 issue 区即可。',
        },
      ],
      resourceIds: ['langchain-docs', 'claude-agent-sdk'],
    },
    {
      id: 'agent-frameworks/build-vs-buy',
      chapterId: 'agent-frameworks',
      slug: 'build-vs-buy',
      title: '反方立场：12-Factor Agents',
      summary: '「agent = 确定性软件 + 少量 LLM 决策点」—— 这个立场值得认真对待。',
      estimatedMinutes: 18,
      difficulty: 'intermediate',
      hasBody: false,
      status: 'outlined',
      keywords: ['build-vs-buy', 'determinism'],
      checkpoints: [
        {
          id: 'twelve-factor-stance',
          basis: 'documented',
          question: '12-Factor Agents 的核心主张是什么？它对框架的态度是什么？',
          answer:
            '核心主张是把 agent 当作**确定性软件**来写：大部分流程由你自己的代码控制，只在真正需要判断的地方调用模型。它的反对对象不是某个框架，而是「把控制流整个交给模型和框架」这种默认做法。\n\n放到本站的语境里，它与第 9 章手写循环的立场一致：**先知道轮子怎么造，再看官方抽象。** 顺序反过来，你就失去了判断哪些抽象是必要的、哪些只是多一层的机会。\n\n要注意这份材料是**立场声明而不是在演进的项目**（仓库最后更新停留在 2025 年 9 月），读它的观点即可，不必等新版本。',
          sourceIds: ['twelve-factor-agents'],
        },
        {
          id: 'when-buy-wins',
          basis: 'inferred',
          question: '什么情况下「买」明显优于「自己写」？',
          answer:
            '三种情况：**需要持久化执行**（自己实现检查点与恢复的成本远高于引入一个成熟方案）、**需要团队协作**（统一抽象降低沟通成本，新人不必读你手写的循环）、以及**需要现成的可观测与部署链路**（追踪、评测、部署配套齐全）。\n\n反过来，如果你的流程并不复杂、只有一个团队维护、而且对成本与延迟极其敏感，那么一个几百行的自研循环往往比引入框架更划算 —— 你付的框架成本（学习、版本升级、抽象绕行）会超过你省下的代码量。',
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
      hasBody: false,
      status: 'outlined',
      keywords: ['selection', 'migration'],
      checkpoints: [
        {
          id: 'selection-questions',
          basis: 'inferred',
          question: '不依赖具体框架名，选型时该回答哪几个问题？',
          answer:
            '五个：**流程是显式已知还是会动态决定**（决定抽象模型）；**任务是否需要持久化执行**（决定要不要引入执行层）；**是否需要多智能体**（大多数情况下不需要，见第 10 章）；**团队规模与既有技术栈**（决定学习成本能否摊薄）；**是否需要下探自定义**（决定抽象是否安全）。\n\n把这五个问题的答案写下来，再去看候选框架的文档，你会发现问题从「哪个更好」变成了「哪个匹配」。前者没有答案，后者有。',
        },
        {
          id: 'migration-cost',
          basis: 'inferred',
          question: '怎样为将来换框架留出余地？',
          answer:
            '三个约定，都不依赖具体框架：**业务逻辑与编排逻辑分开写**（工具的实现、校验、数据访问不要蘸上框架的类型）；**状态用你自己的 schema 表达**（框架的存储格式当作序列化细节）；**把模型调用收口在一个薄适配层**（本站的 Playground 就是这个做法 —— 适配器按协议选，而不是按厂商）。\n\n判断标准很直接：**你的业务代码里 import 了多少框架符号？** 越少，迁移越便宜。如果数据访问层直接 import 了框架的节点类型，那么换框架就等于重写。',
        },
      ],
      resourceIds: ['langchain-docs', 'google-adk-docs', 'langchain-academy'],
    },
  ],
  resourceIds: ['langchain-docs', 'openai-agents-sdk-python', 'claude-agent-sdk', 'twelve-factor-agents', 'google-adk-docs', 'langchain-academy'],
  backendMapping: {
    analogy: '框架选型 ≈ 选 Web 框架：真正的差别不在功能表，而在「默认帮你做的那部分」是否合你的意',
    transferable: [
      '技术选型的通用方法：先列需求清单，再看匹配度，而不是先看热度',
      '「薄适配层」的经验：把外部依赖收口在一处，换起来才便宜',
      '评估迁移成本的方式：数一数业务代码里渗透了多少框架符号',
    ],
    pitfalls: [
      '把框架当能力来源：功能列表最长的不一定最适合你',
      '跳过手写直接上框架，于是无法判断哪些抽象是必要的',
      '选型测试只跑 hello world，没有验证「默认行为不够用时能否下探」',
      '业务逻辑与编排逻辑混写，导致换框架等于重写',
    ],
    cost: 'low',
  },
  status: 'outlined',
  updatedAt: '2026-10-08',
  verifiedAt: '2026-10-08',
} satisfies Chapter;
