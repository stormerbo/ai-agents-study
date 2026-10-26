import type { Chapter } from '@/content/curriculum/schema';

export const chapter = {
  id: 'agent-paradigms',
  stageId: 'stage-3-orchestration',
  order: 10,
  title: 'Agent 范式',
  subtitle: 'ReAct、Plan-Execute 与它们的适用边界',
  summary:
    '本章区分控制流骨架、复核/搜索策略与多智能体拓扑，说明模型提议和宿主执行边界，并用任务级证据比较质量、成本与失效模式。',
  outcomes: [
    '能区分单次调用、workflow、ReAct、Plan-Execute 等控制流骨架与可叠加的复核策略',
    '能依据依赖、分支可确定性、反馈需求、失败代价与系统约束选择并验证范式',
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
      summary: '区分四种控制流骨架与 Reflection 复核策略，并指出宿主保留授权和执行责任。',
      estimatedMinutes: 20,
      difficulty: 'beginner',
      hasBody: true,
      status: 'drafting',
      keywords: ['react', 'plan-execute', 'taxonomy'],
      checkpoints: [
        {
          id: 'what-actually-differs',
          basis: 'inferred',
          question: '这些实现模式分别描述控制流、复核策略还是协作拓扑？宿主与模型各自负责什么？',
          answer:
            '先区分描述对象：单次调用、显式 workflow、ReAct 与 Plan-Execute 是控制流骨架；Reflection 是可叠加的复核策略；多智能体是协作拓扑。它们不是互斥的能力等级。\n\nReAct 让模型基于观察逐步提出动作或结束建议；Plan-Execute 让模型在执行前提出候选计划。两者都不绕过宿主：宿主负责身份授权、动作校验、工具执行、状态保存、预算和最终验收。Reflection 只有在利用任务反馈、明确标准或其他证据时，才可能被评估为有效复核；反思文本本身不能证明正确。多智能体也不会因上下文分开而自动获得质量或安全收益。选择应针对目标任务，比较准确性、失败类型、成本、延迟与系统复杂度。',
        },
        {
          id: 'why-start-with-react',
          basis: 'inferred',
          question: '在需求与环境不确定时，为什么可以先从最简单的闭环基线开始？',
          answer:
            '可以先从单次调用、确定性 workflow 或最小闭环开始，取决于是否需要工具与反馈。ReAct 能逐步根据观察决定动作，但不意味着它在任何不确定场景都最稳或最便宜。Plan-Execute 适用于计划可预先表示且执行前可校验的任务；Reflection 需要独立信号或新增证据。每一层都要用目标任务评估准确性、成本、延迟与失败模式，再决定是否增加复杂度。',
        },
      ],
      resourceIds: ['anthropic-building-effective-agents', 'react-paper', 'reflexion-paper', 'tree-of-thoughts-paper'],
    },
    {
      id: 'agent-paradigms/react-loop',
      chapterId: 'agent-paradigms',
      slug: 'react-loop',
      title: 'ReAct 的本质与失效模式',
      summary: '理解模型动作提议与宿主执行的边界，并用状态分类、整批校验和多重预算处理循环失效。',
      estimatedMinutes: 22,
      difficulty: 'intermediate',
      hasBody: true,
      status: 'drafting',
      keywords: ['react', 'loop', 'failure-modes'],
      checkpoints: [
        {
          id: 'why-react-works',
          basis: 'documented',
          question: 'ReAct 交替生成推理轨迹与动作提议，环境观察如何影响后续输出？宿主仍负责什么？',
          answer:
            '原论文将模型生成的推理轨迹与动作提议交替，让环境观察有机会影响后续输出。这里的“推理”是模型生成的可见文本，不等于可信或完整的内部思维；宿主仍负责解析动作、执行授权与工具调用、施加预算并决定何时继续或停止。工程上，可读轨迹能提供调试线索，但需要配合实际工具结果和宿主状态来解释。',
          sourceIds: ['react-paper'],
        },
        {
          id: 'repeat-call-failure',
          basis: 'inferred',
          question: 'ReAct 循环最容易出现的失效模式是什么？',
          answer:
            '三类值得监控的失败：\n\n1. **原地打转** —— 模型可能重复提出相同工具调用。第 4 章有一个此类观测；宿主应把错误结果回传清楚，并可用重复调用检测与预算上限控制风险。\n2. **目标漂移** —— 多轮后输出可能偏离原目标；上下文变长是一个待验证的风险因素，需结合目标检查点判断。\n3. **过早收敛** —— 模型可能在看似合理时停止，但是否缺少验证取决于任务与验收条件。\n\n这些风险说明**宿主需要可编程的终止、授权与结果校验条件**；模型输出的结束信号只是输入之一，不能作为唯一控制条件。',
        },
      ],
      resourceIds: ['react-paper', 'anthropic-stop-reasons', 'twelve-factor-agents'],
    },
    {
      id: 'agent-paradigms/plan-and-execute',
      chapterId: 'agent-paradigms',
      slug: 'plan-and-execute',
      title: '计划是候选执行图，不是不可变契约',
      summary: '区分静态计划、代码条件路由与模型重规划；学习校验依赖、完整性、实时授权与过期前提。',
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
            '静态计划适合步骤与参数可在执行前表达并校验的部分；若分支条件能从已观察状态机械计算，可由宿主代码路由。Plan-Execute 不保证并行、准确或成本更低。应在相同任务与验收标准下比较端到端结果、工具轨迹、失败类型和资源用量。',
        },
        {
          id: 'why-plans-go-stale',
          basis: 'inferred',
          question: '为什么计划经常在执行到一半时失效？该怎么处理？',
          answer:
            '计划依赖生成时的状态，数据、权限或外部副作用可能在执行过程中改变前提。执行前或每个敏感步骤前，都应检查该步骤依赖的版本、授权和业务条件；发现失效时暂停后续步骤，对已发生的副作用先对账，再决定是否重规划。是否每步重规划由状态变化风险、调用预算与恢复语义决定，并非所有任务都要为每一步额外调用模型。',
        },
      ],
      resourceIds: ['anthropic-building-effective-agents', 'langgraph-graph-api', 'open-deep-research'],
    },
    {
      id: 'agent-paradigms/reflection',
      chapterId: 'agent-paradigms',
      slug: 'reflection',
      title: '自我复核何时有用，何时只是多一次调用',
      summary: '区分自评、反馈修订、Reflexion 与 self-consistency；用独立验收控制复核与交付。',
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
            '要区分“找出分歧”和“证明答案正确”。提供新证据、使用不同计算方法或采样多个候选，都可能让系统发现不一致；但不一致本身不是纠错成功的证明。若要声称修订正确，需要任务级 grader、确定性校验或经校准的人类评审。\n\n2026-10-08 的历史摘要称，模型检查手工构造的错答时捉错 8/8、误报 0/8；逐次响应、模型快照和评分过程未归档，不能独立复算，也不足以估计对未知错误的审阅能力。第 2 章 self-consistency 的摘要属于另一组采样实验，不可据此认定两者有相同机制。\n\n可操作的判据：**先定义独立验收信号，再决定是否需要模型提出修订**。例如算术重算、结构校验、外部事实核对、代码测试或盲评；信号本身的来源和覆盖范围也要记录。',
        },
        {
          id: 'reflexion-cost',
          basis: 'documented',
          question: 'Reflexion 这类「失败后反思再重试」的方法，代价是什么？',
          answer:
            '后续尝试通常会新增模型调用和上下文处理；具体 token、费用与延迟取决于每轮请求内容及 provider 计量，不能简化成固定倍数。原论文使用环境反馈信号驱动语言化反思并用于后续尝试。工程上应先定义任务成功条件及失败反馈如何产生；没有可用反馈时，反思循环无法知道何时或如何更新，但反馈也不自动保证后续尝试成功。',
          sourceIds: ['reflexion-paper'],
        },
      ],
      resourceIds: ['reflexion-paper', 'self-refine-paper', 'anthropic-demystifying-evals'],
    },
    {
      id: 'agent-paradigms/choosing',
      chapterId: 'agent-paradigms',
      slug: 'choosing',
      title: '怎么选：风险边界与下一步决策',
      summary: '分开评估失败风险与控制流，按目标任务验证最简单可行的候选。',
      estimatedMinutes: 20,
      difficulty: 'intermediate',
      hasBody: true,
      status: 'drafting',
      keywords: ['selection', 'trade-offs'],
      checkpoints: [
        {
          id: 'two-questions',
          basis: 'inferred',
          question: '选范式时，如何分别评估失败风险与下一步决策？',
          answer:
            '**第一，这一步失败一次的代价有多大？** 代价与授权、可逆性、影响范围及恢复能力共同决定校验、审批、拒绝和对账策略；不能简单用“不可逆”推导一律人工确认。\n\n**第二，下一步的条件与参数由谁、依据什么决定？** 可预先表示且经校验的步骤可考虑静态计划；可从中间状态计算的分支可由代码路由；需要模型根据新观察作语义判断时，再评估 ReAct 或重规划。顺序是分析方法，不是技术限制。\n\n可先用这两个问题提出候选方案，再由任务评测验证：可变 + 需要模型根据反馈决策 → ReAct；有条件但路由可确定 → 条件 workflow；计划可预先完整表达 → Plan-Execute 加执行前校验；准确性要求高 → 加独立校验与验收条件。失败代价另行决定授权、审批、幂等与恢复策略。',
        },
        {
          id: 'paradigms-compose',
          basis: 'inferred',
          question: '范式之间是互斥的吗？',
          answer:
            '不是，范式可以组合，但生产系统是否需要嵌套取决于任务。组合时应分别估算模型往返、工具调用、代码校验和并行度；例如每个子任务最多 6 次模型往返、5 个子任务并发时，上限是 30 次模型往返（不含重试），但墙钟延迟不必是串行 30 轮，成本也不能由调用数单独推出。应在明确预算与故障语义后测量最坏情况。',
        },
      ],
      resourceIds: ['anthropic-building-effective-agents', 'langgraph-graph-api', 'twelve-factor-agents'],
    },
  ],
  resourceIds: [
    'react-paper',
    'reflexion-paper',
    'self-refine-paper',
    'anthropic-building-effective-agents',
    'twelve-factor-agents',
    'tree-of-thoughts-paper',
  ],
  backendMapping: {
    analogy: '控制流设计 ≈ 为状态机定义转移和守卫；模型可以提出下一步，宿主负责授权、执行与终止',
    transferable: [
      '状态机与工作流编排的经验可以直接迁移',
      '「先测量再优化」的排查习惯：先定位是哪一类不确定性在伤害你',
      '幂等、重试、超时这些基础机制在每种范式里都同样必要',
    ],
    pitfalls: [
      '仅凭 Tree-of-Thoughts、Reflexion 或 Multi-Agent 等名称选择方案；先看它们解决的任务问题，再按预算和验收条件实测',
      '用「自我审视」替代「独立校验」：没有新信息的批评基本无效',
      '指望范式解决工具设计问题：工具描述写得差，换什么范式都救不回来',
      '忽略环境可变性，写出一次性计划然后带着过期前提跑到黑',
    ],
    cost: 'medium',
  },
  status: 'published',
  updatedAt: '2026-10-21',
  verifiedAt: '2026-10-21',
} satisfies Chapter;
