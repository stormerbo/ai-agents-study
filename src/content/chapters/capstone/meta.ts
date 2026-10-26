import type { Chapter } from '@/content/curriculum/schema';

export const chapter = {
  id: 'capstone',
  stageId: 'stage-5-practice',
  order: 25,
  title: '综合项目',
  subtitle: '从需求到交付走一遍',
  summary:
    '前面的章节讲的是零件，这一章把它们装成一台机器：划范围、搭骨架、加固、交付、复盘，再用证据完成最终验收。',
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
      summary: '先写清用户目标、数据与动作边界、验收证据和重开条件，再决定本版承诺什么。',
      estimatedMinutes: 30,
      difficulty: 'advanced',
      hasBody: true,
      status: 'drafting',
      keywords: ['scoping', 'requirements'],
      checkpoints: [
        {
          id: 'scope-rules',
          basis: 'inferred',
          question: '给一个 agent 项目划范围，哪些信息能让承诺可检查？',
          answer:
            '没有适用于所有项目的固定条数。至少写明目标用户结果、数据来源与身份边界、工具及副作用、可观察的验收信号、明确排除项和重开条件。涉及有影响的动作时，还要写清授权主体与失败/未知状态如何处理。范围是否足够，取决于这些承诺是否能被实现和验收；列出一个不可逆动作本身不是通用硬性要求。',
        },
        {
          id: 'pick-a-real-need',
          basis: 'inferred',
          question: '教学综合项目为什么可以用合成需求，而不一定使用真实业务数据？',
          answer:
            '合成场景能让输入、权限和预期结果可控，适合练习工具边界、失败处理和验收流程，也避免把真实客户数据带入不必要的教学环境。但合成数据不能证明真实分布下的质量或生产适用性。若选真实需求，应先取得必要授权并做数据最小化、脱敏和访问控制；同时保留独立判分依据，不能因为作者熟悉业务就省略评测。',
        },
      ],
      resourceIds: ['ai-engineering-huyen', 'twelve-factor-agents'],
    },
    {
      id: 'capstone/skeleton',
      chapterId: 'capstone',
      slug: 'skeleton',
      title: '骨架：先跑通，但别绕过边界',
      summary: '把第一条纵向路径与它能证明的状态、权限、恢复和评测边界说清楚。',
      estimatedMinutes: 40,
      difficulty: 'advanced',
      hasBody: true,
      status: 'drafting',
      keywords: ['implementation', 'skeleton'],
      checkpoints: [
        {
          id: 'skeleton-order',
          basis: 'inferred',
          question: '在当前综合项目里，搭第一条可验证路径时如何安排依赖顺序？',
          answer:
            '没有适用于所有项目的固定次序。对本书 P5，先冻结合成任务、工具 schema 和验收状态；再建立持久 task/action/provider-call 状态与宿主授权边界；接着实现不自动重发的 provider 往返、审批暂停/恢复、本地 sink 投递和未知结果对账；最后跑数据库集成、故障 drills、离线评测，再按 runbook 做有界 live smoke。每一步需有对应断言。简单、无副作用的原型可以先用 fake adapter；那只验证本地控制流，不能算真实模型集成或生产验证。',
        },
        {
          id: 'what-must-exist-day-one',
          basis: 'inferred',
          question: '哪些边界要在首个可验证切片前确定，哪些可以按风险延期？',
          answer:
            '先根据目标风险确定数据/主体边界、授权由哪一层执行、外部副作用的状态与未知结果如何处理，以及会产生费用的调用如何限额与对账；若首个切片包含远程调用或有副作用动作，这些控制不能靠以后补。轨迹记录应在可定位与数据最小化之间取平衡，不能默认保存原始参数和返回值。多模型路由、缓存或跨区域能力只有在目标承诺需要时才纳入；“以后再做”要有触发条件和明确的未覆盖风险。',
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
            '按本项目选出的六类检查组织：**评估** —— 代表性用例、改动基线与目标指标；**可观测性** —— 故障能否定位到轮次，日志是否最小化且可关联；**隔离与权限** —— 工具能力、主体与资源范围分别受何处约束；**安全** —— 外部内容和工具结果如何进入上下文，动作授权在哪里执行；**预算** —— 单任务限制与更大范围配额分别覆盖什么；**人机协作** —— 哪些动作依策略审批、审批信息是否充分、中断后如何安全恢复。六类是课程章节的归纳，不是完整安全清单；具体控制按系统风险补充。',
        },
        {
          id: 'hardening-priority',
          basis: 'inferred',
          question: '如果时间有限，加固的优先顺序是什么？',
          answer:
            '不存在对所有项目通用的加固优先级。先确定最坏影响和威胁边界，再看当前授权/隔离是否有效、风险降低是否可验证、各修复之间的依赖与成本；对本例而言，未授权动作与原始敏感轨迹是需要先处理的候选项，接着再为评测、版本和降级定义明确验收条件。提示词调优也不应替代宿主授权和环境控制；具体排序要按目标系统证据决定。',
        },
      ],
      resourceIds: ['ai-engineering-huyen', 'twelve-factor-agents', 'owasp-authorization-cheat-sheet', 'owasp-logging-cheat-sheet'],
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
            '按本节六块组织：**怎么跑**（依赖、命令、期望输出）、**不做什么**（范围边界）、**怎么验**（评测/冒烟方法与结果）、**出事怎么查**（轨迹与排查入口）、**已知缺口**（尚未实现或未验证的事项）、**判断依据**（关键决定的来源与适用范围）。它们可以合并成更少的文档，但应让未参与者能区分系统能力、限制、证据和设计判断。',
        },
        {
          id: 'handover-drill',
          basis: 'inferred',
          question: '怎么验证「确实能接手」？',
          answer:
            '安排一个未参与实现的人，只看交付材料完成启动、跑评测和处理模拟故障；记录环境、耗时、求助次数、完成情况与卡点。自测可用于发现明显缺项，但不等于独立交接。演练耗时由任务和环境决定，不预设为半天；它能发现文档缺口，但不能单独证明生产可用。',
        },
      ],
      resourceIds: ['twelve-factor-agents', 'ai-engineering-huyen', 'owasp-logging-cheat-sheet'],
    },
    {
      id: 'capstone/retrospective',
      chapterId: 'capstone',
      slug: 'retrospective',
      title: '复盘：判断与证据是否匹配',
      summary: '把假设、观测、测量质量和适用范围连起来，决定下一步该改什么或继续验证什么。',
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
            '复盘可以看三类问题：**技术判断**是否被观察支持、**成本判断**的估算口径是否贴合运行条件、**流程安排**是否遗漏了控制点。用失败重复次数作为调查线索，而不是自动裁决：重复可能来自同一根因，也可能是不同事件；先定位轨迹和共同条件，再决定是否补校验、审批或其它机制。不要用固定的全站未复现实验数量作价值证明，实验汇总会随数据和审计状态变化。',
        },
        {
          id: 'why-negative-results-matter',
          basis: 'inferred',
          question: '为什么「未复现」的结果也值得记录？',
          answer:
            '未复现的结果值得记录，是因为它能限制某个具体假设在当前条件下的可信度；但有限样本没有观察到效应，不等于效应不存在，也不说明其它场景会相同。记录时保留预测、任务、模型/版本、运行次数、评分规则、失败与缺失样本，以及结论不能外推到哪里。广泛流传的经验应视为待验证假设，引用数量本身既不证明也不否定它。',
        },
      ],
      resourceIds: ['ai-engineering-huyen', 'twelve-factor-agents'],
    },
    {
      id: 'capstone/acceptance',
      chapterId: 'capstone',
      slug: 'acceptance',
      title: '最终验收：让证据替项目说话',
      summary: '把项目场景矩阵、运行证据、独立环境交接方案与能力答辩组成可审查的发布验收包。',
      estimatedMinutes: 45,
      difficulty: 'expert',
      hasBody: true,
      status: 'drafting',
      keywords: ['acceptance', 'release-evidence', 'handoff'],
      checkpoints: [
        {
          id: 'fixtures-do-not-prove-live-model',
          question: '离线 fixture 和证据门禁都通过，能否说真实模型项目已验收？',
          answer: '不能。fixture 只验证判定逻辑，证据门禁只整理和裁决已提交的证据；真实模型往返、目标环境集成、恢复与独立交接仍需分别留存真实产物。',
          basis: 'inferred',
          note: '这是本课程的验收范围规则；离线测试与在线能力证据是不同证据类型。',
        },
        {
          id: 'human-release-decision',
          question: '所有自动 gate 通过后，脚本应直接批准发布吗？',
          answer: '不应。自动门禁只给出“可进入人工验收”；最终发布仍由负责人结合风险、未验证项和组织发布流程决定。',
          basis: 'inferred',
          note: '门禁能检查证据结构和硬不变量，不能替代风险所有者的上线决定。',
        },
      ],
      resourceIds: ['twelve-factor-agents', 'ai-engineering-huyen'],
    },
  ],
  resourceIds: ['ai-engineering-huyen', 'twelve-factor-agents', 'claude-agent-sdk'],
  projectIds: ['p5-agent-delivery'],
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
  updatedAt: '2026-10-19',
  verifiedAt: '2026-10-19',
} satisfies Chapter;
