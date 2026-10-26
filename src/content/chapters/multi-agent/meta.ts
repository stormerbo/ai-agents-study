import type { Chapter } from '@/content/curriculum/schema';

export const chapter = {
  id: 'multi-agent',
  stageId: 'stage-3-orchestration',
  order: 12,
  title: '多智能体',
  subtitle: '什么时候值得那份成本',
  summary:
    '多智能体通过任务拆分、上下文边界或并行执行等设计改变工作方式，也增加调用、协调和交接成本。本章按同任务的质量、用量、延迟与失败边界比较是否值得。',
  outcomes: [
    '能算出多智能体的成本量级，而不是凭感觉判断「贵不贵」',
    '能评估上下文隔离、任务分工与并行执行在目标工作负载中的收益和代价',
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
          basis: 'documented',
          sourceIds: ['anthropic-building-effective-agents', 'anthropic-multi-agent-research'],
          question: '按本文工作定义，主管协调、固定 workflow 与对等辩论的控制流有什么区别？',
          answer:
            '主管协调者拆分并汇总任务；固定 workflow 的步骤由应用预先规定；对等辩论让多个参与者交换意见，再由规则或人工聚合。Anthropic 文档区分预定 workflow 与由模型动态控制过程的 agent，并列出 orchestrator-worker 模式；Anthropic 研究系统是一个具体实现案例。这些材料不提供行业普及率或拓扑稳定性比较。',
        },
        {
          id: 'topology-communication-scale',
          basis: 'inferred',
          question: '在明确的消息假设下，中心协调和完全互联的通信规模如何估算？',
          answer:
            '若中心节点有 W 个工人，并向每人派发一次任务、收回一次结果，则有约 2W 条有向消息和 W 条工人-主管通信边，均为 O(W)。若有 P 个参与者的完全互联图中每一对至少通信一次，则无向参与者对数为 P(P−1)/2，即 O(P²)；稀疏图、单向链路、多轮对话会改变边数与消息数。通信边和消息数都不等于 API 调用数；一次请求可包含多条消息。并行收益还依赖任务独立、实际并发、队列和限流，拓扑本身不保证延迟或质量收益。',
        },
        {
          id: 'swarm-caveat',
          basis: 'inferred',
          question: '无中心协调的交接网络可能出现哪些风险，怎样控制？',
          answer:
            '如果参与者共享状态不完整、转交条件含糊或缺少任务终态，可能出现循环交接、无人汇总、重复调用或结果冲突；这些是依拓扑和实现而定的风险，不是 swarm 的必然属性。应记录 handoff 边与任务状态，设预算/截止时间，定义终结与失败状态，并对重复动作和外部副作用做幂等保护。自由交接也可能是有意的设计，是否需要中心协调要按控制责任、可观测性和任务质量评估。',
        },
      ],
      resourceIds: ['anthropic-multi-agent-research', 'anthropic-building-effective-agents', 'deepseek-anthropic-api', 'anthropic-stop-reasons'],
    },
    {
      id: 'multi-agent/cost-model',
      chapterId: 'multi-agent',
      slug: 'cost-model',
      title: '多 Agent 成本估算：从输入量到账单',
      summary: '同一组多智能体与单 agent 的历史 token 摘要会随对照组和任务构造变化，不能外推为普遍成本倍率。',
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
          answer: '先区分 token volume 与账单。Token volume 要汇总两种方案每一次调用的输入和输出；费用还需按 provider/model 对新输入、缓存读取、缓存写入、输出分别计价。字段口径与价格必须针对当前 endpoint 核对，不能把缓存字段缺失当成零。历史摘要记录了 20 篇检索任务中主上下文峰值 6816→1258、总 token 25913→9182，以及另一对照下 68,548 对 8,430（8.1×）；这些汇总缺少可用的逐次请求/响应、完整模型快照和评分记录，不能独立复算，也不构成普遍规律。比较时应使用同一任务集与验收标准，记录全部调用的输入、输出、重试、停止原因与端到端结果，再按目标 endpoint 的当前价格逐项计算。',
        },
        {
          id: 'when-multiagent-cheaper',
          basis: 'inferred',
          question: '什么情况下多智能体反而更便宜？',
          answer: '当**单 agent 会在多轮中反复携带大量历史，而可拆分的子任务只需返回小型、可验证的结果**时，多智能体可以成为降低主上下文用量的候选方案；这不是费用更低的保证。需要把所有 worker、supervisor 与重试的输入/输出 usage、摘要验证成本和检索/调度开销都计入，再按当前 endpoint 计价。摘要可能丢信息；如果主 agent 后续还需要原始资料，重新检索和转发会增加成本；如果并行没有实际发生，也不能声称延迟下降。用代表性任务比较总账单、延迟分布和任务质量后，才能判断是否值得。',
        },
      ],
      resourceIds: ['anthropic-multi-agent-research', 'anthropic-context-engineering', 'claude-prompt-caching', 'deepseek-anthropic-api', 'anthropic-stop-reasons'],
    },
    {
      id: 'multi-agent/isolation-is-the-point',
      chapterId: 'multi-agent',
      slug: 'isolation-is-the-point',
      title: '上下文隔离的收益与边界',
      summary: '上下文隔离是一个可评估的设计机制；效果取决于输入边界、任务分工、验证与运行时传递。',
      estimatedMinutes: 20,
      difficulty: 'intermediate',
      hasBody: true,
      status: 'drafting',
      keywords: ['context-isolation', 'attention'],
      checkpoints: [
        {
          id: 'isolation-as-design-option',
          basis: 'inferred',
          question: '上下文隔离可能改变什么，哪些结果需要实际测量？',
          answer:
            '宿主为不同子任务提供不同材料时，可以减少某个调用接收的无关上下文；如果共享信息被重复装载，或主管需要更多回传/摘要，总用量也可能上升。隔离对窗口使用、质量、并行时间和失败传播的净效果取决于任务与实现，应在同一任务集上比较，不把“上下文更小”自动等同于更好。',
        },
        {
          id: 'anthropic-browsecomp-scope',
          basis: 'documented',
          sourceIds: ['anthropic-multi-agent-research'],
          question: 'Anthropic 关于 token 用量解释 BrowseComp 性能方差的结果，能支持什么结论？',
          answer:
            'Anthropic 2025 年 Research 系统文章称，在其 BrowseComp 分析中，token usage、tool calls 与 model choice 三因素合计解释了 95% 的性能方差，token usage 单独解释 80%。这是该评测与其分析的报告值，不是对上下文隔离的因果消融，也不能推出隔离是所有多智能体系统的主要或唯一收益。',
        },
        {
          id: 'historical-isolation-token-summary',
          basis: 'unverified',
          question: '本站 20 篇材料的隔离/单流程 token 摘要能证明什么？',
          answer:
            '历史摘要列出最大请求 input 6,816 与 1,258 token，以及全流程总 token 25,913 与 9,182；原始请求/响应、逐次 usage、样本映射、模型指纹和 scorer 未归档。当前不能独立确认数值分别对应哪条路线，也不能推出质量等价、窗口余量或账单变化。',
          note: '这是 2026-10-08 附近的汇总记录；缺少逐次原始请求/响应、准确 endpoint/model、usage 口径、任务映射和评分器，无法重放或独立复算。',
        },
      ],
      resourceIds: ['anthropic-multi-agent-research', 'deepseek-anthropic-api', 'anthropic-stop-reasons'],
    },
    {
      id: 'multi-agent/failure-modes',
      chapterId: 'multi-agent',
      slug: 'failure-modes',
      title: '边界上的三种失败模式',
      summary: '交接可能遗漏信息、掩盖口径冲突或放大汇总负担；风险取决于任务、拓扑与交接契约。',
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
            '可检查三类风险，但它们不是穷尽清单，也不是所有拓扑的必然故障：\\n\\n1. **交接遗漏或压缩失真。** 历史记录曾报告 8 条要点压成 7 条、漏掉生产写入约束；原始请求/响应与评分未留存，不能据此估计发生率。本章旧脚本只用“生产库”子串判分，不能确认语义遵守，所以撤回“两边都存活/未复现”的结论。\\n2. **口径或证据不一致。** 独立 worker 可能依据不同范围、时间窗或分母回答不同问题；是否冲突需对齐指标与原始证据，不能凭模型自报裁决。\\n3. **汇总资源成为瓶颈。** 多个 worker 的回传、重试和证据可能增加主管的输入、延迟与成本；是否抵消隔离或并行收益，要用同任务、同验收标准和完整全链路 usage 测量。',
        },
        {
          id: 'structured-handoff',
          basis: 'inferred',
          question: '针对上面三种失败，回传格式该怎么设计？',
          answer:
            '让 worker 返回包含 task_id、状态、必需事实 ID、来源引用、失败信息与未完成项的结构化结果，并由宿主校验。schema 只能约束可解析的形状/类型，不能证明事实、来源或业务语义正确；高风险硬约束还需权威证据检查和宿主授权。保存原始材料或可回查引用，定义缺项、冲突、拒绝和未知状态的处理路径。',
        },
        {
          id: 'integer-count-validation',
          basis: 'documented',
          sourceIds: ['python-built-in-types'],
          question: '为什么率值示例要显式排除 bool 类型？',
          answer:
            'Python 文档将 bool 定义为 int 的子类型，因此 isinstance(True, int) 为真。计数数据若要求整数，应同时排除 bool；否则 True/False 会悄悄作为 1/0 参与汇总。',
        },
      ],
      resourceIds: ['anthropic-multi-agent-research', 'anthropic-context-engineering', 'anthropic-structured-outputs'],
    },
    {
      id: 'multi-agent/alternatives',
      chapterId: 'multi-agent',
      slug: 'alternatives',
      title: '先别用：三个替代方案',
      summary: '在引入协调成本前，先比较上下文整理、工具调用与 workflow 等候选方案。',
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
            '三类候选方案值得先与单 agent 基线比较：\n\n1. **改进上下文组织** —— 检查无关材料、历史与工具回填是否占用上下文；用任务级评分确认压缩或筛选没有丢失关键信息。\n2. **按需检索** —— 对比预加载与检索方案的端到端质量、输入/输出用量和延迟。第 3 章历史实验的交叉点受限于小样本与不完整原始记录，不能当作通用阈值。\n3. **确定性代码做编排，模型只做判断/生成** —— 固定步骤可评估由 workflow/host 控制；具体成本和可靠性仍取决于工作负载与实现，不能笼统断言一定比 supervisor 更便宜。\n\n共同点是：**先建立同任务的基线和验收口径，再选更简单的候选方案做配对验证。**',
        },
        {
          id: 'when-multiagent-justified',
          basis: 'inferred',
          question: '什么信号出现时，才说明多智能体是合理的？',
          answer:
            '多智能体是否合理要看同一任务上的净收益，而不是某个单一信号：任务能否拆解、子任务是否提供互补证据/隔离、调度能否获得真实并行，以及质量、覆盖、风险或延迟的改善是否足以抵偿新增调用、输出、协调和故障处理成本。角色名本身不能保证能力专门化；单 agent 当前成功率只描述基线，不能推出多智能体可达到的上限。应使用代表性任务、预先定义的 rubric 与产品门槛做配对评估。',
        },
      ],
      resourceIds: ['twelve-factor-agents', 'anthropic-building-effective-agents'],
    },
    {
      id: 'multi-agent/failure-modes-collaboration',
      chapterId: 'multi-agent',
      slug: 'failure-modes-collaboration',
      title: '协作层的三种失败：并发、趋同、级联',
      summary: '检查共享状态更新、观点覆盖与来源依赖；这些是按任务验证的风险线索，不是 agent 的必然故障。',
      estimatedMinutes: 26,
      difficulty: 'advanced',
      hasBody: true,
      status: 'published',
      keywords: ['concurrency', 'homogenization', 'cascade', 'multi-agent-failure'],
      checkpoints: [
        {
          id: 'concurrent-write',
          basis: 'documented',
          sourceIds: ['postgres-row-locking-18', 'postgres-insert-18'],
          question: '多个执行单元共享可变状态时，怎样避免读-改-写丢失更新？',
          answer:
            '先定位共享状态与写入边界。PostgreSQL 文档说明行级锁会阻塞冲突更新，`INSERT ... ON CONFLICT DO UPDATE` 在其约束范围内提供原子冲突处理；隔离级别也可能产生需要整笔事务重试的序列化错误。选择原子更新、唯一约束、锁或版本/CAS 要依据真实存储和业务不变量测试；进程内 mutex 不覆盖其他进程，模型调用期间长时间持锁也可能造成阻塞。本文屏障示例只稳定重现 Python 内存 lost update，不代表生产 agent 系统的发生率。',
        },
        {
          id: 'homogenization',
          basis: 'documented',
          sourceIds: ['eacl-evaluating-diversity-metrics'],
          question: '为什么词面差异不能直接证明观点多样？',
          answer:
            'Jaccard 等词面指标衡量所选 token 集合的重合，不直接测立场、证据覆盖或任务质量。Tevet 与 Berant 的研究显示，在其 NLG 任务与评估设置中，人类判断内容多样性优于自动指标；这不是所有指标或任务的统一排序。本节 2026-10-12 的 0.24 历史均值缺少原始输出、分词器和 scorer，不能复算；把观点压成标签也需定义主张轴并检查编码一致性。要评估多 agent 是否带来有用多样性，应先给出目标 rubric，再用代表性任务与单 agent/替代分工做配对比较，并披露评估器限制。',
        },
        {
          id: 'lineage-and-cascade',
          basis: 'inferred',
          question: '来源与派生关系的记录可以证明什么，不能证明什么？',
          answer:
            '稳定记录来源 ID、as_of、转换规则版本和 derived_from 边，可以帮助找出下游依赖链、缺失引用与过期候选；完整图本身不证明来源真实、新鲜或解释正确，也不代表最终副作用获准。按业务设定 freshness 策略并重新检查权威来源；用代码验证图结构，用任务 rubric 验证语义，用宿主策略授权动作。',
        },
      ],
      resourceIds: ['anthropic-multi-agent-research', 'open-deep-research', 'postgres-row-locking-18', 'postgres-insert-18', 'eacl-evaluating-diversity-metrics', 'opentelemetry-genai-semconv'],
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
      '把「多个角色」或「上下文隔离」视为自动提升质量的保证',
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
