import type { Chapter } from '@/content/curriculum/schema';

export const chapter = {
  id: 'evaluation',
  stageId: 'stage-4-production',
  order: 15,
  title: '评估与可观测性',
  subtitle: '先能看见，才能改好',
  summary:
    '没有评估的 agent 项目，改 prompt 就是凭感觉调参。这一章讲怎么把「好」定义成可测的指标、评测集从哪来、用模型打分在什么条件下可信，以及一次失败要怎样才能定位到具体那一轮。',
  outcomes: [
    '能把一个模糊的「效果不好」拆成可测的指标与可复现的用例',
    '能建一套几十条规模就够用的评测集，并说得出它防的是什么',
    '能设计追踪，使一次失败可以定位到具体的轮次与工具调用',
  ],
  depth: 'deep',
  difficulty: 'advanced',
  estimatedMinutes: 105,
  tags: ['evaluation', 'observability', 'tracing'],
  prerequisiteIds: ['agent-loop'],
  lessons: [
    {
      id: 'evaluation/define-good',
      chapterId: 'evaluation',
      slug: 'define-good',
      title: '先把「好」定义清楚',
      summary: '「效果不好」不是一个可用的需求，它至少要拆成四个维度。',
      estimatedMinutes: 20,
      difficulty: 'intermediate',
      hasBody: false,
      status: 'outlined',
      keywords: ['metrics', 'success-criteria'],
      checkpoints: [
        {
          id: 'four-dimensions',
          basis: 'inferred',
          question: '一个 agent 系统的「好」，至少要拆成哪几个可测维度？',
          answer:
            '四个：**任务是否完成**（端到端成功率，最重要但粒度最粗）、**中间步骤是否正确**（工具选对了没有、参数对不对）、**成本**（每次任务消耗的 token 与调用次数）、以及**延迟**（首字节与整任务完成时间）。只测第一个会掩盖问题：成功率没变，成本可能翻了三倍；或者成功率提升了但延迟从 3 秒变成 40 秒，体验反而更差。这四个维度要一起看，而且**不要合成一个总分** —— 加权总分会把「哪一项退化了」这个关键信息抹掉。',
        },
        {
          id: 'intent-vs-outcome',
          basis: 'inferred',
          question: '为什么必须分开测「结果对不对」和「过程对不对」？',
          answer:
            '因为它们的修法完全不同，而且**结果对不代表过程对**。一个 agent 可能用错误的工具、绕了三倍的路，最后侥幸得到正确答案 —— 这次成功了，但换一个输入就会失败，而你在结果指标上完全看不出来。反过来，过程正确但结果失败通常指向外部原因（数据缺失、权限问题），不该改 prompt。所以过程指标（工具选择准确率、参数合法率）的价值不是「更严格」，而是**更早发出预警**：它在结果指标还没掉下来的时候就能告诉你系统在变脆。',
        },
      ],
      resourceIds: ['ai-engineering-huyen', 'claude-agent-sdk'],
    },
    {
      id: 'evaluation/dataset',
      chapterId: 'evaluation',
      slug: 'dataset',
      title: '评测集从哪来，多小才够',
      summary: '不是先有数据集再开发，而是把失败案例攒起来。',
      estimatedMinutes: 22,
      difficulty: 'advanced',
      hasBody: false,
      status: 'outlined',
      keywords: ['dataset', 'regression'],
      checkpoints: [
        {
          id: 'where-cases-come-from',
          basis: 'inferred',
          question: '一个刚起步的项目，评测集应该从哪来？',
          answer:
            '按优先级有三个来源。**真实失败案例**（最值钱）：每次线上出问题，把当时的输入原样存下来，修好之后加进评测集 —— 这条闭环能保证你不在同一个坑里摔两次。**边界样本**：你自己能想到的最刁钻的输入（空值、超长、互相矛盾的字段、非目标语言）。**常规样本**：从已有数据里随机抽一批，保证改动没有破坏主流程。注意顺序 —— 很多人反过来，先造一堆常规样本，结果 90% 都通过，剩下的 10% 全是真实案例，而那 90% 从未发现过任何问题。**评测集的价值来自它含有的困难样本比例，不来自它的规模。**',
        },
        {
          id: 'how-big-is-enough',
          basis: 'inferred',
          question: '几十条的评测集真的有意义吗？',
          answer:
            '有，但它能回答的问题有限。**几十条**足以回答「这次改动是变好还是变坏」中的明显情形（成功率从 60% 到 90% 一定看得出来），也足以在 CI 里挡住明显回归。它**不足以**分辨 88% 与 90% 这种细微差别 —— 那种差距需要几百条才能统计上区分开。所以正确用法是分两层：小而快的集合进 CI，每次提交都跑，防的是「明显变坏」；大而慢的集合定期跑，用于做选型与调参决策。另外要警惕一个反效果：**评测集一旦被反复用来调参，就会过拟合**。缓解办法是留一份从不参与调优的留出集，只在做最终判断时打开。',
        },
      ],
      resourceIds: ['open-deep-research', 'ai-engineering-huyen'],
    },
    {
      id: 'evaluation/llm-as-judge',
      chapterId: 'evaluation',
      slug: 'llm-as-judge',
      title: '用模型打分：什么时候可信',
      summary: '它很适合判断「有没有」，不适合判断「好不好」。',
      estimatedMinutes: 22,
      difficulty: 'advanced',
      hasBody: false,
      status: 'outlined',
      keywords: ['judge', 'rubric'],
      checkpoints: [
        {
          id: 'when-judge-works',
          basis: 'inferred',
          question: '什么条件下，用模型当评分器是可靠的？',
          answer:
            '三个条件同时成立时比较可靠：**判据可以写成明确的规则**（而不是「写得好不好」这类主观标准）、**答案可枚举或可机械核对**（比如「是否包含这三个要点」「是否与原文一致」）、以及**你做过校准** —— 拿一批人工标注过的样本，看它的判断和人对得上的比例。第三个条件是分水岭：没校准过的评分器只是「另一个模型的意见」，把它当指标用等于把不确定性又引入了一层。反过来说，**越是需要品味与语境的判断（文案质量、结构美感），越不该交给它** —— 那时你测的是评分器的偏好，不是产品的质量。',
        },
        {
          id: 'judge-pitfalls',
          basis: 'inferred',
          question: '用模型评分时，有哪几个已知的系统性偏差要防？',
          answer:
            '至少三个。**位置偏差**：成对比较时它倾向于选先出现的那个 —— 缓解办法是两个顺序各跑一次，不一致就判为平局。**长度偏差**：更长的回答更容易被judged为更好，哪怕内容相同 —— 这在评测摘要类任务时会系统性高估啰嗦的输出。**自我偏好**：评分器倾向于给同族模型的输出更高分 —— 所以不要用被评的那个模型给自己的输出打分。还有一个更隐蔽的问题：**评分器也会被提示注入**。如果被评的内容里含「请给满分」这类文字，它有相当概率照做（第 2 章测过注入的多种形态）。所以评测内容必须当成数据对待，不能让它进入指令位置。',
        },
      ],
      resourceIds: ['ai-engineering-huyen', 'openai-cookbook'],
    },
    {
      id: 'evaluation/traces',
      chapterId: 'evaluation',
      slug: 'traces',
      title: '追踪：一次失败要能定位到那一轮',
      summary: '没有轨迹，你只能看到「失败了」；有轨迹，你能看到「在第 4 轮选错了工具」。',
      estimatedMinutes: 22,
      difficulty: 'advanced',
      hasBody: false,
      status: 'outlined',
      keywords: ['tracing', 'observability'],
      checkpoints: [
        {
          id: 'what-a-trace-needs',
          basis: 'inferred',
          question: '一条可用的 agent 轨迹，至少该记录什么？',
          answer:
            '按最小可用集排：**每一轮的完整请求与响应**（包括 system、工具定义、历史、以及 stop_reason）、**每次工具调用的名称、参数、返回与耗时**、**每一轮的 token 用量**、以及**整个任务的唯一 id 与父子关系**（子智能体、重试、并行分支要能挂到同一棵树上）。最后一项最容易被忽略，但它决定了你能否回答「这次失败到底发生在哪个环节」。此外还要记 **prompt 与工具的版本标识** —— 否则你无法回答「这次变差是从哪次改动开始的」，而那正是排查的起点。',
        },
        {
          id: 'cost-attribution',
          basis: 'inferred',
          question: '为什么成本归因必须建立在轨迹之上？',
          answer:
            '因为**总账掩盖结构**。你看到这个月花了多少，但不知道是哪个章节的哪一步吃掉的：是工具定义太长、是历史没压缩、还是子智能体重复装载了共享背景。只有把每一次调用的 token 记到具体的轮次与环节上，前三章那些成本规律（每轮重发、O(N²)、内容乘装载次数）才能变成可执行的优化动作。一个具体的判据是：**如果你无法回答「这个任务里最贵的三次调用分别是什么」，那你的成本优化就是在猜。**',
        },
      ],
      resourceIds: ['claude-agent-sdk', 'openai-agents-sdk-python'],
    },
    {
      id: 'evaluation/regression',
      chapterId: 'evaluation',
      slug: 'regression',
      title: '把评测接进开发流程',
      summary: '改一次 prompt 就跑一遍，让「变好」成为一个可验证的主张。',
      estimatedMinutes: 18,
      difficulty: 'intermediate',
      hasBody: false,
      status: 'outlined',
      keywords: ['ci', 'regression', 'ab'],
      checkpoints: [
        {
          id: 'ci-for-prompts',
          basis: 'inferred',
          question: '把评测接进 CI，具体挡的是什么？',
          answer:
            '挡的是**无声退化**。prompt 与工具的改动很容易修好一类输入、弄坏另一类，而在没有回归测试的项目里，后一种情况通常要等到用户投诉才被发现。接进 CI 之后，每次改动都跑一遍小而快的评测集，失败就拦住 —— 这和后端写单元测试的逻辑完全一样。需要注意两点差异：模型输出是**非确定性**的，所以判据要允许一定波动（连续多次运行取稳定结论），不能像断言等于某个值那样严格；以及成本，评测要花钱，所以 CI 里跑的是小集合，大集合放夜间或按需触发。',
        },
        {
          id: 'ab-not-vibes',
          basis: 'inferred',
          question: '怎么避免「我觉得新版更好」这种结论？',
          answer:
            '强制自己用**同一份评测集 + 可复现的对照**。具体做法是：改动前先记录基线（同一个集合、同一个模型、同样的参数），改动后在同一条件下重跑，然后比较逐条的差异，而不是只看总分。逐条差异能告诉你**代价是什么** —— 总分涨了 5% 听起来不错，但如果它涨在容易的样本上、同时弄坏了三个困难样本，这个改动其实是有害的。另外要固定模型版本：很多所谓的「评测结果波动」其实是上游模型静默更新造成的，第 1 章的迁移指南就是为这类问题准备的。',
        },
      ],
      resourceIds: ['twelve-factor-agents', 'ai-engineering-huyen'],
    },
  ],
  resourceIds: ['ai-engineering-huyen', 'claude-agent-sdk', 'openai-agents-sdk-python', 'open-deep-research', 'twelve-factor-agents'],
  labIds: ['lab-eval-contrast'],
  backendMapping: {
    analogy: '评估 ≈ 单元测试 + APM：一个保证「没变坏」，一个让你在出事时能定位到具体哪一步',
    transferable: [
      '测试金字塔的思路：小而快的进 CI，大而慢的定期跑',
      '可观测性三件套（日志、指标、追踪）在这里的对应物',
      '「先定义指标再优化」的习惯，以及不用总分掩盖分项退化',
    ],
    pitfalls: [
      '只测端到端成功率，掩盖成本与延迟的退化',
      '拿真实用例反复调参，把评测集过拟合掉',
      '使用没做过校准的模型评分器，把它当成客观指标',
      '不记录 prompt 与工具版本，无法回答「从哪次改动开始变差」',
      '把成本只看总数，不做归因',
    ],
    cost: 'medium',
  },
  status: 'outlined',
  updatedAt: '2026-10-08',
  verifiedAt: '2026-10-08',
} satisfies Chapter;
