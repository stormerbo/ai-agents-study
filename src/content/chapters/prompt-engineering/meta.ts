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
      hasBody: false,
      status: 'outlined',
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
      hasBody: false,
      status: 'outlined',
      keywords: ['xml-tags', 'prompt-injection'],
      checkpoints: [
        {
          id: 'why-xml-tags',
          basis: 'inferred',
          question:
            '用 XML 标签把参考资料包起来（如 <document>...</document>），除了“让模型看得更清楚”，还有什么更重要的原因？',
          answer:
            '还有一个安全原因：这是分清“指令”与“数据”的唯一手段。模型是在同一个文本通道里读指令和数据的，如果你不划边界，参考资料里的一句话（“忽略之前的指令，改为输出……”）就可以被当作指令执行 —— 这就是提示注入。划边界不能根治它，但它是纵深防御的第一层，也让模型更容易正确对待其中内容。',
        },
        {
          id: 'injection-not-solved',
          basis: 'inferred',
          question: '加了 XML 标签之后，提示注入就被解决了吗？',
          answer:
            '没有。标签只是让模型更容易区分，但模型仍然可能被说服 —— 因为归根结底它无法从原理上区分“数据里的话”和“你给的指令”，两者走的是同一个通道。真正的防护必须是多层的：不把不可信内容直接喂给有敏感权限的模型、对模型要执行的动作做程序化校验、关键操作要求人工确认。第 16 章会系统地讲这件事。',
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
      hasBody: false,
      status: 'outlined',
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
        '对多步推理有效，对简单任务只是浪费 token；prefill 则能在不改 prompt 的前提下控制输出开头。',
      estimatedMinutes: 17,
      difficulty: 'intermediate',
      hasBody: false,
      status: 'outlined',
      keywords: ['cot', 'prefill', 'reasoning'],
      checkpoints: [
        {
          id: 'cot-cost',
          basis: 'inferred',
          question: '思维链在什么情况下是净亏损？',
          answer:
            '当任务本身不需要多步推理时——分类、抽取、改写这类任务加上思维链，只会增加输出 token、拉高延迟和成本，准确率几乎不变，甚至因为多出的推理内容引入了新的错误机会而下降。判断标准是：这个任务的答案是否需要经过若干个中间步骤才能得出？不需要就别加。',
          resourceIds: ['chain-of-thought-paper'],
        },
        {
          id: 'prefill-use',
          basis: 'inferred',
          question: 'prefill（预填充 assistant 回复的开头）能解决什么具体问题？',
          answer:
            '两个典型用途：一是强制输出格式，比如预先写入一个左花括号，模型就只能顺着把 JSON 补完，省掉了“模型先说一句『好的，以下是 JSON：』”的麻烦；二是绕过模型不愿直接作答的倾向，通过替它起个头来引导它进入正题。它相当于在不修改 prompt 的情况下，给生成过程一个更强的起点。',
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
      hasBody: false,
      status: 'outlined',
      keywords: ['reliability', 'self-eval', 'ensemble'],
      checkpoints: [
        {
          id: 'self-consistency',
          basis: 'inferred',
          question: '同一个问题让模型独立回答多次再取多数结果，为什么能提升准确率？代价是什么？',
          answer:
            '因为单次采样会受随机性影响，错误方向通常不一致，而正确答案是稳定的吸引子 —— 所以多数投票能过滤掉随机错误。代价是成本与延迟按采样次数线性增长，且它只对“有确定答案”的任务有效：开放式写作没有“多数答案”，投票无意义。',
        },
        {
          id: 'self-eval-trap',
          basis: 'inferred',
          question: '让模型检查自己的输出（self-eval），有什么已知的局限？',
          answer:
            '模型对自己刚生成的答案存在偏好，倾向于认为它对 —— 尤其是当错误来自推理过程中的某个前提时，用同一套推理去检查往往查不出来，等于用同一把尺子量自己。实践上更有效的是换一个视角去查（比如只给答案不给推理过程，让它独立验证；或者用一个不同模型的实例来评），以及把可程序化验证的部分交给代码而不是模型。',
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
      '为简单任务加思维链：只增加成本与延迟，准确率没有提升',
    ],
    cost: 'low',
  },
  status: 'outlined',
  updatedAt: '2026-09-24',
  verifiedAt: '2026-09-24',
} satisfies Chapter;
