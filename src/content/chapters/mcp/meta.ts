import type { Chapter } from '@/content/curriculum/schema';

export const chapter = {
  id: 'mcp',
  stageId: 'stage-3-orchestration',
  order: 14,
  title: 'MCP',
  subtitle: '工具生态的协议层',
  summary:
    'MCP 标准化 host/client 与能力提供方之间的接口，减少 N×M 成对集成，但不消除业务适配、授权和运维成本。这一章讲清它的角色与边界、2026-07-28 无状态协议路径，以及接入第三方 server 的信任代价。',
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
            '假设有 N 个 host 应用和 M 个能力提供方。直接为每一对组合维护专用集成，最多形成 N×M 个接口；采用 MCP 后，概念上是 N 个 host 侧 client 接入 + M 个 server 适配，即 N+M 个边界。它减少成对接口的重复，但不消除业务适配、host 授权、配置和运维，也不表示工程工时必然按同一比例下降。\n\n收益更可能出现在两端都能被多个实现复用，且工具语义、版本和权限范围兼容的场景。一对一也可能因现成 SDK、治理要求或未来复用而值得使用；是否引入要比较抽象收益与部署、安全和维护成本。',
        },
        {
          id: 'mcp-scope',
          basis: 'documented',
          question: 'MCP 不负责什么？这个边界为什么重要？',
          answer:
            '官方架构文档将 MCP 定义为 AI 应用之间交换上下文的协议。它标准化 host、client 与 server 的消息和能力接口，但不替应用决定使用哪个模型、怎样组织 agent loop，或具体的业务数据与动作授权。协议本身也包含授权与安全要求/建议，因此不能把它概括成“只搬运工具消息”或“完全不负责安全”。对 tools 来说，规范将其描述为 model-controlled，但也明确允许 host 用其他 UI 交互模式；MCP 不强制每个 host 都把工具定义直接交给模型。\n\n应用仍要落实自己的模型调用、上下文编排、预算和授权策略；MCP 的 Tasks 等扩展提供特定协议能力，不会替代整套 agent runtime。',
          sourceIds: ['mcp-docs', 'mcp-security-best-practices-2026', 'mcp-2026-tools-spec'],
        },
      ],
      resourceIds: ['mcp-docs', 'mcp-2026-spec', 'mcp-security-best-practices-2026'],
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
            '**host** 是用户面对的那个 AI 应用。host 通常按 MCP server 分别创建 client，以隔离配置、能力与调用策略；但 client 对象不等于一条永久连接。旧版协议可在连接或 session 上保留协商状态；2026-07-28 版逐请求携带协议元数据，底层仍可能是长寿命 stdio 进程或按请求往返的 Streamable HTTP。**server** 则对外暴露能力。按 server 划分 client 是常见的 host 实现方式，不是 MCP 规范强制的连接或 session 模型。',
          sourceIds: ['mcp-docs', 'mcp-2026-spec'],
        },
        {
          id: 'capability-kinds',
          basis: 'documented',
          question: 'MCP server 能对外提供哪几类能力？“谁决定使用”是协议强制流程吗？',
          answer:
            '三类主要能力是 tools（可调用操作）、resources（以 URI 标识的可读数据）和 prompts（server 提供的结构化消息）。常见交互模式分别是 tools 由模型决定何时调用、resources 由应用决定如何纳入上下文、prompts 设计为 user-controlled；这些是设计意图，不是 MCP 强制的 host UI。Tools 规范允许其他 UI 模式，resources 可按规则或模型选择，prompts 的内容由 server 提供。Host 仍须负责暴露、策略、授权和模型 API 适配。',
          sourceIds: ['mcp-2026-tools-spec', 'mcp-2026-resources-spec', 'mcp-2026-prompts-spec'],
        },
        {
          id: 'resource-prompt-trust-boundary',
          basis: 'documented',
          question: '第三方 server 的 resources 或 prompts 是否因“只读 / 用户触发”而可信？',
          answer:
            '不是。Resources 的访问控制和 URI 校验仍需落实；返回内容也可能泄露敏感数据或带有提示注入内容。Prompts 的内容由 server 提供，user-controlled 指使用时机，不代表内容可信。Host 应按身份授权、最小化数据，并在模型上下文中保留来源与信任边界。',
          sourceIds: ['mcp-2026-resources-spec', 'mcp-2026-prompts-spec', 'mcp-security-best-practices-2026'],
        },
        {
          id: 'prompt-message-shape',
          basis: 'documented',
          question: 'prompts/get 是否保证返回一条普通 user 消息？',
          answer:
            '不保证。Prompt 定义中的 arguments 是可选列表；prompts/get 返回已解析的 messages，可包含 user 或 assistant role，内容也可以是图像、音频、resource link 或 embedded resource。MCP 定义该协议结果，不规定 host 必须将其渲染为一条 user 消息或如何映射到 provider API。',
          sourceIds: ['mcp-2026-prompts-spec'],
        },
        {
          id: 'resource-wire-shape',
          basis: 'documented',
          question: 'Resource 哪些字段必需？resources/read 的结果如何区分完成状态？',
          answer:
            'Resource 定义要求 uri 与 name；mimeType 是可选字段。2026-07-28 结果响应必须包含 resultType，例如 complete。每个现代 MCP 请求还必须在 params._meta 中携带协议版本与 client capabilities。',
          sourceIds: ['mcp-2026-resources-spec', 'mcp-2026-spec'],
        },
        {
          id: 'server-discovery-boundary',
          basis: 'documented',
          question: '2026-07-28 的 server/discover 是 server 还是 client 的可选功能？',
          answer:
            'server 必须实现 server/discover；client 是否先调用它是可选的，也可以直接发送其他 RPC，并处理 UnsupportedProtocolVersionError。',
          sourceIds: ['mcp-2026-discovery-spec', 'mcp-2026-spec'],
        },
      ],
      resourceIds: [
        'mcp-docs',
        'mcp-2026-spec',
        'mcp-2026-tools-spec',
        'mcp-2026-discovery-spec',
        'mcp-2026-resources-spec',
        'mcp-2026-prompts-spec',
        'mcp-security-best-practices-2026',
      ],
    },
    {
      id: 'mcp/stateless-2026',
      chapterId: 'mcp',
      slug: 'stateless-2026',
      title: '2026-07-28：协议被改成无状态',
      summary: '现代路径移除握手与协议级 session；兼容旧版本时仍须保留 legacy 分支。',
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
            '核心是**把有状态的协议改成无状态**：移除了 initialize / notifications-initialized 握手，也移除了协议级的 session 与 Mcp-Session-Id 头。现在每个请求自己携带协议版本与客户端能力（放在 _meta 里），版本不匹配会返回 JSON-RPC error code `-32022`（Unsupported protocol version）；同时新增了 server/discover，让 server 主动声明自己支持的版本与能力。\n\n配套的还有几处替换：资源订阅从 resources/subscribe 改为 subscriptions/listen（一条长连接流）；ping、logging/setLevel 被移除，日志级别改为逐请求传递；任务相关方法从核心协议降级为官方扩展。\n\n**对你的直接影响**：旧版 initialize 示例不能直接用于 2026-07-28 现代路径；dual-era 实现仍需按版本与传输保留 legacy 分支。',
          sourceIds: ['mcp-2026-spec', 'mcp-spec-changelog', 'mcp-streamable-http-2026', 'mcp-subscriptions-2026', 'mcp-caching-2026', 'mcp-sep-2260', 'mcp-sep-2322'],
        },
        {
          id: 'legacy-version-scope',
          basis: 'documented',
          question: '“现代协议逐请求校验版本”能否推广成“所有有状态协议只能在握手时校验一次”？',
          answer:
            '不能。2026-07-28 现代 MCP 在每条请求中携带协议版本并独立接受或拒绝；2025-11-25 及更早的 legacy MCP 在 initialize/session 生命周期中确定版本。这个对照说明两种 MCP era 的版本处理差异，不是对所有有状态协议的通则。',
          sourceIds: ['mcp-2026-spec', 'mcp-spec-changelog'],
        },
        {
          id: 'streamable-http-request-headers',
          basis: 'documented',
          question: '2026-07-28 Streamable HTTP 请求除 JSON-RPC body 外还需哪些标准头？',
          answer:
            '每个 POST 都需要 MCP-Protocol-Version 与 Mcp-Method，并与 body 一致；tools/call、resources/read、prompts/get 还需要对应 params.name 或 params.uri 的 Mcp-Name。stdio 不使用这些 HTTP binding headers。',
          sourceIds: ['mcp-streamable-http-2026'],
        },
        {
          id: 'cacheable-result-boundary',
          basis: 'documented',
          question: '哪些 2026-07-28 MCP 结果必须携带缓存提示，MRTR 重试结果能否缓存？',
          answer:
            'complete 的 server/discover、tools/list、prompts/list、resources/list、resources/templates/list 与 resources/read 结果必须携带 ttlMs 和 cacheScope；input_required 中间结果及带 inputResponses 或 requestState 的 MRTR 重试不得缓存。cacheScope=private 的缓存不可跨授权上下文复用。',
          sourceIds: ['mcp-caching-2026'],
        },
        {
          id: 'server-tool-input-validation',
          basis: 'documented',
          question: 'tools/call 的 arguments 符合 schema 是否可以只交给模型负责？',
          answer:
            '不可以。server 必须在处理工具调用前验证实际输入；模型提供的 arguments 不能替代服务端校验。本节示例拒绝畸形对象和类型错误，但仍是本地教学实现，不是完整生产 server。',
          sourceIds: ['mcp-2026-tools-spec'],
        },
        {
          id: 'mrtr',
          basis: 'documented',
          question: '什么是 MRTR？它替换掉了原来的什么做法？',
          answer:
            'MRTR 是**多轮往返请求**（Multi Round-Trip Requests）。它替换的是旧版 server→client JSON-RPC request 通道；旧版的 roots/list、sampling/createMessage、elicitation/create 必须关联到一个正在处理的 client request，不是任意时刻都能独立发起。\n\n改成 MRTR 之后，server 把待处理输入放进 InputRequiredResult，由 client 以新 request ID 重试原始请求。部分 SDK 可能自动满足输入并重试；MRTR 不保证展示给用户或人工审批，安全决策仍由 host 与 server 的策略承担。',
          sourceIds: ['mcp-2026-spec', 'mcp-spec-changelog', 'mcp-caching-2026', 'mcp-sep-2260', 'mcp-sep-2322'],
        },
      ],
      resourceIds: ['mcp-docs', 'mcp-2026-spec', 'mcp-2026-tools-spec', 'mcp-spec-changelog', 'mcp-streamable-http-2026', 'mcp-subscriptions-2026', 'mcp-caching-2026', 'mcp-sep-2260', 'mcp-sep-2322'],
    },
    {
      id: 'mcp/build-a-server',
      chapterId: 'mcp',
      slug: 'build-a-server',
      title: '写一个最小 server',
      summary: '手写一个现代 stdio 工具型 server，并分清协议核心与远程 HTTP transport 的边界。',
      estimatedMinutes: 22,
      difficulty: 'intermediate',
      hasBody: true,
      status: 'drafting',
      keywords: ['sdk', 'server'],
      checkpoints: [
        {
          id: 'server-minimum',
          basis: 'documented',
          question: '自己写一个 MCP server，最少要实现什么？',
          answer:
            '本文实现的是一个**工具型** MCP server，而不是所有 server 都必须提供工具：这个例子声明 tools 能力、实现 `tools/list` 与 `tools/call`，并按 2026-07-28 规范实现 `server/discover`。用官方 SDK 时，你通常写「注册工具 + 实现函数」，协议细节（版本、消息编解码、传输）由 SDK 处理；若手写，就必须自己遵守对应版本与传输的要求。\n\nMCP 2026-07-28 对工具名的措辞是 **SHOULD**：建议长度为 1–128 个字符、区分大小写、使用 ASCII 字母/数字/`_`/`-`/`.`，并在同一 server 内唯一。这是协议建议，不是 `^[a-zA-Z0-9_-]+$` 这样的 MUST 正则；例如点号在 MCP 建议字符中。特定模型 API 或 SDK 可能另有约束，需分别遵守。`inputSchema` 必须是有效的 JSON Schema 对象；server 仍必须验证实际输入。',
          sourceIds: ['mcp-2026-spec', 'mcp-2026-tools-spec'],
        },
        {
          id: 'pick-transport',
          basis: 'documented',
          question: '本地 server 与远程 server 在选择上有什么不同？',
          answer:
            '本地 server 通常走 STDIO：由 host 作为子进程启动，生命周期与 host 绑定，适合访问本地文件、开发工具这一类。远程 server 可使用 Streamable HTTP，但每请求 POST 的版本/方法/名称头、JSON/SSE 响应与 Origin 校验都属于 transport 实现；不能把 stdio 示例直接搬到 HTTP。远程 server 可以被多个客户端共享，但随之而来的是网络、鉴权与多租户隔离的问题。\n\n选择的分水岭不是「方便」，而是**信任与归属**：本地 server 是你自己启动的进程，边界清楚；远程 server 是别人运营的服务，你要按第三方依赖来对待（下一节展开）。',
          sourceIds: ['mcp-docs', 'mcp-streamable-http-2026'],
        },
      ],
      resourceIds: ['mcp-docs', 'mcp-2026-spec', 'mcp-2026-tools-spec', 'mcp-streamable-http-2026', 'mcp-caching-2026', 'mcp-sep-2322'],
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
            '**一是数据暴露与本地执行风险**：host 实际发送的工具参数、协议元数据和 HTTP 授权信息会到达对应 server；本地 stdio server 则以启动用户权限运行，能接触哪些文件、环境变量和网络由操作系统/sandbox 决定。不要假设工具调用会自动把整个对话发送给 server，也不要把远程 server 与本地进程的权限模型混在一起。\n\n**二是动作越权与上下文注入风险**：工具定义、resource 内容和 tool result 可能影响模型选择或输出；工具名、描述、注解与 schema 是接口元数据，不能证明实现行为或授权范围。模型可能依据这些内容提出调用，host 必须在执行边界独立授权。\n\n防线分别落在数据最小化、进程隔离、host 调用策略和对外部内容的处理上；信任评审能提供供应链证据，但不是运行时授权。',
        },
        {
          id: 'least-privilege',
          basis: 'inferred',
          question: '工程上可以用哪些手段把这两类风险压下来？',
          answer:
            '**先盘点，再收口**：\n\n1. **最小化数据** —— host 只把该次调用需要的字段传给 server；本地进程则只获得所需文件、环境变量和网络权限。\n2. **验证外部输入与输出** —— 工具描述、resource 和 tool result 都是外部数据；把它们与指令分开，并用程序校验结构和业务约束。第 2 章留存的 DeepSeek XML 标签命中率缺逐次请求、响应与评分器，不能独立复核或当作防御率。\n3. **在 host 执行策略** —— 用本地 server ID + 工具名 allowlist，默认拒绝未登记项；敏感操作由 host 实施确认和授权。\n4. **降低运行权限** —— 对本地进程用 sandbox 和受限网络；对远端服务限制凭据范围与下游权限，并记录审计。\n\n供应链评审、固定版本和可移除性有助于风险管理，但都不能替代逐次授权与隔离。',
        },
        {
          id: 'protocol-security-controls',
          basis: 'documented',
          question: 'MCP 2026-07-28 对工具 server/client 的安全控制有哪些明确要求或建议？',
          answer: '工具 server MUST 校验输入、实施访问控制、限流并清理输出；client SHOULD 在敏感操作前请求用户确认、向用户展示工具输入、把结果校验后再交给模型、为工具调用设置超时并记录审计日志。Streamable HTTP 还有 Origin 校验要求。本规范提供协议层控制基线，应用仍需定义具体的数据最小化与业务授权策略。',
          sourceIds: ['mcp-security-best-practices-2026', 'mcp-streamable-http-2026'],
        },
        {
          id: 'remote-ssrf-boundary',
          basis: 'documented',
          question: '远程 MCP 场景下，如何区分 server 出站网络风险与 client-side SSRF？',
          answer:
            '两者位于不同执行边界。远程 server 的网络可达性由其服务端凭据、部署和 egress policy 决定；MCP 不会把它限制在本次工具参数或自有资源。client 处理 OAuth resource/authorization metadata 时也会主动抓取 URL，恶意 metadata、重定向或 DNS 变化可能诱发 SSRF。部署端应限制出站网络；client 应按运行环境校验 OAuth URL 与每次 redirect，并防止访问不允许的内部地址。',
          sourceIds: ['mcp-security-best-practices-2026'],
        },
        {
          id: 'mrtr-not-approval',
          basis: 'documented',
          question: 'MRTR 的 `input_required` 是否保证用户能看到并审批 server 的请求？',
          answer: '不保证。MRTR 将待补输入编码在原请求的结果中，客户端可携带 `inputResponses` 和 `requestState` 以新的 JSON-RPC id 重试；具体是否展示给用户或由 SDK 自动处理，取决于 host/SDK。host 必须另外实现授权与确认策略，不能把 MRTR 等同于人工审批。',
          sourceIds: ['mcp-sep-2322'],
        },
      ],
      resourceIds: ['mcp-docs', 'mcp-2026-spec', 'mcp-spec-changelog', 'mcp-security-best-practices-2026', 'mcp-sep-2322', 'mcp-sep-2260'],
    },
    {
      id: 'mcp/remote-authorization',
      chapterId: 'mcp',
      slug: 'remote-authorization',
      title: '远程授权：token 属于哪个资源',
      summary: '区分 stdio 凭据与 HTTP OAuth，验证 token 面向的 MCP resource，并隔离下游授权。',
      estimatedMinutes: 30,
      difficulty: 'advanced',
      hasBody: true,
      status: 'drafting',
      keywords: ['oauth', 'authorization', 'audience', 'stdio', 'token-passthrough'],
      checkpoints: [
        {
          id: 'transport-auth-boundary',
          basis: 'documented',
          question: 'MCP 授权规范分别建议 HTTP 与 stdio 如何处理授权？',
          answer: 'MCP 授权规范为 HTTP-based transport 定义远程 OAuth 流程；支持授权的 HTTP 实现 SHOULD 遵循它。STDIO 实现 SHOULD NOT 使用该 HTTP OAuth 流程，而应从环境取得凭据。stdio host 仍要控制是否启动子进程以及传入哪些权限和秘密。',
          sourceIds: ['mcp-authorization-2026'],
        },
        {
          id: 'resource-audience',
          basis: 'documented',
          question: 'MCP client 请求中带了 `resource` 参数，是否足以证明 token 可以被 MCP server 接受？',
          answer: '不足。client 必须将目标 MCP server 的 canonical resource URI 放入 authorization 与 token request；server 仍必须独立验证 access token，并确认 audience 指向自己。请求参数不能替代服务端对签名、issuer、有效期与 audience 的检查。',
          sourceIds: ['mcp-authorization-2026'],
        },
        {
          id: 'downstream-token',
          basis: 'documented',
          question: 'MCP server 能否把收到的 bearer token 原样转发给下游 API？',
          answer: '不能。该 token 是发给 MCP resource 的访问凭据，不是下游 API 的凭据；server 需为下游资源使用独立授权或明确设计的委托流程。原样透传会扩大凭据受众与权限边界。',
          sourceIds: ['mcp-authorization-2026', 'mcp-security-best-practices-2026'],
        },
        {
          id: 'client-registration-priority',
          basis: 'documented',
          question: '2026-07-28 MCP 授权规范规定了哪些 client registration 方式与选择顺序？',
          answer:
            'client 必须通过预注册、CIMD 或 DCR 取得 client ID。若 client 支持多种方式，规范建议先用该 server 的预注册信息，再看 AS metadata 是否声明支持 CIMD，再把 DCR 作为 AS 支持时的回退；都不可用时询问用户。CIMD 是 SHOULD 支持，DCR 是为兼容而 MAY 支持且已 deprecated。预注册和 DCR 凭据需绑定签发它们的 issuer。',
          sourceIds: ['mcp-authorization-2026'],
        },
        {
          id: 'authorization-code-integrity',
          basis: 'documented',
          question: 'MCP OAuth client 如何防止授权码拦截、issuer mix-up 与伪造响应？',
          answer:
            '授权码流程必须使用 PKCE，确认 AS metadata 声明 PKCE 支持；技术上可行时用 S256，不支持则拒绝继续。client 应发送并校验 state。client 还要把经过验证的 AS issuer 与同一请求的 PKCE verifier/state 关联；若 metadata 声明支持 response `iss` 但响应缺失就拒绝，若响应含 `iss` 则精确比较、不规范化；错误响应也一样，issuer 不匹配时不得相信或展示 error 字段。',
          sourceIds: ['mcp-authorization-2026'],
        },
        {
          id: 'insufficient-scope-challenge',
          basis: 'documented',
          question: '运行期 access token scope 不足时，MCP server 应如何响应？',
          answer:
            '规范将权限不足归为 HTTP 403；对运行期 insufficient_scope，server SHOULD 在 Bearer challenge 中提供 error="insufficient_scope"、当前操作所需 scope 和 PRM URI 对应的 resource_metadata。client 代表用户时 SHOULD 尝试 scope step-up 或以其他适当方式处理，并应限制重试。',
          sourceIds: ['mcp-authorization-2026'],
        },
      ],
      resourceIds: ['mcp-authorization-2026', 'mcp-security-best-practices-2026'],
    },
  ],
  resourceIds: ['mcp-docs', 'mcp-2026-spec', 'mcp-spec-changelog', 'claude-agent-sdk'],
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
      '把 2026-07-28 现代路径与 legacy initialize/session 混用；dual-era 实现需按传输与版本规则保留兼容分支',
      '默认相信第三方 server 的工具描述与返回内容：它们是会进入上下文的不可信输入',
      '为了「标准化」而引入协议，但实际只有一个应用、三五个工具',
    ],
    cost: 'medium',
  },
  status: 'published',
  updatedAt: '2026-10-19',
  verifiedAt: '2026-10-08',
} satisfies Chapter;
