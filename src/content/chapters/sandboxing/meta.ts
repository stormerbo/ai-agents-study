import type { Chapter } from '@/content/curriculum/schema';

export const chapter = {
  id: 'sandboxing',
  stageId: 'stage-4-production',
  order: 16,
  title: '沙箱与权限',
  subtitle: '让模型动手，但别让它拆家',
  summary:
    '一旦 agent 能执行代码、读写文件、访问网络，它就从「一个文本生成器」变成了「一个有权限的进程」。这一章讲怎么给它划出活动范围：隔离层级、最小权限、凭据处理，以及执行策略与审计。',
  outcomes: [
    '能判断一个 agent 的能力组合需要哪一级隔离',
    '能设计文件系统与网络的最小权限，而不是默认全开',
    '能让凭据永不进入上下文，并说清为什么这是硬要求',
  ],
  depth: 'deep',
  difficulty: 'advanced',
  estimatedMinutes: 95,
  tags: ['sandbox', 'permissions', 'security'],
  prerequisiteIds: ['tool-calling', 'agent-loop'],
  lessons: [
    {
      id: 'sandboxing/why-isolate',
      chapterId: 'sandboxing',
      slug: 'why-isolate',
      title: '为什么必须隔离',
      summary: '不是因为它会恶意，而是因为你无法穷举它会做什么。',
      estimatedMinutes: 18,
      difficulty: 'intermediate',
      hasBody: true,
      status: 'drafting',
      keywords: ['isolation', 'blast-radius'],
      checkpoints: [
        {
          id: 'threat-model',
          basis: 'inferred',
          question: '给 agent 加隔离，防的是什么？',
          answer:
            '防的主要不是「模型有恶意」，而是**你无法穷举它的行为空间**。你给它一个 shell 工具时，想象的是它会用来跑测试；但同一个工具也能删文件、拉取任意 URL、读取环境变量。你没有授权这些动作，可它们在能力上是被授予的。第二类风险来自**外部输入**：agent 读到的网页、文档、工具返回值里可能含有诱导它的文字（提示注入），它自己无法分辨这是数据还是指令。第三类是最现实的：**正常情况下的失误** —— 一条 rm 写错了路径，或者重试逻辑把写操作跑了两遍。隔离的价值在于：无论上面哪种情况发生，事故半径都被限制在一个可预期的范围内。',
        },
        {
          id: 'capability-decides-isolation',
          basis: 'inferred',
          question: '隔离级别该由什么决定？',
          answer:
            '由**能力组合**决定，而不是由「这个 agent 重不重要」决定。一个只读文档、只返回文本的 agent 几乎不需要隔离；一个能执行任意代码的 agent 需要进程级甚至更强的隔离；一个能访问内部网络、又同时能读取外部内容的 agent 风险最高 —— 因为这两项组合起来就是一个数据外泄通道。所以判断顺序是：先列出它实际需要的能力（读什么、写什么、连什么网、用谁的凭据），再问「如果这一项被滥用，最坏会怎样」。最坏后果可接受就不隔离，不可接受就隔离到能把它关住的那一级。',
        },
      ],
      resourceIds: ['twelve-factor-agents', 'ai-engineering-huyen'],
    },
    {
      id: 'sandboxing/isolation-levels',
      chapterId: 'sandboxing',
      slug: 'isolation-levels',
      title: '隔离的层级',
      summary: '从「同一个进程」到「另一台机器」，成本与强度同步上升。',
      estimatedMinutes: 20,
      difficulty: 'advanced',
      hasBody: true,
      status: 'drafting',
      keywords: ['container', 'vm', 'process'],
      checkpoints: [
        {
          id: 'isolation-spectrum',
          basis: 'inferred',
          question: '按强度从低到高，隔离有几档？各自适合什么？',
          answer:
            '大致四档。**无隔离**：工具在 agent 进程内执行，只靠参数校验 —— 只适合纯读、无网络、不碰文件系统的工具。**进程级**：子进程执行、限制资源与超时，能挡住跑飞和误删，但同一用户下的文件权限仍然共享。**容器级**：独立文件系统与网络命名空间，是目前最常用的平衡点 —— 启动快、边界清楚，代价是要处理镜像与依赖。**虚拟机或另一台机器**：最强隔离，适合要执行完全不可信的代码、或需要真正多租户的场景，代价是启动慢、成本高。选择的关键不是「越强越好」，而是**最强的那个是否与你的延迟预算冲突** —— 一个交互式 agent 每次都起虚拟机，体验会先崩掉。',
        },
        {
          id: 'escape-surface',
          basis: 'inferred',
          question: '容器隔离最容易在哪几个地方漏？',
          answer:
            '三个常见漏洞。**挂载**：为了让它读到项目代码，把宿主机目录直接挂进去 —— 如果挂的是读写且范围过大，容器隔离就形同虚设（它能改你的源码、能读到工作区里的凭据文件）。正确做法是只挂必要路径，且尽量只读。**网络**：默认允许出网，于是它能访问内网服务与云元数据端点；这一条和提示注入组合起来就是数据外泄。**凭据**：把 API key 作为环境变量传进容器，等于让容器里运行的任何代码都能读到它 —— 而 agent 执行的第一段代码未必是你写的。这三处的共同点是：**隔离的强度取决于最弱的那一环**，配好文件系统却开着网络，等于没配。',
        },
      ],
      resourceIds: ['claude-agent-sdk', 'openhands'],
    },
    {
      id: 'sandboxing/least-privilege',
      chapterId: 'sandboxing',
      slug: 'least-privilege',
      title: '文件系统与网络的最小权限',
      summary: '默认拒绝、按需开通 —— 这条你已经熟的原则在这里同样有效。',
      estimatedMinutes: 20,
      difficulty: 'advanced',
      hasBody: true,
      status: 'drafting',
      keywords: ['least-privilege', 'allowlist'],
      checkpoints: [
        {
          id: 'filesystem-policy',
          basis: 'inferred',
          question: '给 agent 划文件系统权限，默认该设成什么？',
          answer:
            '**默认只读、默认很小、写操作白名单化**。具体三条：能读的目录限定在任务真正需要的范围（不是整个工作区，更不是用户主目录）；写操作单独开一个可丢弃的工作目录，任务结束就清理；对敏感路径（凭据文件、SSH 目录、云配置）一律显式拒绝，而不是指望「它大概不会去读」。还有一条容易漏：**路径校验必须防住符号链接与相对路径穿越** —— 只检查字符串前缀是不够的，一个指向外部的软链接能让你的白名单失效。这类检查和你写过的任何文件上传校验是同一类问题。',
        },
        {
          id: 'network-policy',
          basis: 'inferred',
          question: '网络的默认策略为什么应该是「禁止出网」？',
          answer:
            '因为出网是**数据外泄的最后一步**。agent 读到的内容（可能含敏感信息、也可能含注入指令）如果同时具备「读敏感数据」和「发任意请求」两项能力，那么把数据发出去只需要一次工具调用。默认禁止之后按需放行，能把这条路径关掉。放行时也要注意不是简单的域名白名单就够：**要防内网地址与云元数据端点**（本站 BYOK 中转端点的 SSRF 校验就是这个问题 —— 只允许 https、禁止内网 IP、禁止云元数据地址），并且要防 DNS 重绑定这类绕过。判断标准可以简化成一句：**如果这个 agent 不需要访问互联网就能完成任务，那就别给它出网权限。**',
        },
      ],
      resourceIds: ['claude-agent-sdk', 'mcp-docs'],
    },
    {
      id: 'sandboxing/secrets',
      chapterId: 'sandboxing',
      slug: 'secrets',
      title: '凭据不该进入上下文',
      summary: '一旦被模型看到，它就同时存在于历史、日志与下一次请求里。',
      estimatedMinutes: 20,
      difficulty: 'advanced',
      hasBody: true,
      status: 'drafting',
      keywords: ['secrets', 'credentials'],
      checkpoints: [
        {
          id: 'why-secrets-out-of-context',
          basis: 'inferred',
          question: '为什么「不要让凭据进入模型上下文」是一条硬要求？',
          answer:
            '因为它一旦进入，就会**在三个地方同时留下副本**：对话历史（后续每一轮都会重发）、你的追踪日志、以及上游厂商的请求记录。而且它无法可靠撤回 —— 你没法保证历史被完整清理，也没法保证日志被删除。再叠加两个放大因素：模型可能把凭据**回显在输出里**（于是进了更多地方），以及提示注入可以诱导它把上下文里的内容发出去。所以正确做法是让凭据在**使用它的那一层**存在，而不是在模型那一层：工具实现内部从环境或密钥服务读取，模型只看到「需要认证」这个事实。这和本站 Playground 的处理一致 —— Key 走请求头、不放在请求体里，因为请求体更容易被中间层记录。',
        },
        {
          id: 'secret-hygiene',
          basis: 'inferred',
          question: '除了不放进上下文，凭据管理还有哪几条要做到？',
          answer:
            '四条：**权限最小** —— 给 agent 用的凭据只开它需要的 scope，不要复用一个全权限的主账号；**可轮换且定期轮换** —— 假设它迟早会泄露，轮换成本要低；**可归因** —— 审计日志里能区分「这次调用是 agent 发的还是人发的」（专用凭据天然满足这一点）；以及**出口过滤** —— 在把日志与追踪落盘前做一次凭据模式扫描，防止某个工具把 key 拼进了返回内容里而被记录下来。最后一条看起来多余，但它能抓住「凭据意外泄漏到上下文」这类事故的第一次发生。',
        },
      ],
      resourceIds: ['claude-api-docs', 'twelve-factor-agents'],
    },
    {
      id: 'sandboxing/execution-policy',
      chapterId: 'sandboxing',
      slug: 'execution-policy',
      title: '执行策略与审计',
      summary: '上限、审计与可终止，是让「能动手」这件事可控的三件套。',
      estimatedMinutes: 18,
      difficulty: 'intermediate',
      hasBody: true,
      status: 'drafting',
      keywords: ['limits', 'audit'],
      checkpoints: [
        {
          id: 'execution-limits',
          basis: 'inferred',
          question: '执行层需要设哪些上限？',
          answer:
            '至少四类：**时间**（单次调用超时、整个任务墙钟上限）、**资源**（CPU、内存、磁盘、进程数 —— 没有这些，一段跑飞的代码能拖垮整台机器）、**调用次数**（同一个工具被调用多少次后中断）、以及**输出体积**（工具返回内容的大小上限，防止一次读取把上下文撑爆）。这和第 9 章 agent 循环的预算是同一种设计，只是作用在更外一层：**循环预算约束模型的行为，执行策略约束代码的行为**，两者都要有，因为它们的失效模式不重叠。',
        },
        {
          id: 'audit-trail',
          basis: 'inferred',
          question: '审计日志该记到什么粒度？',
          answer:
            '粒度要足以回答三个问题：**谁**（哪个用户、哪个 agent、哪次任务）、**做了什么**（具体动作、目标、参数）、以及**结果如何**（成功、失败、还是状态未知）。关键是第三项要如实记录「状态未知」这个中间态 —— 很多系统只记成功与失败，而状态未知恰恰是最需要人工介入的那一类。另外要记**触发来源**：这个动作是模型自主发起的，还是人确认过的。这条在事后追责与改进时价值极高 —— 它能告诉你哪些动作经常需要确认（说明权限划得过宽，或者工具设计有问题）。',
        },
      ],
      resourceIds: ['claude-agent-sdk', 'openhands'],
    },
  ],
  resourceIds: ['claude-agent-sdk', 'twelve-factor-agents', 'openhands', 'mcp-docs', 'ai-engineering-huyen'],
  backendMapping: {
    analogy: '沙箱 ≈ 你给一个第三方服务划的权限边界：最小权限、独立身份、可审计、可随时收回',
    transferable: [
      '容器与命名空间、挂载与网络策略，这些是后端的日常',
      '最小权限与专用身份：运维里怎么给服务账号划权，这里就怎么给 agent 划',
      'SSRF 防护：禁止内网与云元数据端点，与 BYOK 端点遇到的是同一个问题',
    ],
    pitfalls: [
      '只做参数校验就当隔离：模型的行为空间远大于你设计的工具语义',
      '挂载了读写的工作区，却以为容器隔离已经生效',
      '开着出网权限，同时又能读到敏感数据 —— 这是一条完整的外泄通道',
      '把凭据作为环境变量传进执行环境，或让它出现在模型上下文里',
      '只记录成功与失败，丢掉了「状态未知」这个最需要人工介入的中间态',
    ],
    cost: 'medium',
  },
  status: 'published',
  updatedAt: '2026-10-08',
  verifiedAt: '2026-10-08',
} satisfies Chapter;
