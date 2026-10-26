import type { Chapter } from '@/content/curriculum/schema';

/**
 * 章 1，样板章之一。
 * 选它做样板的原因：它是整条路径上**最容易跑通、最难做好**的一章 ——
 * 调通一次 API 只要十分钟，但"为什么这次调用会失败、贵在哪里、
 * 哪里会截断"这些问题，会一直跟到阶段 4。
 */
export const chapter = {
  id: 'llm-api-basics',
  stageId: 'stage-1-foundation',
  order: 1,
  title: 'LLM 基础与 API 调用',
  subtitle: '把模型当作一种新型依赖来对待',
  summary:
    'token 与上下文窗口、采样参数、Messages API 与流式响应、模型选型与成本、prompt caching。后面每一个 bug，追根溯源大多能在这一章找到出处。',
  outcomes: [
    '能独立完成一次带流式输出的模型调用，并正确处理超时、中断与重试',
    '能解释 temperature / top_p / max_tokens 各自控制什么，以及为什么不该随手调',
    '能在动手写代码前估算一次调用的 token 成本，并判断 prompt caching 是否值得引入',
  ],
  depth: 'deep',
  difficulty: 'beginner',
  estimatedMinutes: 120,
  tags: ['llm', 'api', 'streaming', 'cost'],
  prerequisiteIds: ['what-is-an-agent'],
  lessons: [
    {
      id: 'llm-api-basics/tokens-and-context',
      chapterId: 'llm-api-basics',
      slug: 'tokens-and-context',
      title: 'token 与上下文窗口：真正的稀缺资源',
      summary: 'token 常参与上下文容量和延迟核算；计费还取决于模型、模态、缓存与 provider usage 口径。',
      estimatedMinutes: 15,
      difficulty: 'beginner',
      hasBody: true,
      status: 'drafting',
      keywords: ['token', 'context-window'],
      checkpoints: [
        {
          id: 'token-estimation',
          question: '为什么不能按字符数估算 token？',
          answer:
            'token 是目标模型 tokenizer 的编码单位，字符数与 token 数没有可跨文本、模型或 provider 复用的固定换算系数。Anthropic 的 count_tokens 可按 Messages 请求形状估算 input tokens，但该结果不等于账单，也不能代表其他 provider；生产容量与费用应按目标 API 的请求和 usage 口径核验。',
          basis: 'documented',
          sourceIds: ['claude-token-counting'],
          note: '本节 2026-09-24 DeepSeek 历史样本只是五条非受控字符串记录，已撤回固定开销与跨语言 token 密度结论。Anthropic 计数端点能力和结果边界只适用于其官方 API。',
        },
        {
          id: 'context-not-memory',
          question: '把关键信息放在很长的上下文中部，会发生什么？这对 prompt 的结构有什么指导？',
          answer:
            'Lost in the Middle 论文在其评测任务与模型上观察到长上下文位置利用率不均、部分设置呈 U 形；这不意味着所有模型、任务或窗口长度都呈现同一效果。本节 2026-10-08 DeepSeek 样本及第 0 章复现实验没有观察到位置效应，样本范围不足以推翻论文，也不足以推广到所有长上下文应用。工程上可把关键信息放在易检索的位置、减少无关上下文，但应在自己的模型与任务上测量。',
          basis: 'documented',
          sourceIds: ['lost-in-the-middle'],
          note: '前半段（位置利用率不均）是论文结论；后半段「应该怎么放」是由结论推出的工程建议，属于推论而非论文原文。',
        },
      ],
    },
    {
      id: 'llm-api-basics/sampling-params',
      chapterId: 'llm-api-basics',
      slug: 'sampling-params',
      title: '采样参数：按模型与 SDK 契约迁移',
      summary:
        '区分 Anthropic 模型 API 与 Python SDK 的采样参数支持差异；用可复核的契约测试和任务评测指导迁移，不把 effort、prompting 或兼容端点行为误作通用替代。',
      estimatedMinutes: 18,
      difficulty: 'beginner',
      hasBody: true,
      status: 'drafting',
      keywords: ['temperature', 'top-p', 'top-k', 'effort', 'provider-contract'],
      checkpoints: [
        {
          id: 'sampling-params-contract',
          question: '为什么同一个 temperature 参数会在某个 Claude 请求中报错，而在 DeepSeek Anthropic-compatible API 中仍可能生效？',
          answer:
            '需要区分 API version、SDK 方法签名、model 和 endpoint。Anthropic Python SDK 1.0+ 不再接受 Messages 方法的 temperature/top_p/top_k 关键字；API version 2026-10-21 携带任意这些字段（包括默认值）均返回 400，更早 API version 对 Claude 4.7+ 与 Mythos Preview 拒绝非默认值。DeepSeek Anthropic-compatible 文档则声明 temperature 支持、top_k 忽略、top_p 依模型与模式变化。兼容请求形状不等于行为等价。',
          basis: 'documented',
          sourceIds: ['claude-model-deprecations', 'anthropic-api-version-2026-10-21', 'anthropic-sdk-python-migration', 'deepseek-chat-api', 'deepseek-anthropic-api'],
          resourceIds: ['claude-model-migration'],
          note: '参数支持随模型代际、SDK 主版本、平台和 endpoint 变化。本检查点要求核对当前文档与锁定版本，不表示所有 Anthropic/DeepSeek 模型都采用同一行为。',
        },
        {
          id: 'sampling-api-version-boundary',
          question: '把温度参数放进 SDK 的 extra_body 后，是否就能绕过 Anthropic 对采样参数的限制？',
          answer:
            '不能。extra_body 只绕过 Python SDK 方法签名，不绕过服务端 API version 契约。Anthropic API version 2026-10-21 在 Messages 请求中禁止携带 temperature、top_p、top_k，即使是默认值也返回 400；较早版本仍按模型区分，Claude 4.7+ 与 Mythos Preview 拒绝非默认值。SDK 2.0.0 使用新 API version；需要旧行为时必须明确锁定兼容的 SDK/API version 与模型，并通过端到端契约测试确认。',
          basis: 'documented',
          sourceIds: ['anthropic-api-version-2026-10-21', 'anthropic-sdk-python-migration', 'claude-model-deprecations'],
          resourceIds: ['anthropic-api-version-2026-10-21'],
          note: 'API version 与 SDK major version 相关，但可通过显式配置改变；不可从 SDK 名称单独推断实际请求头。',
        },
        {
          id: 'effort-cache-impact',
          question: '更改 Anthropic 顶层 effort 后，是否仍能假设 prompt cache 前缀命中？',
          answer:
            '不能。Anthropic 文档说明，修改 output_config.effort 会使 message cache 失效，tool/system cache 是否同时失效取决于模型；显式设置为模型默认值与省略等价，不会导致失效。支持 per-message effort 的模型可通过 messages 内的 system message 改变轮次设置并保留缓存前缀，但该能力有 beta、模型与平台限制。不能把这些规则外推到兼容 endpoint。',
          basis: 'documented',
          sourceIds: ['claude-prompt-caching', 'claude-effort'],
          note: '以 Anthropic 当前缓存与 Effort 文档为准；不同模型、API 平台、请求层级和 beta 状态可能不同。',
        },
        {
          id: 'sampling-evidence-boundary',
          question: '历史三次 temperature=0 与 temperature=1 的输出差异，能证明温度造成了更高多样性或 temperature=0 不可复现吗？',
          answer:
            '不能。项目仅保留一个每组 3 次的历史摘要，没有完整请求/响应、固定模型快照或可复核评分器；它不足以估计分布、识别因果或支持逐字节可复现性结论。温度对输出的作用应通过受控、可复现的目标任务评测检验。',
          basis: 'unverified',
          note: '旧实验原始轨迹、请求参数和评估记录未归档，无法独立重算。当前官方文档只能支持参数契约，不能反向验证这组历史输出。',
        },
        {
          id: 'effort-is-not-temperature',
          question: '采样参数不被目标模型接受时，effort 是否是等价替代？',
          answer:
            '不是。Prompt 用于表达目标与风格，effort 是 Anthropic 对整体响应投入的行为信号，sampling 参数则影响 token 候选分布；结构校验与任务评测又承担不同职责。应按模型能力与目标指标选择控制方式，不能把它们视为同一旋钮。',
          basis: 'documented',
          sourceIds: ['claude-effort', 'claude-model-deprecations'],
          resourceIds: ['claude-model-migration'],
          note: 'Effort 默认值和可用级别是模型相关且会变化的；该检查点不固定具体模型矩阵。',
        },
        {
          id: 'max-tokens-truncation',
          question:
            '当 max_tokens 耗尽时，为什么结构化文本可能无法解析？它和「输出太长」是同一回事吗？',
          answer:
            '不是同一回事。max_tokens 是本次生成的上限；如果响应以 max_tokens 结束，输出可能不完整，但不能仅凭这个 stop reason 断言 JSON 一定无效，也不能假设每次都会返回半截字符串。应检查 stop_reason，并对实际文本执行解析和业务校验；若结果不完整，再按策略重试、续写或降级。',
          basis: 'documented',
          sourceIds: ['claude-messages-api'],
        },
      ],
    },
    {
      id: 'llm-api-basics/messages-api',
      chapterId: 'llm-api-basics',
      slug: 'messages-api',
      title: 'Messages API：system、多轮对话与流式响应',
      summary: '请求结构、对话历史怎么组织、流式事件怎么解析，以及为什么流式不只是为了体验。',
      estimatedMinutes: 25,
      difficulty: 'beginner',
      hasBody: true,
      status: 'drafting',
      keywords: ['messages-api', 'streaming', 'sse'],
      checkpoints: [
        {
          id: 'system-position',
          question:
            '在 Anthropic 的 Messages API 里，system 提示是放在哪里的？和 OpenAI 的做法有什么差别？',
          answer:
            'Anthropic 把 system 作为请求的**顶层字段**，与 messages 数组平级 —— 官方文档明确写过「there is no system role for input messages in the Messages API」。OpenAI Chat Completions 则允许在 messages 中使用 system 消息；不同 API 形状应分别核对。适配层应显式表达 provider 差异，不能把单个接口的字段布局推广到所有 API。',
          basis: 'documented',
          sourceIds: ['claude-messages-api', 'openai-chat-api'],
          note: 'Anthropic 侧的表述引自 Messages API 参考页；OpenAI 侧的结构引自其 Chat Completions 参考。写适配层时请以两份文档的当前版本为准。',
        },
        {
          id: 'streaming-value',
          question: '流式响应除了“让用户更快看到字”，还有什么工程上的意义？',
          answer:
            '流式可降低用户首次看到可展示内容的等待时间，但首 token 时间（TTFT）、首个可见文本时间和总耗时是不同指标。它也让客户端能在生成期间展示部分文本或缓冲工具参数；是否取消了 provider 端生成、已生成部分如何计费，须按目标 SDK/provider 验证，客户端关闭连接本身不能证明上游已停止。',
          basis: 'inferred',
          note: '这是工程判断。事件格式与 accumulator 以 Anthropic streaming 文档为准；取消和账单语义应使用目标 SDK/provider 的实测与文档，不作通用保证。',
          resourceIds: ['claude-streaming', 'anthropic-python-sdk', 'claude-pricing'],
        },
        {
          id: 'message-stop-reason',
          question: '收到完整消息后，如何解释 Anthropic Messages API 的 stop_reason？',
          answer:
            '按协议状态分流：end_turn 表示 assistant 本轮结束，tool_use 表示有 client tool 提案需由宿主处理，max_tokens 表示达到生成上限而内容可能不完整，refusal 表示拒绝，pause_turn 与 model_context_window_exceeded 也需按官方文档处理。stop_reason 不证明答案正确、授权通过或工具执行成功；未知值应显式处理，不能套用到其他 provider。',
          basis: 'documented',
          sourceIds: ['anthropic-stop-reasons'],
          note: '状态集合与语义以 Anthropic Messages API 当前文档为准；宿主仍需独立完成输出判定、授权与工具执行结果校验。',
        },
      ],
    },
    {
      id: 'llm-api-basics/model-selection',
      chapterId: 'llm-api-basics',
      slug: 'model-selection',
      title: '模型选型与成本：用评测选择候选',
      summary: '按目标任务评估质量、成本和延迟，区分模型路由与高影响动作的授权/审批。',
      estimatedMinutes: 15,
      difficulty: 'beginner',
      hasBody: true,
      status: 'drafting',
      keywords: ['model', 'cost', 'routing'],
      checkpoints: [
        {
          id: 'model-tiering',
          question: '模型选型应比较什么，怎样判断轻量候选是否能替代当前模型？',
          answer:
            '先用代表性任务集和实际 prompt/data 比较质量、边界用例、延迟与费用，再选择满足本地质量门槛的候选。模型和 effort 的推荐矩阵只是对应厂商、时间和 workload 的起点；轻量模型可能适合，也可能无法达到任务门槛。是否有节省，应以每个成功任务成本和目标 SLA 核算，而不是假设多数流量简单或质量损失可以忽略。',
          basis: 'documented',
          sourceIds: ['openai-model-selection', 'anthropic-choosing-model', 'anthropic-cost-intelligence'],
          note: '官方指南都建议用具体任务和评估结果选型；它们的模型矩阵、内部 benchmark 与价格不是其他 provider 或本站负载的普遍结论。',
          resourceIds: ['openai-model-selection', 'anthropic-choosing-model', 'anthropic-cost-intelligence', 'claude-pricing'],
        },
        {
          id: 'pricing-volatility',
          question: '为什么本站不直接写出各模型的单价？',
          answer:
            '价格与收费结构由模型、平台、地区、上下文长度、缓存、批处理等因素决定，且可随官方价格页更新。本站选择不在正文固定写价格，要求读者核对目标端点的现行费率，并把来源和核实日期记入估算。这是编辑原则，不是价格每月必变的技术规律。',
          basis: 'documented',
          sourceIds: ['claude-pricing'],
          note: '官方定价页列出多种模型及可叠加的缓存、批处理、地区和长上下文收费规则；不据此推断固定调整周期。',
          resourceIds: ['claude-pricing'],
        },
        {
          id: 'model-routing-is-not-authorization',
          question: '把高影响请求路由到更强模型，是否足以允许系统自动执行？',
          answer:
            '不足。模型能力分档只决定候选生成方式，不是身份认证、资源授权或业务审批。执行写入、付款、对外发送等动作仍要由宿主按认证身份、资源权限和业务规则独立校验，并在需要时要求人工审批；模型输出或分类分数不能替代这些控制。',
          basis: 'documented',
          sourceIds: ['owasp-authorization-cheat-sheet'],
          note: '该检查点应用 OWASP 服务端授权原则于模型路由场景；它不证明任何具体模型在某任务上的质量。',
        },
      ],
    },
    {
      id: 'llm-api-basics/prompt-caching',
      chapterId: 'llm-api-basics',
      slug: 'prompt-caching',
      title: 'prompt caching：按 provider 契约评估前缀复用',
      summary:
        '如果目标 provider 支持 prompt/context cache，稳定前缀可能降低重复计算或费用；命中条件、断点、TTL、usage 与定价必须按该 API 核实。',
      estimatedMinutes: 15,
      difficulty: 'intermediate',
      hasBody: true,
      status: 'drafting',
      keywords: ['caching', 'cost', 'latency'],
      checkpoints: [
        {
          id: 'cache-provider-contracts',
          question:
            'Anthropic、OpenAI 与 DeepSeek 的缓存观测字段和启用契约能否互换？',
          answer:
            '不能。Anthropic Messages API 使用 cache_control 断点/自动缓存，并分别报告 cache_creation_input_tokens、cache_read_input_tokens 与未缓存 input_tokens；OpenAI 按模型区分隐式与显式断点，Responses API 报告 cached_tokens 与 cache_write_tokens；DeepSeek 原生 API 默认按持久化前缀单元尽力匹配，并报告 prompt_cache_hit_tokens 与 prompt_cache_miss_tokens。字段、TTL、最小长度、匹配规则和计费口径必须按 provider、endpoint 与模型文档逐项核验；兼容 endpoint 的历史观测不能代替原生 API 契约。',
          basis: 'documented',
          sourceIds: ['claude-prompt-caching', 'openai-prompt-caching', 'deepseek-context-caching'],
          note: '官方文档核对日期为 2026-10-22；OpenAI 模型版本、Anthropic 当前读价与 DeepSeek 磁盘缓存策略均可能变化。DeepSeek Anthropic 兼容 endpoint 的历史结果缺少原始响应，不据此断言其当前行为。',
        },
      ],
    },
    {
      id: 'llm-api-basics/provider-contracts',
      chapterId: 'llm-api-basics',
      slug: 'provider-contracts',
      title: '多厂商 API 契约：兼容不等于等价',
      summary: '从 Responses、Messages 与兼容端点中提炼可迁移边界，建立能力矩阵、适配层与故障语义测试。',
      estimatedMinutes: 25,
      difficulty: 'intermediate',
      hasBody: true,
      status: 'drafting',
      keywords: ['provider', 'responses-api', 'messages-api', 'compatibility'],
      checkpoints: [
        {
          id: 'provider-compatibility-boundary',
          question: '为什么 OpenAI 兼容端点不能直接当作 OpenAI 行为兼容？',
          answer: '兼容通常只覆盖部分请求和响应形状；参数、工具调用、流事件、错误、usage、模型能力仍可能不同。必须按具体 endpoint 与 model 做能力声明并运行契约测试。',
          basis: 'documented',
          sourceIds: ['openai-responses-api', 'openai-responses-reference', 'deepseek-chat-api', 'deepseek-responses-api'],
        },
        {
          id: 'tool-call-id-pairing',
          question: 'Responses、Anthropic Messages 与 DeepSeek Chat 的工具调用和结果分别用哪个 ID 字段关联？',
          answer: 'OpenAI Responses 使用 function_call.call_id 与 function_call_output.call_id；Anthropic Messages 使用 tool_use.id 与 tool_result.tool_use_id；DeepSeek Chat Completions 使用 assistant message 的 tool_calls[].id 与 tool message 的 tool_call_id。它们应逐协议配对，不能把字段名或调用 ID 互换。',
          basis: 'documented',
          sourceIds: ['openai-responses-api', 'anthropic-tool-use', 'deepseek-chat-api'],
          note: 'ID 配对只保证协议关联，不证明调用有权限、参数正确或副作用可重试。',
        },
        {
          id: 'normalize-lossily',
          question: '适配层何时应该拒绝归一化？',
          answer: '当统一字段会抹掉调用方需要的语义，例如拒绝、截断原因、异步暂停或工具调用标识时，应保留原始响应并返回明确的能力/状态，而不是伪造一个看似成功的统一结果。',
          basis: 'inferred',
          note: '这是基于多厂商协议差异的工程建议。',
          resourceIds: ['openai-responses-api', 'openai-responses-reference', 'openai-structured-outputs', 'anthropic-tool-use', 'anthropic-stop-reasons', 'deepseek-chat-api', 'deepseek-responses-api'],
        },
        {
          id: 'only-dispatch-classified-tool-calls',
          basis: 'inferred',
          question: '响应里出现工具调用对象，是否就可以执行？',
          answer:
            '不可以。只有适配层将完整响应分类为 `tool_calls` 时，才把通过一致性检查的调用放入可派发字段；截断、拒绝、失败或未知状态中的部分调用应仅留作诊断。宿主还必须独立校验调用 ID、注册工具、参数 schema、用户授权和副作用策略。',
          note: '这是 fail-closed 控制流建议；协议结构本身不授予工具执行权限。',
        },
      ],
    },
  ],
  resourceIds: [
    'claude-models-overview',
    'openai-model-selection',
    'anthropic-choosing-model',
    'anthropic-cost-intelligence',
    'owasp-authorization-cheat-sheet',
    'openai-responses-api',
    'openai-responses-reference',
    'openai-structured-outputs',
    'anthropic-tool-use',
    'anthropic-stop-reasons',
    'anthropic-sdk-python-migration',
    'anthropic-api-version-2026-10-21',
    'claude-model-deprecations',
    'deepseek-chat-api',
    'deepseek-anthropic-api',
    'deepseek-responses-api',
    'claude-messages-api',
    'claude-streaming',
    'claude-prompt-caching',
    'claude-effort',
    'claude-model-migration',
    'claude-pricing',
    'openai-chat-api',
    'openai-cookbook',
    'hf-agents-course-zh',
    'lost-in-the-middle',
  ],
  labIds: ['lab-sampling-params', 'lab-raw-sse-observer'],
  backendMapping: {
    analogy: '上下文窗口 ≈ 一个有损的、按 token 计费的 session state',
    transferable: [
      'HTTP 客户端、超时、重试、连接复用这套东西原样适用',
      'JSON 序列化与 schema 校验',
      '密钥管理、环境变量、密钥轮换',
      '流式传输——SSE 本质就是 HTTP 分块传输，你已经很熟',
    ],
    pitfalls: [
      '按字符数估算 token：字符与 token 的换算随文本类型剧烈变化，自己算必然偏差',
      '把上下文窗口当成内存：**放进去不等于读得到**，中间部分最容易被忽略',
      '假设所有 provider 的 prompt caching 都自动命中或采用相同折扣；应按具体 endpoint 的缓存契约和 usage 核算收益',
      '把 max_tokens 到限视为必然无效或必然得到半截 JSON：输出可能不完整，需检查 stop_reason 与实际内容',
    ],
    cost: 'low',
  },
  status: 'published',
  updatedAt: '2026-09-24',
  verifiedAt: '2026-10-09',
  flagship: true,
  projectIds: ['p1-reliable-extraction'],
} satisfies Chapter;
