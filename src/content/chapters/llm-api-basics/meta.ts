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
      summary: 'token 同时是计费单位、容量单位与延迟来源。理解它，才知道后面为什么要做上下文工程。',
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
            '因为字符与 token 的换算关系随文本类型剧烈变化。官方给出的参照是：当前 tokenizer 下 100 万 token 约等于 555k 个单词或 250 万个 Unicode 字符 —— 这是针对英文等拉丁文本的估算。中文的 token 密度明显更高，同样字符数通常消耗更多 token，但具体倍数取决于内容与分词器，不要用固定系数硬算。工程上的做法是调用官方提供的计数接口，而不是自己估。',
          basis: 'documented',
          sourceIds: ['claude-models-overview'],
          note: '字符比率来自官方模型总览页。「中文 token 密度更高」是普遍共识，但我没有找到官方给出的确切倍数，因此只做定性描述、不写具体数字。',
        },
        {
          id: 'context-not-memory',
          question: '把关键信息放在很长的上下文中部，会发生什么？这对 prompt 的结构有什么指导？',
          answer:
            '模型对长上下文各位置的利用率并不均匀：开头和结尾记得最清楚，中间最容易被忽略。所以在拼装 prompt 时，指令应当放在开头或结尾，而不要把最关键的约束埋在大量参考资料中间；如果参考资料很长，宁可用检索挑出少量相关片段放在末尾，也不要整段塞进去。',
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
      title: '采样参数的消失：temperature 去哪了',
      summary:
        'temperature、top_p、top_k 在新一代模型上已被移除，传了会直接报错。这一节讲清发生了什么、现在该用什么控制输出，以及从旧教程或旧代码迁移时会撞上什么。',
      estimatedMinutes: 18,
      difficulty: 'beginner',
      hasBody: true,
      status: 'drafting',
      keywords: ['temperature', 'top-p', 'effort', 'breaking-change'],
      checkpoints: [
        {
          id: 'sampling-params-removed',
          question: '在新一代 Claude 模型上继续传 temperature 或 top_p，会发生什么？',
          answer:
            '会直接失败。对 Opus 4.6 之后发布的模型，传 temperature（非 1.0）、top_p（小于 0.99）或 top_k（任意值）会返回 400 错误；temperature=1.0 与 top_p>=0.99 这两个默认值为了向后兼容仍被接受，但不产生任何效果。Python SDK 从 1.0 起已不再定义这些参数，传了会抛 TypeError。仍然接受这些参数的只剩旧模型。',
          basis: 'documented',
          sourceIds: ['claude-messages-api', 'claude-model-migration'],
          note: '依据 2026-09 的官方文档。另外注意不同平台的失败方式不一样：直连 API 报 400，而经过 OpenRouter 这类聚合层是静默忽略 —— 后者更难排查，因为请求会成功但参数毫无作用。',
        },
        {
          id: 'effort-replaces-sampling',
          question: '采样参数被移除后，用什么控制模型的「思考深度」？',
          answer:
            '用 effort 参数。它控制模型在回答前思考多少，直接影响力、延迟与成本；各模型的默认值不同（例如 Opus 5.5 默认 medium，Sonnet 5 与 Fable 5.1 默认 high，而 Haiku 4.5 不支持）。至于输出风格与格式这类原本靠 temperature 微调的东西，官方的迁移建议是回归 prompting —— 用指令和示例来引导，而不是调参数。',
          basis: 'documented',
          sourceIds: ['claude-effort', 'claude-models-overview'],
        },
        {
          id: 'max-tokens-truncation',
          question:
            '为什么 max_tokens 设得过小会导致 JSON 解析失败？它和「输出太长」是同一回事吗？',
          answer:
            '不是同一回事。max_tokens 是硬截断：达到上限就停，不会给你一个完整的结构。所以当你要求模型输出 JSON 而 max_tokens 不够时，拿到的是一个被腰斩的字符串 —— JSON.parse 会直接抛错。工程上必须同时做两件事：把上限设得比预期输出宽裕，以及检查 stop_reason，截断时走重试或降级而不是盲目解析。',
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
            'Anthropic 把 system 作为请求的**顶层字段**，与 messages 数组平级 —— 官方文档明确写过「there is no system role for input messages in the Messages API」。OpenAI 则把它作为 messages 数组里第一条 role 为 system 的消息。这个差别看起来琐碎，但它正是多厂商适配层存在的原因：上层业务代码不应该知道这件事。',
          basis: 'documented',
          sourceIds: ['claude-messages-api', 'openai-chat-api'],
          note: 'Anthropic 侧的表述引自 Messages API 参考页；OpenAI 侧的结构引自其 Chat Completions 参考。写适配层时请以两份文档的当前版本为准。',
        },
        {
          id: 'streaming-value',
          question: '流式响应除了“让用户更快看到字”，还有什么工程上的意义？',
          answer:
            '三点。一是**首字节延迟**变成了用户感知的主要指标，而不是总时长 —— 生成 30 秒的内容，第一秒就开始显示和等 30 秒后一次性显示，体验差别巨大。二是可以在生成过程中**提前中断**（用户改主意、检测到输出跑偏），省下未生成部分的费用。三是可以边收边做增量处理，比如流式解析工具调用参数，不必等完整响应。',
          basis: 'inferred',
          note: '这是工程判断，不是文档规定。流式的具体能力边界（哪些事件可分片、中断后已生成部分如何计费）请以官方 streaming 与 pricing 文档为准。',
          resourceIds: ['claude-streaming', 'claude-pricing'],
        },
      ],
    },
    {
      id: 'llm-api-basics/model-selection',
      chapterId: 'llm-api-basics',
      slug: 'model-selection',
      title: '模型选型与成本：什么时候该用贵的',
      summary: '分层路由的判断标准，以及为什么“统一用最强模型”通常是个昂贵且不必要的选择。',
      estimatedMinutes: 15,
      difficulty: 'beginner',
      hasBody: true,
      status: 'drafting',
      keywords: ['model', 'cost', 'routing'],
      checkpoints: [
        {
          id: 'model-tiering',
          question: '为什么不该让所有请求都走最强的模型？分层路由应该按什么标准切？',
          answer:
            '因为任务难度分布极不均匀：多数请求是分类、抽取、改写这类小模型就能做好的事，真正的复杂推理只占少数。按“任务需要多少推理深度”和“错了的代价有多大”两个维度切分，把简单任务路由到便宜模型，把复杂或高风险的留给强模型。这样通常能在几乎不损失质量的前提下显著降低成本。',
          basis: 'inferred',
          note: '这是工程判断。具体差距取决于当时的模型定价与能力分布，请对照官方模型总览页自行核算 —— 本站在正文里不写价格数字。',
          resourceIds: ['claude-models-overview', 'claude-pricing'],
        },
        {
          id: 'pricing-volatility',
          question: '为什么本站不直接写出各模型的单价？',
          answer:
            '因为模型定价与型号的变动频率以月计，任何写死在学习资料里的价格都会在几周内变成误导。正确做法是：在这里学会**成本的估算方法**（token 数 × 单价 × 调用次数），价格数值到官方定价页现查。这也是本站对「具体数字」的统一处理原则 —— 要么标注来源与核实日期，要么不写。',
          basis: 'inferred',
          note: '这是本站的编辑原则，不是技术事实。写这一节时我确实查到了当时的定价，正因为它在几周内就可能变，才决定不写进正文。',
          resourceIds: ['claude-pricing', 'openai-cookbook'],
        },
      ],
    },
    {
      id: 'llm-api-basics/prompt-caching',
      chapterId: 'llm-api-basics',
      slug: 'prompt-caching',
      title: 'prompt caching：把重复的前缀变成折扣',
      summary:
        '如果你的请求有一个很长且很少变化的前缀（系统提示、工具定义、参考文档），这里有一笔明显的省钱空间。',
      estimatedMinutes: 15,
      difficulty: 'intermediate',
      hasBody: true,
      status: 'drafting',
      keywords: ['caching', 'cost', 'latency'],
      checkpoints: [
        {
          id: 'cache-prefix-order',
          question:
            'prompt caching 能命中的前提是什么？为什么把经常变化的内容放在请求前面会让缓存完全失效？',
          answer:
            '前提是前缀**完全一致** —— 官方文档的原文是「Cache hits require 100% identical prompt segments」。缓存按 tools → system → messages 的层级做前缀哈希，一旦某处出现差异，从该处往后的所有内容都无法复用。所以顺序必须遵循「稳定的在前、易变的在后」：工具定义、系统提示、固定参考文档放最前，用户本次的问题放最后。把时间戳这类每次都变的内容放在开头，命中率会直接归零。',
          basis: 'documented',
          sourceIds: ['claude-prompt-caching'],
          note: '同一页面里还有两个容易被忽略的硬门槛：不同模型有 512~4096 的最小可缓存 token 数（低于门槛会静默不缓存、且不报错），以及每个请求最多 4 个缓存断点。',
        },
      ],
    },
  ],
  resourceIds: [
    'claude-models-overview',
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
      '忽略 prompt caching：一个长系统提示反复付费，成本会高出数倍',
      '把 max_tokens 理解为“输出长度建议”：它是硬截断，会给你半截 JSON',
    ],
    cost: 'low',
  },
  status: 'published',
  updatedAt: '2026-09-24',
  verifiedAt: '2026-10-09',
  flagship: true,
} satisfies Chapter;
