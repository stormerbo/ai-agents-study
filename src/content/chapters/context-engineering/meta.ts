import type { Chapter } from '@/content/curriculum/schema';

/**
 * 章 3。这一章是阶段 1 的收口，也是整站最能体现“后端经验值钱”的地方 ——
 * 上下文管理本质上就是资源调度：有容量上限、有淘汰策略、有热冷分层。
 */
export const chapter = {
  id: 'context-engineering',
  stageId: 'stage-1-foundation',
  order: 3,
  title: '上下文工程',
  subtitle: '决定模型每一次能看到什么',
  summary:
    'context rot 与 Lost in the Middle 的实证、system prompt 该写多具体、什么时候该检索而不是预先塞入、上下文快满时如何压缩、以及子智能体隔离为什么首先是上下文技巧而非并行技巧。',
  outcomes: [
    '能判断一份材料该放进上下文、该检索获取、还是根本不该让模型看到',
    '能设计一套上下文接近上限时的压缩与丢弃策略，而不是等它报错',
    '能说清 system prompt 写得过于具体和过于抽象各自会出什么问题',
  ],
  depth: 'deep',
  difficulty: 'intermediate',
  estimatedMinutes: 100,
  tags: ['context', 'compaction', 'subagent'],
  prerequisiteIds: ['prompt-engineering'],
  lessons: [
    {
      id: 'context-engineering/context-is-finite',
      chapterId: 'context-engineering',
      slug: 'context-is-finite',
      title: '上下文不是越多越好：两个实证',
      summary:
        'Lost in the Middle 与 context rot 说明：上下文窗口的标称容量，和模型实际能用好的容量，是两回事。',
      estimatedMinutes: 18,
      difficulty: 'intermediate',
      hasBody: true,
      status: 'drafting',
      keywords: ['context-rot', 'lost-in-the-middle'],
      checkpoints: [
        {
          id: 'middle-neglect',
          basis: 'inferred',
          question: '如果必须在一个很长的上下文里放置一条关键约束，你会放在哪里？为什么？',
          answer:
            '放开头，并在结尾重复一次。但要注意理由 —— Lost in the Middle 报告的 U 形位置效应，我用四种设计、最高 22.8k token 重测，**没有复现**。所以依据不是「放中间模型就读不到」，而是**放头尾是零成本的保险**：万一效应在你的数据与模型上存在，你已经避开；即使不存在，你也没有付出任何代价。真正决定成本的是 token 总量，不是摆放顺序。',
          note: '本节实测：400 段异质文档 + 复合条件定位任务，五个位置全部 15/15，未复现位置效应。',
          resourceIds: ['lost-in-the-middle'],
        },
        {
          id: 'context-rot-definition',
          basis: 'inferred',
          question: 'context rot 说的是什么？它和「上下文窗口不够用」是同一个问题吗？',
          answer:
            '不是同一个问题。窗口不够用是容量问题，会直接报错；context rot 指的是「即使远未达到容量上限，内容变多也会让每一部分更不被重视」。我实测到 22.8k token 也没观察到性能下降 —— 但这**不构成「可以随便塞」的理由**：成本按轮次重复计费、输入越长首字节延迟越高，而且真实语料比合成文档脏得多，效应更可能出现在那里。',
          note: '本节实测上限 22.8k token，未见容量导致的性能下降；但成本与延迟约束独立于「模型读不读得到」而成立。',
          resourceIds: ['anthropic-context-engineering'],
        },
      ],
    },
    {
      id: 'context-engineering/system-prompt-altitude',
      chapterId: 'context-engineering',
      slug: 'system-prompt-altitude',
      title: 'system prompt 的高度：太具体会僵化，太抽象会失控',
      summary:
        '把 system prompt 看成一份“给一个非常聪明但没有背景的新同事的说明”，而不是一份详尽的操作手册。',
      estimatedMinutes: 17,
      difficulty: 'intermediate',
      hasBody: true,
      status: 'drafting',
      keywords: ['system-prompt', 'instructions'],
      checkpoints: [
        {
          id: 'over-specification',
          basis: 'inferred',
          question: '把每种情况的处理方式都写进 system prompt，会带来什么问题？',
          answer:
            '最严重的问题不是「模型会做错」，而是**行为变得不可预测**。规则一多必然出现彼此矛盾的条目，而规则列表没有优先级、没有冲突检测 —— 模型每次生成时重新权衡，挑哪一条是随机的。本节实测：一条要求「承诺 24 小时到账」和一条「不得承诺时间」同时存在时，同一个 prompt 跑 12 次出现 8:4 的分裂；而单独任一条时都是确定的（4/4 与 0/4）。这意味着你无法复现、无法排查、也写不出回归测试。',
          note: '本节实测（deepseek-flash，2026-10-08）：单条规则确定，双条冲突时 8/12 vs 4/12。',
        },
        {
          id: 'too-abstract',
          basis: 'inferred',
          question: '反过来，system prompt 写得太抽象（只说“你是一个有帮助的助手”）会怎样？',
          answer:
            '模型会用它的默认行为填补所有空白 —— 措辞风格、详略程度、遇到不确定时的处理方式，全由训练时的通用偏好决定。本节实测到一个具体表现：问「退款多久到账」时，抽象 prompt 下模型**主动给出了具体天数**（「1-3 个工作日」这类），而带「不要承诺无法保证的事」这条原则的写法里，模型明确说了「无法保证具体天数」。抽象到没有约束，等于把产品行为交给了模型的默认值。',
          note: '本节实测（deepseek-flash，2026-10-08）：抽象组 3/3 给出具体天数，原则组 3/3 明确拒绝承诺。',
        },
      ],
      resourceIds: ['anthropic-context-engineering'],
    },
    {
      id: 'context-engineering/just-in-time',
      chapterId: 'context-engineering',
      slug: 'just-in-time',
      title: '即时检索：不要预先塞入所有可能用到的资料',
      summary: '把“预先准备一个完备的上下文”换成“让模型在需要时主动去取”，这两条路线的取舍。',
      estimatedMinutes: 20,
      difficulty: 'intermediate',
      hasBody: true,
      status: 'drafting',
      keywords: ['retrieval', 'just-in-time', 'tools'],
      checkpoints: [
        {
          id: 'jit-vs-preload',
          basis: 'inferred',
          question:
            '与其把整个知识库预先塞进上下文，不如让模型按需检索 —— 这样做的核心优势是什么？它什么时候会失效？',
          answer:
            '核心优势是**上下文里只装真正被用到的内容**：预加载的成本随资料库线性增长，按需取则几乎与资料库大小无关（只加载用到的那几篇）。但它有一个可测的边界 —— 决定成本的是「**需要多少篇**占全部的多少」，不是资料库有多大。本节实测：需要 2/40 篇时按需取省 36%，需要 8/40 篇时打平，需要 20/40 篇时**反而贵 2.5 倍**（轮次从 2 涨到 5，每轮都要重发历史）。交叉点约在 20%。',
          note: '本节实测（deepseek-flash，2026-10-08）：40 篇资料库，需要 2/8/20/40 篇时按需取分别是 0.64x / 0.95x / 2.47x / 3.60x。',
        },
        {
          id: 'file-path-pattern',
          basis: 'inferred',
          question:
            '有一种介于两者之间的做法：只把“目录结构”或“文件路径列表”放进上下文，需要时再让模型去读具体内容。它的巧妙之处在哪？',
          answer:
            '它把「索引」和「内容」分开：索引很便宜（路径、标题、一句话摘要），20 篇的目录约 400 token、60 篇约 1200 token，可以常驻上下文让模型知道有什么可选；内容很贵，只在被选中时才加载。这和你熟悉的按需加载／惰性求值是同一个思路，而且它同时解决了「模型不知道自己不知道什么」的问题 —— 先给它一张地图，它才会去问对的问题。',
          resourceIds: ['aider'],
        },
      ],
    },
    {
      id: 'context-engineering/compaction',
      chapterId: 'context-engineering',
      slug: 'compaction',
      title: '压缩与结构化笔记：上下文快满了怎么办',
      summary:
        '朴素做法是“总结一下之前的内容”。但压缩真正难的地方，是决定丢掉什么而不会在下一步后悔。',
      estimatedMinutes: 22,
      difficulty: 'advanced',
      hasBody: true,
      status: 'drafting',
      keywords: ['compaction', 'summary', 'memory'],
      checkpoints: [
        {
          id: 'compaction-risk',
          basis: 'inferred',
          question: '对历史对话做摘要压缩，最大风险是什么？（还有一个容易忽略的成本，是什么？）',
          answer:
            '风险是**丢掉后面恰好要用的那条信息**，而且丢的方式不可预测。本节实测：8 条散布在对话里的具体信息，摘要保住 7 条，**唯一丢掉的是「不要动生产库」这条硬约束** —— 因为它单独看起来只像一句备注。成本方面容易被忽略的是：**压缩不是免费的**，第一步就要把完整历史读一遍，所以在只用一次的上下文里，摘要比不压缩更贵（实测 2272 vs 1952 token）。压缩只有在结果被反复复用时才划算。',
          note: '本节实测（deepseek-flash，2026-10-08）：摘要 7/8、结构化笔记 8/8；一次性任务里摘要 2272 token > 完整历史 1952 token。',
        },
        {
          id: 'structured-notes',
          basis: 'inferred',
          question: '为什么用“结构化的笔记文件”来承载跨轮次的信息，比把它们留在对话历史里更可靠？',
          answer:
            '因为它的**结构是你定义的，不是模型当场判断的**。摘要的取舍标准由模型临时决定，你无法预知它会丢什么，而且丢了不会报错；结构化笔记的字段是固定的（标识符、数值、约束、否决理由各占一格），模型只负责填，缺字段是可检测的。实测佐证：同样是那 8 条信息，结构化的版本 8/8 全部保住。代价是产物更长、更贵（880 字 / 2776 token vs 摘要 138 字 / 812 token）。本质上这是把「状态」从「过程」里拆出来 —— 状态挪进笔记后，压缩历史就不必再小心翼翼。',
          resourceIds: ['anthropic-context-engineering'],
        },
      ],
    },
    {
      id: 'context-engineering/subagent-isolation',
      chapterId: 'context-engineering',
      slug: 'subagent-isolation',
      title: '子智能体：它首先是个上下文技巧',
      summary: '大家把它讲成“并行提速”，但生产系统里用它最常见的理由，其实是隔离上下文。',
      estimatedMinutes: 23,
      difficulty: 'advanced',
      hasBody: false,
      status: 'outlined',
      keywords: ['subagent', 'isolation', 'multi-agent'],
      checkpoints: [
        {
          id: 'subagent-real-value',
          basis: 'inferred',
          question:
            '一个探索型子任务（比如“在这 50 个文件里找出所有调用点”）交给子智能体去做，最主要的收益是什么？',
          answer:
            '主要收益是**上下文隔离**，而不是速度。主 agent 需要的是结论（“调用点在这些文件里”），而不是探索过程中的几十次文件读取与试错——那些中间输出如果留在主上下文里，会迅速占满窗口并稀释注意力。子智能体在自己的独立上下文里承受这些噪声，只把精炼结论回传。速度提升只是附带效果，且只在子任务之间真正独立时才存在。',
          resourceIds: ['anthropic-multi-agent-research'],
        },
        {
          id: 'subagent-cost',
          basis: 'inferred',
          question: '子智能体方案的主要代价是什么？什么情况下不该用它？',
          answer:
            '代价是 token 消耗显著上升——每个子智能体都要重新装载任务背景，并且它的探索过程本身也在消耗 token，整体用量通常比单 agent 高出数倍。所以当任务本身很短、或者子任务之间高度依赖（需要频繁共享中间状态）时，不该用它：此时隔离带来的收益抵不过重复装载与协调的成本。',
          resourceIds: ['anthropic-multi-agent-research'],
        },
      ],
    },
  ],
  resourceIds: [
    'anthropic-context-engineering',
    'lost-in-the-middle',
    'anthropic-multi-agent-research',
    'aider',
    'memgpt-paper',
  ],
  backendMapping: {
    analogy: '上下文工程 ≈ 内存管理与缓存淘汰，只不过这块“内存”有损、且每字节每次都重新计费',
    transferable: [
      '缓存淘汰与 GC 的思路：容量有限、需要策略、需要分层',
      '热数据 / 冷数据分层，按访问频率决定留存',
      '批处理与流式的取舍，以及“延迟换吞吐”这类权衡',
    ],
    pitfalls: [
      '以为窗口大就不必取舍：注意力会稀释，塞得越多每一条越不被重视',
      '把检索结果无差别全部塞入，反而把真正关键的那条淹没了',
      '以为压缩就是“总结一下”：摘要会丢掉后续步骤真正需要的细节',
      '把子智能体当成纯并行手段：它的主要价值是上下文隔离，代价是数倍 token',
    ],
    cost: 'medium',
  },
  status: 'outlined',
  updatedAt: '2026-09-24',
  verifiedAt: '2026-09-24',
  flagship: true,
} satisfies Chapter;
