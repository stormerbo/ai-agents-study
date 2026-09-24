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
      hasBody: false,
      status: 'outlined',
      keywords: ['context-rot', 'lost-in-the-middle'],
      checkpoints: [
        {
          id: 'middle-neglect',
          basis: 'inferred',
          question: '如果必须在一个很长的上下文里放置一条关键约束，应该放在哪里？为什么？',
          answer:
            '放在开头或结尾，绝不要放在中间。研究显示模型对长上下文各位置的利用率是 U 形的：开头和结尾最高，中间明显衰减。实践上的做法是把最重要的约束放在开头（或结尾重复一次），把大段参考资料放中间，而不是反过来。',
          resourceIds: ['lost-in-the-middle'],
        },
        {
          id: 'context-rot-definition',
          basis: 'inferred',
          question: 'context rot 说的是什么现象？它和“上下文窗口不够用”是同一个问题吗？',
          answer:
            '不是同一个问题。上下文窗口不够用是容量问题，会直接报错；context rot 是**注意力稀释**——即使远未达到容量上限，随着塞入的内容增多，模型对其中每一部分的关注度也在下降，表现为遗漏约束、抓错重点。这意味着“窗口还有空间”不能作为继续塞内容的理由。',
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
      hasBody: false,
      status: 'outlined',
      keywords: ['system-prompt', 'instructions'],
      checkpoints: [
        {
          id: 'over-specification',
          basis: 'inferred',
          question: '把每种情况的处理方式都写进 system prompt，会带来什么问题？',
          answer:
            '两个问题。一是僵化：真实输入的组合几乎无穷，逐条列举既列不全，又会让模型在遇到未列举的情况时不知如何变通；二是自相冲突，规则一多就必然出现彼此矛盾的条目，模型只能任选一条执行，行为变得不可预测。更好的做法是给出判断原则与几个典型示例，让模型在原则下自行处理长尾情况。',
        },
        {
          id: 'too-abstract',
          basis: 'inferred',
          question: '反过来，system prompt 写得太抽象（只说“你是一个有帮助的助手”）会怎样？',
          answer:
            '模型会用它的默认行为来填补所有空白，而那个默认行为大概率不是你想要的——措辞风格、详略程度、遇到不确定时的处理方式，全都由训练时的通用偏好决定。抽象到没有约束，等于把产品行为交给了模型的默认值。',
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
      hasBody: false,
      status: 'outlined',
      keywords: ['retrieval', 'just-in-time', 'tools'],
      checkpoints: [
        {
          id: 'jit-vs-preload',
          basis: 'inferred',
          question:
            '与其把整个知识库预先塞进上下文，不如让模型按需检索 —— 这样做的核心优势是什么？',
          answer:
            '核心优势是**上下文里只装真正被用到的内容**。预先加载必然塞入大量与当前任务无关的材料，既占容量又稀释注意力（见 context rot）；按需检索则让每一份进入上下文的内容都有明确用途。代价是增加了一轮往返，并且要求系统具备检索能力——所以这个取舍取决于“资料有多大”和“每次需要多少”。资料小到能全放，预先加载反而更简单可靠。',
        },
        {
          id: 'file-path-pattern',
          basis: 'inferred',
          question:
            '有一种介于两者之间的做法：只把“目录结构”或“文件路径列表”放进上下文，需要时再让模型去读具体内容。它的巧妙之处在哪？',
          answer:
            '它把“索引”和“内容”分开：索引很便宜（路径、标题、一句话摘要），可以常驻上下文让模型知道有什么可选；内容很贵，只在被选中时才加载。这和你熟悉的按需加载／惰性求值是同一个思路，而且它同时解决了“模型不知道自己不知道什么”的问题——先给它一张地图，它才会去问对的问题。',
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
      hasBody: false,
      status: 'outlined',
      keywords: ['compaction', 'summary', 'memory'],
      checkpoints: [
        {
          id: 'compaction-risk',
          basis: 'inferred',
          question: '对历史对话做摘要压缩，最大风险是什么？',
          answer:
            '丢掉的信息恰好是后面要用的。摘要天然偏向保留“结论”和“主线”，而细节（一个具体的错误信息、一个被否决的方案的否决理由、一个数字）往往被视为冗余而被丢弃——但 agent 后续恰恰经常需要这些细节。因此压缩策略要区分层次：决策与结论可以摘要，事实性细节（标识符、路径、错误原文、数值）应当结构化地保留下来，而不是交给模型自由摘要。',
        },
        {
          id: 'structured-notes',
          basis: 'inferred',
          question: '为什么用“结构化的笔记文件”来承载跨轮次的信息，比把它们留在对话历史里更可靠？',
          answer:
            '因为笔记是**外置且可增量维护**的：它不受上下文窗口限制，可以随时读取回来，而且它的结构是你定义的（进度、已确认的事实、待解决的问题各自一块），不会像对话历史那样被压缩算法无差别揉碎。对话历史适合承载“过程”，笔记适合承载“状态”——把状态从历史里挪出来，压缩时就不必再小心翼翼。',
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
