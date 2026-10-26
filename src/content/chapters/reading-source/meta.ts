import type { Chapter } from '@/content/curriculum/schema';

export const chapter = {
  id: 'reading-source',
  stageId: 'stage-5-practice',
  order: 22,
  title: '源码研读',
  subtitle: '按「读它的理由」挑项目',
  summary:
    '到了一个临界点之后，最高效的学习方式不再是读教程，而是读实现。这一章讲怎么带着问题去读、怎么挑值得读的项目、以及读完之后该产出什么 —— 否则读了十份源码，能力还是停在「见识过」。',
  outcomes: [
    '能说清读一个 agent 项目时该追问的五个问题',
    '能沿着一次真实任务的调用链把源码读到底，而不是通读文件',
    '能把读到的实现对比成一张表，形成自己的选型依据',
  ],
  depth: 'guided',
  difficulty: 'advanced',
  estimatedMinutes: 85,
  tags: ['source-reading', 'architecture'],
  prerequisiteIds: ['agent-loop', 'agent-frameworks'],
  lessons: [
    {
      id: 'reading-source/why-and-how',
      chapterId: 'reading-source',
      slug: 'why-and-how',
      title: '什么时候该读源码，以及怎样核实实现边界',
      summary: '从具体问题出发，按需选择文档、源码、测试或运行观测。',
      estimatedMinutes: 16,
      difficulty: 'intermediate',
      hasBody: true,
      status: 'drafting',
      keywords: ['source-reading'],
      checkpoints: [
        {
          id: 'langchain-docstring-schema-boundary',
          basis: 'documented',
          question: 'LangChain Core 0.3.63 中，文档字符串、Literal 和显式 args_schema 分别怎样影响工具 schema？',
          answer:
            '固定示例中默认 parse_docstring=False 时，Args 段没有进入字段 description，但原始文档字符串出现在工具级 description；打开解析会填入字段 description，不会从散文生成 enum。默认推断路径与显式 Pydantic args_schema 都能生成所示 enum；tool_call_schema 形成模型可见字段，model_json_schema() 导出已经构造的 schema。只适用于 0.3.63 的固定示例。',
          sourceIds: ['langchain-core-063-tool-convert', 'langchain-core-063-tool-structured', 'langchain-core-063-tool-base', 'pydantic-json-schema'],
          note: '由版本化源码和固定依赖下的本地四组构造断言支持；不外推到其他 LangChain/Pydantic 版本或 endpoint。',
        },
        {
          id: 'why-source',
          basis: 'inferred',
          question: '为什么在有了框架文档之后，还需要读源码？',
          answer:
            '文档与源码关注的层次可能不同。源码能展示**当前版本、当前调用路径**里的默认值、失败分支和设计结构；这些是需要进一步验证的线索，不能单独证明生产行为或作者动机。读到关键实现后，应结合对应文档、测试以及目标环境的观测来判断它是否适用于自己的系统。',
        },
        {
          id: 'five-questions',
          basis: 'inferred',
          question: '读一个 agent 项目时，该带着哪几个问题？',
          answer:
            '用第 9 章的零件当检查框架：追问**终止条件**、**工具调度与授权**、**预算**、**循环检测**、**状态持久化与恢复语义**，再检查**错误处理**（哪些错误重试、哪些直接失败）。把答案定位到目标版本的实现或官方契约，并标清哪些只是当前代码路径的观察；完成后得到的是一份初步判断，仍需目标任务、测试数据和生产约束来验证适用性。',
        },
      ],
      resourceIds: ['twelve-factor-agents', 'claude-agent-sdk', 'langchain-core-063-tool-convert', 'langchain-core-063-tool-structured', 'langchain-core-063-tool-base', 'pydantic-json-schema'],
    },
    {
      id: 'reading-source/picking-projects',
      chapterId: 'reading-source',
      slug: 'picking-projects',
      title: '挑项目：按理由，不按热度',
      summary: '一个项目的价值不在于它有多流行，而在于它能回答你哪个问题。',
      estimatedMinutes: 18,
      difficulty: 'intermediate',
      hasBody: true,
      status: 'drafting',
      keywords: ['selection', 'repositories'],
      checkpoints: [
        {
          id: 'picking-criteria',
          basis: 'inferred',
          question: '怎么判断一个开源 agent 项目值不值得读？',
          answer:
            '先写下**要回答的问题**，然后选择拥有相关行为、且与你项目路径或学习目标有关的模块。比如想查**循环与工具调度**，追一个具体调用链；想学**评测与数据集**，看项目如何定义数据、评分和错误分析；想了解**持久化、重试与审批**，检查相关状态和失败路径；想看**协议接入**，读协议边界附近的实现。规模只是阅读范围的线索，不能单独判断项目是否有价值；热度也不能替代维护状态和适用性检查。',
        },
        {
          id: 'langchain-provider-integration-boundary',
          basis: 'documented',
          question: '追 LangChain 工具 schema 和模型 HTTP 请求时，是否应该把 langchain-core、Pydantic 与 provider client 画成一条调用链？',
          answer:
            '不应把不同目标的路径默认串成一条链。LangChain 当前文档说明 provider integrations 通常由独立的 `langchain-<provider>` 包实现标准接口，例如 `langchain-anthropic`；工具 schema 路径可从 `langchain_core.tools` 开始，模型请求路径则从目标 provider integration 开始，再按目标版本追到具体 SDK 和 transport。不要仅凭包名或安装清单推断运行时调用关系。',
          sourceIds: ['langchain-python-integrations', 'langchain-core-063-tool-convert', 'langchain-core-063-tool-base'],
          note: 'Provider 包布局以官方当前文档为准；本课 schema 示例固定在 langchain-core 0.3.63。目标项目要按安装版本和真实调用路径复核。',
        },
        {
          id: 'package-size-boundary',
          basis: 'inferred',
          question: '文件数和物理行数能否预测一个下午是否读得完？',
          answer:
            '不能。它们只比较所统计目录中的代码规模，不表达相关调用路径的长度、依赖复杂度、读者背景或阅读目标；应先定位目标行为，再按需扩展到相邻模块。',
        },
        {
          id: 'archived-means-something',
          basis: 'inferred',
          question: '读到一个已归档或长期不更新的项目，该怎么对待？',
          answer:
            '把它当**历史样本**读，而不是当依赖。它有价值的场景是：它演示了一种现在少见的取舍（比如某个已被主流放弃的架构），或者它的设计文档比代码更有信息量。要警惕的是把它的结论当现状 —— 领域变化很快，一个两年前的「最佳实践」可能已经被证伪。判断方法很直接：看它最后一次实质性更新是什么时候，以及那之后你所依赖的接口有没有变化（第 12 章的 MCP 规范就是例子：2026-07-28 的破坏性修订会让更早的示例代码直接跑不通）。',
        },
      ],
      resourceIds: ['openhands', 'open-deep-research', 'aider', 'langchain-core-063-tool-convert', 'langchain-core-063-tool-base', 'langchain-python-integrations'],
    },
    {
      id: 'reading-source/trace-one-task',
      chapterId: 'reading-source',
      slug: 'trace-one-task',
      title: '沿着一次任务读到底',
      summary: '不要通读文件；跟着一次真实调用走一遍。',
      estimatedMinutes: 22,
      difficulty: 'advanced',
      hasBody: true,
      status: 'drafting',
      keywords: ['debugging', 'call-chain'],
      checkpoints: [
        {
          id: 'langchain-parse-docstring-behavior',
          basis: 'documented',
          question: 'LangChain Core 0.3.63 中 parse_docstring 和 Literal 类型分别如何影响工具 schema？',
          answer:
            '该版本 parse_docstring 默认是 False；开启后可把函数文档中的参数说明放入字段 schema 的 description，但不会把自然语言改写成 enum。Literal 类型可由 Pydantic schema 生成 enum；显式 args_schema 也可定义字段约束。结论仅适用于固定版本和示例，其他版本需重跑断言。',
          sourceIds: ['langchain-core-063-tool-convert', 'langchain-core-063-tool-base'],
          note: '源代码定位与固定版本本地断言共同支持；不是当前 LangChain 全版本保证。',
        },
        {
          id: 'langchain-tool-call-schema-path',
          basis: 'documented',
          question: 'LangChain Core 0.3.63 的 @tool 如何从默认推断或显式 args_schema 形成模型可见 schema？',
          answer:
            'StructuredTool.from_function 在默认推断路径调用 create_schema_from_function；显式 args_schema 路径复用调用者提供的模型。BaseTool.tool_call_schema 构造模型可见字段，model_json_schema() 导出 JSON Schema。固定版本中 _get_filtered_args 有定义但不在本节追踪的调用路径内。Literal 约束与显式 Pydantic 约束分别来自两种构造方式；不应把 schema 导出位置误作约束起点。',
          sourceIds: ['langchain-core-063-tool-structured', 'langchain-core-063-tool-base', 'python-typing-overload-314', 'pydantic-json-schema'],
          note: '版本边界通过固定源码链接和离线调用链检查核对；不代表其他 LangChain/Pydantic 版本或 provider 行为。',
        },
        {
          id: 'trace-method',
          basis: 'inferred',
          question: '面对一个陌生的 agent 代码库，最高效的读法是什么？',
          answer:
            '**从入口开始，跟着一次真实的单次任务往下走**，每一步只读「这一段做了什么、把控制权交给了谁」，不深究实现细节。路径通常是：请求入口 → 组装上下文（system、工具、历史）→ 调用模型 → 解析响应 → 判断是否要继续 → 执行工具 → 回填 → 再循环。走完一遍你就有了一张调用图，之后想深入哪一块再回去读。这比按目录顺序读文件有效得多，因为**agent 的复杂度在流程上，而不在单个模块里** —— 只有沿着流程走，你才能看到各个决策点分散在哪些层。',
        },
        {
          id: 'what-to-note',
          basis: 'inferred',
          question: '沿着调用链读的时候，重点该记什么？',
          answer:
            '记**决策点**，而不是函数名。具体是三类：**判断条件**（if stop_reason == tool_use 这类分支 —— 它们是框架对协议的理解）、**默认值**（超时、重试次数、截断策略）、以及**数据在哪一层被转换了形态**（比如消息在进入模型前经过哪几次归一化）。第三类在实践中价值最高：出问题时你往往需要知道「这个字段是在哪里被改掉的」，而这在模块化阅读里是看不出来的。至于函数名与实现细节，需要时再查即可 —— 它们不像决策点那样承载判断。',
        },
      ],
      resourceIds: ['claude-agent-sdk', 'openai-agents-sdk-python', 'langchain-core-063-tool-convert', 'langchain-core-063-tool-base', 'langchain-core-063-tool-structured', 'python-typing-overload-314', 'pydantic-json-schema'],
    },
    {
      id: 'reading-source/compare',
      chapterId: 'reading-source',
      slug: 'compare',
      title: '横向对比：同一个能力的不同实现',
      summary: '单个实现只能告诉你「有人这么做」，对比才能告诉你「为什么这么做」。',
      estimatedMinutes: 20,
      difficulty: 'advanced',
      hasBody: true,
      status: 'drafting',
      keywords: ['comparison', 'abstraction'],
      checkpoints: [
        {
          id: 'compare-dimensions',
          basis: 'inferred',
          question: '横向对比几个框架时，该拿哪几个维度去比？',
          answer:
            '用第 9 章的零件加三条：**循环的所有权**（框架替你跑循环，还是你显式写每一步）、**状态的表达**（它把状态建模成什么 —— 消息列表、图上的节点、还是会话对象）、**工具的接入方式**（内置注册表、还是通过协议接外部 server）、**人类介入点**（哪里有钩子、能拦到什么粒度）、以及**可观测性的默认值**（默认给多少追踪、能不能导出）。五个维度的组合基本决定了一个框架适合什么形态的系统 —— 而这比「它功能多不多」有用得多，因为功能表拉长到最后大家都差不多。',
        },
        {
          id: 'compare-output',
          basis: 'inferred',
          question: '对比之后应该产出什么？',
          answer:
            '一张**自己的选型表**，而且它能被后来的事实检验。要点有三：每个维度写清「这个框架怎么做的」以及「这个做法在什么情况下会成为问题」（后者是关键 —— 只写优点的对比没有决策价值）；标注你是**读代码得出的还是读文档得出的**（两者可信度不同）；以及写下**什么条件下你会换掉它**。最后一条常被省略，但它是选型质量的最好证明：如果你说不出什么情况会让自己改变选择，那这个选择多半不是分析出来的。',
        },
        {
          id: 'mcp-input-schema-contract',
          basis: 'documented',
          question: 'MCP 的 inputSchema 没有列某字段为 required，能否推出 server 一定接受该字段缺省？',
          answer:
            '不能。JSON Schema 没有 `required` 时，该 schema 不会以 required 约束这些 properties；MCP 2026-07-28 规范仍要求 server 校验工具输入，server 还可能按业务规则拒绝缺参。客户端应按声明的 schema 构造请求并处理工具执行错误；schema 未表达的业务要求需通过文档或实际契约确认。',
          sourceIds: ['mcp-2026-tools-spec', 'json-schema-object-reference'],
          note: '只陈述 MCP 2026-07-28 工具规范中的 schema 与输入校验责任，不推断任意 server 的业务行为。',
        },
        {
          id: 'mcp-schema-generation-source',
          basis: 'documented',
          question: 'MCP 协议是否规定 inputSchema 必须手写？官方 Python SDK 的工具装饰器怎样处理它？',
          answer:
            'MCP 规范定义 tools/list 在线提供的 inputSchema 契约，不规定 schema 必须手写。官方 Python SDK v2 的 @mcp.tool() 会从函数类型标注生成 JSON Schema；这是该 SDK 的实现行为，不能推广到其他 server 或版本。应检查目标项目实际使用的 SDK 和 release。',
          sourceIds: ['mcp-python-sdk-tools', 'mcp-2026-tools-spec'],
          note: 'Python SDK 文档链接在 main 分支，2026-10-22 核验；其内容可能随 release 变化。',
        },
      ],
      resourceIds: ['langchain-docs', 'openai-agents-sdk-python', 'claude-agent-sdk', 'mcp-2026-tools-spec', 'json-schema-object-reference', 'mcp-python-sdk-tools'],
    },
    {
      id: 'reading-source/outputs',
      chapterId: 'reading-source',
      slug: 'outputs',
      title: '读完要产出什么',
      summary: '没有产出的阅读，下次还得重读一遍。',
      estimatedMinutes: 18,
      difficulty: 'intermediate',
      hasBody: true,
      status: 'drafting',
      keywords: ['notes', 'learning'],
      checkpoints: [
        {
          id: 'reading-outputs',
          basis: 'inferred',
          question: '读完一份源码，值得留下哪几种产出？',
          answer:
            '可以留下四类产出：**笔记**帮助回忆上下文；**调用链图**帮助定位决策与失败路径；**可执行判据**把发现转成团队可检查的约束；**可复现实验**在固定依赖、明确断言和适用范围后，帮助检查特定行为是否变化。哪一类最有用取决于目标与维护成本；运行成功本身不等于结论正确。',
        },
        {
          id: 'langchain-parse-docstring-behavior',
          basis: 'documented',
          question: 'LangChain Core 0.3.63 中 parse_docstring 和 Literal 类型分别如何影响工具 schema？',
          answer:
            '该版本 `parse_docstring` 默认是 False；开启后可把函数文档中的参数说明放入 schema 的 description，但不会把自然语言改写成 enum。`Literal` 类型可由 Pydantic schema 生成 enum。结论仅适用于 langchain-core 0.3.63 的固定示例，其他版本需重跑断言。',
          sourceIds: ['langchain-core-063-tool-convert', 'langchain-core-063-tool-base'],
          note: '由固定版本源代码和本地断言支持；不是当前 LangChain 全版本保证。',
        },
        {
          id: 'avoid-collecting',
          basis: 'inferred',
          question: '「读了很多源码但没长进」通常是什么原因？',
          answer:
            '把阅读当成了**收集**而不是**对照**。具体表现是：读完只记得「它用了 A 模式」，却回答不了「如果换我来做会怎么选、为什么」。缺少对照，读到的设计就只是一堆事实，无法迁移到自己的问题上。解法很具体：每读一个项目，强迫自己写下至少一条**不同意的地方**，以及**它在什么输入下会失效**。这两个问题逼着你从「它怎么做」转向「它为什么这么做、代价是什么」—— 而这个转变才是读源码真正的收益。它和本站反复出现的立场一致：**结论不值钱，取舍的依据才值钱。**',
        },
      ],
      resourceIds: ['ai-engineering-huyen', 'twelve-factor-agents', 'langchain-core-063-tool-convert', 'langchain-core-063-tool-base'],
    },
  ],
  resourceIds: [
    'claude-agent-sdk',
    'openai-agents-sdk-python',
    'langchain-docs',
    'openhands',
    'open-deep-research',
    'twelve-factor-agents',
  ],
  backendMapping: {
    analogy: '读 agent 源码 ≈ 读一个你打算引入的中间件：先看它的关键路径与失败处理，再决定信不信它',
    transferable: [
      '读陌生代码库的方法：从入口沿线走，不通读文件',
      '关注默认值与失败路径 —— 这是判断一个库是否可靠的关键',
      '对比选型的习惯：列维度、写代价、留下可被检验的结论',
    ],
    pitfalls: [
      '按目录通读文件，读完仍说不清一次任务是怎么跑完的',
      '按 star 数挑项目，读了大量与当前问题无关的代码',
      '把已归档项目的结论当现状',
      '只记录「它做了什么」，不记录「代价是什么」',
      '读而不产出，下次还要从头再读一遍',
    ],
    cost: 'low',
  },
  status: 'published',
  updatedAt: '2026-10-08',
  verifiedAt: '2026-10-08',
} satisfies Chapter;
