import type { Chapter } from '@/content/curriculum/schema';

export const chapter = {
  id: 'agent-deployment',
  stageId: 'stage-4-production',
  order: 20,
  title: '部署与交付',
  subtitle: '上线，以及上线之后',
  summary:
    '这是本阶段的收口章：把评估、沙箱、安全、成本、人机协作这些线拧在一起，回答「怎么把它交付出去」。以及一件更长期的事 —— 上线不是终点，而是一个「轨迹到改进」的循环的起点。',
  outcomes: [
    '能为一个 agent 功能选对部署形态，并说清它在长任务与取消语义上的后果',
    '能对 prompt、工具、模型三者做版本管理，并在出问题时快速回滚',
    '能建立起「轨迹 → 评测 → 改进 → 再评测」的循环，而不是靠感觉迭代',
  ],
  depth: 'deep',
  difficulty: 'advanced',
  estimatedMinutes: 100,
  tags: ['deployment', 'ops', 'versioning'],
  prerequisiteIds: ['agent-loop', 'sandboxing', 'evaluation'],
  lessons: [
    {
      id: 'agent-deployment/deployment-shape',
      chapterId: 'agent-deployment',
      slug: 'deployment-shape',
      title: '部署形态',
      summary: '同步、异步、还是队列 —— 这个选择会决定后面所有运维问题的形状。',
      estimatedMinutes: 20,
      difficulty: 'intermediate',
      hasBody: false,
      status: 'outlined',
      keywords: ['deployment', 'async'],
      checkpoints: [
        {
          id: 'sync-vs-async',
          basis: 'inferred',
          question: 'agent 该部署成同步接口还是异步任务？',
          answer:
            '按**执行时长与是否需要人介入**来分。**同步**适合秒级以内、不需要审批、结果直接返回的任务（分类、抽取、单轮问答）—— 它的好处是简单，调用方拿到就是结果。**异步任务**适合分钟级以上、可能暂停等审批、或者要跑很多轮的任务 —— 这时同步请求会超时，长连接也不可靠，必须改成「提交任务 → 轮询或回调」的形态。判断的分界线不是「技术偏好」，而是：**这个任务的最坏耗时会不会超过你基础设施允许的单请求时长。** 会，就必须异步，而且要在设计阶段就定下来 —— 把同步流程改成异步，几乎等于重写交互层与状态管理。',
        },
        {
          id: 'cancellation-semantics',
          basis: 'inferred',
          question: '为什么「取消」的语义必须在部署阶段就想清楚？',
          answer:
            '因为取消在 agent 里**不是一个瞬时动作**，至少涉及三种情况：任务还没开始（直接从队列移除）、正在调用模型（要中断请求，已产生的 token 仍会计费）、以及正在执行有副作用的工具（**不能撤销**，只能等它结束再决定要不要补偿）。如果接口只提供一个「取消」而没有区分这三者，调用方会以为已经停下来了，而实际上某个转账可能正在进行。所以取消语义要显式设计：**能取消什么、取消后已完成的部分怎么处理、以及不可取消的步骤如何告知调用方。** 这和第 9 章那几道上限是同一种思路 —— 边界要在设计阶段写清楚，因为它一定会被用到。',
        },
      ],
      resourceIds: ['twelve-factor-agents', 'claude-agent-sdk'],
    },
    {
      id: 'agent-deployment/versioning',
      chapterId: 'agent-deployment',
      slug: 'versioning',
      title: '版本与灰度',
      summary: 'agent 的行为由三样东西共同决定，它们都得能单独回滚。',
      estimatedMinutes: 20,
      difficulty: 'advanced',
      hasBody: false,
      status: 'outlined',
      keywords: ['versioning', 'rollback'],
      checkpoints: [
        {
          id: 'what-to-version',
          basis: 'inferred',
          question: 'agent 系统里，哪些东西需要版本化？',
          answer:
            '至少四样，而且它们**各自独立变化**：**prompt 与 system 指令**（改一句话就可能改变行为）、**工具定义**（描述、schema、以及它的实现）、**模型与模型版本**（上游会静默更新）、以及**编排逻辑**（循环、预算、重试策略）。四样里最容易失控的是第二和第三 —— 工具定义常常散在代码里没有版本概念，模型版本则可能只写了一个会漂移的别名。实践上的最低要求是：**每次任务轨迹都记录这四样的标识**。没有它，一次「变差了」的排查就只能靠猜时间点。第 1 章的模型迁移指南里列的那些破坏性变更，正是因为模型侧也会变。',
        },
        {
          id: 'graderollout',
          basis: 'inferred',
          question: 'agent 的灰度发布和普通服务有什么不同？',
          answer:
            '难点是**评估指标不如传统服务即时**。延迟、错误率这些可以按流量切开对比，但「agent 效果好不好」往往要等更久才能看出来（甚至需要人工判断）。所以灰度的做法要调整为：**先离线对照，再小流量上线**。离线对照就是评估那一章的做法 —— 同一份评测集跑新旧两版，看逐条差异；确认没有退化再放量。放量后要盯的不只是错误率，还有几个 agent 特有的信号：**平均轮次、工具调用分布、以及「需要人工介入」的比例**。这几个指标的移动往往早于用户投诉出现。',
        },
      ],
      resourceIds: ['claude-model-migration', 'ai-engineering-huyen'],
    },
    {
      id: 'agent-deployment/incident-response',
      chapterId: 'agent-deployment',
      slug: 'incident-response',
      title: '故障与降级',
      summary: '上游会挂、模型会变、账单会超 —— 每一类都要有预设的动作。',
      estimatedMinutes: 20,
      difficulty: 'advanced',
      hasBody: false,
      status: 'outlined',
      keywords: ['incident', 'degradation'],
      checkpoints: [
        {
          id: 'failure-classes',
          basis: 'inferred',
          question: 'agent 服务有哪几类典型故障？各自该降级成什么？',
          answer:
            '四类。**上游模型不可用或限流** —— 降级成重试加退避，超过阈值后回退到更小/更便宜的模型，或者直接返回「稍后再试」，而不是无限重试把队列堆满。**工具故障** —— 降级成把失败如实回填给模型（第 4 章实测过：标 is_error 并说明原因时，模型会正确处理），让它绕过这一步继续。**成本或轮次超限** —— 按预算那一章的收口策略，返回部分结果而不是抛异常。**效果退化**（模型更新或数据漂移）—— 这一类最难，因为没有硬错误信号；唯一可靠的发现手段是持续跑评测，以及监控前面提到的轮次与介入率。',
        },
        {
          id: 'rollback-readiness',
          basis: 'inferred',
          question: '「能回滚」具体要准备什么？',
          answer:
            '三件事：**版本可切换**（前面那四样都有标识，且能独立回退 —— 只回退 prompt 而保留新工具，往往比整体回退更有用）；**旧版本仍然可用**（模型版本尤其要注意，很多平台会下线下线旧模型，所以「回滚到上一个模型」这条路径要在平时就验证过，而不是在事故中第一次尝试）；以及**回滚不需要改代码**（如果回滚要走一次发版流程，那它在事故中的作用就很有限）。判断标准可以很直接：**凌晨三点，值班的人能不能在不改代码、不问原作者的条件下把一个变量切回去。** 做不到，就不算能回滚。',
        },
      ],
      resourceIds: ['twelve-factor-agents', 'claude-agent-sdk'],
    },
    {
      id: 'agent-deployment/ops-loop',
      chapterId: 'agent-deployment',
      slug: 'ops-loop',
      title: '上线之后的循环',
      summary: '路径不是一条直线：部署只是这条循环的起点。',
      estimatedMinutes: 22,
      difficulty: 'advanced',
      hasBody: false,
      status: 'outlined',
      keywords: ['iteration', 'feedback-loop'],
      checkpoints: [
        {
          id: 'the-loop',
          basis: 'inferred',
          question: '「轨迹 → 评测 → 改进」这个循环具体怎么转？',
          answer:
            '四步。**一，从轨迹里找失败**：按失败类型聚类（工具选错、参数非法、检索没召回、被注入带偏……），而不是逐个看 —— 逐条看会让你只修最显眼的那个。**二，把代表案例固化进评测集**，带上正确答案。**三，改一处并跑离线对照**：一次只改一个变量（prompt、工具描述、检索策略、模型档位），否则你无法归因。**四，确认没退化后放量，继续观察**。这个循环的价值在于它把「感觉效果不好」变成了可执行的步骤；而它的每一次迭代都会让评测集变大变准，形成一个正向积累 —— 这也正是为什么评测那章说「真实失败案例最值钱」。',
        },
        {
          id: 'what-not-to-do',
          basis: 'inferred',
          question: '在这个循环里，最常见的两个错误是什么？',
          answer:
            '**一，同时改多个变量。** 一次性调 prompt、换模型、又改工具描述，然后「感觉好多了」—— 这是最贵的错误，因为它让你无法知道哪个改动起了作用，下次也不敢回退其中任何一个。**二，只改不测。** 直接从轨迹里挑几条看起来失败的，改完就上线；没有对照，你无法知道改动是否真的有效，也不知道它有没有弄坏别的输入。这两个错误的共同点是**它们跳过了「可验证性」**：前者放弃了归因，后者放弃了验证。而要把它们做好并不需要额外工具，只需要坚持一次一个变量、每次都有对照 —— 这正是第 0 章那条贯穿全站的原则在运维阶段的形态。',
        },
      ],
      resourceIds: ['ai-engineering-huyen', 'twelve-factor-agents'],
    },
  ],
  resourceIds: ['twelve-factor-agents', 'claude-agent-sdk', 'claude-model-migration', 'ai-engineering-huyen', 'openai-agents-sdk-python'],
  backendMapping: {
    analogy: '交付一个 agent ≈ 交付一个调用链很长、依赖外部不确定服务、且有副作用的新服务：灰度、回滚、降级、审计一样都不能省',
    transferable: [
      '同步/异步的选型经验，以及取消语义的设计',
      '版本化与灰度：把 prompt 与工具也当制品来管',
      '事故响应的分级降级：从你在微服务里做的那些降级策略直接迁移',
    ],
    pitfalls: [
      '把 agent 部署成同步接口，直到第一次超时才面对长任务问题',
      '只版本化代码，不版本化 prompt、工具与模型版本',
      '取消接口不区分「未开始 / 生成中 / 副作用进行中」，给出错误的安全感',
      '把「回滚」设计成需要发版的操作，事故中根本用不上',
      '迭代时一次改多个变量，丧失归因能力',
      '改完不跑对照就上线，无法判断是变好还是变坏',
    ],
    cost: 'medium',
  },
  status: 'outlined',
  updatedAt: '2026-10-08',
  verifiedAt: '2026-10-08',
} satisfies Chapter;
