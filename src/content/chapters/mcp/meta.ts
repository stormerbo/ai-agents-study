import type { Chapter } from '@/content/curriculum/schema';

export const chapter = {
  id: 'mcp',
  stageId: 'stage-3-orchestration',
  order: 14,
  title: 'MCP',
  subtitle: '工具生态的协议层',
  summary:
    'MCP 解决的不是「怎么调用工具」，而是「怎么让工具可以被复用」—— 把 N×M 的对接工作变成 N+M。这一章讲清它的角色与能力边界、2026 年那次把协议改成无状态的破坏性修订，以及为什么接入第三方 server 本质上是在运行别人的代码。',
  outcomes: [
    '能说清 MCP 与「自己写工具」的取舍边界，以及它不负责什么',
    '能读懂当前规范版本的关键接口，并识别旧教程里的过时写法',
    '能评估接入一个第三方 MCP server 的安全代价',
  ],
  depth: 'deep',
  difficulty: 'intermediate',
  estimatedMinutes: 100,
  tags: ['mcp', 'protocol', 'tools'],
  prerequisiteIds: ['agent-loop', 'tool-calling'],
  lessons: [
    {
      id: 'mcp/why-protocol',
      chapterId: 'mcp',
      slug: 'why-protocol',
      title: '为什么要一个协议',
      summary: 'N×M 变 N+M —— 但先确认这个乘法在你的场景里成立。',
      estimatedMinutes: 18,
      difficulty: 'beginner',
      hasBody: true,
      status: 'drafting',
      keywords: ['mcp', 'integration'],
      checkpoints: [
        {
          id: 'nxm-problem',
          basis: 'inferred',
          question: 'MCP 解决的 N×M 问题具体是什么？',
          answer:
            '假设你有 N 个 AI 应用、要接 M 个外部系统（数据库、文件系统、工单系统……）。各写各的适配，工作量是 N×M，而且每一对都要单独维护。\n\n有了协议之后，每个外部系统只实现一次 server（M 份），每个应用只实现一次 client（N 份），总工作量变成 N+M。\n\n但要注意这个收益的前提：**同一个外部系统确实会被多个应用接入**。如果你只有一个应用、只接三五个系统，自己写工具（第 4 章那种）反而更直接 —— 引入协议只增加了一层抽象，却没有摊薄任何东西。',
        },
        {
          id: 'mcp-scope',
          basis: 'documented',
          question: 'MCP 不负责什么？这个边界为什么重要？',
          answer:
            '官方架构文档写得很明确：MCP **只负责上下文交换的协议**，它不规定 AI 应用如何使用模型、也不管理规定上下文的方式。\n\n也就是说，MCP 不是 agent 框架，它不替你决定循环、预算、上下文顺序与提示词。这些仍然由第 9 章那些零件负责。把 MCP 当成「有了它就有 agent 了」是常见的误解 —— 它只是把工具这一项标准化了。\n\n这个边界也解释了它为什么能和任何框架共存：协议层与编排层正交。',
          sourceIds: ['mcp-docs'],
        },
      ],
      resourceIds: ['mcp-docs'],
    },
    {
      id: 'mcp/roles-and-capabilities',
      chapterId: 'mcp',
      slug: 'roles-and-capabilities',
      title: '三个角色与它们交换什么',
      summary: 'host / client / server，以及 tools、resources、prompts 三类能力。',
      estimatedMinutes: 20,
      difficulty: 'intermediate',
      hasBody: true,
      status: 'drafting',
      keywords: ['host', 'client', 'server', 'capabilities'],
      checkpoints: [
        {
          id: 'three-roles',
          basis: 'documented',
          question: 'host、client、server 三者的关系是什么？',
          answer:
            '**host** 是用户面对的那个 AI 应用（比如一个编码助手）。它要为**每一个** MCP server 创建一个对应的 **client**，每个 client 与自己的 server 维持一条专属连接。**server** 则对外暴露能力。\n\n所以 client 不是「一个客户端」，而是「一条连接的代表」。这个设计让 host 可以同时连多个 server 而不必把它们混在一起 —— 每个 server 的能力边界与生命周期各自独立。',
          sourceIds: ['mcp-docs'],
        },
        {
          id: 'capability-kinds',
          basis: 'documented',
          question: 'MCP server 能对外提供哪几类东西？它们分别适合什么？',
          answer:
            '三类主要能力：**tools**（可被模型调用的动作，有副作用与否都可能）、**resources**（可读的上下文数据，类似文件或记录）、**prompts**（预设的提示模板）。\n\n选择哪种取决于「谁来决定用它」：tools 是**模型**决定要不要调；resources 通常是**应用**决定要不要放进上下文；prompts 多半是**用户**主动挑选的入口。这个区分在接入第三方 server 时很重要 —— 它决定了你能在多大程度上控制「什么东西会进入模型的上下文」。',
          sourceIds: ['mcp-docs'],
        },
      ],
      resourceIds: ['mcp-docs'],
    },
    {
      id: 'mcp/stateless-2026',
      chapterId: 'mcp',
      slug: 'stateless-2026',
      title: '2026-07-28：协议被改成无状态',
      summary: '一次破坏性修订 —— 旧教程里的握手与 session 写法已经全部作废。',
      estimatedMinutes: 24,
      difficulty: 'advanced',
      hasBody: true,
      status: 'drafting',
      keywords: ['spec', 'breaking-change', 'stateless'],
      checkpoints: [
        {
          id: 'what-changed',
          basis: 'documented',
          question: '2026-07-28 版本相比上一版，最核心的变化是什么？',
          answer:
            '核心是**把有状态的协议改成无状态**：移除了 initialize / notifications-initialized 握手，也移除了协议级的 session 与 Mcp-Session-Id 头。现在每个请求自己携带协议版本与客户端能力（放在 _meta 里），版本不匹配会返回 UnsupportedProtocolVersionError；同时新增了 server/discover，让 server 主动声明自己支持的版本与能力。\n\n配套的还有几处替换：资源订阅从 resources/subscribe 改为 subscriptions/listen（一条长连接流）；ping、logging/setLevel 被移除，日志级别改为逐请求传递；任务相关方法从核心协议降级为官方扩展。\n\n**对你的直接影响**：任何写着「先 initialize 再调用」的教程或示例代码，在这个版本上都不再适用。',
          sourceIds: ['mcp-spec-changelog'],
        },
        {
          id: 'mrtr',
          basis: 'documented',
          question: '什么是 MRTR？它替换掉了原来的什么做法？',
          answer:
            'MRTR 是**多轮往返请求**（Multi Round-Trip Requests）。它替换的是「服务端主动向客户端发请求」这一类做法 —— 原本 roots/list、sampling/createMessage、elicitation/create 都是 server 主动发起的。\n\n改成 MRTR 之后，server 不再主动发请求，而是返回一个 InputRequiredResult（resultType 为 input_required），由客户端补上所需输入后再调用一次。这样一次交互的**发起权始终在客户端**，与协议整体无状态化的方向一致。\n\n顺带说，这也让「服务端能不能反过来用你的模型（sampling）」这件事从「随时可发生」变成了「在明确的一轮里发生」—— 对安全边界是个改善。',
          sourceIds: ['mcp-spec-changelog'],
        },
      ],
      resourceIds: ['mcp-docs', 'mcp-spec-changelog'],
    },
    {
      id: 'mcp/build-a-server',
      chapterId: 'mcp',
      slug: 'build-a-server',
      title: '写一个最小 server',
      summary: '把第 4 章的工具，换一种方式暴露出去。',
      estimatedMinutes: 22,
      difficulty: 'intermediate',
      hasBody: true,
      status: 'drafting',
      keywords: ['sdk', 'server'],
      checkpoints: [
        {
          id: 'server-minimum',
          basis: 'inferred',
          question: '自己写一个 MCP server，最少要实现什么？',
          answer:
            '一个可用的 server 至少要能**声明能力**（我提供哪些工具）并**响应调用**。用官方 SDK 时，你通常写的是「注册工具 + 实现函数」这两步，协议细节（能力协商、版本、消息编解码）由 SDK 处理。\n\n要注意的是第 4 章的结论在这里**原样成立**：工具名要匹配 ^[a-zA-Z0-9_-]+$ 且唯一、schema 顶层必须是 object、描述本身就是 prompt。协议换了，这些约束没变 —— 因为它们是工具设计的约束，不是某个 API 的约束。',
        },
        {
          id: 'pick-transport',
          basis: 'documented',
          question: '本地 server 与远程 server 在选择上有什么不同？',
          answer:
            '本地 server 通常走 STDIO：由 host 作为子进程启动，生命周期与 host 绑定，适合访问本地文件、开发工具这一类。远程 server 走 HTTP 传输，可以被多个客户端共享，但随之而来的是网络、鉴权与多租户隔离的问题。\n\n选择的分水岭不是「方便」，而是**信任与归属**：本地 server 是你自己启动的进程，边界清楚；远程 server 是别人运营的服务，你要按第三方依赖来对待（下一节展开）。',
          sourceIds: ['mcp-docs'],
        },
      ],
      resourceIds: ['mcp-docs'],
    },
    {
      id: 'mcp/security-boundary',
      chapterId: 'mcp',
      slug: 'security-boundary',
      title: '安全边界：接入第三方 server 意味着什么',
      summary: '你在运行别人的代码，并且把它的描述放进了模型的上下文。',
      estimatedMinutes: 22,
      difficulty: 'expert',
      hasBody: true,
      status: 'drafting',
      keywords: ['security', 'prompt-injection', 'permissions'],
      checkpoints: [
        {
          id: 'two-risks',
          basis: 'inferred',
          question: '接入一个第三方 MCP server，会同时引入哪两类风险？',
          answer:
            '**一是代码执行风险**：server 是一个你能触及的外部程序，它拿到的是你授予的权限。给它文件系统访问、数据库连接或凭据，就等于把这些交给了它的实现质量。\n\n**二是上下文注入风险**：server 提供的工具描述与 resource 内容会**直接进入模型的上下文**。第 4 章讲过工具描述就是 prompt —— 那么一个不受你控制的描述，就是一段不受你控制的 prompt。它可以引导模型去调用别的工具、泄露上下文，或者在返回内容里夹带指令（第 2 章实测过提示注入的多种形态）。\n\n两类风险的应对方向不同：前者靠权限最小化与隔离，后者靠把外部内容当**数据**而不是指令来对待。',
        },
        {
          id: 'least-privilege',
          basis: 'inferred',
          question: '工程上可以用哪些手段把这两类风险压下来？',
          answer:
            '四条，按落地成本排序：\n\n1. **权限最小化** —— 只授予这个 server 完成其职责所必需的访问，尤其是有副作用的操作要单独确认。\n2. **把外部内容标记为数据** —— 在上下文里明确区分「你的指令」与「工具返回的内容」。第 2 章的实测表明这只能挡住一部分注入（加 XML 标签把格式操纵从 6/6 降到 2/6，但内容操纵仍 6/6），所以它是**缓解**不是**解决**。\n3. **对不可逆动作做人工确认** —— 与第 9 章的权限收口是同一件事，放在工具注册表里统一实现。\n4. **默认不相信远端声明** —— server 声称的能力、资源范围都应当被你的代码校验一遍，而不是照单全收。\n\n最根本的一条判断是：**引入第三方 server 的决策，本质上等于一次第三方依赖引入。** 该有的评审、锁版本、可移除性，一个都不能少。',
        },
      ],
      resourceIds: ['mcp-docs', 'mcp-spec-changelog'],
    },
  ],
  resourceIds: ['mcp-docs', 'mcp-spec-changelog', 'claude-agent-sdk'],
  backendMapping: {
    analogy:
      'MCP ≈ 给工具生态定一套 RPC 协议：和当年从「每个服务各写各的客户端」走向标准协议是同一件事',
    transferable: [
      '接口协议设计的经验：能力协商、版本兼容、错误语义',
      '第三方依赖的治理习惯：权限最小化、锁版本、可移除',
      '传输选型（本地进程 vs 远程服务）的取舍判断',
    ],
    pitfalls: [
      '把 MCP 当成 agent 框架：它只管上下文交换，不管循环与预算',
      '照抄旧教程里的 initialize 握手与 session 写法 —— 当前版本已移除',
      '默认相信第三方 server 的工具描述与返回内容：它们是会进入上下文的不可信输入',
      '为了「标准化」而引入协议，但实际只有一个应用、三五个工具',
    ],
    cost: 'medium',
  },
  status: 'published',
  updatedAt: '2026-10-08',
  verifiedAt: '2026-10-08',
} satisfies Chapter;
