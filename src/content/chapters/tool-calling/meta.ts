import type { Chapter } from '@/content/curriculum/schema';

export const chapter = {
  id: 'tool-calling',
  stageId: 'stage-2-primitives',
  order: 4,
  title: 'Tool / Function Calling',
  subtitle: '让模型能动手',
  summary:
    '工具调用到底发生了什么、工具描述为什么本质上是 prompt、如何用 poka-yoke 的思路让错误在结构上不可能发生，以及工具数量膨胀带来的隐性代价。',
  outcomes: [
    '能手写一次完整的工具调用往返，包括把结果喂回去',
    '能设计出一份让模型难以误用的工具 schema',
    '能判断一个工具该不该拆、该不该合并，以及工具数量何时开始伤害效果',
  ],
  depth: 'deep',
  difficulty: 'intermediate',
  estimatedMinutes: 110,
  tags: ['tool-use', 'function-calling', 'api-design'],
  prerequisiteIds: ['context-engineering', 'prompt-engineering'],
  lessons: [
    {
      id: 'tool-calling/what-really-happens',
      chapterId: 'tool-calling',
      slug: 'what-really-happens',
      title: '工具调用到底发生了什么',
      summary:
        '最重要的一件事：模型从不执行任何东西。它只生成一个结构化的调用意图，剩下的全是你的事。',
      estimatedMinutes: 18,
      difficulty: 'intermediate',
      hasBody: true,
      status: 'drafting',
      keywords: ['tool-use', 'mechanics'],
      checkpoints: [
        {
          id: 'who-executes',
          basis: 'inferred',
          question: '当模型“调用”了一个工具，实际发生了什么？中间有哪些环节是你必须实现的？',
          answer:
            '模型做的事只有一件：在输出里生成一个结构化的调用请求（工具名 + 参数 JSON）然后停下，此时 `stop_reason` 是 `tool_use` 而不是 `end_turn` —— 这是判断循环该继续还是该结束的**唯一可靠信号**。之后必须由你的代码完成三件事：从 `content` 里挑出 `tool_use` 块、执行真正的函数、把返回值作为 `tool_result` 追加进历史再请求一次。好在协议会强制你补齐：漏掉 `tool_result` 或 `tool_use_id` 写错，都是 **400 错误**，报文会指出是哪条消息、哪个 id 不匹配 —— 不会静默通过。',
          note: '本节实测（deepseek-flash，2026-10-08）：两种配对错误均返回 400，报文明确指出缺失位置。',
        },
        {
          id: 'tool-result-is-prompt',
          basis: 'inferred',
          question: '为什么说工具返回的内容“也是 prompt”？这个说法在实践中意味着什么？',
          answer:
            '因为工具返回值会作为消息进入模型的上下文，和你的指令处在**同一个文本通道**里 —— 模型没有机制区分「我的工具返回的数据」和「用户写的文字」，所以返回值的内容同样会影响它的行为。实践含义有两层：返回值里混入误导性文字时模型可能当真；格式清晰是**零成本的保险**。但别过度设计 —— 本节实测里，同一份数据用晦涩 JSON 与清晰文本两种格式返回，模型的最终回答**没有出现差异**（4 条记录、几个数字的规模下）。原理成立，收益要到数据量更大、字段更多时才显现。',
          note: '本节实测（deepseek-flash，2026-10-08）：两种返回格式下模型都完整保住了全部字段，未见差异。',
        },
      ],
      resourceIds: ['claude-api-docs'],
    },
    {
      id: 'tool-calling/schema-design',
      chapterId: 'tool-calling',
      slug: 'schema-design',
      title: '工具描述即 prompt',
      summary:
        '模型决定用不用某个工具、怎么填参数，唯一的依据就是你写的那段描述。它不是文档，是 prompt。',
      estimatedMinutes: 20,
      difficulty: 'intermediate',
      hasBody: false,
      status: 'outlined',
      keywords: ['schema', 'description'],
      checkpoints: [
        {
          id: 'description-quality',
          basis: 'inferred',
          question:
            '两个功能相同的工具，一个描述是“查询天气”，另一个是“查询指定城市当前天气，参数 city 需为英文城市名或邮政编码”。模型的表现会有什么差别？',
          answer:
            '差别很大。后者明确了两件事：什么时候该用（当前天气，而不是历史或预报），以及参数该长什么样（英文城市名或邮编）。前者会让模型在参数里塞进“北京今天热不热”这种自然语言，或者在本该查预报时误用。工具描述是模型唯一的判断依据，把边界条件写清楚比把功能写漂亮更重要。',
        },
        {
          id: 'enum-over-free-text',
          basis: 'inferred',
          question: '如果一个参数只允许几个固定取值，应该在 schema 里怎么写？为什么？',
          answer:
            '用 enum 明确列出所有合法值，而不是写成自由字符串再在代码里校验。因为 enum 会在工具定义里直接告诉模型可选范围，它从一开始就不会生成非法值——错误在源头就被排除了。写成自由字符串则等于把校验收到了运行时，你会拿到“UTC+8”、“utc 8”、“北京时间”这些本不该出现的东西。',
        },
      ],
    },
    {
      id: 'tool-calling/poka-yoke',
      chapterId: 'tool-calling',
      slug: 'poka-yoke',
      title: 'poka-yoke：让错误在结构上不可能',
      summary:
        '与其在文档里叮嘱模型“不要这样做”，不如把接口设计成它根本做不出来。这是本章最值钱的一节。',
      estimatedMinutes: 22,
      difficulty: 'advanced',
      hasBody: false,
      status: 'outlined',
      keywords: ['design', 'poka-yoke'],
      checkpoints: [
        {
          id: 'poka-yoke-example',
          basis: 'inferred',
          question:
            '一个删除文件的工具接受 file_path 参数。怎样改造它，能让“删错文件”变得结构上不可能？',
          answer:
            '把“指明要删什么”变成“必须先看清楚再删”：拆成两步——第一步 list_files 返回候选文件及其内容摘要，第二步 delete_file 只接受上一步返回的 file_id，而不是任意路径。这样模型无法删除一个它没看过的文件，因为 id 只能从第一步获得。这就是 poka-yoke（防呆）：不是靠提示词请求模型谨慎，而是让危险动作在接口层面无法被表达。',
        },
        {
          id: 'optional-params-trap',
          basis: 'inferred',
          question: '把工具参数设计成“大多可选、可任意组合”，会带来什么风险？',
          answer:
            '会产生大量无意义的参数组合，而模型会在其中挑一个看似合理但实际错误的组合——因为可选参数在它看来都是“可以用”的。更糟的是这类错误很难在代码里拦截，因为每个组合单看都合法。应对方式是把必填项做实、把互斥参数用联合类型明确表达（而不是两个可选的字段靠代码隐含约束），必要时拆成多个语义单一的工具。',
        },
      ],
      resourceIds: ['anthropic-building-effective-agents'],
    },
    {
      id: 'tool-calling/parallel-and-errors',
      chapterId: 'tool-calling',
      slug: 'parallel-and-errors',
      title: '并行调用、错误处理与幂等',
      summary:
        '模型可以一次请求多个工具。这带来效率，也带来你熟悉的一整套问题：顺序、失败与重复执行。',
      estimatedMinutes: 25,
      difficulty: 'intermediate',
      hasBody: false,
      status: 'outlined',
      keywords: ['parallel', 'idempotency', 'error-handling'],
      checkpoints: [
        {
          id: 'partial-failure',
          basis: 'inferred',
          question: '模型在一轮里请求了三个工具，其中一个执行失败。你该怎么把结果回传？',
          answer:
            '三个结果都要回传，失败的也要——而且要带上有信息量的失败原因。如果你只回传成功的两个，模型会以为第三个从未被请求，可能再次发起同样的调用，陷入循环；如果你把异常栈直接扔回去，模型也不知道该怎么办。正确做法是回传一条结构化的错误（哪些参数有问题、可选值有哪些、是否可重试），让模型有机会自己纠正参数重试一次。',
        },
        {
          id: 'write-idempotency',
          basis: 'inferred',
          question: '为什么带副作用的工具（写文件、发消息、下单）必须考虑重复执行？',
          answer:
            '因为重试发生在多个层次：你的代码可能因超时而重试、模型可能因为没看懂结果而重复调用、流式连接中断后整轮可能重放。对读操作无所谓，对写操作意味着重复下单、重复发消息。应对就是你已经熟悉的幂等键：让模型或调用方带一个唯一标识，服务端按标识去重，重复请求返回首次的结果而不是再执行一遍。',
        },
      ],
    },
    {
      id: 'tool-calling/tool-count',
      chapterId: 'tool-calling',
      slug: 'tool-count',
      title: '工具数量的代价',
      summary: '把 50 个工具全部暴露给模型，效果会明显变差。这背后有可解释的原因，也有对应的解法。',
      estimatedMinutes: 25,
      difficulty: 'advanced',
      hasBody: false,
      status: 'outlined',
      keywords: ['scaling', 'tool-selection'],
      checkpoints: [
        {
          id: 'why-too-many-tools',
          basis: 'inferred',
          question: '工具数量变多之后，模型的选择准确率为什么会下降？',
          answer:
            '三个叠加的原因：一是工具定义本身占据大量上下文，稀释了对任务的注意力（context rot 的典型表现）；二是相似工具之间产生歧义，模型难以区分“该用哪个”；三是选择空间变大后，选错的概率自然上升。这不是模型“变笨”，而是你给它的决策问题变难了。',
        },
        {
          id: 'tool-organizing',
          basis: 'inferred',
          question: '有哪些办法能在工具很多时保持选择准确率？',
          answer:
            '常见手段有四种：按当前任务场景只暴露相关的一组工具（分组按需加载，而不是全量常驻）；把相似工具合并成一个带明确动作参数的接口；用一层轻量的路由先判断意图，再决定加载哪组工具；以及让工具可以“发现”——先提供搜索工具的能力，模型查到需要什么再加载具体工具。共同点是都避免让模型同时面对全部选项。',
          resourceIds: ['anthropic-building-effective-agents'],
        },
      ],
    },
  ],
  resourceIds: [
    'claude-api-docs',
    'anthropic-building-effective-agents',
    'toolformer-paper',
    'openai-cookbook',
  ],
  labIds: ['lab-tool-schema'],
  backendMapping: {
    analogy: '工具调用 ≈ RPC 接口设计，但契约由自然语言描述、且调用方是一个概率性推理者',
    transferable: [
      '接口设计经验：参数校验、错误语义、向后兼容',
      '幂等键与重试安全——这里同样必须做',
      '错误码设计：要能被调用方理解并据此采取行动',
    ],
    pitfalls: [
      '把工具描述当作给人看的 API 文档来写：它是 prompt，模型完全依赖它做判断',
      '在工具内部抛异常：模型看不到栈，它只看到你返回的那段字符串',
      '设计出参数可任意组合的工具，等于邀请模型组合出无效状态',
      '工具数量膨胀后仍全量暴露：选择准确率会明显下降',
    ],
    cost: 'medium',
  },
  status: 'outlined',
  updatedAt: '2026-09-24',
  verifiedAt: '2026-09-24',
} satisfies Chapter;
