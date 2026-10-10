import type { Chapter } from '@/content/curriculum/schema';

export const chapter = {
  id: 'continuous-evolution',
  stageId: 'stage-5-practice',
  order: 24,
  title: '持续进化',
  subtitle: '上线之后，它怎么变更好',
  summary:
    '前面的章节讲怎么把 agent 做出来，这一章讲做出来之后的事。轨迹是唯一一份「真实分布上表现如何」的记录，从它里面能提炼出四种形态的产物；但「完成」不等于「进步」，闭环只优化它能观测的东西。',
  outcomes: [
    '能判断一条经验该写成哪种形态：知识、指令、程序还是参数',
    '能从失败轨迹里提炼规则，并说清它为什么常常测不出效果',
    '能说清可验证闭环的边界在哪，以及为什么它会自信地跑偏',
  ],
  depth: 'deep',
  difficulty: 'expert',
  estimatedMinutes: 50,
  tags: ['continuous-improvement', 'distillation', 'closed-loop'],
  prerequisiteIds: ['evaluation', 'memory'],
  lessons: [
    {
      id: 'continuous-evolution/from-traces',
      chapterId: 'continuous-evolution',
      slug: 'from-traces',
      title: '从轨迹里能学到什么',
      summary: '四种产物按成本排序：知识、指令、程序、参数。',
      estimatedMinutes: 24,
      difficulty: 'advanced',
      hasBody: true,
      status: 'published',
      keywords: ['traces', 'learning-loops', 'distillation'],
      checkpoints: [
        {
          id: 'four-forms',
          basis: 'inferred',
          question: '从轨迹里学到的经验，可以写成哪四种形态？怎么判断该用哪种？',
          answer:
            '四种，按改动成本从低到高：**知识**（检索库里的条目，分钟级生效、容易回滚）、**指令**（提示词里的一条规则，同上）、**程序**（一段可执行代码或工具，需要测试与发布）、**参数**（模型权重，周级生效、回滚困难）。判据是一个简单的问法：**这条经验能写成一句话、一段代码、还是一条数据？** 能写成一句话的进指令，能写成代码的进程序，能写成数据的进知识；**三个都写不出来的，才轮到参数**。由此还得出一条实用规则：**凡是能写成代码的规则，都不该留给提示词** —— 写进提示词的版本要靠模型每次遵守，写进代码的版本不可能被违反，两者可靠性不在一个量级。',
        },
        {
          id: 'non-failure-sources',
          basis: 'inferred',
          question: '除了失败案例，轨迹里还有哪三类同样有价值的信号？',
          answer:
            '**一、人的修正** —— 人在审批点改了什么、拒绝时说了什么（第 19 章）。这是最贵的信号，因为一个人愿意花时间改，说明这个点值得改。**二、成功但绕了远路** —— 结果对了但步数或成本远超预期；这类案例不会出现在失败日志里，却最容易优化，判据是对比同类任务成功案例里成本与步数分布的尾部。**三、模型的犹豫** —— 一个任务在多次运行里时对时错（第 15 章第 2 节的 Pass^k），它比一个稳定失败的任务更有价值：后者说明根本不会，前者说明差一点，而差一点的地方往往投入产出比最高。',
        },
      ],
      resourceIds: ['open-deep-research', 'ai-engineering-huyen'],
    },
    {
      id: 'continuous-evolution/distill-and-test',
      chapterId: 'continuous-evolution',
      slug: 'distill-and-test',
      title: '从失败里提炼规则：实测与三个边界',
      summary: '提炼出的规则没有带来可测提升 —— 因为基线已经满分。',
      estimatedMinutes: 26,
      difficulty: 'expert',
      hasBody: true,
      status: 'published',
      keywords: ['rule-distillation', 'generalization', 'closed-loop'],
      checkpoints: [
        {
          id: 'distill-no-gain',
          basis: 'documented',
          sourceIds: ['open-deep-research'],
          question: '实测里从失败提炼的规则为什么没带来提升？「从失败学习」的结构性矛盾是什么？',
          answer:
            '实测：条件 A 从 1 条样本提炼规则后处理其余 7 条全对；条件 B 从 8 条样本提炼规则后处理 4 条新格式 4/4 —— **而对照组（不加任何规则）同样是 4/4**。所以规则没有带来可测提升，**原因是基线已接近满分**（第 15 章第 2 节那个评测集饱和的第三次出现）。条件 A 尤其说明问题：它提炼的规则是窄的（只管中文年月日），其余 7 条却全过 —— 那些是模型本来就会的。**结构性矛盾**是：你会拿失败案例去测规则，但失败案例本身稀有；规则从罕见情况学来，而验证需要大量同类任务，**可那些任务模型本来就做得对，所以它们没进失败日志** —— 你手里根本没有能验证这条规则的数据集。这不是方法问题，是数据问题。可行的三条路：注入式构造（人为加难，把基线压到中间区间）、**只看回归**（测规则有没有让别的用例变差 —— 这类样本总是充足的）、以及先上线再观察命中率。',
        },
        {
          id: 'closed-loop-boundary',
          basis: 'inferred',
          question: '可验证闭环的边界在哪？为什么说它会「自信地跑偏」？',
          answer:
            '闭环的形态是「运行 → 收集 → 提炼 → 上线 → 再运行」，它有一个隐含假设：**「这次做得对」等于「系统变好了」**。两件事在三种情况下会分开：**一、目标被改写** —— 如果规则本身是错的，闭环会高效地把错误固化下来，而从失败提炼的规则，其质量取决于「失败原因的判断」，那个判断通常也是模型做的；**二、反馈被稀释** —— 如果规则只在一小部分流量上生效，它对总体指标影响很小，你既看不出有没有用，也无法回滚；**三、指标被优化而目标没有** —— 通过率涨了，但涨的是你测的那个通过率，不是用户满意度。所以结论是：**闭环能优化的只有它能观测的东西；对观测不到的部分，它不会保守，它会自信地跑偏。** 三个闸门：规则必须能被人读懂、必须能回滚、必须有独立于它的指标。',
        },
      ],
      resourceIds: ['open-deep-research', 'ai-engineering-huyen'],
    },
  ],
  resourceIds: ['open-deep-research', 'ai-engineering-huyen', 'anthropic-context-engineering'],
  backendMapping: {
    analogy:
      '持续进化 ≈ 一个不能只靠改配置、还要靠运行数据自我修正的服务：慢是慢的，但停下来就会落后',
    transferable: [
      '线上反馈驱动改进的整套习惯：收集、归因、灰度、回滚',
      '回归测试的思路：改动的风险主要来自副作用，而不是它本身没生效',
      '配置与代码的边界判断：能写死的就别做成可配置的',
    ],
    pitfalls: [
      '只从失败里学，忘了「成功但绕远路」和「时对时错」这两类更有价值的样本',
      '把能写成代码的规则写进提示词，于是它随时可能被违反',
      '一直在往提示词里加规则，从不删 —— 第 3 章实测过规则一多必然自相矛盾',
      '用同一套指标准备优化又用来评价，于是它开始失真',
      '规则上线后没有「命中」信号，看不出有没有用，也无法回滚',
      '在解释「模型没做到」之前不看 stop_reason —— 空输出会被读成能力问题',
    ],
    cost: 'high',
  },
  status: 'published',
  updatedAt: '2026-10-10',
  verifiedAt: '2026-10-10',
} satisfies Chapter;
