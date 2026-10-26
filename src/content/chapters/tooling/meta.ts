import type { Chapter } from '@/content/curriculum/schema';

export const chapter = {
  id: 'tooling',
  stageId: 'stage-5-practice',
  order: 21,
  title: '工具与上手',
  subtitle: '知道该装什么，然后装一次',
  summary:
    '前面二十章讲的是机制，这一章讲生态：检索链路要装什么、编排框架给你什么又拿走什么、本地模型什么时候值得、以及界面那层怎么做。每一节都配了在本机真跑出来的数字 —— 因为工具会过时，而「怎么量、怎么判」不会。',
  outcomes: [
    '能根据规模与运维需求，判断一个检索场景要不要上向量库',
    '能在装框架之前先算出它会动到哪些已有依赖',
    '能用真实框架搭一个最小状态图，并区分工作流骨架、Agent 循环、检查点与外部副作用',
    '能把审批与进度做成界面，并说得出为什么不需要客户端状态',
  ],
  depth: 'guided',
  difficulty: 'intermediate',
  estimatedMinutes: 90,
  tags: ['tooling', 'ecosystem', 'hands-on'],
  prerequisiteIds: ['retrieval', 'agent-frameworks', 'human-in-the-loop'],
  resourceIds: ['langchain-docs'],
  backendMapping: {
    analogy:
      '选 agent 工具链 ≈ 选一套中间件：先量自己的规模与运维需求，再看候选；能自己写的那一层不要引依赖',
    transferable: [
      '先量后选：别问「哪个最好」，先问「我的规模落在哪一侧」',
      '依赖是有成本的：装一个框架会动到已有的版本约束，先算再装',
      '能自己写的那一层不引依赖 —— 一行矩阵乘法顶得上一套向量库',
    ],
    pitfalls: [
      '按榜单/热度挑工具，而不是按自己的规模与运维需求',
      '上来就自建推理服务，而没有先试「编码型任务换本地小模型」这条轻路径',
      '以为用了框架就不用自己写幂等 —— 检查点管状态，不管副作用',
      '把审批界面做成带状态的前端组件，而它其实只是四条不同的请求',
    ],
    cost: 'medium',
  },
  status: 'published',
  updatedAt: '2026-10-09',
  verifiedAt: '2026-10-09',
  lessons: [
    {
      id: 'tooling/retrieval-stack',
      chapterId: 'tooling',
      slug: 'retrieval-stack',
      title: '工具地图（一）：检索链路',
      summary: '按检索模态、数据规模和实际负载选择词法检索、embedding、ANN 与重排；历史基准不作为通用阈值。',
      estimatedMinutes: 18,
      difficulty: 'intermediate',
      hasBody: true,
      status: 'drafting',
      keywords: ['tooling'],
      checkpoints: [
        {
          id: 'vector-db-when',
          basis: 'inferred',
          question: '为什么不能只问「哪个向量库好」？',
          answer:
            '向量库只适用于选定向量检索路径的需求；如果用 BM25 等词法检索，不需要 embedding 或向量数据库。本站 2026-10-09 的一次历史单机基准（当时 1311 块、512 维、CPU、Chroma 默认 HNSW 配置）里，numpy 0.02ms 和 Chroma 0.83ms 的历史摘要不能直接证明快 40 倍：配套代码的 NumPy 只取 top-1、Chroma 返回 top-5，合成规模比较还使用不相同的重复次数/统计值；逐次延迟未归档。它不评估语义质量或 ANN 召回。当前示例已让两边都取 top-1，预热一次后以 11 次测量的中位数比较方法，并输出模型设备；它不复现历史表。选型要按自己的检索模态、数据规模、质量、过滤、更新、持久化和目标硬件实测。',
        },
        {
          id: 'embedding-local-vs-api',
          basis: 'inferred',
          question: '本地 embedding 和调 API，该怎么选？',
          answer:
            '本站一次离线 CPU 批量运行中，`BAAI/bge-small-zh-v1.5`（512 维）对 1311 块编码 5.3 秒（246 块/秒，向量矩阵约 2.6 MiB）。该数值只适用于原机器、模型、批大小与语料；后续新增或更新文档仍可能需要编码，不能视为一次性成本。它不能证明线上持续编码无需 GPU，也不能据此断言本地一定够快或托管 API 更值得。应按目标更新频率、并发、质量、资源和数据边界比较本地与获批托管方案。',
        },
        {
          id: 'retrieval-modalities-and-rerank',
          basis: 'documented',
          sourceIds: ['sentence-transformers-retrieve-rerank', 'openai-embeddings-create'],
          question: '检索是否一定需要 embedding？cross-encoder 能否直接用于小语料？',
          answer:
            '不一定。Sentence Transformers 文档将第一阶段召回描述为可选词法检索（例如 Elasticsearch）或 bi-encoder 稠密检索；cross-encoder 对 query-document pairs 共同打分，在大语料上逐对打分通常很慢，因此常先召回候选再重排。对小语料可以直接逐对打分，例如单文档段落搜索示例。此策略是工程折衷，不等于对所有语料都有更高质量或可接受延迟。',
        },
        {
          id: 'embedding-dimensions-are-model-specific',
          basis: 'documented',
          sourceIds: ['openai-embeddings-create'],
          question: 'embedding 输出维度能否随意调整？',
          answer:
            '不能跨模型或 API 一概而论。OpenAI 的 text-embedding-3 系列支持在请求中指定 dimensions；其他模型/endpoint 需查各自文档。本节的 bge-small-zh-v1.5 示例输出 512 维。查询和文档向量必须使用兼容的模型及维度；切换后应重建索引，并在代表性数据上重测检索质量与成本。',
        },
        {
          id: 'benchmark-top-k',
          basis: 'documented',
          sourceIds: ['chroma-python-collection-query'],
          question: '为什么基准比较前要让向量库和暴力检索返回相同数量的结果？',
          answer:
            'Chroma 的 `collection.query` 用 `n_results` 指定每个查询返回的近邻数。本节把它设为 1，与 NumPy `argmax` 的 top-1 对齐；不同 top-k 的延迟结果不能直接比较。',
        },
      ],
      resourceIds: ['sentence-transformers-retrieve-rerank', 'openai-embeddings-create', 'openai-embeddings-faq', 'faiss-index-guide', 'chroma-python-collection-query'],
    },
    {
      id: 'tooling/orchestration-stack',
      chapterId: 'tooling',
      slug: 'orchestration-stack',
      title: '工具地图（二）：编排与可观测性',
      summary: '框架给你什么、拿走什么；以及 trace 平台解决了哪一刻的问题。',
      estimatedMinutes: 18,
      difficulty: 'intermediate',
      hasBody: true,
      status: 'drafting',
      keywords: ['tooling'],
      checkpoints: [
        {
          id: 'version-constraint',
          basis: 'documented',
          sourceIds: ['pypi-langgraph-1-2-14', 'pypi-langchain-0-3-7', 'pypa-packaging-version', 'pip-user-guide', 'pip-install-cli'],
          question: '为什么「装一个框架」是选型里被低估的一步？',
          answer:
            'PyPI 精确发行元数据显示，`langgraph 1.2.14` 要求 `langchain-core>=1.4.7,<2`，而 `langchain 0.3.7` 要求 `langchain-core>=0.3.15,<0.4`，两个区间没有交集；`pydantic 2.9.2` 满足两者声明的 Pydantic 范围。2026-10-09 的已装环境版本是历史记录，原始 pip resolver 输出没有归档，因此不能声称本轮重现了安装过程。pip 文档说明分次安装可能破坏未列入本次目标的已装包；应对完整项目约束做 dry run，并在隔离环境验证。直接约束比较示例用第三方 `packaging`，不替代 resolver。',
        },
        {
          id: 'observability-what',
          basis: 'inferred',
          question: '可观测性平台解决的是哪一刻的问题？',
          answer:
            '自建轨迹可以记录一次运行发生了什么；符合需求的平台可能提供跨运行聚合、共享与版本比较，但功能、数据保留和访问控制因产品而异。是否采用平台，除团队协作外，还要看数据敏感边界、保留期限、集成成本、可用性与预算。',
        },
        {
          id: 'trace-data-minimization',
          basis: 'documented',
          sourceIds: ['opentelemetry-semconv-guidance'],
          question: '为什么不应默认把原始 prompt、tool 参数和结果写进 trace？',
          answer:
            'OpenTelemetry 的语义约定指导只记录对操作有明确价值的属性；敏感、冗长或昂贵的属性应设置为 opt-in。原始输入/输出可能含个人信息、凭据或业务敏感内容，因此先用最小化摘要，并对必要原文落实脱敏、访问控制、加密与保留期限。本规则是工程数据最小化建议，不构成法律合规结论。',
        },
        {
          id: 'pip-resolver-installed-package-scope',
          basis: 'documented',
          sourceIds: ['pip-user-guide', 'pip-install-cli'],
          question: '单独运行 pip install 是否保证整个当前环境仍满足依赖声明？',
          answer:
            '不保证。pip 文档说明，单独安装某个包时 resolver 通常只考虑本次命令列出的包及其依赖，可能使其他已安装包不再满足声明约束。对完整项目依赖清单做 dry run 可预览解析计划；该预览仍取决于 pip 版本、索引和输入约束，不能证明运行时兼容。安装后还可用 pip check 检查已安装包声明的冲突。',
        },
      ],
      resourceIds: ['langchain-docs', 'pip-user-guide', 'pip-install-cli', 'pypa-packaging-version', 'pypi-langgraph-1-2-14', 'pypi-langchain-0-3-7', 'opentelemetry-semconv-guidance'],
    },
    {
      id: 'tooling/local-models',
      chapterId: 'tooling',
      slug: 'local-models',
      title: '本地与开源模型：什么时候该自己跑',
      summary: '按数据边界、离线要求和变更控制选型，并用目标任务评测质量、容量与全生命周期成本。',
      estimatedMinutes: 16,
      difficulty: 'intermediate',
      hasBody: true,
      status: 'drafting',
      keywords: ['tooling'],
      checkpoints: [
        {
          id: 'why-local',
          basis: 'inferred',
          question: '什么约束会让本地或自托管成为候选方案？',
          answer:
            '先把数据处理边界、断网时必须支持的能力和可复现性要求写成可验证条件。再核对每个获批的托管产品/部署/合同是否满足条件；只有没有可接受的托管方案时，数据或网络约束才会要求自托管。版本标识也不保证底层权重和运行栈不可变。硬约束满足后，再以目标任务集比较质量、延迟、容量、运维和全生命周期成本。',
        },
        {
          id: 'local-embedding',
          basis: 'inferred',
          question: '怎样判断本地 embedding 是否适合当前负载？',
          answer:
            '用代表性语料和并发负载同时测质量、吞吐、延迟、资源和更新频率。本站一次离线 CPU 批量运行中，`bge-small-zh-v1.5`（512 维）对 1311 块耗时 5.3 秒（246 块/秒，向量矩阵约 2.6 MiB）；该数字只适用于原机器、模型、批大小与语料。新增或更新文档可能触发新的编码工作，不能视为一次性成本。它不能证明线上持续编码无需 GPU，也不能证明 embedding 比生成任务简单。再按数据边界比较本地与获批托管方案。',
        },
        {
          id: 'model-rights',
          basis: 'documented',
          sourceIds: ['osi-open-source-ai-definition', 'huggingface-model-card-guides'],
          question: '如何判断本地可下载模型的权重是否可用于目标产品？',
          answer:
            '“开放权重”不自动等于满足 Open Source AI Definition 的开放 AI 系统，也不自动回答具体商业部署、修改或再分发是否获准。OSI 的定义列出使用、研究、修改与分享自由及相关组成材料；Hugging Face 模型卡可展示许可证元数据，但标签不是法律结论。应对选定版本核对完整许可文本、可接受使用政策、署名、修改、商业使用、再分发、基座模型和依赖条款；无法确认的条件登记为风险并走组织审核，不据“开源”标签推定可用。',
        },
        {
          id: 'hosted-data-boundary',
          basis: 'documented',
          sourceIds: ['microsoft-foundry-data-privacy', 'openai-enterprise-privacy'],
          question: '使用托管模型是否必然意味着数据不受治理或用于训练？',
          answer:
            '不能一概而论。Microsoft Foundry 与 OpenAI 分别说明了各自产品边界内的数据用途、保留与配置选项；这些承诺不等于数据留在客户本地，也不能外推到其他服务、地区、功能或合同。选型时要按实际 endpoint、功能与部署配置核对数据流、存储和日志。',
        },
      ],
      resourceIds: ['microsoft-foundry-data-privacy', 'openai-enterprise-privacy', 'claude-model-deprecations', 'osi-open-source-ai-definition', 'huggingface-model-card-guides'],
    },
    {
      id: 'tooling/first-agent',
      chapterId: 'tooling',
      slug: 'first-agent',
      title: '动手：用 LangGraph 搭最小状态图',
      summary: '用离线状态图观察检查点与节点重试，明确它不是完整 Agent，也不提供外部副作用的 exactly-once 保证。',
      estimatedMinutes: 20,
      difficulty: 'intermediate',
      hasBody: true,
      status: 'drafting',
      keywords: ['tooling'],
      checkpoints: [
        {
          id: 'graph-skeleton-scope',
          basis: 'inferred',
          question: '这个示例为什么不是一个完整的 Agent？',
          answer:
            '它只有确定性节点和静态边，没有模型决策、工具调用或继续/结束判定。它演示的是 LangGraph 状态图骨架；要称作完整 Agent，还需补上模型、工具协议、宿主执行与安全边界。',
          note: '此依据来自本节代码结构与课程中 Agent loop 的定义；示例本身不发起 provider 请求。',
        },
        {
          id: 'checkpoint-boundary',
          basis: 'documented',
          sourceIds: ['langgraph-graph-api'],
          question: 'LangGraph 的普通节点失败后，为什么外部副作用仍可能重复？',
          answer:
            '官方语义是普通图状态在 super-step 边界检查点，节点在完成前中断/失败时可能从函数开头重跑；`task` 可保存已完成任务的结果，但图检查点本身不与任意外部系统共享事务。本节固定脚本在 LangGraph 1.2.14 中复现了同进程节点异常后 3 次执行、测试列表出现 3 条相同业务键。这个本地列表不是数据库，不能代表进程重启、生产 saver 或真实外部服务。要处理外部副作用，仍需使用业务幂等键、事务、接收端去重或结果对账。',
        },
        {
          id: 'framework-value',
          basis: 'documented',
          sourceIds: ['langgraph-persistence', 'langgraph-graph-api', 'owasp-authorization-cheat-sheet'],
          question: '同一个 thread_id 是否足以恢复进程重启前的图状态？',
          answer:
            '不够。`thread_id` 用于定位 thread 的检查点；跨进程恢复还要求持久化 checkpointer 与正确的部署配置。`InMemorySaver` 把检查点放在 RAM，进程重启后会丢失。thread ID 也不是身份凭证：服务端仍需校验用户、租户与任务的访问权限。长期跨 thread 的应用数据属于 store/业务存储，不等于当前 thread 的检查点。',
        },
      ],
      resourceIds: ['langchain-docs', 'langgraph-persistence', 'langgraph-graph-api', 'owasp-authorization-cheat-sheet'],
    },
    {
      id: 'tooling/agent-ui',
      chapterId: 'tooling',
      slug: 'agent-ui',
      title: '界面：把审批与进度做出来',
      summary: '第 19 章那些设计结论，落到代码上是什么样。',
      estimatedMinutes: 16,
      difficulty: 'intermediate',
      hasBody: true,
      status: 'drafting',
      keywords: ['tooling'],
      checkpoints: [
        {
          id: 'ui-no-state',
          basis: 'inferred',
          question: '审批界面为什么可以不需要客户端状态？',
          answer:
            '客户端 React state 不是审批工作流状态。独立动作可由原生表单或链接提交；但 Server Component 的普通 `type="button"` 不会自动发请求，事件处理器需要 Client Component，表单可以绑定 Server Action。无论 UI 如何呈现，服务端都要逐请求认证、授权、校验，并以持久化状态处理并发、过期和未知外部结果。本站 `<ApprovalDemo />` 当前只是静态示意，按钮被禁用，不接后端。',
        },
        {
          id: 'ui-progress',
          basis: 'inferred',
          question: '进度为什么不该用百分比？',
          answer:
            '百分比只有在总工作量有稳定且可解释的分母时才有意义。动态分支、重试或可变工具调用会使分母不确定；此时展示已发生动作、当前等待或有明确语义的阶段，避免把估算值显示成精确完成度。稳定流程仍可用百分比，但不能把它当成任务成功保证。',
        },
        {
          id: 'nextjs-server-form-boundary',
          basis: 'documented',
          sourceIds: ['nextjs-server-client-components', 'nextjs-forms-server-actions'],
          question: 'Server Component 中的审批控件怎样在不写客户端事件处理器时提交？这是否省略服务端授权？',
          answer:
            'Next.js 文档说明 Server Component 可以渲染带 Server Action 的表单；表单支持渐进增强。普通 `type="button"` 不会自动提交，事件处理器属于需要 Client Component 的交互。即使表单只在登录页面渲染，Server Action 仍须在请求内单独执行认证和授权，并验证输入。该结论只描述框架交互能力，不证明本站示意组件已接入后端。',
        },
      ],
      resourceIds: ['nextjs-server-client-components', 'nextjs-forms-server-actions'],
    },
  ],
} satisfies Chapter;
