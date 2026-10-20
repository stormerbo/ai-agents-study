import type { Chapter } from '@/content/curriculum/schema';

export const chapter = {
  id: 'cost-and-latency',
  stageId: 'stage-4-production',
  order: 18,
  title: '成本与延迟',
  subtitle: '两笔账都要能算',
  summary:
    '前七章反复出现的那些数字，在这一章汇总成可操作的账：成本由哪四块构成、延迟被什么主导、缓存能省哪一部分、以及预算闸门该设在哪儿。目标不是省钱，而是让你能回答「这个功能值不值这个价」。',
  outcomes: [
    '能拆解一个 agent 任务的成本构成，并指出最贵的三次调用',
    '能判断一个功能的延迟瓶颈在串行轮次、首字节还是工具本身',
    '能设计预算闸门，让成本超限时行为可预期而不是直接失败',
  ],
  depth: 'deep',
  difficulty: 'advanced',
  estimatedMinutes: 95,
  tags: ['cost', 'latency', 'caching'],
  prerequisiteIds: ['agent-loop', 'llm-api-basics'],
  lessons: [
    {
      id: 'cost-and-latency/cost-model',
      chapterId: 'cost-and-latency',
      slug: 'cost-model',
      title: '成本的四块来源',
      summary: '输入、输出、工具定义、以及被忽略的那一块：重发。',
      estimatedMinutes: 20,
      difficulty: 'intermediate',
      hasBody: true,
      status: 'drafting',
      keywords: ['cost', 'tokens'],
      checkpoints: [
        {
          id: 'four-cost-parts',
          basis: 'inferred',
          question: '一个 agent 任务的成本由哪几块构成？',
          answer:
            '四块。**输入**（每轮重发的上下文）、**输出**（含模型的思考过程）、**工具定义**（每次请求都随 body 带上，第 4 章实测约 60 token 每工具）、以及**重发** —— 它不是独立的一项，而是前三项在每一轮被重复计入的放大系数。第 1 章那条算式就是这块的体现：简化模型中，多轮累计输入按每轮输入量求和，呈 O(N²) 二次增长；实际增长取决于输入构成与调用轨迹。所以观察成本时，**不要看单次调用，要看整任务的累计**。一个只有 5 轮的 agent，其累计输入可能是单轮的五倍以上。',
        },
        {
          id: 'cost-attribution-first',
          basis: 'inferred',
          question: '优化成本之前，第一步该做什么？',
          answer:
            '**归因**，而不是优化。先回答「这个任务里最贵的三次调用分别是什么」，否则你优化的是自己想象中的瓶颈。常见的错配是：团队一上来就压缩 system prompt，而真正的开销是某个工具每次返回几千 token 的原始数据（它进入历史后每轮都重发）。归因需要前一章讲的追踪 —— 每次调用记下轮次、环节与 token 数。有了它，优化方向通常会自己浮现，而且往往是**结构性的**（把大块数据移到子智能体、改用按需取、缩短历史），而不是「把提示词写短一点」这种边际调整。',
        },
      ],
      resourceIds: ['claude-pricing', 'ai-engineering-huyen'],
    },
    {
      id: 'cost-and-latency/latency-sources',
      chapterId: 'cost-and-latency',
      slug: 'latency-sources',
      title: '延迟被什么主导',
      summary: '在 agent 里，延迟通常不是「模型慢」，而是「轮次多」。',
      estimatedMinutes: 20,
      difficulty: 'intermediate',
      hasBody: true,
      status: 'drafting',
      keywords: ['latency', 'round-trips'],
      checkpoints: [
        {
          id: 'latency-parts',
          basis: 'inferred',
          question: '一个 agent 任务的延迟由哪几部分组成？',
          answer:
            '三部分，且它们可优化的方式完全不同。**首字节延迟**：与输入长度相关 —— 上下文越长，模型开始输出越慢。**生成时间**：与输出长度相关，包括思考过程；第 2 章实测过，思考会让输出 token 数显著上升。**工具耗时**：每一次外部调用都要等，而且它是**串行叠加**的 —— 一轮里 5 次调用如果串行执行，延迟就是 5 倍。所以最有效的延迟优化往往不是「换更快的模型」，而是**减少轮次**：把可以并行展开的调用合并到一轮（第 4 章讲过一轮可以带多个 tool_use），或者把「先规划再执行」的往返压成一次。',
        },
        {
          id: 'perceived-latency',
          basis: 'inferred',
          question: '为什么「实际延迟」和用户感受到的延迟常常不是一回事？',
          answer:
            '因为用户感知的是**反馈间隔**，而不是总时长。一个总耗时 30 秒但每 2 秒就有可见进展的任务，体验好过一个总耗时 8 秒却全程转圈的任务。这对 agent 尤其重要，因为 agent 的耗时天然长且不确定 —— 它要跑很多轮。所以工程上该做的是**让中间状态可见**：流式输出文本、显示当前在第几步、把工具调用以「正在查询 X」的形式暴露出来。第 1 章讲过流式事件的完整序列，那一章解决的是协议层；这里解决的是产品层 —— 同一份流式数据，怎么组织成用户能理解的进展。',
        },
      ],
      resourceIds: ['claude-streaming', 'ai-engineering-huyen'],
    },
    {
      id: 'cost-and-latency/caching',
      chapterId: 'cost-and-latency',
      slug: 'caching',
      title: '缓存与复用',
      summary: '前缀缓存可复用计算并可能降低计价，但缓存读取仍计入 usage，单价依厂商和模型而异。',
      estimatedMinutes: 20,
      difficulty: 'advanced',
      hasBody: true,
      status: 'drafting',
      keywords: ['caching', 'prompt-caching'],
      checkpoints: [
        {
          id: 'what-can-be-cached',
          basis: 'documented',
          question: 'prompt caching 能省哪一部分，前提是什么？',
          answer:
            'prompt/context caching 的复用范围、缓存键、显式断点、自动缓存和计价都由具体 provider、模型与 endpoint 定义。请求通常仍包含相关 token，usage 与费用分类按接口规则报告。第 1 章记录的 `deepseek-flash` Anthropic 兼容 endpoint 在 2026-09-24 的一组历史观测中，命中时未缓存输入从 2688 降到 256，改单词的请求未报告 cache read；这不能证明其他 endpoint 使用相同缓存键或「改一个字会使后面全部失效」。Anthropic API 文档描述的 tools → system → messages 顺序、断点与匹配规则只适用于其文档所述契约。保持目标接口中参与缓存匹配的输入稳定可能有帮助，但须按该接口文档和 usage 验证。',
          sourceIds: ['claude-prompt-caching'],
        },
        {
          id: 'what-not-to-cache',
          basis: 'inferred',
          question: '什么不该指望缓存？',
          answer:
            '两类。**后半段的内容**：缓存是前缀式的，越靠后的内容越难命中 —— 对话历史每轮都在增长，指望它被缓存基本无效。**工具返回值**：它每次都可能不同，而且它一进入历史就变成「后半段」的一部分。所以对工具返回的大块数据，正确的思路不是「缓存它」，而是**根本不把它留在主上下文里** —— 用子智能体隔离（第 3 章）或按需取。这也解释了为什么缓存和上下文工程是两件事：**缓存优化的是「重复发送同一段」，上下文工程优化的是「要不要发这一段」。** 后者往往收益更大。',
        },
      ],
      resourceIds: ['claude-prompt-caching', 'anthropic-context-engineering'],
    },
    {
      id: 'cost-and-latency/routing',
      chapterId: 'cost-and-latency',
      slug: 'routing',
      title: '分级与路由',
      summary: '不是每个步骤都值得用最强的模型 —— 但也不是每个都值得省钱。',
      estimatedMinutes: 18,
      difficulty: 'intermediate',
      hasBody: true,
      status: 'drafting',
      keywords: ['routing', 'model-selection'],
      checkpoints: [
        {
          id: 'how-to-route',
          basis: 'inferred',
          question: '在一个 agent 里，怎么决定每一步用哪个模型？',
          answer:
            '按**这一步失败的代价**来分，而不是按「难度」来分。第 1 章那条判断在这里同样成立：一个把商品分类标错的请求，和一个生成对账 SQL 的请求，即使难度相近也不该用同一个模型 —— 因为你买的是可靠性，不是难度。落到实践上通常有三档：**判定与路由类**步骤（选哪个工具、要不要继续）可以用便宜模型；**生成类**（写正文、写代码）用中档；**不可逆动作前的最终决策**（是否提交、金额是否一致）用最强模型加人工确认。一个务实的提醒：**分档之前先量**。如果便宜模型在这一步的准确率和贵的差不多，升级就是浪费；而这件事不做对照实验是看不出来的。',
        },
        {
          id: 'routing-risk',
          basis: 'inferred',
          question: '多模型路由会引入什么新的风险？',
          answer:
            '三个。**能力假设失效**：路由决策往往基于「便宜模型做这件事够了」，而模型更新后这个假设可能不再成立 —— 所以分档要有对照测试，不是一次定终身。**上下文差异**：不同模型对同一提示的响应格式可能不同（第 1 章提过温度参数在新旧模型上的差异），跨模型复用同一套 prompt 与解析逻辑会偶发失败。**故障面翻倍**：多一个供应商就多一处限流、配额与可用性问题，而 agent 是多轮调用，任何一步失败都会中断整个任务。所以路由的价值要在「节省的成本」与「多出来的复杂度」之间衡量，小规模系统从单模型起步通常更划算。',
        },
      ],
      resourceIds: ['claude-models-overview', 'ai-engineering-huyen'],
    },
    {
      id: 'cost-and-latency/budget-guardrails',
      chapterId: 'cost-and-latency',
      slug: 'budget-guardrails',
      title: '预算闸门与熔断',
      summary: '超限时的行为要在设计阶段定好 —— 因为它在生产里一定会被走到。',
      estimatedMinutes: 18,
      difficulty: 'advanced',
      hasBody: true,
      status: 'drafting',
      keywords: ['budget', 'circuit-breaker'],
      checkpoints: [
        {
          id: 'budget-layers',
          basis: 'inferred',
          question: '预算闸门应该分几层？',
          answer:
            '三层，而且它们防的不是同一件事。**单次任务**：这个任务最多花多少 —— 防的是逻辑错误导致的无限循环（第 9 章那四道上限里的 token 与轮次预算）。**单用户或单会话**：一段时间内的总量上限 —— 防的是单个用户刷量、或者某个输入模式系统性地触发昂贵路径。**全局**：整个系统每天/每月的天花板 —— 防的是上游异常（比如某次发布引入了一个无限重试）把账单打穿。第三层最容易被忽略，但它是唯一能兜住「你没预料到的那种错误」的一层。三层都要有，因为前两层的阈值都建立在「你已经知道有哪些路径」这个前提上。',
        },
        {
          id: 'exhausted-behavior',
          basis: 'inferred',
          question: '预算用尽时，正确的行为是什么？',
          answer:
            '**带着已完成的进度优雅收口，而不是抛异常。** 第 9 章讲过这条，这里再强调它为什么是成本问题而非体验问题：一个跑到一半的任务已经花了钱，直接失败会让这笔投入归零；而一次「基于当前信息给出部分结果 + 说明还差什么」的收尾调用很便宜。更重要的是一致性 —— 超限行为必须是**可预期的**：调用方知道会拿到什么、监控知道该看哪个指标。最常见的坏做法是让请求一直挂着重试，那既没省钱也没给出结果，只是把账单推到了下一分钟。',
        },
      ],
      resourceIds: ['twelve-factor-agents', 'claude-agent-sdk'],
    },
  ],
  resourceIds: [
    'claude-pricing',
    'claude-prompt-caching',
    'claude-models-overview',
    'claude-streaming',
    'ai-engineering-huyen',
    'twelve-factor-agents',
  ],
  backendMapping: {
    analogy:
      'agent 的成本与延迟 ≈ 一个调用链很长的服务：贵在重复传输，慢在串行往返，优化点在减少轮次而不是微调单次',
    transferable: [
      '调用链追踪与成本归因：和后端做链路分析与分摊是同一件事',
      '缓存策略：前缀缓存与「哪些能缓存」的判断',
      '预算与熔断：分层的限额设计、优雅降级而不是硬失败',
    ],
    pitfalls: [
      '只看单次调用成本，忽略每轮重发的放大效应',
      '不归因就开始优化，压缩了不是瓶颈的那一部分',
      '奢望缓存对话历史：前缀缓存对持续增长的后半段无效',
      '按「难度」而不是「失败代价」来分模型档位',
      '预算超限时抛异常，把已经花掉的钱和进度一起丢掉',
    ],
    cost: 'medium',
  },
  status: 'published',
  updatedAt: '2026-10-08',
  verifiedAt: '2026-10-08',
} satisfies Chapter;
