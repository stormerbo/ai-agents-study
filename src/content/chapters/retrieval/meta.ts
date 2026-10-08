import type { Chapter } from '@/content/curriculum/schema';

export const chapter = {
  id: 'retrieval',
  stageId: 'stage-2-primitives',
  order: 6,
  title: '检索',
  subtitle: '把外部知识接进上下文',
  summary:
    '模型不知道的东西，只有三种给法：塞进 prompt、检索、微调。这一章讲第二种为什么是多数场景的默认选择、切分与召回各在哪里决定上限、向量检索的天花板在哪，以及怎么在怪模型之前先量清楚检索本身。',
  outcomes: [
    '能判断一个需求该用检索、该微调，还是该把数据直接放进 prompt',
    '能设计切分与召回策略，并说得出每一步的取舍依据',
    '能搭一套最小评测集，把「检索错了」和「模型答错了」分开定位',
  ],
  depth: 'deep',
  difficulty: 'intermediate',
  estimatedMinutes: 100,
  tags: ['rag', 'retrieval', 'embeddings'],
  prerequisiteIds: ['context-engineering', 'structured-output'],
  lessons: [
    {
      id: 'retrieval/why-retrieval',
      chapterId: 'retrieval',
      slug: 'why-retrieval',
      title: '检索解决的是「模型不知道」，不是「模型不会」',
      summary: '三种把外部知识交给模型的路径，以及它们各自解决不了的问题。',
      estimatedMinutes: 18,
      difficulty: 'beginner',
      hasBody: true,
      status: 'drafting',
      keywords: ['rag-basics', 'fine-tuning'],
      checkpoints: [
        {
          id: 'retrieval-vs-finetune',
          basis: 'inferred',
          question: '什么情况下该用微调而不是检索？',
          answer:
            '先分清要改变的是**知识**还是**行为**。检索改变的是「模型能看到什么」，它适合知识频繁变化、需要引用出处、或者数据量太大无法全部放进上下文的场景。微调改变的是「模型默认怎么做」—— 固定的输出格式、领域语气、特定的分类体系，这些靠检索是给不进去的。\n\n还有一条现实约束：微调的知识更新需要重新训练，而检索只需要更新索引。所以只要需求里带着「知识会变」，默认答案就是检索。',
        },
        {
          id: 'retrieval-limits',
          basis: 'inferred',
          question: '检索能不能让模型「更聪明」？',
          answer:
            '不能。检索只影响**上下文里有什么信息**，不影响模型的推理能力。一个推不出来的结论，把相关资料全放进去它仍然推不出来。\n\n判断方法很简单：如果任务失败的原因是「模型没有这条信息」，检索有机会；如果是「模型有信息但推理错了、格式不遵守、工具不会用」，该去改 prompt、schema 或工具设计，而不是加大检索力度。把这两类失败混在一起，是检索项目里最常见的浪费。',
        },
      ],
      resourceIds: ['rag-paper', 'anthropic-context-engineering'],
    },
    {
      id: 'retrieval/chunking',
      chapterId: 'retrieval',
      slug: 'chunking',
      title: '切分决定上限',
      summary: '大多数检索问题在切分阶段就已经注定，而它最容易被跳过。',
      estimatedMinutes: 20,
      difficulty: 'intermediate',
      hasBody: true,
      status: 'drafting',
      keywords: ['chunking', 'preprocessing'],
      checkpoints: [
        {
          id: 'chunk-size-tradeoff',
          basis: 'inferred',
          question: 'chunk 切得太大或太小，分别会出什么问题？',
          answer:
            '切得太大：一段里混进了多个主题，向量被平均成一个「什么都不太像」的表示，召回精度下降，而且每次都把无关内容一起塞进上下文，成本上升。\n\n切得太小：语义被切断。一个需要跨两句才能理解的表述，被拆开后任何一片单独看都不完整，模型拿到它也不知道在讲什么。\n\n工程上的常规做法是带**重叠**（overlap）来缓解切断，并且优先按**结构边界**（标题、段落、函数、表格行）切，而不是按固定字数硬切。长度只是兜底。',
        },
        {
          id: 'chunk-structure',
          basis: 'inferred',
          question: '为什么「按固定长度切」对表格和代码特别有害？',
          answer:
            '因为这两类内容的含义绑定在**结构**上。一张表被从中间切开后，后半段的列头丢失，变成一堆没有字段名的数字；一段代码被切开后，缩进与作用域断裂，语义完全变了。\n\n这类内容更稳的做法是**整体保留**：表格按行切但每片都带上表头，代码按函数或类切，并保留必要的导入上下文。判断标准可以统一成一句话 —— **切完之后，这一片单独交给一个没看过原文的人，他能不能看懂。**',
        },
      ],
      resourceIds: ['ragflow', 'langchain-docs'],
    },
    {
      id: 'retrieval/vector-limits',
      chapterId: 'retrieval',
      slug: 'vector-limits',
      title: '向量检索的天花板',
      summary: '「语义相似」不等于「相关」，而这正是纯向量检索最常失手的地方。',
      estimatedMinutes: 22,
      difficulty: 'intermediate',
      hasBody: true,
      status: 'drafting',
      keywords: ['embeddings', 'hybrid-search', 'rerank'],
      checkpoints: [
        {
          id: 'why-keyword-still-matters',
          basis: 'inferred',
          question: '为什么纯向量检索对订单号、错误码、专有名词这类查询特别差？',
          answer:
            '因为嵌入模型把文本压成语义向量，而**它训练时见过的语言里，这类标识符的信息量很低** —— 一串随机字符在语义空间里几乎不携带可区分的含义，很多标识符还会被切分成无意义的碎片。结果就是两个完全不同的订单号，向量距离可能比它和一个普通词更近。\n\n而这类查询恰好是**精确匹配**的强项：倒排索引（BM25 一类）能一字不差地命中。所以生产系统普遍采用**混合检索** —— 关键词与向量各取一部分候选，再用重排（rerank）合并排序。只上向量，等于主动放弃了精确匹配能力。',
        },
        {
          id: 'rerank-value',
          basis: 'inferred',
          question: '召回阶段多取一些候选、再用重排筛，为什么比直接取 top-k 更好？',
          answer:
            '因为**召回与排序是两件事，而它们的最优策略不同**。向量检索快，适合从海量文档里粗筛出几十上百个候选；重排模型慢但更准，适合在这一小撮里精细排序。\n\n先粗后精的好处是：粗筛阶段可以故意放宽（多召回），把「正确答案没被召回」这个最致命的失败模式压下去。如果直接用向量 top-5 当最终结果，一旦正确答案排在第 12 位，后面再怎么优化 prompt 都救不回来 —— 因为你根本没把它交给模型。',
        },
      ],
      resourceIds: ['ragflow', 'open-deep-research'],
    },
    {
      id: 'retrieval/evaluating-retrieval',
      chapterId: 'retrieval',
      slug: 'evaluating-retrieval',
      title: '先量检索，再怪模型',
      summary: '把「检索错了」和「模型答错了」分开，是这类项目最重要的定位能力。',
      estimatedMinutes: 22,
      difficulty: 'advanced',
      hasBody: true,
      status: 'drafting',
      keywords: ['evaluation', 'recall', 'metrics'],
      checkpoints: [
        {
          id: 'separate-failure-layers',
          basis: 'inferred',
          question: '最终答案错了，怎么判断是检索的问题还是模型的问题？',
          answer:
            '做一个**分层检查**：把「正确答案所在的那篇文档」是否出现在召回结果里，和「模型有没有给出正确答案」分开看。两种组合的含义完全不同 ——\n\n- 正确答案**没被召回** → 检索的问题。改 prompt 没有任何用。\n- 正确答案**已召回**，模型仍答错 → 模型或上下文组织的问题（内容被淹没了、指令没说清、或者答案需要跨文档综合）。\n\n这个检查需要一份带标注的小评测集：若干问题，每个标注「答案在哪篇文档里」。几十条就够用，而它能省下的时间远超建它的时间。',
        },
        {
          id: 'metric-choice',
          basis: 'inferred',
          question: '评估检索时，recall@k 和 precision@k 该看哪个？',
          answer:
            '先看 **recall@k**。因为在这个链路里，没被召回的文档就等于不存在 —— 后面所有环节都无法挽回。precision 低一些只是浪费一点上下文预算，recall 低则是直接断掉了正确答案的来源。\n\n但 recall 有个前提：k 必须与最终真正送进模型的数量匹配。如果召回 20 篇、重排后只留 3 篇，那该看的是**重排之后**的 recall@3，而不是召回阶段的 recall@20 —— 否则你会得到一个漂亮但没意义的数字。',
        },
      ],
      resourceIds: ['open-deep-research', 'ai-engineering-huyen'],
    },
    {
      id: 'retrieval/agentic-retrieval',
      chapterId: 'retrieval',
      slug: 'agentic-retrieval',
      title: '把检索接进循环：一次还是多轮',
      summary: '固定管线的 RAG 与「让模型自己决定查什么」，差的不只是成本。',
      estimatedMinutes: 20,
      difficulty: 'advanced',
      hasBody: true,
      status: 'drafting',
      keywords: ['agentic-rag', 'tool-use'],
      checkpoints: [
        {
          id: 'single-vs-agentic',
          basis: 'inferred',
          question: '「检索一次就回答」和「把检索做成工具让模型多轮调用」，各自适合什么场景？',
          answer:
            '一次检索适合**问题本身已经清楚**的场景：客服问答、文档查询，用户的问题就是检索词，一轮就够。它的优点是延迟低、成本可预测、行为好调试。\n\n多轮适合**问题需要先被拆解、或者第一轮的结果会改变下一步要查什么**的场景：多跳问答、跨文档比对、需要先定位再细查的任务。代价是轮次不确定 —— 成本和延迟都变成变量，同时会引入新的失败模式（反复查同样的东西、越查越偏）。\n\n一个实用的中间形态：**默认一次，把「再查一次」做成显式的工具调用**，并由你设上限。这样既保留了多跳能力，又把成本关在了笼子里。',
        },
        {
          id: 'context-vs-retrieval-cost',
          basis: 'inferred',
          question: '什么时候「一次把资料全塞进去」反而比按需检索更划算？',
          answer:
            '当**需要的资料占资料总量的比例足够高**时。按需检索不是免费的：每一轮都要多一次工具往返，而且取回的内容会进入历史、在后续每一轮重复计费。\n\n第 3 章给过一个实测的交叉点：固定 40 篇文档，需要 2 篇时按需取只要 0.64 倍成本，需要 40 篇时要 3.60 倍 —— **交叉点大约在「需要的占 20%」**。所以判断依据不是「资料多不多」，而是「这次任务需要其中的多大一部分」。',
        },
      ],
      resourceIds: ['anthropic-context-engineering', 'anthropic-building-effective-agents'],
    },
  ],
  resourceIds: ['rag-paper', 'anthropic-context-engineering', 'ragflow', 'open-deep-research', 'langchain-docs'],
  backendMapping: {
    analogy: '检索 ≈ 给一堆非结构化文档建索引，再对外暴露一个由模型生成的查询接口 —— 而查询语句本身不可靠',
    transferable: [
      '索引设计、分词、倒排与向量索引的取舍经验',
      '召回率 / 精确率的评估方法，以及「先量再调」的排查习惯',
      '缓存与预计算：嵌入可以离线算好，重排不能',
    ],
    pitfalls: [
      '把「答案错」一律归因于模型：多数时候该先看召回结果里有没有正确答案',
      '以为向量检索可以完全取代关键词检索，放弃精确匹配能力',
      '跳过切分直接调参：切分方式决定了上限，后面怎么调都补不回来',
      '「检索到了」就假定「模型会用」：无关或过长内容会稀释注意力，需要自己把验证做进链路',
    ],
    cost: 'medium',
  },
  status: 'published',
  updatedAt: '2026-10-08',
  verifiedAt: '2026-10-08',
} satisfies Chapter;
