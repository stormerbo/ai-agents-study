import type { Chapter } from '@/content/curriculum/schema';

export const chapter = {
  id: 'agent-loop',
  stageId: 'stage-3-orchestration',
  order: 11,
  title: '手写一个 Agent 循环',
  subtitle: '从零实现一遍，再回头看框架',
  summary:
    '一个 agent 循环的全部零件其实只有五个：终止信号、工具调度、预算、循环检测、状态持久化。这一章从零把它写出来，写到能跑长任务、能从崩溃里恢复为止 —— 之后再看任何框架，你都能一眼看出它替你做了什么、以及它藏起了什么。',
  outcomes: [
    '能不看框架文档、用一个 while 循环写出可用的 agent',
    '能给循环加上预算上限、重复检测与超时，而不是等它跑飞',
    '能说清一个框架的抽象覆盖了这五个零件中的哪几个',
  ],
  depth: 'deep',
  difficulty: 'advanced',
  estimatedMinutes: 110,
  tags: ['agent-loop', 'orchestration', 'durability'],
  prerequisiteIds: ['agent-paradigms'],
  lessons: [
    {
      id: 'agent-loop/minimal-loop',
      chapterId: 'agent-loop',
      slug: 'minimal-loop',
      title: '最小循环：循环的边界在哪里',
      summary: '哪些事必须由你的代码决定，哪些可以交给模型 —— 这条线画错了，后面全是补丁。',
      estimatedMinutes: 20,
      difficulty: 'intermediate',
      hasBody: false,
      status: 'outlined',
      keywords: ['loop', 'stop-reason'],
      checkpoints: [
        {
          id: 'stop-condition',
          basis: 'documented',
          question: '判断「循环该继续还是该结束」，唯一可靠的信号是什么？',
          answer:
            '是响应的 `stop_reason`，不是输出文本的内容。第 4 章实测过：模型发出工具调用时 `stop_reason` 是 `tool_use`，正常收尾时是 `end_turn`。\n\n为什么要强调「不是文本内容」：如果你靠「输出里有没有包含某个词」来判断结束，就同时依赖了措辞与模型的配合，这两样都不可靠。而 `stop_reason` 是协议字段 —— 更关键的是，协议会**强制**你补齐：漏掉 `tool_result` 或不匹配 `tool_use_id` 都会直接 400。也就是说这个信号不只是「推荐」，它是被协议保证的。',
          sourceIds: ['claude-messages-api'],
        },
        {
          id: 'what-stays-in-code',
          basis: 'inferred',
          question: '循环里有哪几件事必须由代码决定，不能交给模型？',
          answer:
            '至少四件：**什么时候停**（轮次与预算上限）、**工具调用要不要真的执行**（权限与确认）、**失败之后怎么办**（重试、降级、终止）、以及**状态存在哪里**（内存还是持久化）。\n\n这条界线可以概括成一句话：**模型决定「下一步做什么」，代码决定「允不允许、做几次、失败怎么办」。** 把后者交给模型，等于放弃了系统的确定性边界 —— 而这一章后面几节讲的都是如何把这条边界建起来。',
        },
      ],
      resourceIds: ['claude-messages-api', 'twelve-factor-agents'],
    },
    {
      id: 'agent-loop/tool-registry',
      chapterId: 'agent-loop',
      slug: 'tool-registry',
      title: '工具注册表要承担什么',
      summary: '注册表不只是一张 name 到函数的映射 —— 它是权限、校验与错误的收口处。',
      estimatedMinutes: 20,
      difficulty: 'intermediate',
      hasBody: false,
      status: 'outlined',
      keywords: ['tool-registry', 'validation'],
      checkpoints: [
        {
          id: 'registry-responsibilities',
          basis: 'inferred',
          question: '一个工具注册表除了「按名字找到函数」，还该负责什么？',
          answer:
            '至少四项，而且它们都必须在**同一个地方**实现，否则会散落到各个调用点：\n\n1. **schema 自检** —— 第 4 章实测过 `required` 引用不存在的字段时 API 不报错，只能自己拦。\n2. **参数校验** —— 同一份 schema 在运行时再校验一次，因为 `maximum` / `pattern` 这类关键字并不会被强制。\n3. **权限与确认** —— 哪些工具有副作用、哪些需要人工确认，应该在注册时就标注，而不是在执行时临时判断。\n4. **错误语义** —— 把异常翻译成模型能理解的结构化错误（哪些参数有问题、能否重试）。第 4 章实测过：不标 `is_error` 或不说原因，模型的行为会完全不同。',
        },
        {
          id: 'why-single-choke-point',
          basis: 'inferred',
          question: '为什么这些职责必须收口在一个地方？',
          answer:
            '因为**它们是策略，而策略散落就会不一致**。今天在 A 工具的执行路径上加了「写操作需要确认」，明天在 B 工具上忘了加 —— 这种漏洞不会报错，只会静默地留下一个可被绕过的入口。\n\n收口还有一个直接收益：**可观测性**。所有工具调用都经过同一个入口，你才能在那里统一记录耗时、参数、成败与 token 消耗。否则想做成本归因时，你得去改十几个调用点。',
        },
      ],
      resourceIds: ['claude-messages-api', 'twelve-factor-agents'],
    },
    {
      id: 'agent-loop/budgets-and-guards',
      chapterId: 'agent-loop',
      slug: 'budgets-and-guards',
      title: '预算、上限与循环检测',
      summary: '一个没有上限的循环不会失败，它只会一直花钱。',
      estimatedMinutes: 22,
      difficulty: 'advanced',
      hasBody: false,
      status: 'outlined',
      keywords: ['budget', 'loop-detection'],
      checkpoints: [
        {
          id: 'what-needs-a-cap',
          basis: 'inferred',
          question: '一个 agent 循环至少需要设哪几道上限？',
          answer:
            '四道，缺一道都会出现「停不下来」的形态：\n\n1. **轮次上限** —— 最粗的一道，防的是无限循环。\n2. **token 预算** —— 比轮次更贴近真实成本，因为每一轮的输入都在增长（第 1 章的 O(N²) 算式）。\n3. **墙钟超时** —— 防的是单次调用卡住，轮次上限管不了它。\n4. **重复调用检测** —— 相同工具 + 相同参数连续出现就中断。第 4 章实测过模型原地重试的模式，轮次上限能兜住它，但你会在浪费十几轮之后才发现。\n\n这四道要一起设，因为它们的失效方式不重叠。',
        },
        {
          id: 'budget-exhausted-behavior',
          basis: 'inferred',
          question: '预算用完了，正确的行为是什么？',
          answer:
            '**不是抛异常，而是带着已有信息优雅收口。** 一个跑到一半的 agent 通常已经完成了部分工作，直接失败会把那部分也丢掉。\n\n更稳的做法是给它最后一次调用（不挂工具），要求它基于当前掌握的信息输出「已完成什么、还差什么、为什么停下」。这样调用方拿到的是一个可读的状态，而不是一个堆栈。\n\n这条和结构化输出那一章的重试策略是同一种设计：**异常路径要在设计阶段就想好，因为它在生产里一定会被走到。**',
        },
      ],
      resourceIds: ['twelve-factor-agents', 'ai-engineering-huyen'],
    },
    {
      id: 'agent-loop/state-and-resume',
      chapterId: 'agent-loop',
      slug: 'state-and-resume',
      title: '状态、持久化与断点恢复',
      summary: '长任务一定会中途断掉。区别只在于你能不能从断点接着跑。',
      estimatedMinutes: 24,
      difficulty: 'expert',
      hasBody: false,
      status: 'outlined',
      keywords: ['durable-execution', 'checkpoint', 'idempotency'],
      checkpoints: [
        {
          id: 'why-durable',
          basis: 'inferred',
          question: '为什么跑长任务的 agent 必须把状态放到内存之外？',
          answer:
            '因为进程会重启、连接会断、部署会发生 —— 这些都不是异常，是常态。状态只在内存里，就意味着**任何一次重启都要从头再来**，而重来的代价随任务长度线性上升（每一轮的输入都更长）。\n\n对照你自己的后端经验：这正是「工作流引擎」存在的理由。区别只有一个 —— 这里的每一步是概率性的，所以恢复时还要处理「上一步到底成功了没有」这个不确定性问题。',
        },
        {
          id: 'resume-idempotency',
          basis: 'inferred',
          question: '从中断处恢复时，最大的风险是什么？',
          answer:
            '**重复执行有副作用的步骤**。恢复点记录的是「执行到第 N 步」，但第 N 步可能已经产生了副作用而结果没被记录下来 —— 重放一遍就会重复下单、重复发消息。\n\n第 4 章实测过一个反直觉的结果：模型在「状态未知」时反而很谨慎，主动选择不重试；真正会造成重复的是**你自己的恢复逻辑**。所以恢复机制必须配幂等键：每个有副作用的步骤带一个唯一标识，服务端按标识去重，重复请求返回首次结果而不是再执行一遍。\n\n这也是「持久化」与「可恢复」的差别：把状态存下来只让你知道该从哪继续，幂等才让你**敢**继续。',
        },
      ],
      resourceIds: ['twelve-factor-agents', 'ai-engineering-huyen'],
    },
    {
      id: 'agent-loop/what-frameworks-do',
      chapterId: 'agent-loop',
      slug: 'what-frameworks-do',
      title: '你写的这些，框架替你做了什么',
      summary: '手写一遍之后，选框架的标准才变得可判断。',
      estimatedMinutes: 20,
      difficulty: 'intermediate',
      hasBody: false,
      status: 'outlined',
      keywords: ['framework', 'abstraction'],
      checkpoints: [
        {
          id: 'five-parts-mapping',
          basis: 'inferred',
          question: '把本节的五个零件对着一个框架看，你应该重点确认什么？',
          answer:
            '逐项确认框架提供了哪几个、以及**它把哪个藏起来了**：\n\n- 终止信号：它是不是替你判断循环结束？判断依据是协议字段还是文本？\n- 工具调度：schema 校验与权限确认在哪一层？\n- 预算：有没有 token / 轮次上限？默认值是多少？\n- 循环检测：有没有？没有的话你接得进去吗？\n- 持久化：状态存在哪、能不能换存储、恢复语义是什么？\n\n最后一项最容易被忽略，也最贵。一个把状态放在进程内存里的框架，做 demo 时毫无问题，上生产时你才发现要换掉整个执行层。',
        },
        {
          id: 'abstraction-cost',
          basis: 'inferred',
          question: '框架的抽象在什么情况下会从帮助变成负担？',
          answer:
            '当你需要**下探到被封装的那一层**时。典型触发点有三个：想自定义重试与预算策略（框架的默认策略不合适）、想换掉存储（状态存在了你不想要的地方）、以及想看清一次失败到底发生在哪一轮（日志被抽象吞掉了）。\n\n判断标准很实际：**挑一个你预期会出问题的环节，看看框架允许你不改源码就改掉它。** 允许，抽象就是安全的；不允许，你迟早要 fork 或者绕开它。第 11 章会把这条展开成一份选型矩阵。',
        },
      ],
      resourceIds: ['claude-agent-sdk', 'openai-agents-sdk-python', 'twelve-factor-agents'],
    },
  ],
  resourceIds: ['twelve-factor-agents', 'claude-agent-sdk', 'openai-agents-sdk-python', 'claude-messages-api', 'ai-engineering-huyen'],
  backendMapping: {
    analogy: 'agent 循环 ≈ 一个带外部副作用的工作流引擎：状态机 + 重试 + 幂等 + 看门狗',
    transferable: [
      '状态机与工作流编排：这一步做什么、失败回哪去',
      '幂等键、重试退避、超时与熔断 —— 一样都用得上',
      '检查点与恢复：和你写过的任务队列是同一类问题',
    ],
    pitfalls: [
      '用输出文本判断循环是否结束，而不是用 stop_reason 这类协议字段',
      '不设预算上限：跑飞的循环不会报错，只会一直计费',
      '不做重复调用检测，让模型原地打转十几轮才发现',
      '把循环状态只放在内存里，进程重启就从头再来',
      '恢复时直接重放，导致有副作用的步骤被执行两次',
    ],
    cost: 'medium',
  },
  status: 'outlined',
  updatedAt: '2026-10-08',
  verifiedAt: '2026-10-08',
} satisfies Chapter;
