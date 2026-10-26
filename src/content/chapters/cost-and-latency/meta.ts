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
      title: '成本的四种观察角度',
      summary: '按调用轨迹与 provider usage 归因输入、输出和重复请求，工具 schema 不能重复计费。',
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
            '四种观察角度并非四个互斥账单项：**输入和输出**按 provider usage 与费率核算，**工具定义**是输入的归因子集，**重复**是多次请求放大输入的机制，不能把 schema 在 usage 中已计量后再次相加。只有 stateless 每轮重发完整且逐轮增长的上下文时，简化累计输入才呈二次增长；其他会话状态、缓存和延迟加载应按实际 trace 判断。历史 token 比值不证明质量等价或账单成本；应采集 provider、模型、每次请求 usage、结束状态和重试关系，并用当前费率汇总任务成本。',
        },
        {
          id: 'cost-attribution-first',
          basis: 'inferred',
          question: '优化成本之前，第一步该做什么？',
          answer:
            '**归因**，而不是优化。先回答「这个任务里最贵的三次调用分别是什么」，否则你优化的是自己想象中的瓶颈。常见错配是只压 system prompt，却忽略工具返回的巨大数据可能被后续请求继续携带；是否继续出现取决于状态协议与上下文策略。追踪至少要记录轮次、环节、provider usage、结束状态和重试关系。有了它，优化方向通常会自己浮现，可能是**结构性的**（把大块数据移到隔离任务、按需取、缩短历史），而不是只把提示词写短。',
        },
        {
          id: 'provider-cost-accounting',
          basis: 'documented',
          question: '如何把 usage 变成任务成本？',
          answer:
            '先依据 provider/model/endpoint 文档解释 response usage，再按当前费率分别折算普通输入、缓存读取/写入、输出及其他计费项，并对一个任务的所有请求求和。Anthropic Messages API 的三个 input 类别可相加得到 total input；DeepSeek 与 OpenAI 有各自的 total/detail/cache 字段关系，必须确认哪些是总量、哪些是明细，不能跨 provider 混用或重复求和。价格会随模型和产品变化，应检查官方当前价格表；工具 schema 若已经计入 input usage，只作为归因子集，不再额外加到账单。',
          sourceIds: ['claude-pricing', 'claude-prompt-caching', 'deepseek-chat-api', 'deepseek-context-caching', 'deepseek-models-pricing', 'openai-api-pricing', 'openai-prompt-caching'],
        },
      ],
      resourceIds: ['claude-pricing', 'claude-prompt-caching', 'deepseek-chat-api', 'deepseek-context-caching', 'deepseek-models-pricing', 'openai-api-pricing', 'openai-prompt-caching', 'ai-engineering-huyen'],
    },
    {
      id: 'cost-and-latency/latency-sources',
      chapterId: 'cost-and-latency',
      slug: 'latency-sources',
      title: '延迟被什么主导',
      summary: '拆开模型请求、工具与排队时间，沿 agent 任务关键路径定位延迟。',
      estimatedMinutes: 20,
      difficulty: 'intermediate',
      hasBody: true,
      status: 'drafting',
      keywords: ['latency', 'round-trips'],
      checkpoints: [
        {
          id: 'latency-parts',
          basis: 'documented',
          question: 'TTFT、首个可见文本、TPOT 和任务端到端延迟分别表示什么？',
          answer:
            'TTFT 是约定计时起点至首个输出 token/事件的时间，不等于纯 prefill，也不保证该事件是用户可见文本；TPOT 描述首 token 后的输出节奏，不是跨模型与负载通用的常数。首个可见文本时间应以界面呈现为终点；任务端到端延迟从用户提交到结果满足任务契约。模型阶段、网络、provider 排队、工具耗时、重试与客户端处理都可能进入任务时间。',
          sourceIds: ['openai-latency-optimization', 'anthropic-reduce-latency', 'claude-streaming', 'pd-serve-paper'],
        },
        {
          id: 'agent-critical-path',
          basis: 'inferred',
          question: '多步骤 agent 的整体延迟如何估算？',
          answer:
            '根据执行依赖画出 trace：串行阶段求和；语义独立且可并行的分支取最长，并加入启动、汇合、排队与调度开销。共享限流、锁、外部副作用或先后依赖会限制并行。把工具失败重试和人工审批纳入关键路径；用任务级延迟分布、成功率、重试次数和质量一起判断优化效果。',
        },
        {
          id: 'perceived-latency',
          basis: 'inferred',
          question: '为什么「实际延迟」和用户感受到的延迟常常不是一回事？',
          answer:
            '感知延迟应在用户动作到有意义反馈实际呈现之间测量；它与任务完成时间是两个指标。流式文本或可信的阶段状态可提前提供反馈，但不会自动缩短任务端到端时间。只展示用户有权看到的状态，不能泄露内部思考，也不能把运行中任务误报为已完成。',
        },
      ],
      resourceIds: ['openai-latency-optimization', 'anthropic-reduce-latency', 'pd-serve-paper', 'claude-streaming', 'ai-engineering-huyen'],
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
            'prompt/context caching 的复用范围、缓存键、显式断点、自动缓存和计价都由具体 provider、模型与 endpoint 定义。请求通常仍包含相关 token，usage 与费用分类按接口规则报告。第 1 章记录的 `deepseek-flash` Anthropic 兼容 endpoint 在 2026-09-24 的一组历史观测中，命中时未缓存输入从 2688 降到 256，改单词的请求未报告 cache read；原始逐次响应未归档，不能复算或证明因果，也不能证明其他 endpoint 使用相同缓存键。Anthropic API 文档描述的工具/系统/消息顺序、断点与匹配规则只适用于其文档所述契约。保持目标接口中参与缓存匹配的输入稳定可能有帮助，但须按该接口文档和 usage 验证。',
          sourceIds: ['claude-prompt-caching', 'deepseek-context-caching', 'deepseek-anthropic-api', 'openai-prompt-caching'],
        },
        {
          id: 'what-not-to-cache',
          basis: 'inferred',
          question: '什么不该指望缓存？',
          answer:
            '两类。**后半段的内容**：对采用前缀匹配的 prompt cache 契约，后缀变化可能使其后的前缀无法复用；实际命中范围要按供应商、模型和端点规则核实，不能把这一行为推广到所有缓存。**工具返回值**：它每次都可能不同，而且它一进入历史就可能影响可复用前缀。所以对工具返回的大块数据，仍应评估是否留在主上下文里 —— 可用子智能体隔离（第 3 章）或按需取。这也解释了缓存和上下文工程是两件事：**缓存优化的是「重复发送同一段」，上下文工程优化的是「要不要发这一段」。** 两者收益都要按目标 workload 测量。',
        },
        {
          id: 'provider-usage-contracts',
          basis: 'documented',
          question: '如何解释缓存相关 usage？',
          answer: '缓存 usage 和价格字段按 API/provider 解释，不能套用一个跨厂商公式。Anthropic Messages API 的输入总量由 input_tokens、cache_read_input_tokens 与 cache_creation_input_tokens 组成；DeepSeek Chat API 使用 prompt_cache_hit_tokens 与 prompt_cache_miss_tokens 等字段，其 Anthropic 兼容接口当前文档把 cache_control 标为 ignored；OpenAI 在输入 usage details 中报告 cached tokens。逐字段含义与费用仍以对应接口文档为准。',
          sourceIds: ['claude-prompt-caching', 'deepseek-context-caching', 'deepseek-anthropic-api', 'openai-prompt-caching'],
        },
      ],
      resourceIds: ['claude-prompt-caching', 'deepseek-context-caching', 'deepseek-anthropic-api', 'openai-prompt-caching', 'anthropic-context-engineering'],
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
            '先定义任务正确性、风险/SLO 与候选模型可用能力，再用代表性评估集比较候选的质量、每成功任务成本与 P95。只有满足质量、安全和延迟门槛的路线才参与成本比较；路由规则应按本任务集的错误代价校准，不以输入长度或“规划/执行”标签直接等同能力。高影响动作仍须由服务端授权、验证与必要的人工确认，不能靠升级到强模型替代。',
        },
        {
          id: 'provider-model-selection-guidance',
          basis: 'documented',
          question: '供应商官方文档如何指导模型选择与路由？',
          answer:
            'OpenAI 与 Anthropic 的官方指南都要求根据具体需求和评估结果选择候选；Anthropic 明确提出在同一模型内调整 effort 也可能影响成本与延迟，且按 cost per completed task 与自己的 workload 测量。指南中的模型矩阵或平台 benchmark 是特定时间、模型、任务集和设置的起点，不是跨厂商或本地流量的普遍路由规则。',
          sourceIds: ['openai-model-selection', 'anthropic-choosing-model', 'anthropic-cost-intelligence'],
        },
        {
          id: 'routing-benchmark-boundary',
          basis: 'documented',
          question: '近期统一基准对 LLM 路由有哪些提醒？',
          answer:
            'Findings ACL 2026 的 LLMRouterBench 在 21 个数据集、33 个模型和 10 种路由基线上进行统一评估；作者报告多种路由方法表现接近，部分方法（包括商业路由器）未能稳定优于简单基线。该结果只描述论文的候选池、数据集与指标，不证明路由在其他工作负载上无效；应把固定最佳候选作为基线，验证自有任务集上的增量质量、成本与延迟。',
          sourceIds: ['llmrouterbench-paper'],
        },
        {
          id: 'routing-risk',
          basis: 'inferred',
          question: '多模型路由会引入什么新的风险？',
          answer:
            '能力、响应格式、工具/模态支持与可用性都可能因模型版本或 provider 而不同。更新候选、prompt、schema、路由特征或价格后应重跑分层回归集；运行时记录 model snapshot、策略版本、决策原因、usage、重试和结果。多供应商也会增加限流、配额、隐私审查和故障处理路径，评估时计入这些运维成本。',
        },
      ],
      resourceIds: ['openai-model-selection', 'anthropic-choosing-model', 'anthropic-cost-intelligence', 'openai-agent-cost-quality-cookbook', 'routerbench-paper', 'llmrouterbench-paper', 'claude-models-overview', 'ai-engineering-huyen'],
    },
    {
      id: 'cost-and-latency/budget-guardrails',
      chapterId: 'cost-and-latency',
      slug: 'budget-guardrails',
      title: '预算闸门与熔断',
      summary: '为每个任务定义可计量的资源预算、请求前预留与耗尽后的契约化行为；依赖熔断则单独隔离持续故障。',
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
            '没有适用于所有系统的固定层数。至少分别考虑**单次请求**的输入/输出上限与 deadline、**单次任务/run**的费用/token/调用数/时长，以及**用户/租户/项目/系统时间窗**的配额、并发与费用。每一层都要写明计量单位、重置周期、强制执行位置与超限行为。`max_tokens` 通常只限制本次生成，不能替代任务累计预算；不同 provider 的 usage 字段、缓存计量与价格需要由 adapter 归一化并保留原始值。',
        },
        {
          id: 'exhausted-behavior',
          basis: 'inferred',
          question: '预算用尽时，正确的行为是什么？',
          answer:
            '由任务契约决定，不能一律返回部分结果。允许部分完成的任务可以返回已有进度，但必须标记 `incomplete`、列出缺项并确保权限与数据边界仍成立；要求原子一致、授权确认或完整结构的任务应明确失败/待处理，不能把部分输出伪装成成功。宿主应在请求前预留资源，响应后按 provider usage 对账；超时或 usage 未知时按保守策略保留额度，不能计为零。任何 continuation 都必须同时满足剩余预算、deadline、幂等与副作用约束。',
        },
        {
          id: 'provider-specific-usage',
          basis: 'documented',
          question: '能否用一组通用字段或价格公式累计所有 provider 的任务成本？',
          answer: '不能。usage 字段及缓存输入的归类因 provider、model、endpoint 而异；应保留原始响应口径，在 adapter 中归一化，并按生效费率估算。OpenAI 的 spend limit 与 API 请求错误/组织支出控制有关，不等同于应用里的每任务预算。',
          sourceIds: ['claude-pricing', 'deepseek-chat-api', 'openai-spend-limits'],
        },
        {
          id: 'output-cap-stop-reason',
          basis: 'documented',
          question: 'Anthropic Messages 的 `stop_reason: max_tokens` 表示什么？',
          answer: '表示本次生成达到输出 token 上限；它本身不证明业务任务成功或失败。调用方还要按输出协议和任务契约检查完整性。兼容端点需单独核实字段与语义。',
          sourceIds: ['anthropic-stop-reasons'],
        },
        {
          id: 'circuit-breaker-lifecycle',
          basis: 'documented',
          question: '依赖熔断器打开后如何恢复？',
          answer: '典型模式在 OPEN 状态快速拒绝请求，冷却后只放行有限探测进入 HALF_OPEN；探测成功后关闭，仍失败则重新打开。阈值、窗口与恢复探测属于依赖和工作负载的设计参数，不是固定通用值。',
          sourceIds: ['aws-circuit-breaker', 'azure-circuit-breaker'],
        },
      ],
      resourceIds: ['twelve-factor-agents', 'claude-agent-sdk', 'openai-spend-limits', 'anthropic-stop-reasons', 'claude-pricing', 'deepseek-chat-api', 'aws-circuit-breaker', 'azure-circuit-breaker'],
    },
    {
      id: 'cost-and-latency/concurrency-and-backpressure',
      chapterId: 'cost-and-latency',
      slug: 'concurrency-and-backpressure',
      title: '并发与背压：让拥塞有边界',
      summary: '结合有限队列、并发槽、预算预留、deadline 与分类重试控制 Agent 任务的拥塞和成本。',
      estimatedMinutes: 30,
      difficulty: 'advanced',
      hasBody: true,
      status: 'drafting',
      keywords: ['concurrency', 'backpressure', 'retry-after', 'deadline', 'rate-limit'],
      checkpoints: [
        {
          id: 'retry-after-is-minimum',
          basis: 'documented',
          question: '收到 provider 的 Retry-After 后，客户端可以在提示时间之前重试吗？',
          answer: '不应早于有效提示重试。RFC 9110 允许 Retry-After 是 HTTP-date 或秒数；OpenAI 与 Anthropic 当前文档分别描述其 API 返回的等待值，具体格式、字段是否存在和 SDK 长延迟处理要按 endpoint 与版本核对。',
          sourceIds: ['openai-rate-limits', 'anthropic-rate-limits', 'http-retry-after'],
        },
        {
          id: 'quota-failure-retry',
          basis: 'documented',
          question: '只要收到 HTTP 429，就应该指数退避后继续重试吗？',
          answer: '不应该。部分 429 是临时限速，但额度/账单上限可能需要配置或等待额度恢复；此类错误没有有效重试时机，自动重发只会增加失败请求。必须结合响应错误类别和 provider 文档判断。',
          sourceIds: ['openai-rate-limits', 'anthropic-errors'],
        },
        {
          id: 'bounded-admission',
          basis: 'inferred',
          question: '为什么 admission 时要同时检查队列容量、deadline 和预算预留？',
          answer: '它们保护不同的资源：队列上限约束积压，deadline 避免接纳注定超时的工作，预算预留限制后续模型与工具步骤的资源消耗。只有都通过才启动或排队，否则应明确拒绝或按已定义策略降级。',
          note: '这是示例中的本地 admission policy，不代表所有部署场景的最佳阈值。',
        },
        {
          id: 'capacity-count-types',
          basis: 'documented',
          question: 'Python admission helper 为什么要拒绝布尔值和小数作为并发槽、队列长度或 attempt 次数？',
          answer: '这些字段表示离散计数，应只接受整数；Python 中 bool 是 int 的子类型，普通整数类型检查会让 True 冒充 1。示例用精确类型检查拒绝布尔值与小数，其他语言应按本语言的类型规则实现。',
          sourceIds: ['python-built-in-types'],
        },
      ],
      resourceIds: ['openai-rate-limits', 'anthropic-rate-limits', 'anthropic-errors', 'http-retry-after', 'python-built-in-types'],
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
      '假设持续增长的对话后缀一定能命中前缀缓存；复用范围取决于接口的键、断点与 TTL 规则',
      '按「难度」而不是「失败代价」来分模型档位',
      '预算超限时抛异常，把已经花掉的钱和进度一起丢掉',
    ],
    cost: 'medium',
  },
  status: 'published',
  updatedAt: '2026-10-19',
  verifiedAt: '2026-10-08',
} satisfies Chapter;
