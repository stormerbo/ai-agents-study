import type { Chapter } from '@/content/curriculum/schema';

export const chapter = {
  id: 'agent-paradigms',
  stageId: 'stage-3-orchestration',
  order: 10,
  title: 'Agent 范式',
  subtitle: 'ReAct、Plan-Execute 与它们的适用边界',
  summary:
    '范式不是风格选择，而是对「环境有多不确定」的下注。这一章把五类主流范式放在同一张表里对比，说清每一种在什么条件下有效、失效时是什么样子，以及为什么多数生产系统该从最简单的那个开始。',
  outcomes: [
    '能用一句话说清五类范式的本质差别与代价',
    '能判断一个任务该用哪种范式，并说出判断依据',
    '能识别范式的典型失效模式，而不是把失败归因于「模型不行」',
  ],
  depth: 'deep',
  difficulty: 'intermediate',
  estimatedMinutes: 105,
  tags: ['react', 'planning', 'reflection'],
  prerequisiteIds: ['retrieval', 'memory'],
  lessons: [
    {
      id: 'agent-paradigms/five-paradigms',
      chapterId: 'agent-paradigms',
      slug: 'five-paradigms',
      title: '五类范式：一张对照表',
      summary: 'ReAct、Plan-Execute、Reflexion、Tree-of-Thoughts、Multi-Agent —— 差别的本质在哪。',
      estimatedMinutes: 20,
      difficulty: 'beginner',
      hasBody: true,
      status: 'drafting',
      keywords: ['react', 'plan-execute', 'taxonomy'],
      checkpoints: [
        {
          id: 'what-actually-differs',
          basis: 'inferred',
          question: '这五类范式真正的差别是什么？不要用「有的先规划、有的边做边想」这种描述。',
          answer:
            '差别在**对不确定性的下注方式**：\n\n- **ReAct**：不赌，每一步都根据上一步的观测重新决定 —— 适合路径未知、环境会反馈的任务。\n- **Plan-Execute**：赌「计划不会中途作废」，用一次前置规划换取后续步骤的稳定与可并行 —— 适合步骤可预测的结构化任务。\n- **Reflexion**：赌「第二次尝试比第一次好」，用额外的评估轮次换准确率。\n- **Tree-of-Thoughts**：赌「多试几条路优于一条路走到底」，用分支搜索换难题上的质量。\n- **Multi-Agent**：赌「上下文隔离的收益大于协调成本」。\n\n每一种都是拿**成本或延迟**去换**某类不确定性**。所以判断该用哪种，等价于判断你的任务里最大的不确定性是什么。',
        },
        {
          id: 'why-start-with-react',
          basis: 'inferred',
          question: '为什么多数生产系统应该从 ReAct 开始？',
          answer:
            '因为它**假设最少**，因而在你不确定的时候最不容易错。Plan-Execute 假设你能预先知道步骤，Reflexion 假设失败可以被自己识别，ToT 假设存在多个可枚举的候选路径 —— 这些假设一旦不成立，额外开销就白花了。\n\nReAct 的另一优势是**可观测**：每一步的 Thought / Action / Observation 都是显式的，出问题时你能看到它在哪一步跑偏。相比之下，一个花了 8 次调用做分支搜索的 ToT，失败时你很难判断是搜索策略的问题还是评估函数的问题。\n\n从最简单的开始，只在被实测证明不够用时才升级 —— 这与本站对「不要为未必存在的风险付出确定性代价」的一贯立场一致。',
        },
      ],
      resourceIds: ['anthropic-building-effective-agents', 'react-paper'],
    },
    {
      id: 'agent-paradigms/react-loop',
      chapterId: 'agent-paradigms',
      slug: 'react-loop',
      title: 'ReAct 的本质与失效模式',
      summary: '把推理外化成可观察的步骤 —— 这是它有效的原因，也是它失效的原因。',
      estimatedMinutes: 22,
      difficulty: 'intermediate',
      hasBody: true,
      status: 'drafting',
      keywords: ['react', 'loop', 'failure-modes'],
      checkpoints: [
        {
          id: 'why-react-works',
          basis: 'documented',
          question: 'ReAct 把「思考」写成显式文本，为什么这会有帮助？',
          answer:
            '原论文的论证是：把推理轨迹与动作交替生成，使模型能够**在做下一步之前先写下依据**，同时让外部观测有机会修正已经写下的推理 —— 两者互相补足。推理让动作有依据，观测让推理有事实纠错的机会。\n\n工程上还有一个额外收益：**这条轨迹是可读的**。相比一个直接输出最终答案的调用，ReAct 的中间步骤给了你调试的抓手 —— 你能看到它在哪一步、基于什么信息做了决定。',
          sourceIds: ['react-paper'],
        },
        {
          id: 'repeat-call-failure',
          basis: 'inferred',
          question: 'ReAct 循环最容易出现的失效模式是什么？',
          answer:
            '三种，而且都不难识别：\n\n1. **原地打转** —— 反复用同样的参数调同一个工具。第 4 章实测过这个模式：模型知道「失败了」但不知道「为什么失败」，于是重试。解法是把失败原因写清楚，并在代码层检测重复调用。\n2. **目标漂移** —— 几轮之后模型开始解决一个相近但不同的问题。上下文越长越容易出现，因为早期的目标被后来的细节稀释了。\n3. **过早收敛** —— 拿到第一个看起来合理的答案就停下，不再验证。它比前两种更难发现，因为输出看起来没问题。\n\n三者都指向同一个工程要求：**循环必须有外部的、可编程的终止与校验条件**，不能完全交给模型自己判断何时结束。',
        },
      ],
      resourceIds: ['react-paper', 'twelve-factor-agents'],
    },
    {
      id: 'agent-paradigms/plan-and-execute',
      chapterId: 'agent-paradigms',
      slug: 'plan-and-execute',
      title: '计划即契约，以及它为什么常常在第 3 步失效',
      summary: '先规划的全部价值来自「计划不会中途作废」这个假设 —— 而它会作废。',
      estimatedMinutes: 20,
      difficulty: 'intermediate',
      hasBody: true,
      status: 'drafting',
      keywords: ['planning', 'replanning'],
      checkpoints: [
        {
          id: 'when-planning-wins',
          basis: 'inferred',
          question: '什么条件下 Plan-Execute 明显优于 ReAct？',
          answer:
            '当**步骤可以在开始前确定，且步骤之间可并行**时。典型场景是报告生成、批量数据转换、代码审查流水线 —— 这类任务的子步骤彼此独立，先规划可以把它们并行派发，而 ReAct 的逐步决策会把本可以并行的部分串行化。\n\n另一个优势是**可审计与可干预**：计划是一份明确的清单，人能在执行前看一眼并改掉它。逐步决策的循环没有这个介入点。',
        },
        {
          id: 'why-plans-go-stale',
          basis: 'inferred',
          question: '为什么计划经常在执行到一半时失效？该怎么处理？',
          answer:
            '因为**规划时看到的世界与执行时不同**。计划基于当时的观测，而执行本身会改变环境（写入了数据、调用了有副作用的接口），后续步骤的前提可能已经不成立。第 3 步失效是最常见的形态 —— 前两步总是相对安全的探查，真正的改变从第三步开始。\n\n处理方式不是「计划得更好」，而是给计划留**重新规划的入口**：在每一步执行后检查前提是否仍成立，不成立就回到规划阶段重来。代价是你会多付一次规划成本，收益是不会带着过期前提一路跑到底。\n\n判断标准可以简化成一句：**如果执行过程中环境可能变化，就不要写「一次性计划」，要写「可重规划的计划」。**',
        },
      ],
      resourceIds: ['anthropic-building-effective-agents', 'open-deep-research'],
    },
    {
      id: 'agent-paradigms/reflection',
      chapterId: 'agent-paradigms',
      slug: 'reflection',
      title: '自我批评什么时候真的有用',
      summary: '「再读一遍自己的答案」几乎没用；「换一个方法重算一遍」有用。',
      estimatedMinutes: 23,
      difficulty: 'advanced',
      hasBody: true,
      status: 'drafting',
      keywords: ['reflexion', 'self-critique', 'evaluation'],
      checkpoints: [
        {
          id: 'effective-self-critique',
          basis: 'inferred',
          question: '什么样的自我批评是有效的？',
          answer:
            '关键区分是：**它有没有引入新的信息或新的计算**。\n\n本项目实测过一个看起来有效的例子：让模型检查一份被构造出来的错误答案，8/8 都捉住了、0/8 误报。但仔细看它的过程，它做的是**独立重算**一遍，然后对比结果 —— 那是一次新的计算，不是「审视自己刚才的思路」。\n\n反面是「请检查上面的答案有没有问题」这类指令：模型读到的是同一个上下文，没有任何新依据，于是它多半会给出「看起来没问题」。这也是本站实测里 self-consistency 多数投票收益为零的同一个根因 —— 当采样之间没有真正的分歧时，投票与自我审视都无事可做。\n\n可操作的判据：**自我批评必须附带一个能产生分歧的东西** —— 重新计算、外部校验器、检索回来的事实，或者一个明确到可机械检查的标准。',
        },
        {
          id: 'reflexion-cost',
          basis: 'documented',
          question: 'Reflexion 这类「失败后反思再重试」的方法，代价是什么？',
          answer:
            '它把每次尝试的成本乘以尝试次数，而且**只在失败可被自动识别时才有意义** —— 如果你无法判定一次尝试是否成功，反思循环就无从触发。\n\n原论文的设定正是如此：它依赖一个可用的成功信号（环境反馈或测试结果）来驱动语言化的反思。放到工程里，这意味着采用 Reflexion 的第一步不是写反思提示，而是**先有一个可靠的失败判定器**。没有它，你得到的只是更多次调用。',
          sourceIds: ['reflexion-paper'],
        },
      ],
      resourceIds: ['reflexion-paper', 'self-refine-paper'],
    },
    {
      id: 'agent-paradigms/choosing',
      chapterId: 'agent-paradigms',
      slug: 'choosing',
      title: '怎么选：先看失败代价，再看环境可变性',
      summary: '把范式选择还原成两个可回答的问题。',
      estimatedMinutes: 20,
      difficulty: 'intermediate',
      hasBody: true,
      status: 'drafting',
      keywords: ['selection', 'trade-offs'],
      checkpoints: [
        {
          id: 'two-questions',
          basis: 'inferred',
          question: '选范式时，最先该问哪两个问题？',
          answer:
            '**第一，这一步失败一次的代价有多大？** 代价低（能重试、人能看到）就不必上重装备；代价高（写库、下单、不可逆）就该把校验与人工确认做进流程，而不是指望模型自我审查。\n\n**第二，环境在执行过程中会不会变？** 会变就不适合一次性计划；不变则可以放心规划并并行。\n\n这两个问题的答案组合基本就决定了起点：可变 + 低代价 → ReAct；不变 + 高代价 → Plan-Execute 加显式检查点；低代价但要求准确率 → 加独立校验（而不是自我审视）。',
        },
        {
          id: 'paradigms-compose',
          basis: 'inferred',
          question: '范式之间是互斥的吗？',
          answer:
            '不是 —— 生产系统里它们通常是**嵌套**的。常见组合是：外层用 Plan-Execute 把任务拆成可并行的子任务，每个子任务内部跑一个 ReAct 循环，最后由一个独立的校验器（而不是模型自评）检查产出。\n\n但嵌套会带来一个必须正视的问题：**成本与延迟的乘积效应**。外层 5 个子任务、每个内部 6 轮、每轮还要加一次校验，就是 30 次以上的调用 —— 第 3 章那条「成本 = 内容 × 装载次数」的规律在这里同样适用。所以组合之前先算一遍最坏情况的调用数，这比事后优化便宜得多。',
        },
      ],
      resourceIds: ['anthropic-building-effective-agents', 'twelve-factor-agents'],
    },
  ],
  resourceIds: ['react-paper', 'reflexion-paper', 'self-refine-paper', 'anthropic-building-effective-agents', 'twelve-factor-agents'],
  backendMapping: {
    analogy: '选范式 ≈ 选并发模型：先想清楚失败代价与环境可变性，再决定是乐观重试还是先立计划',
    transferable: [
      '状态机与工作流编排的经验可以直接迁移',
      '「先测量再优化」的排查习惯：先定位是哪一类不确定性在伤害你',
      '幂等、重试、超时这些基础机制在每种范式里都同样必要',
    ],
    pitfalls: [
      '把 Tree-of-Thoughts / Reflexion 当默认选项：成本高，而收益在本项目中多次未能复现',
      '用「自我审视」替代「独立校验」：没有新信息的批评基本无效',
      '指望范式解决工具设计问题：工具描述写得差，换什么范式都救不回来',
      '忽略环境可变性，写出一次性计划然后带着过期前提跑到黑',
    ],
    cost: 'medium',
  },
  status: 'published',
  updatedAt: '2026-10-08',
  verifiedAt: '2026-10-08',
} satisfies Chapter;
