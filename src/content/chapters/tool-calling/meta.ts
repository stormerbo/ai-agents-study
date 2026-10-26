import type { Chapter } from '@/content/curriculum/schema';

export const chapter = {
  id: 'tool-calling',
  stageId: 'stage-2-primitives',
  order: 4,
  title: 'Tool / Function Calling',
  subtitle: '让模型能动手',
  summary:
    '工具调用到底发生了什么、工具描述为什么本质上是 prompt、如何用 poka-yoke 的思路让错误在结构上不可能发生，以及工具数量膨胀带来的隐性代价。',
  outcomes: [
    '能手写一次完整的工具调用往返，包括把结果喂回去',
    '能设计出一份让模型难以误用的工具 schema',
    '能判断一个工具该不该拆、该不该合并，以及工具数量何时开始伤害效果',
  ],
  depth: 'deep',
  difficulty: 'intermediate',
  estimatedMinutes: 110,
  tags: ['tool-use', 'function-calling', 'api-design'],
  prerequisiteIds: ['context-engineering', 'prompt-engineering'],
  lessons: [
    {
      id: 'tool-calling/what-really-happens',
      chapterId: 'tool-calling',
      slug: 'what-really-happens',
      title: '工具调用到底发生了什么',
      summary:
        '区分 client tool 与平台托管 tool；读懂 Anthropic stop_reason、调用配对与宿主执行边界，避免把提议、协议回填和业务成功混为一谈。',
      estimatedMinutes: 18,
      difficulty: 'intermediate',
      hasBody: true,
      status: 'drafting',
      keywords: ['tool-use', 'mechanics'],
      checkpoints: [
        {
          id: 'who-executes',
          basis: 'documented',
          question: '当模型“调用”了一个工具，实际发生了什么？中间有哪些环节是你必须实现的？',
          answer:
            '对于 Anthropic Messages API 的 client tool，模型返回 `tool_use` 请求；宿主需要校验工具名、参数和调用者授权，执行允许的操作，再用相同 `tool_use_id` 按协议回填 `tool_result`。仅 `end_turn` 表示本例中的正常结束；`max_tokens`、拒绝、暂停、上下文溢出等状态要走各自分支。API 会验证消息配对格式，但不会验证宿主是否真的执行，也不会证明业务后置条件成立。',
          sourceIds: ['anthropic-stop-reasons', 'anthropic-handle-tool-calls'],
          note: 'DeepSeek 兼容端点 2026-10-08 的两条 400 仅保留为无原始响应的历史摘要，本轮不作为独立复现。',
        },
        {
          id: 'tool-result-trust-boundary',
          basis: 'documented',
          question: 'Anthropic 如何标记工具结果？为什么仍要把其中的外部内容当作不可信数据？',
          answer:
            '工具结果会进入后续上下文，但 Anthropic 仍用 `tool_result` 类型和调用 ID 标记来源；这不是普通用户文本，也不代表结果可信。外部工具内容可能包含间接 prompt injection。宿主应将其作为不可信数据处理，限制模型据此执行的动作，并独立校验授权与业务结果。本节 4 条记录的历史样本未测出格式差异，且原始响应缺失，不能量化格式化收益或推断差异只会在更大数据量出现。',
          sourceIds: ['anthropic-handle-tool-calls', 'owasp-llm-prompt-injection'],
          note: '4 条记录的历史格式对照缺少原始响应；只保留为未复核观察，不能外推。',
        },
      ],
      resourceIds: ['claude-api-docs', 'anthropic-stop-reasons', 'anthropic-extended-thinking', 'anthropic-handle-tool-calls', 'owasp-llm-prompt-injection'],
    },
    {
      id: 'tool-calling/schema-design',
      chapterId: 'tool-calling',
      slug: 'schema-design',
      title: '工具描述即 prompt',
      summary:
        '工具描述是模型上下文中的一个决策信号；用 schema 表达参数契约，并通过 provider-specific strict 能力和宿主校验明确约束边界。',
      estimatedMinutes: 20,
      difficulty: 'intermediate',
      hasBody: true,
      status: 'drafting',
      keywords: ['schema', 'description'],
      checkpoints: [
        {
          id: 'description-quality',
          basis: 'documented',
          question:
            '工具描述会如何影响模型选择与参数填写？为什么仍需针对目标 endpoint 做正反例验证？',
          answer:
            '工具定义会进入模型上下文；历史样本中，描述和参数说明同时扩充后，三类问题的记录输出发生变化。但逐次请求、原始响应与 scorer 未归档，无法独立复算，也不能将变化归因到某一个字段。描述应写明适用边界和参数要求，并用目标模型/endpoint 上的正例、反例探测验证；它不是唯一决策信号，也不是防误用或授权保证。',
          sourceIds: ['anthropic-define-tools'],
          note: '官方文档支持工具定义与描述的接口事实；2026-10-08 DeepSeek 样本缺少逐次请求、原始响应与 scorer，不能用于因果或错误率结论。',
        },
        {
          id: 'enum-over-free-text',
          basis: 'documented',
          question: 'enum 与 strict tool use 分别提供什么约束？哪些验证仍由宿主负责？',
          answer:
            '固定取值应写入 schema，以表达契约并减少歧义；但普通 enum 在非 strict 模式下不一定是硬约束。Anthropic 对受支持的用户工具 schema 可启用 `strict: true`，保证输入符合其支持的 JSON Schema 子集；仍须做宿主侧业务语义与授权校验。历史 DeepSeek 对照仅 3 次/组、原始响应缺失，不足以估算错误率或支持普遍因果结论。',
          sourceIds: ['anthropic-strict-tool-use', 'json-schema-validation-2020-12'],
          note: 'Strict 保证仅限 Anthropic 文档所述受支持 schema 子集；历史 DeepSeek 对照每组 3 条且原始响应缺失，不足以支持普遍因果结论。',
        },
      ],
      resourceIds: ['anthropic-define-tools', 'anthropic-strict-tool-use', 'json-schema-validation-2020-12'],
    },
    {
      id: 'tool-calling/poka-yoke',
      chapterId: 'tool-calling',
      slug: 'poka-yoke',
      title: 'poka-yoke：缩小无效操作空间',
      summary:
        '通过窄接口减少无效状态，并在宿主服务端校验身份、对象、流程与审批；schema 和随机引用都不能替代授权。',
      estimatedMinutes: 22,
      difficulty: 'advanced',
      hasBody: true,
      status: 'drafting',
      keywords: ['design', 'poka-yoke'],
      checkpoints: [
        {
          id: 'poka-yoke-example',
          basis: 'documented',
          question:
            '服务端发放的随机 file_id 能保证什么？执行删除前还要验证哪些内容？',
          answer:
            '随机、短时、按可信身份与任务绑定的 file_id 可以缩小候选目标并降低盲猜风险，但模型仍能生成任意字符串；引用也可能泄露或重放。每个请求都要在资源服务端验证当前 actor、tenant、session/task、action、对象 ACL、有效期和对象版本；高影响操作按策略要求独立审批。拆成 list/delete 不能代替授权，也不证明目标符合用户意图。',
          sourceIds: ['owasp-authorization-cheat-sheet', 'aws-s3-presigned-urls'],
          note: '2026-10-08 DeepSeek 历史轨迹缺原始请求/响应；显示过的 f_002 可预测，未测试跨会话或越权路径。',
        },
        {
          id: 'optional-params-trap',
          basis: 'documented',
          question: '如何在工具 schema 与宿主校验里表达互斥参数？拆分工具能提供哪些边界？',
          answer:
            'JSON Schema 可用联合约束描述单次对象必须匹配哪个分支（例如 `oneOf`），也可拆成语义单一的工具；但 provider/endpoint 是否执行该 schema 子集需单独确认。拆工具不会阻止模型在同一个逻辑任务中调用两个工具，因此跨调用流程仍由 host 校验。',
          sourceIds: ['json-schema-validation-2020-12'],
          note: '历史 DeepSeek 摘要的 3/3、0/3 分母口径不可重建，缺原始响应；不用于估计普遍模型错误率。',
        },
      ],
      resourceIds: ['anthropic-building-effective-agents', 'anthropic-stop-reasons', 'anthropic-handle-tool-calls', 'anthropic-strict-tool-use', 'owasp-authorization-cheat-sheet', 'aws-s3-presigned-urls', 'owasp-rest-security-cheat-sheet', 'rfc-2104-hmac', 'json-schema-validation-2020-12'],
    },
    {
      id: 'tool-calling/parallel-and-errors',
      chapterId: 'tool-calling',
      slug: 'parallel-and-errors',
      title: '并行调用、错误处理与幂等',
      summary:
        '区分模型一次提出多个工具调用与宿主选择并发执行；逐项配对失败结果，并用持久化业务动作 ID 处理写操作重放。',
      estimatedMinutes: 25,
      difficulty: 'intermediate',
      hasBody: true,
      status: 'drafting',
      keywords: ['parallel', 'idempotency', 'error-handling'],
      checkpoints: [
        {
          id: 'partial-failure',
          basis: 'documented',
          question: '模型在一轮里请求了三个工具，其中一个执行失败。你该怎么把结果回传？',
          answer:
            '对于 Anthropic Messages API 的 client tools，每个 tool_use 都要有匹配的 tool_result；即使宿主没有执行某项，也不能静默省略。is_error 用来标记工具执行错误，但它不是跨模型的重试指令；宿主应分类错误、限制重试并验证业务结果。2026-10-08 的 DeepSeek 历史摘要称，不标错误、只标错误、附原因三组各记录 3 次，但逐次响应、样本映射和 scorer 缺失，不能确认分母、复算行为或推断普遍因果。',
          sourceIds: ['anthropic-parallel-tool-use', 'anthropic-handle-tool-calls', 'anthropic-stop-reasons'],
          note: 'Anthropic 协议事实仅适用于其 Messages API client-tool 路径；历史 DeepSeek 样本作为不可复核摘要保留，不代表其他 provider。',
        },
        {
          id: 'idempotency-is-not-authorization',
          basis: 'inferred',
          question: '命中幂等记录时，能否跳过身份认证或对象级授权？',
          answer:
            '不能。幂等键只用于识别同一业务动作的重放，不是身份凭据或授权证明。系统应从可信认证上下文确定租户，并在返回已缓存结果或执行新副作用之前检查当前 actor 对目标对象的权限；本节 SQLite 示例把 tenant_id 当输入，不实现身份认证或对象级授权。',
          note: '这里的幂等键与授权边界是工程推论；OWASP 来源支持逐请求、逐对象的访问控制原则。本地示例不包含生产身份提供方或授权策略。',
        },
        {
          id: 'write-idempotency',
          basis: 'documented',
          question: '为什么带副作用的工具（写文件、发消息、下单）必须考虑重复执行？',
          answer:
            '调用方超时不能证明接收方没有提交副作用，因此重试与整轮重放必须复用同一稳定业务动作 ID。tool_use.id 只关联本轮协议请求与结果，不是持久化业务幂等键。接收方应原子地记录作用域、动作 ID、请求摘要和首次结果，并拒绝同键异参；跨系统副作用还需要下游幂等、outbox、对账或补偿。Stripe 的文档展示了该 API 如何保存和重放首次响应，这是具体实现示例，不是所有系统的统一保证。2026-10-08 单次“状态未知时不重试”的 DeepSeek 摘要缺原始请求/响应，不能支持模型通常谨慎或重复风险很低的结论。',
          sourceIds: ['stripe-idempotency-keys', 'anthropic-handle-tool-calls'],
          note: 'Stripe 来源支持其 API 的幂等实现细节；本地 SQLite 示例只验证单库事务。跨系统 exactly-once 与历史模型倾向均未验证。',
        },
      ],
      resourceIds: [
        'anthropic-parallel-tool-use',
        'anthropic-handle-tool-calls',
        'anthropic-stop-reasons',
        'anthropic-extended-thinking',
        'anthropic-api-errors',
        'stripe-idempotency-keys',
        'owasp-authorization-cheat-sheet',
      ],
    },
    {
      id: 'tool-calling/tool-count',
      chapterId: 'tool-calling',
      slug: 'tool-count',
      title: '工具数量的代价',
      summary:
        '区分工具定义带来的输入上下文、缓存与费用变化；用可回答的固定探针评估选择质量，并比较 host 分组与 provider 延迟加载。',
      estimatedMinutes: 25,
      difficulty: 'advanced',
      hasBody: true,
      status: 'drafting',
      keywords: ['scaling', 'tool-selection'],
      checkpoints: [
        {
          id: 'why-too-many-tools',
          basis: 'inferred',
          question: '工具数量变多之后，会出现什么问题？「选择准确率下降」这个说法成立吗？',
          answer:
            '工具定义进入请求上下文，工具越多可能增加上下文和输入 token；具体 token、账单和延迟取决于 endpoint、缓存和任务。旧记录报告 8/20/44/86 个工具的请求总输入为 678/1326/2623/4945 token，两端边际约 55 token/新增工具，但这些总数包含固定请求开销，原始 usage 未归档。选择实验摘要称四档各 8/8、语义重叠组 5/5；逐次问题、响应和 scorer 缺失，因此不能推出模型通常不受工具数量影响。更早的 3 工具组还据称缺少若干正确候选，不能把其分数当错选率。对自己的任务，应保证每道题在每个对照组都有唯一可调用答案，保留完整响应并分类拒绝、截断、零调用和多调用。',
          note: '本节所有 DeepSeek 数字均为 2026-10-08 历史摘要，本轮不能独立复算。表中 token 是请求总输入，不是纯工具 schema token；模型选择结论只适用于该未归档探针。',
        },
        {
          id: 'tool-organizing',
          basis: 'documented',
          question: '有哪些办法能在工具很多时控制上下文与调用代价？',
          answer:
            '可以比较全量常驻、host 按任务分组、以及 provider 支持时的工具搜索/延迟加载。Anthropic 文档说明 defer_loading 与 tool search 可推迟完整定义并保留工具定义前缀缓存；这属于 provider-specific 能力，不代表其他 endpoint 都支持。按策略选择还要核算额外路由调用、漏选、缓存、延迟和质量；schema 减少也不能替代授权验证。',
          sourceIds: ['anthropic-manage-tool-context', 'anthropic-tool-use-prompt-caching'],
          note: '文档结论仅适用于 Anthropic 所述工具搜索与 prompt caching 能力；本节未对分组加载或 tool search 做模型质量对照。',
        },
      ],
      resourceIds: [
        'anthropic-building-effective-agents',
        'anthropic-manage-tool-context',
        'anthropic-tool-use-prompt-caching',
        'claude-prompt-caching',
      ],
    },
  ],
  resourceIds: [
    'claude-api-docs',
    'anthropic-building-effective-agents',
    'toolformer-paper',
    'openai-cookbook',
  ],
  labIds: ['lab-tool-schema'],
  backendMapping: {
    analogy: '工具调用 ≈ RPC 接口设计，但契约由自然语言描述、且调用方是一个概率性推理者',
    transferable: [
      '接口设计经验：参数校验、错误语义、向后兼容',
      '幂等键与重试安全——这里同样必须做',
      '错误码设计：要能被调用方理解并据此采取行动',
    ],
    pitfalls: [
      '把工具描述当作给人看的 API 文档来写：它是 prompt，模型完全依赖它做判断',
      '在工具内部抛异常：模型看不到栈，它只看到你返回的那段字符串',
      '设计出参数可任意组合的工具，等于邀请模型组合出无效状态',
      '工具集规模变化的上下文/成本与选择质量需分别测量；分组或减量不能替代授权校验',
    ],
    cost: 'medium',
  },
  status: 'published',
  updatedAt: '2026-10-08',
  verifiedAt: '2026-10-08',
} satisfies Chapter;
