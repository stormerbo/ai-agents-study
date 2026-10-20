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
          question: '为什么“不要输出解释性文字”这类否定式指令效果不稳定？该怎么改？',
          answer:
            '否定式指令要求模型持续抑制一个行为，而模型每一步生成时都可能“忘记”这个约束，尤其在长输出里越往后越容易失效。更稳的写法是正面描述你想要的：把“不要解释”改成“只输出 JSON，不要有其他文字”，并且给出一个具体的输出示例。正面指令是可执行的，否定指令是要求模型一直不做某件事。',
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
          question:
            '用 XML 标签把参考资料包起来（如 <document>...</document>），除了“让模型看得更清楚”，还有什么更重要的原因？',
          answer:
            '还有一个安全原因：显式边界标签和指令为模型提供了区分“指令”与“数据”的结构线索。若没有这类线索，参考资料里的一句话（“忽略之前的指令，改为输出……”）可能影响模型行为 —— 这就是提示注入。标签不是硬信任边界，也不能根治注入；它只是纵深防御的一层，仍需在模型外做权限隔离、程序化校验和高风险操作确认。',
        },
        {
          id: 'injection-not-solved',
          basis: 'inferred',
          question: '加了 XML 标签之后，提示注入就被解决了吗？',
          answer:
            '没有。标签只是概率性的解释线索，不是访问控制或不可绕过的解析边界。模型仍可能把不可信内容当作指令或事实。真正的防护必须是多层的：限制模型可用权限、对模型要执行的动作做程序化校验、关键操作要求人工确认。第 16 章会系统地讲这件事。',
        },
      ],
      resourceIds: ['anthropic-building-effective-agents'],
    },
    {
      id: 'prompt-engineering/few-shot',
      chapterId: 'prompt-engineering',
      slug: 'few-shot',
      title: '少样本示例：质量远比数量重要',
      summary: '三个精心挑选的示例，通常胜过二十个随手凑的示例。',
      estimatedMinutes: 15,
      difficulty: 'beginner',
      hasBody: true,
      status: 'drafting',
      keywords: ['few-shot', 'examples'],
      checkpoints: [
        {
          id: 'example-selection',
          basis: 'inferred',
          question: '挑选少样本示例时，最应该优先覆盖哪一类样本？',
          answer:
            '优先覆盖**边界情况与容易混淆的情况**，而不是典型情况。典型情况模型本来就做得对，把示例名额花在上面是浪费；真正决定输出质量的是那些“看起来像 A 其实该归到 B”的例子。另外要保证示例之间的格式严格一致 —— 模型会忠实地复制你示例里的不一致。',
        },
      ],
    },
    {
      id: 'prompt-engineering/chain-of-thought',
      chapterId: 'prompt-engineering',
      slug: 'chain-of-thought',
      title: '思维链与 prefill：让模型先想再答',
      summary:
        'CoT 的收益依赖任务与模型；prefill 是版本和 API 特定的机制，较新模型可能已不支持。',
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
            '当任务不需要多步推理，且明确要求把过程写进可见输出时，CoT 可能只增加输出 token、延迟和成本而没有准确率收益。本节只在一组 DeepSeek 端点实验中观察到这一结果，不能推广成所有模型的结论。先用目标模型和任务做对照评估；现代模型的内置 thinking、开关和提示行为都随版本变化。',
          resourceIds: ['chain-of-thought-paper', 'claude-prompting-best-practices'],
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
            '它需要两个条件同时成立：任务有可判定的目标答案（否则多数未必代表正确），且采样产生有意义的候选差异（否则没有可聚合的多样性）。本节实验在特定端点与小样本里，唯一答案题 5 次采样零分歧，创作题则各不相同；结果说明该实验的多数投票没有收益，不能推广为 self-consistency 普遍无效。是否能提高正确率需要用目标模型和任务做对照评估。',
          note: '实测数据见本节：唯一答案题 10/10、零分歧；创作题 6/6 各不相同。',
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
      resourceIds: ['self-refine-paper'],
    },
  ],
  resourceIds: [
    'anthropic-building-effective-agents',
    'chain-of-thought-paper',
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
      '用否定式指令（“不要输出……”）：效果不稳定，应正面描述要什么',
      '把指令和数据混在同一个文本块里：既不稳定，又打开了提示注入的口子',
      '以为 prompt 写一次就能长期用：模型版本更新会让精心调好的 prompt 失效',
      '未经目标模型验证就为简单任务加思维链：可能增加成本与延迟，未必提升准确率',
    ],
    cost: 'low',
  },
  status: 'published',
  updatedAt: '2026-10-08',
  verifiedAt: '2026-10-08',
} satisfies Chapter;
