import type { Chapter } from '@/content/curriculum/schema';

export const chapter = {
  id: 'structured-output',
  stageId: 'stage-2-primitives',
  order: 5,
  title: '结构化输出',
  subtitle: '把自然语言收窄成可校验的接口',
  summary:
    '为什么“在 prompt 里写清楚要 JSON”远远不够、约束解码是怎么做到的、校验失败之后该怎么办，以及 schema 管不了的那部分（业务规则）该如何兜底。',
  outcomes: [
    '能用 schema 约束让模型输出可被程序直接消费的结构',
    '能设计一套解析失败时的重试与降级策略，而不是把错误抛给用户',
    '能区分“格式错误”和“语义错误”，并知道各自该在哪儿拦',
  ],
  depth: 'deep',
  difficulty: 'intermediate',
  estimatedMinutes: 90,
  tags: ['json', 'schema', 'validation'],
  prerequisiteIds: ['tool-calling'],
  lessons: [
    {
      id: 'structured-output/why-not-prompt-only',
      chapterId: 'structured-output',
      slug: 'why-not-prompt-only',
      title: '为什么“请在 prompt 里写清楚要 JSON”不够',
      summary: '提示级别的约束是概率性的，工程级别的约束才是确定的。这个区别决定了系统能不能上线。',
      estimatedMinutes: 18,
      difficulty: 'intermediate',
      hasBody: true,
      status: 'drafting',
      keywords: ['json', 'reliability'],
      checkpoints: [
        {
          id: 'prompt-level-vs-decoding',
          basis: 'inferred',
          question: '“在 prompt 里要求输出 JSON”和“用约束解码强制输出 JSON”，本质区别是什么？',
          answer:
            '提示会影响输出倾向，但不是格式保证。目标 endpoint 若支持约束输出，它只约束已声明且受支持的 schema 子集；拒绝、截断、传输错误仍要分流。应用仍须解析并在副作用入口前执行本地 schema/业务校验。',
        },
        {
          id: 'failure-rate-math',
          basis: 'inferred',
          question: '如果单次请求的格式正确率是 99%，为什么在真实系统里这个数字不够用？',
          answer:
            '若每次调用独立、成功率相同且没有重试，N 次都通过的概率为 p^N；例如 p=0.99、N=10 时约 90.4%。这只是说明累积效应的简化模型，不是线上预测。少量样本不能证明极低失败率；应按目标端到端验收定义持续测量，并保留校验、重试、降级或人工处理路径。',
        },
        {
          id: 'provider-output-token-limit',
          basis: 'documented',
          question: '为什么不能把 `max_tokens` 当成所有模型 API 的通用字段？',
          answer:
            '输出上限字段属于具体 API 契约：Anthropic Messages 使用 `max_tokens`，OpenAI Chat Completions 推荐 `max_completion_tokens`（旧 `max_tokens` 已弃用），Responses API 使用 `max_output_tokens`。上限可能计入不可见的推理 token；请求与预算要按目标 endpoint 文档解释。',
          sourceIds: ['anthropic-messages-api', 'openai-chat-api', 'openai-responses-reference'],
        },
      ],
    },
    {
      id: 'structured-output/json-schema-strict',
      chapterId: 'structured-output',
      slug: 'json-schema-strict',
      title: 'JSON Schema 与约束解码',
      summary: 'schema 如何从“建议”变成“强制”，以及模型厂商各自是怎么实现它的。',
      estimatedMinutes: 22,
      difficulty: 'intermediate',
      hasBody: true,
      status: 'drafting',
      keywords: ['json-schema', 'constrained-decoding'],
      checkpoints: [
        {
          id: 'schema-limits',
          basis: 'inferred',
          question: '受 schema 约束的输出，为什么仍然可能“内容上是错的”？',
          answer:
            'schema 在 endpoint 支持的子集内可以约束字段形状和值域，但不能证明模型填写的事实有可信来源，也不能替代业务授权。需要把结构/值域校验、证据核验与副作用授权分开。',
        },
        {
          id: 'strict-vs-normal',
          basis: 'documented',
          question: '在使用厂商提供的“严格模式”时，需要注意什么限制？',
          answer:
            '严格约束能力属于具体 API 契约。DeepSeek strict tool calls 需使用其 Beta Chat Completions function 形态；Anthropic strict tool use 与 JSON structured outputs 是不同功能。各自只支持文档列出的 schema 子集，例如递归引用、数值边界和字符串模式的边界并不相同。请求前核对目标 endpoint、模型与当前文档；结构约束仍不代表事实正确或获准执行。',
          sourceIds: ['deepseek-tool-calls', 'anthropic-strict-tool-use', 'anthropic-structured-outputs'],
        },
      ],
    },
    {
      id: 'structured-output/validation-retry',
      chapterId: 'structured-output',
      slug: 'validation-retry',
      title: '校验失败之后：重试、修复与降级',
      summary: '失败一定会发生。区别在于你的系统是优雅地处理它，还是把异常抛给用户。',
      estimatedMinutes: 25,
      difficulty: 'intermediate',
      hasBody: true,
      status: 'drafting',
      keywords: ['retry', 'fallback', 'error-handling'],
      checkpoints: [
        {
          id: 'retry-with-feedback',
          basis: 'inferred',
          question: '输出格式不对时，直接把同样的请求重发一次，效果如何？更好的做法是什么？',
          answer:
            '直接重发效果有限——因为模型是在相同的输入下重新采样，很可能再次犯同类错误，属于碰运气。更好的做法是**把校验错误也发回去**：告诉它“你上次的输出在 field X 处期望是数字，实际得到了字符串”，并附上原始输出。有了具体的错误信息，模型通常能一次改对。同时要给重试次数设上限，避免在模型确实无法完成的任务上反复烧钱。',
        },
        {
          id: 'degradation-path',
          basis: 'inferred',
          question: '重试若干次仍失败，系统应该怎么收场？',
          answer:
            '必须有一条明确的降级路径，且这条路径不能是“抛异常给用户”。可选的做法按代价排序：退化成人工审核队列、返回一个保守的默认结果并标注不确定性、或者把问题拆小后重试。关键是在设计阶段就想清楚——因为这类分支在生产里一定会被走到，而临时补的兜底通常既不被测试覆盖也没人知道它的存在。',
        },
      ],
    },
    {
      id: 'structured-output/beyond-json',
      chapterId: 'structured-output',
      slug: 'beyond-json',
      title: 'schema 之外：业务规则怎么兜',
      summary: '结构合法只是入场券。真正决定系统是否可用的是那些 schema 表达不出来的约束。',
      estimatedMinutes: 25,
      difficulty: 'advanced',
      hasBody: true,
      status: 'drafting',
      keywords: ['business-rules', 'cross-validation'],
      checkpoints: [
        {
          id: 'cross-field-validation',
          basis: 'inferred',
          question:
            '一个输出里有 start_date 和 end_date 两个字段，都是合法日期。需要额外写什么校验？',
          answer:
            '需要跨字段校验：end_date 不能早于 start_date。这类约束在 JSON Schema 里表达起来很别扭甚至无法表达，但它恰恰是业务上最容易出错的地方——模型可能分别生成了两个都合理的日期，却构成一个不可能的区间。所以解析通过之后必须再跑一遍业务层校验，把所有跨字段、跨记录的规则集中在一处实现。',
        },
        {
          id: 'hallucinated-values',
          basis: 'inferred',
          question:
            '模型输出了一个格式完全正确、但内容凭空捏造的字段值（比如一个不存在的订单号）。这类问题能靠 schema 解决吗？该靠什么？',
          answer:
            'schema 完全无能为力——一个不存在的订单号在格式上和真实订单号没有区别。这类问题的解法不在校验层，而在**改变任务设计**：不要问模型“这个订单的状态是什么”然后相信它的答案，而是让它输出一个订单号，由**你的代码**去数据库里查状态再把结果给模型。把“事实来源”从模型转移到可验证的数据源，是应对幻觉最根本的手段。',
        },
      ],
    },
  ],
  resourceIds: [
    'anthropic-messages-api',
    'openai-chat-api',
    'openai-responses-reference',
    'claude-api-docs',
    'openai-cookbook',
    'openai-agents-sdk-python',
    'hf-agents-course-zh',
  ],
  labIds: ['lab-json-retry'],
  backendMapping: {
    analogy: '结构化输出 ≈ 给一个不可靠的第三方服务加一层严格的响应校验层',
    transferable: [
      'schema 校验的整套经验（Pydantic / Zod / JSON Schema）',
      '失败重试、熔断、降级的处理模式',
      '接口版本兼容与字段演进的考虑',
    ],
    pitfalls: [
      '以为加了 schema 就万无一失：schema 管形状，不管业务规则是否正确',
      '解析失败直接抛异常给用户，而不是重试或降级',
      '把解析失败一律归因为“模型不行”：更常见的原因是 max_tokens 截断或 prompt 没说清',
      '忽略跨字段约束：两个各自合法的字段可以组成一个不可能的状态',
    ],
    cost: 'medium',
  },
  status: 'published',
  updatedAt: '2026-10-22',
  verifiedAt: '2026-10-22',
} satisfies Chapter;
