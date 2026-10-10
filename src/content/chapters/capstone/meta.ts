import type { Chapter } from '@/content/curriculum/schema';

export const chapter = {
  id: 'capstone',
  stageId: 'stage-5-practice',
  order: 24,
  title: '综合项目',
  subtitle: '从需求到交付走一遍',
  summary:
    '前二十一章讲的是零件，这一章把它们装成一台机器。不做玩具 demo，而是完整走一遍：划范围、搭骨架、按生产化清单加固、交付，最后复盘哪些判断被证明是错的。',
  outcomes: [
    '能从一个真实需求出发，划出可交付的最小范围并说明不做什么',
    '能按生产化清单给一个 agent 项目加固：评估、隔离、预算、审计、审批',
    '能在交付时给出可运行、可观测、可维护的产物，而不只是「能跑的代码」',
  ],
  depth: 'deep',
  difficulty: 'expert',
  estimatedMinutes: 240,
  tags: ['capstone', 'project', 'delivery'],
  prerequisiteIds: ['agent-deployment', 'human-in-the-loop', 'agent-security'],
  lessons: [
    {
      id: 'capstone/scope',
      chapterId: 'capstone',
      slug: 'scope',
      title: '划范围：先决定不做什么',
      summary: '项目失败最典型的原因不是做不出来，而是范围始终没定。',
      estimatedMinutes: 30,
      difficulty: 'advanced',
      hasBody: true,
      status: 'drafting',
      keywords: ['scoping', 'requirements'],
      checkpoints: [
        {
          id: 'scope-rules',
          basis: 'inferred',
          question: '给一个 agent 项目划范围，有哪几条硬性要求？',
          answer:
            '三条。**一，任务有明确的成功判据** —— 能写成「输入 X 得到 Y，且 Y 满足条件 Z」，否则你无法做评估那一章的任何事。**二，范围里包含至少一个不可逆动作的取舍决定** —— 要么明确排除它（只做只读），要么把它纳入审批设计；回避这个问题等于把风险留给上线后。**三，写下不做什么**：一个只列出功能而没有排除项的范围说明，实际上没有划定边界。判断依据很实用 —— **如果你说不出这个项目「最坏会做错什么」，说明范围还没划清。**',
        },
        {
          id: 'pick-a-real-need',
          basis: 'inferred',
          question: '为什么建议从一个自己真实需要的需求出发？',
          answer:
            '因为**只有真实需求才会逼你面对脏数据、边界与运维问题**，而这些正是本阶段要练的东西。为了练手编出来的 demo 任务通常输入干净、失败代价为零、也没有人真的会用 —— 于是你自然会跳过评估、隔离、审批这些「麻烦但不性感」的环节，而那恰好是生产化的全部内容。真实需求的三个额外好处：你能自己判断输出对不对（省掉了建标注集的成本）、失败的痛感会迫使你修而不是绕、以及它会持续被使用，从而暴露你没想到的失败模式。',
        },
      ],
      resourceIds: ['ai-engineering-huyen', 'twelve-factor-agents'],
    },
    {
      id: 'capstone/skeleton',
      chapterId: 'capstone',
      slug: 'skeleton',
      title: '骨架：先跑通，但别绕过边界',
      summary: '最小可用不等于最小正确 —— 有些东西第一天就得在。',
      estimatedMinutes: 40,
      difficulty: 'advanced',
      hasBody: true,
      status: 'drafting',
      keywords: ['implementation', 'skeleton'],
      checkpoints: [
        {
          id: 'skeleton-order',
          basis: 'inferred',
          question: '搭骨架时，按什么顺序实现？',
          answer:
            '按第 9 章那五个零件的顺序：**先写循环与终止条件**（用一个真模型、一个真工具，端到端跑通一次）→ **再写工具注册表**（schema 自检、参数校验、结构化错误）→ **然后加预算与循环检测** → **最后接持久化**。这个顺序的关键是每一步都能独立验证：循环跑通了才谈调度，调度对了才谈预算。反过来最容易犯的错是先铺一套漂亮的抽象层（配置系统、插件机制），结果端到端还没跑通就已经背上了设计债 —— 而你对需求的真实理解，恰恰要等它跑起来之后才会有。',
        },
        {
          id: 'what-must-exist-day-one',
          basis: 'inferred',
          question: '有哪些东西必须在第一天就在，不能等「以后再加」？',
          answer:
            '三样：**动作日志**（每一次工具调用的名称、参数、结果、耗时）—— 没有它，你后面所有排查都是猜；**预算上限**（轮次与 token）—— 它的缺失会在某个深夜以账单的形式提醒你；以及**密钥与权限的处理**（凭据不进上下文、专用账号）。这三样的共同点是：**它们都是「事后补代价极高」的东西** —— 日志要回溯历史数据才能补，预算要在所有调用点插入，权限模型改了会影响整个部署。相对地，缓存、路由分级、多模型支持这些都可以后面再加，它们的插入成本是局部的。',
        },
      ],
      resourceIds: ['twelve-factor-agents', 'claude-agent-sdk'],
    },
    {
      id: 'capstone/hardening',
      chapterId: 'capstone',
      slug: 'hardening',
      title: '加固：逐条过生产化清单',
      summary: '把前面几章的问句变成可勾选的清单。',
      estimatedMinutes: 50,
      difficulty: 'expert',
      hasBody: true,
      status: 'drafting',
      keywords: ['hardening', 'checklist'],
      checkpoints: [
        {
          id: 'hardening-checklist',
          basis: 'inferred',
          question: '生产化加固要过哪几类检查？',
          answer:
            '六类，对应前面几章：**评估** —— 有没有一份几十条的评测集？改动前有没有基线？**可观测性** —— 一次失败能不能定位到具体轮次？成本能不能归因到环节？**隔离与权限** —— 能力边界在哪一层？出网与文件权限是否最小？**安全** —— 清点过哪些外部内容会进入上下文？不可逆动作是否有执行层校验？**预算** —— 单任务、单用户、全局三层是否都有？超限行为是否可预期？**人机协作** —— 哪些动作需要审批、审批会展示什么、中断后能否安全恢复？每一类都必须能给出具体答案，而不是「差不多做了」。',
        },
        {
          id: 'hardening-priority',
          basis: 'inferred',
          question: '如果时间有限，加固的优先顺序是什么？',
          answer:
            '按「最坏后果 × 修复成本」排，通常是：**一，不可逆动作的执行层校验与审批** —— 投入最小，直接把最坏结果从不可挽回降到可控；**二，动作日志与成本归因** —— 它让后面所有问题变得可查；**三，评测集** —— 从真实失败里攒，不必一开始就完备；**四，权限与出网收紧**；**五，预算三层**；**六，其余优化**。这个顺序有个共同特征：**前面几项都不依赖对模型行为的精确预测**，所以不会因为换个模型版本就失效。相反，如果先做「更精细的 prompt 调优」，你会把时间花在最不稳定、最难验证的那一层。',
        },
      ],
      resourceIds: ['ai-engineering-huyen', 'twelve-factor-agents'],
    },
    {
      id: 'capstone/deliver',
      chapterId: 'capstone',
      slug: 'deliver',
      title: '交付：让人能接手',
      summary: '交付物不是「能跑的代码」，而是别人能继续维护的系统。',
      estimatedMinutes: 40,
      difficulty: 'advanced',
      hasBody: true,
      status: 'drafting',
      keywords: ['delivery', 'documentation'],
      checkpoints: [
        {
          id: 'deliverables',
          basis: 'inferred',
          question: '一个 agent 项目交付时，除了代码还该给出什么？',
          answer:
            '四样：**运行手册** —— 怎么启动、怎么配置、出了哪类问题看哪个指标；**评测现状** —— 当前评测集规模、通过率、以及已知的失败模式（诚实列出比给一个漂亮数字有用得多）；**成本模型** —— 单次任务的平均与最坏成本，以及三层预算的阈值；**已知限制** —— 哪些输入会失败、哪些动作被刻意排除、以及下一版打算做什么。第四项最容易被省略，但它决定了接手的人会不会在同一个坑里重摔一次。判断标准很简单：**一个没参与开发的人，能不能只靠这些材料回答「这个系统现在能不能放心用」。**',
        },
        {
          id: 'handover-drill',
          basis: 'inferred',
          question: '怎么验证「确实能接手」？',
          answer:
            '做一次**交接演练**：找一个没参与的人（或者隔几天之后的你自己），让他只靠文档完成三件事 —— 部署一次、跑一次评测、按运行手册处理一个模拟故障。全程不问他问题。做不到的地方就是文档的缺口，而不是他的能力问题。这个演练通常能暴露出最实际的信息：缺的往往是「出错时该怎么办」这类过程性知识，而代码注释与 API 文档恰好都不覆盖它。演练成本半天，收益是把交接从「靠口口相传」变成「有据可查」。',
        },
      ],
      resourceIds: ['twelve-factor-agents', 'ai-engineering-huyen'],
    },
    {
      id: 'capstone/retrospective',
      chapterId: 'capstone',
      slug: 'retrospective',
      title: '复盘：哪些判断是错的',
      summary: '把这个项目里被证伪的假设写下来 —— 那是整条路径最值钱的产出。',
      estimatedMinutes: 40,
      difficulty: 'expert',
      hasBody: true,
      status: 'drafting',
      keywords: ['retrospective', 'learning'],
      checkpoints: [
        {
          id: 'what-to-review',
          basis: 'inferred',
          question: '项目复盘时，重点该看什么？',
          answer:
            '重点不是「哪些做得好」，而是**哪些判断被证伪了**。具体三类：**技术上**（本来以为某个效应会很明显，实测没复现 —— 本站已经积累了十二个这样的实验，它们比成功案例更有教学价值）；**成本上**（预算估得准不准，最贵的是不是你预想的那一环）；以及**流程上**（哪一类失败重复出现，说明缺的是什么机制）。第三类最有行动价值 —— 同一个失败出现两次，通常意味着缺一道校验或一个审批点，而不是「运气不好」。把这些写下来，下一个项目就少踩一遍。',
        },
        {
          id: 'why-negative-results-matter',
          basis: 'inferred',
          question: '为什么「未复现」的结论比成功案例更值得记录？',
          answer:
            '因为成功案例只能告诉你「这样做在某一次有效」，而**未复现告诉你「这条流传的经验在我的场景里不成立」** —— 后者直接改变了你的判断依据。这个领域有大量被广泛引用但缺乏实测支撑的说法（位置效应、多数投票提准确率、工具多了会选错……），它们被写进无数教程，却没有人在自己的场景里验过。记录一次未复现，等于给读者（以及未来的自己）提供了一个反例，让那些说法从「常识」降级为「需要验证的假设」。这也是本站从第 0 章起就坚持的立场：**先怀疑测量方法，再怀疑被测对象；所有的结论都附带它的适用边界。**',
        },
      ],
      resourceIds: ['ai-engineering-huyen', 'twelve-factor-agents'],
    },
  ],
  resourceIds: ['ai-engineering-huyen', 'twelve-factor-agents', 'claude-agent-sdk'],
  projectIds: ['p1-reliable-extraction'],
  backendMapping: {
    analogy:
      '交付一个 agent 项目 ≈ 交付一个你愿意半夜被叫醒去维护的服务：可靠性、可观测、可回滚、可交接，缺一不可',
    transferable: [
      '项目管理的通用能力：划范围、排优先级、验证交付',
      '运行手册与交接演练：你现在做服务交接的那套动作',
      '复盘文化：记录假设被证伪的地方，而不只是记录成果',
    ],
    pitfalls: [
      '范围里没有排除项，导致项目边界不断扩张',
      '为练手编一个干净的 demo 任务，于是自然跳过了生产化的全部内容',
      '先铺抽象层再跑通端到端，在对需求还没理解时就背上设计债',
      '把日志、预算、密钥处理推迟到「以后再加」—— 这三样事后补的代价最高',
      '交付时只给代码，不给运行手册、失败模式清单与成本模型',
      '复盘只记成果，不记被证伪的判断',
    ],
    cost: 'high',
  },
  status: 'published',
  updatedAt: '2026-10-08',
  verifiedAt: '2026-10-08',
} satisfies Chapter;
