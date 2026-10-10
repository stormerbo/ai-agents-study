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
      hasBody: true,
      status: 'drafting',
      keywords: ['subagent', 'isolation', 'multi-agent'],
      checkpoints: [
        {
          id: 'subagent-real-value',
          basis: 'inferred',
          question:
            '一个探索型子任务（比如“在这 50 个文件里找出所有调用点”）交给子智能体去做，最主要的收益是什么？',
          answer:
            '主要收益是**上下文隔离**，而不是速度。主 agent 需要的是结论，而不是探索过程中的几十次读取与试错 —— 那些中间输出留在主上下文里，会占容量、稀释注意力，而且**每一轮都要重发一遍**。本节实测：20 篇文档的检索任务 + 3 轮追问，隔离路线的主上下文峰值是 1258 token，而「全文常驻主上下文」路线是 6816（1/5），总 token 也从 25913 降到 9182。',
          note: '本节实测（deepseek-flash，2026-10-08）：主上下文峰值 1258 vs 6816；总 token 9182 vs 25913。',
          resourceIds: ['anthropic-multi-agent-research'],
        },
        {
          id: 'subagent-cost',
          basis: 'inferred',
          question: '子智能体方案的主要代价是什么？什么情况下不该用它？',
          answer:
            '代价的**唯一决定因素是「同一份内容被装载了几次」**，所以「一定更贵」的说法不成立。本节实测两个方向：和「资料全程常驻主上下文」比，隔离反而更省；和「共享背景只装载一次」比，隔离贵 **8.1 倍**（68548 vs 8430 token）—— 因为 8 个子 agent 各自重复装载了那份 3000 字符的背景。所以不该用的情况是：子任务多且都要带大段共享背景（先试着收窄背景、用 prompt caching），以及子任务之间高度依赖需要频繁共享中间状态时。',
          note: '本节实测（deepseek-flash，2026-10-08）：8 个子 agent 各装一次共享背景 → 68548 token，装载 1 次 → 8430 token。',
          resourceIds: ['anthropic-multi-agent-research'],
        },
      ],
    },
    {
      id: 'context-engineering/chat-template',
      chapterId: 'context-engineering',
      slug: 'chat-template',
      title: 'Chat Template：你写的消息，模型看到的 token',
      summary: '同样的内容，拆成 10 轮比合并成 1 轮多 25% 的 token。',
      estimatedMinutes: 22,
      difficulty: 'advanced',
      hasBody: true,
      status: 'published',
      keywords: ['chat-template', 'tokenization', 'message-structure'],
      checkpoints: [
        {
          id: 'structure-costs',
          basis: 'documented',
          sourceIds: ['claude-messages-api'],
          question: '同样的内容，拆成多轮比合并成一轮贵多少？为什么？',
          answer:
            '**Chat Template 是「消息数组 → token 串」的渲染层 —— 你写的输入不等于模型的输入。** 实测：同样 310 字符的规则块加一句问题，合并成一轮 user 时 input 是 238，拆成 10 轮 user + 10 条 assistant 应答时是 298 —— **差 60 token（25%），而内容字符数完全相同**。多出来的部分是 20 个角色边界的控制标记。位置也会影响：同一段规则放 system 是 234、放第一条 user 是 238、拆两轮问同一句是 254。三个推论：**一、能用一轮说完的别拆多轮**（但要权衡注意力稀释）；**二、结构变化不是免费操作** —— 缓存哈希是对渲染后的 token 串做的，所以改消息顺序、插系统提醒都可能断缓存；**三、不要手写 token 估算公式**，用响应里的 usage 字段对比实测。',
        },
        {
          id: 'where-to-add',
          basis: 'inferred',
          question: '要往长会话里加一条每次都适用的规则，应该加在哪里？',
          answer:
            '加在**稳定前缀里**（通常就是 system），不要加在每轮的 user 消息前。理由是位置决定了它是「付一次」还是「付每一次」：放 system 里它是稳定前缀的一部分，之后每轮都命中缓存；放 user 消息里则每轮都不同，**前缀从那条消息开始就断了，缓存全废**。而且后者还有第二个问题：**它会随轮次累积** —— 20 轮之后历史里有 20 句几乎相同的话，既占 token，又可能让模型以为那是 20 条独立的约束。所以规则是：**「每次都适用」的放稳定前缀，「只在这一轮适用」的放末尾**。这个差别在长会话里会被放大几十倍。',
        },
      ],
      resourceIds: ['claude-messages-api', 'claude-prompt-caching'],
    },
    {
      id: 'context-engineering/kv-cache',
      chapterId: 'context-engineering',
      slug: 'kv-cache',
      title: 'KV Cache：为什么前缀一改，成本就翻倍',
      summary: '改一个词，input 从 181 涨回 1205 —— 这是位置化存储的必然。',
      estimatedMinutes: 24,
      difficulty: 'advanced',
      hasBody: true,
      status: 'published',
      keywords: ['kv-cache', 'prompt-cache', 'prefix-stability'],
      checkpoints: [
        {
          id: 'why-prefix',
          basis: 'documented',
          sourceIds: ['claude-prompt-caching'],
          question: '为什么缓存按「前缀」失效，而不是按「内容」？',
          answer:
            '**因为 KV Cache 是按位置累积的，Prompt Cache 只是它跨请求的延伸。** 模型为每个 token 算一对 Key/Value，第 i 个 token 的值依赖它前面所有 token。所以你在**开头**插入一个词，从那个位置往后的每一个 token 的 K/V 都变了，缓存整体作废；而在**末尾**追加，前面完全不受影响。这不是实现偷懒 —— **存储单位就是位置化的 Key/Value，它没法按语义判断这段有没有真的变**。实测：前缀约 1800 token，第 2 次请求自动命中 1024，改一个词后命中归零、input 从 181 涨回 1205（6.7 倍）。由此得出四条架构约束：稳定内容在前变化内容在后；工具定义顺序要固定；压缩有缓存代价；effort 这类参与提示渲染的参数不能中途改。',
        },
        {
          id: 'cache-arch-constraint',
          basis: 'inferred',
          question: '「前缀稳定」为什么是架构约束而不是优化技巧？它带来哪几条具体约束？',
          answer:
            '是架构约束，因为它决定了**什么样的上下文结构是可用的**，而不只是能不能更快。四条具体约束：**一、稳定内容必须在前面、变化内容必须在后面** —— 把时间戳或请求 id 写进 system 开头会导致缓存永远不命中，而请求完全正常、没有任何警告。**二、工具定义顺序要固定** —— 如果每次由无序字典生成，缓存就是零。**三、压缩和改写历史有缓存代价** —— 缓存从被改写的位置断开，这是第 4 节「压缩更贵」的一个底层原因。**四、参与提示渲染的参数不能中途改** —— 第 1 章记过：同一会话里改顶层的 effort 会让之前的缓存失效，为了省钱降 effort 反而可能花更多钱。另外两点：命中缓存时 input_tokens 只算未命中部分（实测 181 vs 1205），所以判断真实成本必须把 cache_read 一起看；以及凡是参与前缀拼接的结构，序列化必须是确定的（排序或有序结构），不能依赖语言默认遍历顺序。',
        },
      ],
      resourceIds: ['claude-prompt-caching', 'claude-pricing'],
    },
    {
      id: 'context-engineering/agent-skills',
      chapterId: 'context-engineering',
      slug: 'agent-skills',
      title: 'Agent Skills：可组合的上下文单元',
      summary: '只给索引省 71%，但正确率掉一个 —— 必须两阶段加载。',
      estimatedMinutes: 24,
      difficulty: 'advanced',
      hasBody: true,
      status: 'published',
      keywords: ['agent-skills', 'lazy-loading', 'instruction-packages'],
      checkpoints: [
        {
          id: 'index-only-danger',
          basis: 'documented',
          sourceIds: ['openai-agents-sdk-python'],
          question: '只给技能索引（不给完整指令）的危险是什么？实测差多少？',
          answer:
            '**因为缺规则时模型不会停下来问，它会用通用直觉给一个看起来合理的错答案。** 实测：6 个 skill、5 个任务，全部预载正文时 5/5 正确（input 516）；只给索引时 4/5 正确（input 148，省 71%）—— 错的那个是「按业务键去重」，完整指令里有一条「大小写与首尾空格不敏感」，索引的简短描述里没有，于是模型按字面把 A1、a1、A2 当成三条。**你写的每一条规则都是「通用直觉会出错」的证据；把它藏起来，等于把错误放出来。** 正确形态是两阶段：索引 → 模型选中 → 加载该 skill 正文 → 再答。实测两阶段 3/3 正确、两轮总 token 201，同样任务下全部预载是 516 —— **省 61% 且正确率不掉**。',
        },
        {
          id: 'skill-vs-tool',
          basis: 'inferred',
          question: 'skill 和 tool 有什么区别？它们怎么配合？',
          answer:
            '**工具描述「能做什么」（能力），skill 描述「该怎么做」（规则）。** 工具的典型粒度是一次操作（查订单、发通知），由你的代码执行；skill 的典型粒度是一类任务的做法（退款金额怎么算），由模型自己按规则执行。加载方式也不同：工具定义必须在上下文里（否则模型不知道有它），skill 的元数据常驻、正文按需加载。它们会配合：一个 skill 里可以写「先调用 lookup_order，再按下面规则判断」，把工具调用顺序也固化下来。**这时候 skill 实际上在承担一部分工作流编排的职责** —— 这是它比工具描述更强的地方，也是它更危险的地方：规则写错了它照做，而且不会报错。',
        },
      ],
      resourceIds: ['openai-agents-sdk-python', 'anthropic-context-engineering'],
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
  status: 'published',
  updatedAt: '2026-10-08',
  verifiedAt: '2026-10-08',
  flagship: true,
} satisfies Chapter;
