import type { Chapter } from '@/content/curriculum/schema';

export const chapter = {
  id: 'prompt-engineering',
  stageId: 'stage-1-foundation',
  order: 2,
  title: 'Prompt 工程',
  subtitle: '把话说到模型能听懂为止',
  summary:
    '清晰直接的指令、指令与数据的分离、少样本示例、思维链，以及多数教程会漏掉的一节：如何让输出变得**稳定**，而不只是“这次对了”。',
  outcomes: [
    '能写出让模型稳定按格式输出的 prompt，而不是靠运气',
    '能判断一段参考资料应该放在 prompt 的哪个位置，以及为什么',
    '知道输出不稳定时该先怀疑什么，而不是盲目加大 prompt 篇幅',
  ],
  depth: 'deep',
  difficulty: 'beginner',
  estimatedMinutes: 90,
  tags: ['prompt', 'reliability'],
  prerequisiteIds: ['llm-api-basics'],
  lessons: [
    {
      id: 'prompt-engineering/instruction-clarity',
      chapterId: 'prompt-engineering',
      slug: 'instruction-clarity',
      title: '清晰直接：把“暗示”换成“明说”',
      summary: '模型不会读心术。你以为说清楚了，是因为你知道自己想说什么 —— 这是最常见的失败来源。',
      estimatedMinutes: 15,
      difficulty: 'beginner',
      hasBody: true,
      status: 'drafting',
      keywords: ['instruction', 'clarity'],
      checkpoints: [
        {
          id: 'negative-instructions',
          basis: 'inferred',
          question: '怎样把模糊或冲突的指令改成可验收的任务契约？旧实验能证明否定式或 system 层普遍更好吗？',
          answer:
            '明确目标、输入边界、正反约束、输出格式和可观察验收条件；结构要求用 schema 检查，语义要求用经校准的评分规则或人工复核。负向规则、正向描述和示例可以组合，但要检查彼此一致，并在目标模型与代表性案例上评测。旧的 8 次与 3 次结果没有逐次轨迹，不能证明因果、普遍优劣或通用角色优先级。',
          note: '两家官方指南支持清晰目标、示例与模型专属评测建议；Anthropic 常见 system 参数与当前特定模型支持的对话中途 system 消息须分别表述。本节没有可复核的旧实验原始轨迹，不能据此声称某种句式普遍更稳。',
          resourceIds: ['openai-prompt-engineering', 'claude-prompting-best-practices', 'anthropic-messages-api', 'anthropic-working-with-messages'],
        },
      ],
    },
    {
      id: 'prompt-engineering/structure-and-separation',
      chapterId: 'prompt-engineering',
      slug: 'structure-and-separation',
      title: '指令与数据分离：为什么必须划边界',
      summary:
        '把用户输入和你的指令混在一起的写法，会同时带来两个问题：效果不稳定，以及一个安全漏洞。',
      estimatedMinutes: 18,
      difficulty: 'beginner',
      hasBody: true,
      status: 'drafting',
      keywords: ['xml-tags', 'prompt-injection'],
      checkpoints: [
        {
          id: 'why-xml-tags',
          basis: 'inferred',
          question: 'XML 标签、JSON 编码和来源说明能提供什么边界线索？它们能形成访问控制吗？',
          answer:
            '它们可以帮助模型识别内容结构与来源，但效果依模型、API 消息结构和工作负载而异，不能形成访问控制或保证拦截注入。把模型输出当作不可信提议；由宿主服务端强制执行身份/对象授权、最小权限、参数与业务约束，并按风险加入审批和副作用控制。',
          resourceIds: ['claude-prompting-best-practices', 'anthropic-handle-tool-calls', 'owasp-llm-prompt-injection'],
        },
        {
          id: 'injection-not-solved',
          basis: 'inferred',
          question: '加了 XML 标签之后，提示注入就被解决了吗？',
          answer:
            '没有。标签只是概率性的解释线索，不是访问控制或不可绕过的解析边界。模型仍可能把不可信内容当作指令或事实。真正的防护必须是多层的：限制模型可用权限、对模型要执行的动作做程序化校验、关键操作要求人工确认。第 16 章会系统地讲这件事。',
        },
      ],
      resourceIds: [
        'anthropic-building-effective-agents',
        'claude-prompting-best-practices',
        'anthropic-handle-tool-calls',
        'anthropic-python-sdk',
        'anthropic-messages-api',
        'owasp-llm-prompt-injection',
      ],
    },
    {
      id: 'prompt-engineering/few-shot',
      chapterId: 'prompt-engineering',
      slug: 'few-shot',
      title: '少样本示例：质量远比数量重要',
      summary: '示例可以表达任务约定与决策边界；是否改善结果，要在独立留出集上验证。',
      estimatedMinutes: 15,
      difficulty: 'beginner',
      hasBody: true,
      status: 'drafting',
      keywords: ['few-shot', 'examples'],
      checkpoints: [
        {
          id: 'example-selection',
          basis: 'inferred',
          question: '如何评估 few-shot 示例是否改善了目标任务？',
          answer:
            '先定义标签/任务规则，用开发集设计示例、独立留出集比较零样本与不同示例组；检查训练/测试重复，固定模型版本和参数，保留逐题结果，结合总体及分组指标、错误严重性与 token/延迟决定是否保留。边界示例可能有价值，但没有普遍最佳数量；格式一致是数据整理习惯，不能仅凭旧的 12/12 摘要断言其模型收益。',
          note: '本节 2026-10-08 历史 few-shot、格式与错误标签实验均缺逐次原始轨迹；旧主表训练/测试有一条精确重复，另一个未运行的消融脚本有三条重复，不能作为泛化证据。',
        },
      ],
      resourceIds: [
        'openai-prompt-engineering',
        'claude-prompting-best-practices',
        'anthropic-python-sdk',
        'anthropic-messages-api',
      ],
    },
    {
      id: 'prompt-engineering/chain-of-thought',
      chapterId: 'prompt-engineering',
      slug: 'chain-of-thought',
      title: 'CoT 与 prefill：效果评估和 API 边界',
      summary:
        'CoT 历史观察不足以支持普遍有效或无效结论；prefill 受模型与 API 版本约束。',
      estimatedMinutes: 17,
      difficulty: 'intermediate',
      hasBody: true,
      status: 'drafting',
      keywords: ['cot', 'prefill', 'reasoning'],
      checkpoints: [
        {
          id: 'cot-cost',
          basis: 'inferred',
          question: '思维链在什么情况下是净亏损？',
          answer:
            '当某个工作负载的对照评估显示可见步骤没有质量收益而增加输出、延迟或预算时，可以省略；CoT 论文和本站有限历史摘要都不能推出适用于所有模型、任务的规则。目标模型、推理设置、评分器和完整 input/output/cache usage 应分别记录。',
          resourceIds: ['chain-of-thought-paper', 'claude-prompting-best-practices'],
        },
        {
          id: 'cot-paper-result-scope',
          basis: 'documented',
          sourceIds: ['chain-of-thought-paper'],
          question: '2022 年 CoT 论文支持怎样的范围结论？',
          answer:
            '论文在当时测试的三个大型语言模型及算术、常识和符号推理基准上研究带推理示例的 few-shot CoT，并报告多个任务有提升；这支持论文设置范围内的结论，不说明所有任务、当前模型或只添加零样本“请一步步思考”都会获得同等收益。',
        },
        {
          id: 'cot-historical-summary',
          basis: 'unverified',
          question: '本站 DeepSeek CoT 与 prefill 历史摘要能证明什么？',
          answer:
            '当前仅能复述历史记录中的小样本答案数、token 汇总和存在冲突的 prefill 输出摘要；不能独立复算准确率、完整 token 用量、成本或 prefill 响应行为，也不能归因于模型 thinking。',
          note: '逐次原始请求/响应、模型指纹、任务与逐题评分记录、完整 usage 及可复现脚本未归档；prefill 结果在同一正文内记录为 temp_c=20 与 temp_c=null，无法判定哪项正确。',
        },
        {
          id: 'reasoning-summary-scope',
          basis: 'documented',
          sourceIds: ['openai-learning-to-reason-llms'],
          question: '用户看到的推理说明一定是原始内部推理吗？',
          answer:
            'OpenAI 对 o1 的说明指出，产品面向用户展示的是模型生成的 reasoning summary，而不是 raw chain of thought。这是该产品系列的实现说明；解释文本仍不能代替答案的独立校验。',
        },
        {
          id: 'anthropic-usage-fields',
          basis: 'documented',
          sourceIds: ['anthropic-messages-api'],
          question: '怎样统计 Anthropic Messages API 的完整 input token 数？',
          answer:
            '按该 API 的 usage 契约，input_tokens、cache_creation_input_tokens 与 cache_read_input_tokens 共同构成 total input tokens；output_tokens 是独立的输出计数。字段语义和账单口径不能直接套到兼容端点或其他厂商。',
        },
        {
          id: 'prefill-use',
          basis: 'documented',
          sourceIds: ['claude-prompting-best-practices'],
          question: 'prefill（预填充 assistant 回复的开头）能解决什么具体问题？',
          answer:
            'Prefill 只适用于目标 API/模型明确支持的场景；它可以在较早模型或兼容端点上预置 assistant 回复前缀，但并不保证模型只续写前缀之后的内容。当前 Anthropic 文档说明 Claude 4.6 起不支持最后一条 assistant prefill（请求会返回 400），推荐清晰指令或结构化输出。跨厂商、模型版本和 API 都应先查文档并做兼容性测试。',
          resourceIds: ['claude-prompting-best-practices'],
        },
      ],
    },
    {
      id: 'prompt-engineering/reliability',
      chapterId: 'prompt-engineering',
      slug: 'reliability',
      title: '可靠性增强：从“这次对了”到“一直都对”',
      summary: '多数 prompt 教程在这里结束。但把 demo 变成能上线的功能，靠的是这一节讲的手段。',
      estimatedMinutes: 25,
      difficulty: 'intermediate',
      hasBody: true,
      status: 'drafting',
      keywords: ['reliability', 'self-eval', 'ensemble'],
      checkpoints: [
        {
          id: 'self-consistency',
          basis: 'inferred',
          question: '多数投票（self-consistency）能生效的窗口为什么很窄？',
          answer:
            '它需要可判定的目标答案，并且采样产生能被聚合器利用的候选差异。本节两组历史摘要须分开看：10 道程序生成的算术/计数题各采样 5 次，报告 0/10 题分歧和单次/五次平均 token 237/1281；另一项温度探测在单个唯一答案题与创作题上各采样 6 次，报告 1/6 与 6/6 个不同答案。原始逐次响应、模型快照、任务映射和 scorer 未归档，不能独立复算或推出普遍结论。是否提高正确率需在目标模型与任务上对照评估。',
          note: '均为 2026-10-08 历史摘要：self-consistency 的 10 道算术/计数题 0/10 题分歧；温度探测为另一个唯一答案题与创作题，各温度 6 次采样，报告 1/6 与 6/6 个不同答案。逐次原始记录缺失，不能复算。',
        },
        {
          id: 'self-eval-trap',
          basis: 'inferred',
          question: '让模型检查自己的输出（self-eval），局限到底在哪里？',
          answer:
            '自查的实际机制是「重做一遍」，而不是「审阅推理」。所以它只能抓住**可独立重算**的错误（本节实验里捉住我构造的 8/8 个错答，正是靠重算）。一旦错误来自推理过程中的前提，重做会沿着同一条路径再次滑过去 —— 用同一套直觉检查同一套直觉，查不出同源的错。因此它的有效用途很窄：检查对象必须就在上下文里（比如「摘要是否忠实于原文」），且不由模型自己的记忆提供依据。',
        },
        {
          id: 'checkability',
          basis: 'inferred',
          question: '为什么说「可靠性的上限是可校验性」，而不是模型的聪明程度？',
          answer:
            '因为决定一个错误能否被发现的，不是谁更聪明，而是这个任务的正确答案能不能被**独立**验证。「独立」是关键 —— 一个用同样假设的复核者（人还是模型都一样），查不出同源的错误。所以工程上的动作只有一个方向：把校验从「仅模型可判」往「结构可校验」「语义可校验」挪，凡是能写成程序算的，就不要交给模型。',
        },
      ],
      resourceIds: ['self-consistency-paper', 'self-refine-paper', 'anthropic-python-sdk', 'anthropic-api-version-2026-10-21'],
    },
  ],
  resourceIds: [
    'anthropic-building-effective-agents',
    'chain-of-thought-paper',
    'openai-learning-to-reason-llms',
    'anthropic-python-sdk',
    'anthropic-messages-api',
    'openai-prompt-engineering',
    'self-refine-paper',
    'hf-agents-course-zh',
    'openai-cookbook',
    'claude-prompting-best-practices',
  ],
  labIds: ['lab-prompt-ab'],
  backendMapping: {
    analogy: '写 prompt ≈ 写一份必须让新同事一次看懂的需求文档，但这个同事每次读都会理解得略有不同',
    transferable: [
      '接口文档那套“边界条件必须显式写出来”的要求',
      '把隐式契约显式化、把默认行为写清楚',
      '输入校验与异常分支的处理习惯',
    ],
    pitfalls: [
      '只写禁止事项而不说明允许范围：补充正面目标和可验收判据，并在目标任务上比较',
      '未区分应用规则与不可信输入：清楚表达数据边界，但仍在服务端执行权限与输出校验',
      '以为 prompt 写一次就能长期用：模型版本变化可能改变行为，应有版本化回归评测',
      '未经目标模型验证就为简单任务加思维链：可能增加成本与延迟，未必提升准确率',
    ],
    cost: 'low',
  },
  status: 'published',
  updatedAt: '2026-10-08',
  verifiedAt: '2026-10-08',
} satisfies Chapter;
