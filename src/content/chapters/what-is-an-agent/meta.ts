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
      title: '为什么现在更容易把 agent 做成工程系统',
      summary: '用动作协议、上下文与状态管理、成本和延迟解释近年工程落地条件；这些是分析视角，不是必要且充分门槛。',
      estimatedMinutes: 6,
      difficulty: 'intro',
      hasBody: true,
      status: 'drafting',
      keywords: ['landscape', 'history'],
      checkpoints: [
        {
          id: 'three-conditions',
          question:
            '本节的三类工程因素是 agent 上线的必要且充分条件吗？',
          answer:
            '不是。它们是分析接口能力、上下文/外部状态管理、成本/延迟的观察框架；具体部署还要看任务风险、评估证据、授权隔离、可观测性、故障恢复和产品价值。较大的上下文窗口也不能替代状态管理或自动保证任务可靠。',
          basis: 'inferred',
          note: '这是工程分析框架，不是某份官方文档定义的必要条件。Anthropic 的 agent/workflow 建议与上下文文档可作为具体厂商的实例，但不能推广为所有系统的固定条件。',
          resourceIds: ['anthropic-building-effective-agents', 'anthropic-context-windows', 'react-paper', 'deepseek-anthropic-api', 'deepseek-context-caching'],
        },
      ],
    },
    {
      id: 'what-is-an-agent/what-counts-as-agent',
      chapterId: 'what-is-an-agent',
      slug: 'what-counts-as-agent',
      title: '什么算 agent，什么不算',
      summary: '本文采用的架构分类：workflow 与 agent 的控制流差异、宿主执行边界，以及何时值得增加模型决策。',
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
            '看控制流由谁编排。如果应用预先决定步骤与分支、LLM 只在固定位置提供能力，那是 workflow；如果模型会基于观察提出下一步动作，宿主再按状态、权限与预算决定是否执行或继续，这属于 agent loop。路径长度可能动态变化，但不是唯一判据；workflow 的成本通常更容易估算，不等于可以精确预知每次输出、缓存、重试的账单。',
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
      summary: '后端经验大多仍然有用；输出可重复、成功响应等于任务成功、上下文等于精确状态这三种默认假设需要重新验证。',
      estimatedMinutes: 7,
      difficulty: 'intro',
      hasBody: true,
      status: 'drafting',
      keywords: ['mindset', 'testing'],
      checkpoints: [
        {
          id: 'deterministic-testing',
          question: '测试 LLM 输出时，什么时候精确断言合适，什么时候需要别的判据？',
          answer:
            '先按层次定义契约：不要比较仅格式不同的原始 JSON 字符串；解析后校验 schema；对必须精确的业务字段做精确断言；对容许措辞变化的自然语言使用经过校准的语义判据。质量/成功率结论需用代表目标任务的样本集与明确 grader 评估，不能因为输出存在变异就放弃精确的业务不变量。',
          basis: 'inferred',
          note: '这是工程判断。第 13 章会把它展开成完整的评估体系（轨迹评估、pass^k 这类可靠性指标）。',
        },
        {
          id: 'determinism-myth',
          question: 'temperature=0 能保证输出逐字节可复现吗？参数行为应如何确认？',
          answer:
            '不能。Anthropic Messages API 文档明确说明，即使 temperature=0，结果也不保证完全确定；同一 API 的参数支持还随模型版本变化，Opus 4.6 之后发布的模型对非默认 temperature 返回 400，而默认值 1 可兼容。这个结论只描述 Anthropic 文档范围，不能推广到其它 provider。应查目标 API/SDK 文档并在目标任务上评测；校验和重试只能处理各自定义的失败，不能保证模型输出稳定。',
          basis: 'documented',
          sourceIds: ['claude-messages-api', 'claude-model-migration'],
          note: '限定为 Anthropic 当前 Messages API 文档说明；模型参数行为会变化，发布时应重新核对目标模型。',
        },
        {
          id: 'context-position-scope',
          question: 'Lost in the Middle 研究能支持什么结论？',
          answer:
            '该研究在特定模型的长上下文问答与键值检索任务中观察到相关信息位置影响；它不能证明所有模型和任务都有相同位置曲线，也不能把某次任务失败的根因归为注意力位置。需要在目标任务、模型和上下文长度上设计受控评测。',
          basis: 'documented',
          sourceIds: ['lost-in-the-middle'],
          note: '来源是论文报告的实验范围；本站关于本地历史标记实验的描述仍不可独立复核。',
        },
      ],
      resourceIds: ['anthropic-context-engineering', 'lost-in-the-middle', 'claude-messages-api', 'claude-model-migration', 'anthropic-stop-reasons'],
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
          question: '阶段顺序是硬性先修要求吗？如何判断能否跳读？',
          answer:
            '不是。阶段表达本站建议的学习顺序和主要概念依赖，不表示后续阶段的每一章都以前面所有章节为先修。可以从知识地图查看具体连线，也可按目标走本文给出的只读工具调用短路径；涉及权限、生产副作用或成本决策时，再补齐对应先修知识与验证。',
          basis: 'inferred',
          note: '这是本站的课程编排建议；读者的实际先修能力和项目目标不同。',
        },
        {
          id: 'redirect-credential-boundary',
          question: '为什么 first-loop 示例拒绝自动跟随 API 重定向？',
          answer:
            'Python urllib 的 Request 普通请求头会被添加到重定向请求。示例携带 x-api-key，因此显式拒绝重定向，避免凭据自动转发到新的 URL；遇到 302 时应核对可信的最终 endpoint 地址。',
          basis: 'documented',
          sourceIds: ['python-urllib-request'],
          note: '这是 Python urllib 文档所述的客户端行为；该限制不等于完整的 SSRF 或目标主机安全策略。',
        },
      ],
      resourceIds: ['claude-messages-api', 'python-urllib-request'],
    },
  ],
  resourceIds: [
    'anthropic-building-effective-agents',
    'hf-agents-course-zh',
    'roadmap-ai-engineer',
    'twelve-factor-agents',
  ],
  backendMapping: {
    analogy: 'LLM API 是外部依赖；可用性、计费、版本承诺因 provider/套餐而异，生成内容还需按业务契约验证',
    transferable: [
      '超时、预算、重试、熔断与降级仍有用，但要按 provider 错误语义、任务 deadline 和副作用边界配置',
      '把不确定性隔离在边界内、让核心逻辑保持确定性的分层设计',
      '可观测性——日志、追踪、成本归因——同样是基本功',
    ],
    pitfalls: [
      '比较未经解析的整段模型文本；把格式变异与业务契约混为一谈',
      '把标称上下文容量当成实际可用能力：容量、注意力效果、成本与跨调用状态持久化都应分别按目标模型和 API 验证',
      '把模型提出的内容当成事实、授权或业务动作已成功，而不做独立校验',
    ],
    cost: 'low',
  },
  status: 'published',
  updatedAt: '2026-10-21',
  verifiedAt: '2026-10-21',
} satisfies Chapter;
