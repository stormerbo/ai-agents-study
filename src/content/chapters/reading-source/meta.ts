import type { Chapter } from '@/content/curriculum/schema';

export const chapter = {
  id: 'reading-source',
  stageId: 'stage-5-practice',
  order: 22,
  title: '源码研读',
  subtitle: '按「读它的理由」挑项目',
  summary:
    '到了一个临界点之后，最高效的学习方式不再是读教程，而是读实现。这一章讲怎么带着问题去读、怎么挑值得读的项目、以及读完之后该产出什么 —— 否则读了十份源码，能力还是停在「见识过」。',
  outcomes: [
    '能说清读一个 agent 项目时该追问的五个问题',
    '能沿着一次真实任务的调用链把源码读到底，而不是通读文件',
    '能把读到的实现对比成一张表，形成自己的选型依据',
  ],
  depth: 'guided',
  difficulty: 'advanced',
  estimatedMinutes: 85,
  tags: ['source-reading', 'architecture'],
  prerequisiteIds: ['agent-loop', 'agent-frameworks'],
  lessons: [
    {
      id: 'reading-source/why-and-how',
      chapterId: 'reading-source',
      slug: 'why-and-how',
      title: '为什么读到一定阶段必须读源码',
      summary: '教程给你的是结论，源码给你的是取舍发生的现场。',
      estimatedMinutes: 16,
      difficulty: 'intermediate',
      hasBody: true,
      status: 'drafting',
      keywords: ['source-reading'],
      checkpoints: [
        {
          id: 'why-source',
          basis: 'inferred',
          question: '为什么在有了框架文档之后，还需要读源码？',
          answer:
            '因为文档记录的是**结论**，而源码里保存着**取舍发生的现场**。具体来说有三样东西文档通常不写：**默认值是怎么定的**（重试几次、超时多久、上下文超限时先丢哪部分）—— 这些默认值是框架作者对现实的判断，往往比文档里的功能列表更有信息量；**失败路径怎么走**（出错了是重试、降级还是抛出），这决定了你在生产里会看到什么；以及**哪些设计是妥协的结果**（代码注释与结构里常留着痕迹）。文档告诉你它能做什么，源码告诉你它在压力下会怎么表现。',
        },
        {
          id: 'five-questions',
          basis: 'inferred',
          question: '读一个 agent 项目时，该带着哪几个问题？',
          answer:
            '用第 9 章那五个零件当骨架，逐个去源码里找答案：**终止条件**（循环靠什么结束）、**工具调度**（schema 校验与权限放在哪一层）、**预算**（有没有上限、默认多少）、**循环检测**（有没有、怎么实现）、以及**状态持久化**（存在哪、恢复语义是什么）。再补一个横向问题：**它的错误处理策略是什么**（哪些错误重试、哪些直接失败）。这六个问题带着读，你能在两小时内建立起对一个陌生 agent 项目的准确判断 —— 比从头读一遍 README 加目录结构快得多，也可靠得多。',
        },
      ],
      resourceIds: ['twelve-factor-agents', 'claude-agent-sdk'],
    },
    {
      id: 'reading-source/picking-projects',
      chapterId: 'reading-source',
      slug: 'picking-projects',
      title: '挑项目：按理由，不按热度',
      summary: '一个项目的价值不在于它有多流行，而在于它能回答你哪个问题。',
      estimatedMinutes: 18,
      difficulty: 'intermediate',
      hasBody: true,
      status: 'drafting',
      keywords: ['selection', 'repositories'],
      checkpoints: [
        {
          id: 'picking-criteria',
          basis: 'inferred',
          question: '怎么判断一个开源 agent 项目值不值得读？',
          answer:
            '先问**你想从它身上学到什么**，再看它是否恰好演示了那件事。几个具体的读法：想学**循环与工具调度**，读最小的那个实现（越简单越容易看清骨架）；想学**评测与数据集**，读自带 benchmark 的项目；想学**生产化处理**，读那些明确写了持久化、重试与审批的项目；想学**协议接入**，读 MCP 的参考实现。要避开的是两类：**只做包装的项目**（薄薄一层套在某个 API 上，读完学不到东西），以及**规模远超你当前问题**的项目（读三天还没进入正题，收益极低）。这与资源库那条原则一致 —— 按「读它的理由」组织，而不是按 star 数排序。',
        },
        {
          id: 'archived-means-something',
          basis: 'inferred',
          question: '读到一个已归档或长期不更新的项目，该怎么对待？',
          answer:
            '把它当**历史样本**读，而不是当依赖。它有价值的场景是：它演示了一种现在少见的取舍（比如某个已被主流放弃的架构），或者它的设计文档比代码更有信息量。要警惕的是把它的结论当现状 —— 领域变化很快，一个两年前的「最佳实践」可能已经被证伪。判断方法很直接：看它最后一次实质性更新是什么时候，以及那之后你所依赖的接口有没有变化（第 12 章的 MCP 规范就是例子：2026-07-28 的破坏性修订会让更早的示例代码直接跑不通）。',
        },
      ],
      resourceIds: ['openhands', 'open-deep-research', 'aider'],
    },
    {
      id: 'reading-source/trace-one-task',
      chapterId: 'reading-source',
      slug: 'trace-one-task',
      title: '沿着一次任务读到底',
      summary: '不要通读文件；跟着一次真实调用走一遍。',
      estimatedMinutes: 22,
      difficulty: 'advanced',
      hasBody: true,
      status: 'drafting',
      keywords: ['debugging', 'call-chain'],
      checkpoints: [
        {
          id: 'trace-method',
          basis: 'inferred',
          question: '面对一个陌生的 agent 代码库，最高效的读法是什么？',
          answer:
            '**从入口开始，跟着一次真实的单次任务往下走**，每一步只读「这一段做了什么、把控制权交给了谁」，不深究实现细节。路径通常是：请求入口 → 组装上下文（system、工具、历史）→ 调用模型 → 解析响应 → 判断是否要继续 → 执行工具 → 回填 → 再循环。走完一遍你就有了一张调用图，之后想深入哪一块再回去读。这比按目录顺序读文件有效得多，因为**agent 的复杂度在流程上，而不在单个模块里** —— 只有沿着流程走，你才能看到各个决策点分散在哪些层。',
        },
        {
          id: 'what-to-note',
          basis: 'inferred',
          question: '沿着调用链读的时候，重点该记什么？',
          answer:
            '记**决策点**，而不是函数名。具体是三类：**判断条件**（if stop_reason == tool_use 这类分支 —— 它们是框架对协议的理解）、**默认值**（超时、重试次数、截断策略）、以及**数据在哪一层被转换了形态**（比如消息在进入模型前经过哪几次归一化）。第三类在实践中价值最高：出问题时你往往需要知道「这个字段是在哪里被改掉的」，而这在模块化阅读里是看不出来的。至于函数名与实现细节，需要时再查即可 —— 它们不像决策点那样承载判断。',
        },
      ],
      resourceIds: ['claude-agent-sdk', 'openai-agents-sdk-python'],
    },
    {
      id: 'reading-source/compare',
      chapterId: 'reading-source',
      slug: 'compare',
      title: '横向对比：同一个能力的不同实现',
      summary: '单个实现只能告诉你「有人这么做」，对比才能告诉你「为什么这么做」。',
      estimatedMinutes: 20,
      difficulty: 'advanced',
      hasBody: true,
      status: 'drafting',
      keywords: ['comparison', 'abstraction'],
      checkpoints: [
        {
          id: 'compare-dimensions',
          basis: 'inferred',
          question: '横向对比几个框架时，该拿哪几个维度去比？',
          answer:
            '用第 9 章的零件加三条：**循环的所有权**（框架替你跑循环，还是你显式写每一步）、**状态的表达**（它把状态建模成什么 —— 消息列表、图上的节点、还是会话对象）、**工具的接入方式**（内置注册表、还是通过协议接外部 server）、**人类介入点**（哪里有钩子、能拦到什么粒度）、以及**可观测性的默认值**（默认给多少追踪、能不能导出）。五个维度的组合基本决定了一个框架适合什么形态的系统 —— 而这比「它功能多不多」有用得多，因为功能表拉长到最后大家都差不多。',
        },
        {
          id: 'compare-output',
          basis: 'inferred',
          question: '对比之后应该产出什么？',
          answer:
            '一张**自己的选型表**，而且它能被后来的事实检验。要点有三：每个维度写清「这个框架怎么做的」以及「这个做法在什么情况下会成为问题」（后者是关键 —— 只写优点的对比没有决策价值）；标注你是**读代码得出的还是读文档得出的**（两者可信度不同）；以及写下**什么条件下你会换掉它**。最后一条常被省略，但它是选型质量的最好证明：如果你说不出什么情况会让自己改变选择，那这个选择多半不是分析出来的。',
        },
      ],
      resourceIds: ['langchain-docs', 'openai-agents-sdk-python', 'claude-agent-sdk'],
    },
    {
      id: 'reading-source/outputs',
      chapterId: 'reading-source',
      slug: 'outputs',
      title: '读完要产出什么',
      summary: '没有产出的阅读，下次还得重读一遍。',
      estimatedMinutes: 18,
      difficulty: 'intermediate',
      hasBody: true,
      status: 'drafting',
      keywords: ['notes', 'learning'],
      checkpoints: [
        {
          id: 'reading-outputs',
          basis: 'inferred',
          question: '读完一份源码，值得留下哪几种产出？',
          answer:
            '三种，按价值排序：**一张调用链图**（一次任务从入口到结束经过哪些决策点）—— 它是你下次回到这个项目时的地图；**一份反面对照**（这个实现哪里让你觉得不对、为什么）—— 判断力是在这里长出来的，而不是在复述别人的设计时；以及**一段可运行的最小复现**（把它最核心的那个机制用几十行自己重写一遍）。第三种最费时间但最有效 —— 能把某个机制独立重写出来，说明你真的看懂了它的边界条件，而不只是记住了它的结构。第 9 章那个手写循环就是这种产出。',
        },
        {
          id: 'avoid-collecting',
          basis: 'inferred',
          question: '「读了很多源码但没长进」通常是什么原因？',
          answer:
            '把阅读当成了**收集**而不是**对照**。具体表现是：读完只记得「它用了 A 模式」，却回答不了「如果换我来做会怎么选、为什么」。缺少对照，读到的设计就只是一堆事实，无法迁移到自己的问题上。解法很具体：每读一个项目，强迫自己写下至少一条**不同意的地方**，以及**它在什么输入下会失效**。这两个问题逼着你从「它怎么做」转向「它为什么这么做、代价是什么」—— 而这个转变才是读源码真正的收益。它和本站反复出现的立场一致：**结论不值钱，取舍的依据才值钱。**',
        },
      ],
      resourceIds: ['ai-engineering-huyen', 'twelve-factor-agents'],
    },
  ],
  resourceIds: ['claude-agent-sdk', 'openai-agents-sdk-python', 'langchain-docs', 'openhands', 'open-deep-research', 'twelve-factor-agents'],
  backendMapping: {
    analogy: '读 agent 源码 ≈ 读一个你打算引入的中间件：先看它的关键路径与失败处理，再决定信不信它',
    transferable: [
      '读陌生代码库的方法：从入口沿线走，不通读文件',
      '关注默认值与失败路径 —— 这是判断一个库是否可靠的关键',
      '对比选型的习惯：列维度、写代价、留下可被检验的结论',
    ],
    pitfalls: [
      '按目录通读文件，读完仍说不清一次任务是怎么跑完的',
      '按 star 数挑项目，读了大量与当前问题无关的代码',
      '把已归档项目的结论当现状',
      '只记录「它做了什么」，不记录「代价是什么」',
      '读而不产出，下次还要从头再读一遍',
    ],
    cost: 'low',
  },
  status: 'published',
  updatedAt: '2026-10-08',
  verifiedAt: '2026-10-08',
} satisfies Chapter;
