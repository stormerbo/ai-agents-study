import type { Chapter } from '@/content/curriculum/schema';

/**
 * 章 0。唯一的目的：让你后面每一步都清楚自己在哪里。
 * 这一章不教技术，教判断力 —— 所以是 guided 而非 deep。
 *
 * ⚠️ 本文件是**纯元数据**，绝不能 import MDX 或任何运行时依赖：
 * 章节树、知识地图、进度组件等客户端组件都会导入它。
 */
export const chapter = {
  id: 'what-is-an-agent',
  stageId: 'stage-0-orientation',
  order: 0,
  title: 'AI Agent 全景与后端工程师的迁移地图',
  subtitle: '先看清全貌，再决定投入什么',
  summary:
    'Agent 到底是什么、什么不算 agent；为什么它是概率性系统而你的后端直觉需要相应调整；以及这条学习路径的全貌与使用方法。',
  outcomes: [
    '能用一个具体标准判断某个需求该用 agent 还是该用 workflow',
    '能说出 LLM 作为依赖，与普通第三方服务的三处关键差别',
    '知道后面每一章分别解决什么问题、以及它们之间的依赖顺序',
  ],
  depth: 'guided',
  difficulty: 'intro',
  estimatedMinutes: 25,
  tags: ['agent', 'orientation', 'mindset'],
  prerequisiteIds: [],
  lessons: [
    {
      id: 'what-is-an-agent/why-now',
      chapterId: 'what-is-an-agent',
      slug: 'why-now',
      title: '为什么是现在：三个条件同时成立了',
      summary: '能力跃迁不是模型单方面变强的结果，而是三个条件恰好同时满足。',
      estimatedMinutes: 6,
      difficulty: 'intro',
      hasBody: true,
      status: 'drafting',
      keywords: ['landscape', 'history'],
      checkpoints: [
        {
          id: 'three-conditions',
          question:
            '让 agent 从「论文里能跑」变成「工程上可用」，除了模型本身变强，还需要哪两类条件？',
          answer:
            '一是工具调用成为模型的可靠原生能力 —— 模型能稳定输出结构化的调用意图，而不是靠解析自由文本去猜；二是工程侧配套成熟，包括够用的沙箱隔离、可观测性方案与成本控制手段。只有模型强、缺后两者，agent 就只能停在演示阶段。',
          basis: 'inferred',
          note: '这是综述性判断，不是某份文档里的原话。Anthropic 的 Building effective agents 对「什么时候该用 agent」有更严格的标准，值得对照着读。',
          resourceIds: ['anthropic-building-effective-agents'],
        },
      ],
    },
    {
      id: 'what-is-an-agent/what-counts-as-agent',
      chapterId: 'what-is-an-agent',
      slug: 'what-counts-as-agent',
      title: '什么算 agent，什么不算',
      summary: '一条判断标准：控制权在谁手里。以及为什么多数需求其实应该用 workflow。',
      estimatedMinutes: 7,
      difficulty: 'intro',
      hasBody: true,
      status: 'drafting',
      keywords: ['workflow', 'agent', 'decision'],
      checkpoints: [
        {
          id: 'agent-vs-workflow',
          question: '区分 agent 与 workflow 的那条标准是什么？',
          answer:
            '控制权在谁手里。如果下一步做什么是你预先在代码里编排好的、LLM 只在固定环节被调用，那是 workflow；如果下一步做什么由模型根据当前观察结果自主决定、且路径长度不固定，那才是 agent。差别不是「高级 vs 低级」，而是可靠性、可预测性与成本的取舍 —— 多数需求其实用 workflow 就够了。',
          basis: 'documented',
          sourceIds: ['anthropic-building-effective-agents'],
          note: '区分标准出自 Anthropic 的 Building effective agents；该文还归纳了若干可组合的 workflow 模式，选型时值得对照。',
        },
      ],
    },
    {
      id: 'what-is-an-agent/mindset-shift',
      chapterId: 'what-is-an-agent',
      slug: 'mindset-shift',
      title: '需要调整的三个后端直觉',
      summary: '你的大部分经验可以直接迁移，但有三处直觉在这里会反过来咬人。',
      estimatedMinutes: 7,
      difficulty: 'intro',
      hasBody: true,
      status: 'drafting',
      keywords: ['mindset', 'testing'],
      checkpoints: [
        {
          id: 'deterministic-testing',
          question: '为什么“为 LLM 输出写精确匹配断言的单元测试”是个坏主意？它应该怎么写？',
          answer:
            '因为输出是概率性的——同一输入两次调用可能给出措辞完全不同的结果，精确匹配会随机失败，最终所有人都学会无视这个测试。正确做法是把断言写在结构性属性上：JSON 能否通过 schema 校验、关键字段是否被提取到、是否调用了预期工具、以及用一组样例统计成功率而非要求 100% 通过。',
          basis: 'inferred',
          note: '这是工程判断。第 13 章会把它展开成完整的评估体系（轨迹评估、pass^k 这类可靠性指标）。',
        },
        {
          id: 'determinism-myth',
          question: '过去人们习惯把 temperature 设为 0 来换取「确定性」，这条路现在还走得通吗？',
          answer:
            '走不通了，而且是双重的。第一，即使在支持该参数的旧模型上，temperature=0 也从来不保证逐字节可复现 —— 浮点运算、批处理与服务端版本更新都会带来差异；第二，对 Opus 4.6 之后发布的模型，temperature 根本不能再设（传非默认值直接返回 400）。所以「靠调参数换确定性」这个思路在当前模型上彻底失效，输出的稳定性要靠结构化校验、重试与统计意义上的成功率来保证。',
          basis: 'documented',
          sourceIds: ['claude-model-migration'],
          note: '「temperature 不可再设」有官方文档依据。「旧模型上也不保证一致」是工程常识，我未在官方文档里找到对此的明确表述，故不作为主要论据。',
        },
      ],
      resourceIds: ['anthropic-context-engineering'],
    },
    {
      id: 'what-is-an-agent/how-to-use-this-site',
      chapterId: 'what-is-an-agent',
      slug: 'how-to-use-this-site',
      title: '这条路径怎么走，这个站怎么用',
      summary: '六个阶段的分工、章与节的区别、实验与自检项该怎么用。',
      estimatedMinutes: 5,
      difficulty: 'intro',
      hasBody: true,
      status: 'drafting',
      keywords: ['meta'],
      checkpoints: [
        {
          id: 'stage-order',
          question: '为什么阶段 4（生产化）不能提前学？',
          answer:
            '因为评估、成本控制、沙箱这些都建立在前面阶段的具体机制之上 —— 你不知道一次 agent 循环会产生多少种失败模式，就没法设计评估指标；不知道工具调用与上下文是怎么消耗 token 的，就没法做成本优化。顺序在这里是有依赖的，不是难度递增。',
          basis: 'inferred',
          note: '这是本站的课程设计判断，不是外部事实。',
        },
      ],
    },
  ],
  resourceIds: [
    'anthropic-building-effective-agents',
    'hf-agents-course-zh',
    'roadmap-ai-engineer',
    'twelve-factor-agents',
  ],
  backendMapping: {
    analogy: 'LLM ≈ 一个没有 SLA、按 token 计费、且输出不确定的第三方依赖',
    transferable: [
      '重试、超时、熔断、降级这套容错思路完全适用',
      '把不确定性隔离在边界内、让核心逻辑保持确定性的分层设计',
      '可观测性——日志、追踪、成本归因——同样是基本功',
    ],
    pitfalls: [
      '按确定性函数的方式为 LLM 写测试：精确匹配断言会立刻碎掉',
      '把标称上下文容量当成实际可用能力：容量、注意力效果、成本与跨调用状态持久化都应分别按目标模型和 API 验证',
      '把概率性输出直接当可信数据源用，不做校验与兜底',
    ],
    cost: 'low',
  },
  status: 'published',
  updatedAt: '2026-09-24',
  verifiedAt: '2026-09-24',
} satisfies Chapter;
