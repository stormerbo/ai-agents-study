import type { Chapter } from '@/content/curriculum/schema';

export const chapter = {
  id: 'multi-agent',
  stageId: 'stage-3-orchestration',
  order: 12,
  title: '多智能体',
  subtitle: '什么时候值得那份成本',
  summary:
    '多智能体的收益与代价都来自同一件事：上下文被切开了。切开意味着更干净的注意力，也意味着信息在边界处被有损压缩。这一章算清这笔账，并给出「先别用」的三个替代方案。',
  outcomes: [
    '能算出多智能体的成本量级，而不是凭感觉判断「贵不贵」',
    '能说清它真正的收益来自上下文隔离，而不是「多个角色协作」',
    '能识别它在边界上的三种失败模式，并设计出对应的结构化回传',
  ],
  depth: 'deep',
  difficulty: 'advanced',
  estimatedMinutes: 95,
  tags: ['multi-agent', 'orchestration', 'cost'],
  prerequisiteIds: ['agent-loop', 'context-engineering'],
  lessons: [
    {
      id: 'multi-agent/topologies',
      chapterId: 'multi-agent',
      slug: 'topologies',
      title: '三种拓扑：谁向谁汇报',
      summary: 'supervisor / pipeline / swarm —— 差别在控制权放在哪一层。',
      estimatedMinutes: 18,
      difficulty: 'intermediate',
      hasBody: true,
      status: 'drafting',
      keywords: ['supervisor', 'pipeline', 'swarm'],
      checkpoints: [
        {
          id: 'topology-difference',
          basis: 'inferred',
          question: 'supervisor 与 pipeline 两种拓扑，控制权的差别在哪？',
          answer:
            '**supervisor** 把控制权留在一个中心 agent 手里：它决定派谁去做、做几轮、结果够不够。子 agent 是「工具」，不掌握流程。好处是全局可控、好加预算；坏处是中心 agent 的上下文会成为瓶颈，而且它必须理解所有子任务的产出。\n\n**pipeline** 把控制权写死在流程里：A 的输出喂给 B，B 喂给 C。没有任何一层在「决定要不要继续」，所以它其实是**确定性工作流**，只是每个环节由模型执行 —— 更接近第 0 章讲的 workflow 而不是 agent。它最稳、最便宜，代价是流程本身不能自适应。\n\n选哪个，本质是问「这个任务的步骤是固定的，还是需要根据中间结果决定」。',
        },
        {
          id: 'swarm-caveat',
          basis: 'inferred',
          question: 'swarm 式的「agent 之间自由转交」在什么情况下会失控？',
          answer:
            '当**没有任何一层掌握全局状态**时。每个 agent 只看得到自己接到的片段，于是会出现两种典型失控：**互相转交**（A 认为该 B 做、B 认为该 A 做，来回几轮）和**无人收口**（所有子任务都完成得不错，但没有人负责给出最终答案）。\n\n可控的做法是给自由转交加上**外部约束**：转交次数上限、必须有一个终结节点、以及每一次转交都记录原因。没有这些，你得到的是一个行为不可预测、成本不可预估的系统。',
        },
      ],
      resourceIds: ['anthropic-multi-agent-research', 'anthropic-building-effective-agents'],
    },
    {
      id: 'multi-agent/cost-model',
      chapterId: 'multi-agent',
      slug: 'cost-model',
      title: '成本模型：内容 × 装载次数',
      summary: '同一个问题「多智能体贵不贵」，换个对照组能把答案从 8 倍变成 0.4 倍。',
      estimatedMinutes: 22,
      difficulty: 'advanced',
      hasBody: true,
      status: 'drafting',
      keywords: ['cost', 'comparison'],
      checkpoints: [
        {
          id: 'cost-formula',
          basis: 'inferred',
          question: '多智能体的成本该怎么算？',
          answer:
            '先区分 token volume 与账单。Token volume 要汇总两种方案每一次调用的输入和输出：worker 的 N 份输出要全部计入，主管接收 worker 回传的输入与自己的最终输出也要计入。实际费用还要按 provider/model 的新输入、缓存读取、缓存写入、输出价格分别加权；不能只把共享上下文乘以调用次数，也不能假定缓存命中。\n\n本项目的观测值说明结论依赖对照：20 篇检索任务里，隔离方案的主上下文峰值从 6816 降到 1258、总 token 从 25913 降到 9182（省了）；把对照换成「共享背景只装载一次」时，8 个子 agent 各装一遍为 68548 对 8430（贵 8.1 倍）。这些结果各自只适用于对应工作负载与统计口径。\n\n比较时应问：**两种方案全部请求的 token volume 和按当前计价规则加权的费用各是多少？**',
        },
        {
          id: 'when-multiagent-cheaper',
          basis: 'inferred',
          question: '什么情况下多智能体反而更便宜？',
          answer:
            '当**单 agent 需要把大量内容留在上下文里反复计费**时。典型是长检索任务：单 agent 每查一批资料就把它留在历史里，之后每一轮都重发一遍；而子 agent 查完只回传一段摘要，原始资料随子 agent 的上下文一起消失。\n\n代价被转移到了别处：你换来了**摘要的信息损失**（下一节展开）。所以这个「更便宜」是有条件的 —— 只有在「原始资料没必要留在主上下文里」时才成立。如果主 agent 后续还需要反复引用原始内容，隔离反而会让你反复重取。',
        },
      ],
      resourceIds: ['anthropic-multi-agent-research', 'anthropic-context-engineering'],
    },
    {
      id: 'multi-agent/isolation-is-the-point',
      chapterId: 'multi-agent',
      slug: 'isolation-is-the-point',
      title: '真正的收益是上下文隔离',
      summary: '不是「多个角色更聪明」，而是「每个角色只看到自己该看的」。',
      estimatedMinutes: 20,
      difficulty: 'intermediate',
      hasBody: true,
      status: 'drafting',
      keywords: ['context-isolation', 'attention'],
      checkpoints: [
        {
          id: 'why-isolation-helps',
          basis: 'inferred',
          question: '多智能体的收益，本质上来自哪里？',
          answer:
            '来自**注意力被分开了**，而不是来自「协作」。每个子 agent 的上下文里只有与它那部分任务相关的内容，于是它不必在被稀释的上下文里做判断。\n\n这一点有实证支撑：Anthropic 在多智能体研究系统的复盘里给出的归因是 —— 在 BrowseComp 这个评测上 **token 用量单独解释了 80% 的性能方差**，多智能体有效主要是因为它们把更多 token 花在了并行推理上，而不是因为某种更聪明的协作机制。\n\n推论很实用：**如果你只是把同一个上下文复制给几个角色，那不叫隔离，那叫重复计费。** 隔离的前提是每个子 agent 的上下文确实不同。',
        },
      ],
      resourceIds: ['anthropic-multi-agent-research'],
    },
    {
      id: 'multi-agent/failure-modes',
      chapterId: 'multi-agent',
      slug: 'failure-modes',
      title: '边界上的三种失败模式',
      summary: '信息在主 agent 与子 agent 之间被有损压缩，而损失对调用方不可见。',
      estimatedMinutes: 22,
      difficulty: 'advanced',
      hasBody: true,
      status: 'drafting',
      keywords: ['failure-modes', 'handoff'],
      checkpoints: [
        {
          id: 'three-boundary-failures',
          basis: 'inferred',
          question: '多智能体在边界上最容易出哪三种问题？',
          answer:
            '1. **摘要丢信息而主 agent 无法察觉。** 第 3 章实测过：压缩会丢掉关键约束，而且在无指令时模型会把「摘要里没写」当作「不允许」直接给出结论。子 agent 的摘要就是主 agent 的事实来源，一旦漏掉硬约束，主 agent 连「原本有什么」都不知道。\n2. **子 agent 的失败被压缩成一句「没找到」。** 内部调了 5 次工具全超时，到摘要里只剩结论；主 agent 看到「无相关信息」，于是再派一个子 agent 做同一件事 —— 你付了两次钱，还看不出这是重试。\n3. **并行子 agent 之间无法协商。** 各自独立工作、各自写摘要，冲突到汇总时才暴露，而主 agent 手里没有裁决依据。',
        },
        {
          id: 'structured-handoff',
          basis: 'inferred',
          question: '针对上面三种失败，回传格式该怎么设计？',
          answer:
            '让子 agent 返回**结构化**结果，而不是一段散文摘要。至少要能回答三个问题：「你做了什么」「哪一步失败了、为什么」「哪些信息没有查到」。\n\n这三项分别对应上面三种失败：第二项让失败不再被折叠成「没找到」，第三项让主 agent 能区分「确实没有」与「查询失败」—— 而这两种情况需要完全不同的下一步动作。第一项则是可观测性的基础。\n\n顺带一个与第 5 章一致的提醒：**结构化回传本身就是一次抽取任务**，所以它同样需要 schema 与校验，别假设子 agent 一定会老实填。',
        },
      ],
      resourceIds: ['anthropic-multi-agent-research', 'anthropic-context-engineering'],
    },
    {
      id: 'multi-agent/alternatives',
      chapterId: 'multi-agent',
      slug: 'alternatives',
      title: '先别用：三个替代方案',
      summary: '在付出协调成本之前，先试试更便宜的三种做法。',
      estimatedMinutes: 18,
      difficulty: 'intermediate',
      hasBody: true,
      status: 'drafting',
      keywords: ['alternatives', 'simplicity'],
      checkpoints: [
        {
          id: 'cheaper-alternatives',
          basis: 'inferred',
          question: '在引入多智能体之前，有哪些更便宜的做法值得先试？',
          answer:
            '三个，按成本从低到高：\n\n1. **改进上下文组织** —— 单 agent 之所以「什么都做不好」，常常是因为无关内容挤占了注意力。先把无关内容移出去，可能就不需要拆分了。\n2. **把检索做成工具，而不是预加载** —— 第 3 章测过：需要的资料占比低于 20% 时，按需取比全量预加载更省。\n3. **确定性代码做编排，模型只做决策点** —— 也就是 12-Factor Agents 的立场：把「按顺序做这几件事」写成代码，只在真正需要判断的地方调用模型。这通常比让一个 supervisor agent 来做同样的调度更便宜、更可测。\n\n共同点是：**先用你的后端经验解决问题，再考虑上多智能体。**',
        },
        {
          id: 'when-multiagent-justified',
          basis: 'inferred',
          question: '什么信号出现时，才说明多智能体是合理的？',
          answer:
            '两个信号同时出现：**任务可以真正并行**（子任务之间没有顺序依赖），以及**每个子任务需要大量相互独立的上下文**（把它们塞进一个上下文会互相干扰）。\n\n反过来，以下情况都不构成理由：「看起来很酷」「论文里说效果好」「需要不同角色的人设」。最后一条尤其要警惕 —— 角色设定不会改变模型的推理能力，只会多花一次调用。\n\n还有一个务实的判据：**先量单 agent 的失败率。** 如果它已经有 90% 的成功率，多智能体最多把上限拉到 100%，却要多付几倍成本；上面那三个替代方案在这个区间里的性价比更高。',
        },
      ],
      resourceIds: ['twelve-factor-agents', 'anthropic-building-effective-agents'],
    },
    {
      id: 'multi-agent/failure-modes-collaboration',
      chapterId: 'multi-agent',
      slug: 'failure-modes-collaboration',
      title: '协作层的三种失败：并发、趋同、级联',
      summary: '8 个 agent 并发读改写，期望 8 实际 1 —— 而且没有任何报错。',
      estimatedMinutes: 26,
      difficulty: 'advanced',
      hasBody: true,
      status: 'published',
      keywords: ['concurrency', 'homogenization', 'cascade', 'multi-agent-failure'],
      checkpoints: [
        {
          id: 'concurrent-write',
          basis: 'documented',
          sourceIds: ['anthropic-multi-agent-research'],
          question: '为什么「读-改-写」在 agent 场景下比在普通程序里更容易出问题？',
          answer:
            '因为**冲突窗口的长度 = 思考时间**，而 agent 的思考时间比普通程序长几个数量级（一次模型调用几百毫秒到几秒）。实测：8 个 agent 各做一次读-改-写，期望结果 8，**实际结果是 1 —— 丢失 7 次更新，而且没有任何报错**，每个 agent 都报告成功。这类失败难查是因为三个性质叠加：**静默**（无异常）、**非确定**（换时间跑丢失次数不同）、**业务层不可见**（你看到的是最终值不对，不是某次更新失败）。排查时最容易走错的方向是去查模型「是不是它算错了」，而真实原因在它外面。判据：**如果同样输入重跑得到不同结果，先怀疑并发。** 缓解用锁、单写者、或乐观并发（版本号）—— 这是三种协作失败里唯一有成熟标准解法的。',
        },
        {
          id: 'homogenization',
          basis: 'inferred',
          question: '怎么判断多个 agent 是否同质趋同？本节的第一版测量错在哪？',
          answer:
            '第一版用 **Jaccard 相似度**衡量，量出两两均值只有 0.24（很低），差点得出「没有趋同」的结论。但那个指标测的是**用词重叠**，而趋同发生在**结论层**。读五条输出的第一条就会发现，五个方案说的其实是同一件事（「agent 只给建议，最终决策留给人」），只是措辞不同。**「表述多样」和「观点多样」是两件事。** 修正后的判据是：**把每个 agent 的结论压成一句话，再比那五句话。** 如果它们指向同一个方案，那这个多视角就没带来多样性，只是带来五份改写。想要真的多样性只有两条路：**给不同的上下文**（不同资料切片），或者**给不同的目标或角色**（一个专门找失败场景，一个专门找成本问题）。差异必须来自输入或角色，不能指望来自模型。',
        },
      ],
      resourceIds: ['anthropic-multi-agent-research', 'open-deep-research'],
    },
  ],
  resourceIds: [
    'anthropic-multi-agent-research',
    'anthropic-context-engineering',
    'anthropic-building-effective-agents',
    'twelve-factor-agents',
    'openhands',
  ],
  backendMapping: {
    analogy: '多智能体 ≈ 把一个大服务拆成微服务：边界带来隔离与并行，也带来跨边界的契约与协调成本',
    transferable: [
      '服务拆分的判断经验：什么时候该拆、拆完怎么保证不重复调用',
      '边界契约设计：跨进程传结构化数据，而不是传自由文本',
      '成本归因：按调用链统计 token，否则算不出是哪个环节贵',
    ],
    pitfalls: [
      '把「多个角色」当成收益来源：真正起作用的是上下文隔离',
      '不做对照就下结论「多智能体更贵/更便宜」—— 换个对照答案会翻转',
      '让子 agent 用散文摘要回传：信息在该处被有损压缩且不可见',
      '没有转交次数上限与终结节点，让自由转交失控',
    ],
    cost: 'high',
  },
  status: 'published',
  updatedAt: '2026-10-08',
  verifiedAt: '2026-10-08',
} satisfies Chapter;
