import type { Chapter } from '@/content/curriculum/schema';

export const chapter = {
  id: 'agent-security',
  stageId: 'stage-4-production',
  order: 17,
  title: '安全与信任边界',
  subtitle: '当输入变成动作',
  summary:
    '文本时代，提示注入最坏的结果是一段错话；agent 时代，它能变成一个被真正执行的动作。这一章讲清注入为什么在 agent 里升级了、工具描述与返回值为什么是不可信输入、引入第三方工具意味着什么，以及纵深防御该怎么分层。',
  outcomes: [
    '能说清提示注入在 agent 场景下与纯文本场景的本质差别',
    '能列出自己系统里所有「会进入上下文的外部输入」并逐一给出对策',
    '能把第三方工具与服务当成依赖来治理，而不是当成配置项',
  ],
  depth: 'deep',
  difficulty: 'expert',
  estimatedMinutes: 100,
  tags: ['security', 'prompt-injection', 'supply-chain'],
  prerequisiteIds: ['tool-calling', 'mcp', 'prompt-engineering'],
  lessons: [
    {
      id: 'agent-security/injection-escalation',
      chapterId: 'agent-security',
      slug: 'injection-escalation',
      title: '注入为什么在 agent 里升级了',
      summary: '提示注入可影响模型输出，也可能在工具授权与宿主执行后触发外部动作；影响取决于能力、权限与副作用路径。',
      estimatedMinutes: 20,
      difficulty: 'advanced',
      hasBody: true,
      status: 'drafting',
      keywords: ['prompt-injection', 'tool-use'],
      checkpoints: [
        {
          id: 'why-worse-with-tools',
          basis: 'inferred',
          question: '同样是提示注入，为什么在有工具的 agent 里后果严重得多？',
          answer:
            '提示注入既可能影响普通 LLM 应用的输出或信息披露，也可能在工具增强系统里影响动作提议；只有宿主继续授权并执行时，才会触发相应副作用。影响取决于已授予的工具能力、身份/资源授权、参数策略和下游恢复机制，而不是“agent”标签本身。第 2 章的提示注入样本只说明该任务与模型配置下的观测，不证明纯文本输出无害，也不证明工具动作必然执行。做威胁建模时要问：模型可提出什么、宿主会执行什么、最坏影响能否撤销或补偿。',
        },
        {
          id: 'injection-sources',
          basis: 'inferred',
          question: '在一个 agent 系统里，有哪些地方会成为注入入口？',
          answer:
            '凡是**被你放进上下文、而你无法控制其内容**的地方，都是入口。至少包括：用户直接输入；网页与文档（检索回来的内容）；工具返回值（尤其是调用外部服务的结果）；第三方 MCP server 提供的工具描述；代码仓库里的文件内容（注释、README、issue 正文）；以及子智能体回传的摘要。最后两项最容易被忽略 —— 团队通常会把「用户输入」列为威胁，却忘了 agent 读进来的代码注释也是外部内容。工程上的做法是**先做一次清点**：把所有这些来源列出来，每一个都标注「它能不能影响模型的行为」以及「如果它能，最坏结果是什么」。',
        },
        {
          id: 'injection-direct-and-indirect-scope',
          basis: 'documented',
          question: 'OWASP 如何区分直接与间接提示注入？间接注入是否只影响 agent？',
          answer:
            'OWASP 将直接注入描述为用户输入改变模型行为，将间接注入描述为网站或文件等外部内容影响模型行为；RAG 或微调不能完全消除此风险。影响取决于具体业务上下文与系统 agency，可能涉及敏感信息披露或未授权功能调用。OWASP 没有给出万无一失的预防方法，缓解需要结合输出限制、最小权限、人工审批与针对性测试。',
          sourceIds: ['owasp-llm-prompt-injection'],
        },
        {
          id: 'client-tool-execution-boundary',
          basis: 'documented',
          question: 'Anthropic Messages 的 tool_use 响应会由 API 自动执行工具吗？',
          answer:
            '不会。模型返回 tool_use 表示宿主需要处理的工具调用请求；应用侧决定是否执行，再按 tool_use_id 回填 tool_result。模型提出调用、宿主授权与执行是不同边界；API 的消息配对规范不替应用做身份、资源或业务授权。',
          sourceIds: ['anthropic-handle-tool-calls'],
        },
        {
          id: 'anthropic-stop-reasons-contract',
          basis: 'documented',
          question: '为什么注入示例不能把所有非 tool_use 响应都当成已完成的自然语言答复？',
          answer:
            'Anthropic Messages 通过 stop_reason 区分 end_turn、tool_use、max_tokens、refusal、pause_turn 等终止状态；max_tokens 表示响应受输出上限影响，refusal 与工具交接也不是普通完成答案。应按该 API 契约分流；不能把这些枚举未经验证地推广到其他 provider 的兼容端点。',
          sourceIds: ['anthropic-stop-reasons'],
        },
      ],
      resourceIds: ['owasp-llm-prompt-injection', 'anthropic-building-effective-agents', 'ai-engineering-huyen', 'anthropic-handle-tool-calls', 'anthropic-stop-reasons', 'deepseek-anthropic-api'],
    },
    {
      id: 'agent-security/tools-as-untrusted-input',
      chapterId: 'agent-security',
      slug: 'tools-as-untrusted-input',
      title: '工具描述与返回值都是输入',
      summary: '第 4 章说过「工具描述即 prompt」—— 那句话在安全语境下还有一半。',
      estimatedMinutes: 20,
      difficulty: 'advanced',
      hasBody: true,
      status: 'drafting',
      keywords: ['tool-poisoning', 'untrusted-input'],
      checkpoints: [
        {
          id: 'tool-description-is-input',
          basis: 'inferred',
          question: '「工具描述即 prompt」这句话，在安全上意味着什么？',
          answer:
            '第三方 server 的工具描述可能含有影响模型选择或调用行为的自然语言内容；它进入上下文，不代表模型必然服从，也不代表模型有可靠的来源验证能力。把非自研描述按不可信元数据处理：评审内容与来源、记录版本和变更，并在宿主侧单独执行工具授权、参数校验和最小权限约束。',
        },
        {
          id: 'tool-results-are-data',
          basis: 'inferred',
          question: '工具返回值里夹带的指令该怎么处理？',
          answer:
            '为工具结果保留来源与不可信边界，能帮助模型按预期解释内容，但标记不是权限或事实验证机制。第 2 章一个小样本里，内容操纵在加标签后仍记为 6/6；它不证明其他任务中的标签效果。工具动作仍需宿主按主体、资源、动作与参数授权，并限制可用权限；这降低特定路径的影响，不构成“被骗了也一定做不成”的保证。',
        },
        {
          id: 'anthropic-tool-result-untrusted-scope',
          basis: 'documented',
          question: 'Anthropic Messages 的 tool_result 边界和不可信内容建议能证明什么？',
          answer:
            'Anthropic 文档说明，客户端工具由应用读取 tool_use 后执行，再用 tool_result 回填；外部网页、邮件、上传文件或第三方 API 内容可能携带间接提示注入，因此建议将这类内容留在 tool_result 并按不可信内容处理。这是该 API 的消息格式和模型处理建议，不是授权、事实核验或不可绕过保证。OWASP LLM01:2025 同样将网站/文件等外部输入列为间接注入来源，并指出 RAG/微调并未完全消除此类风险；这些来源不能推出某个具体 provider 的抵御率。',
          sourceIds: ['anthropic-handle-tool-calls', 'owasp-llm-prompt-injection'],
        },
      ],
      resourceIds: ['mcp-docs', 'mcp-spec-changelog', 'anthropic-handle-tool-calls', 'owasp-llm-prompt-injection'],
    },
    {
      id: 'agent-security/supply-chain',
      chapterId: 'agent-security',
      slug: 'supply-chain',
      title: '第三方工具就是第三方依赖',
      summary: '引入第三方 MCP server 与增加软件依赖有相似的供应链风险，但本地执行、远程数据流与授权边界各不相同。',
      estimatedMinutes: 20,
      difficulty: 'advanced',
      hasBody: true,
      status: 'drafting',
      keywords: ['supply-chain', 'mcp'],
      checkpoints: [
        {
          id: 'mcp-as-dependency',
          basis: 'inferred',
          question: '为什么说接入一个第三方 MCP server 的决策，等同于引入一个第三方依赖？',
          answer:
            '它与普通依赖一样，会带来第三方代码/服务、升级和运行权限风险，但部署边界不同：本地 MCP server 通常以 client 授予的 OS 权限运行；远程 server 收到 host 实际发送的工具参数、认证信息或被显式转发的数据，协议本身不意味着它自动看到完整对话。host 可把工具元数据提供给模型，工具结果也可能被 host 放入上下文。`tools/list` 描述的是规范版本定义的声明元数据，不能证明实现、权限或副作用；实现可能可读，也可能是远程黑盒。治理应分别评审来源与制品、host 数据流、身份授权、运行环境、变更与撤销能力。依据见 MCP Tools 与 Security Best Practices。',
        },
        {
          id: 'mcp-tool-metadata-not-proof-of-implementation',
          basis: 'documented',
          question: 'MCP tools/list 中的工具描述、输入 schema 与 annotations 能否证明 server 的实现或安全权限？',
          answer:
            '不能。MCP Tools 规范定义 tools/list 返回工具名称、描述、输入 schema 以及可选的输出 schema 和 annotations 等元数据；客户端应将工具 annotations 视为不可信，除非来自可信 server。该元数据用于描述工具，不是实现代码、运行时权限或副作用的证明；工具清单还可能随授权上下文变化。',
          sourceIds: ['mcp-tools-2026'],
        },
        {
          id: 'supply-chain-controls',
          basis: 'inferred',
          question: '工程上可以对第三方工具做哪些具体约束？',
          answer:
            '按部署形态核查：审阅来源、描述/schema/annotations 的变化；审查可得的源码、依赖与发布物；本地 server 按 client 进程权限模型配置 sandbox、文件和网络范围；远程 server 核对 host 实际发送的数据、token scope、服务端身份及下游授权。锁定本地包版本和容器 digest；远程服务可记录 tools/list 元数据快照，但快照不固定实现。对日志采取字段最小化、脱敏、访问控制和期限管理。开源并非安全保证；自建决策要比较生命周期维护、测试、权限、审计和恢复成本，不能只比较代码行数。',
        },
      ],
      resourceIds: ['mcp-docs', 'mcp-tools-2026', 'mcp-security-best-practices-2026'],
    },
    {
      id: 'agent-security/exfiltration',
      chapterId: 'agent-security',
      slug: 'exfiltration',
      title: '数据外泄的三要素',
      summary: '沿数据可达性、外发路径与触发事件梳理风险；三项共存表示需要验证的威胁路径，不代表外泄必然成功。',
      estimatedMinutes: 20,
      difficulty: 'advanced',
      hasBody: true,
      status: 'drafting',
      keywords: ['exfiltration', 'data-flow'],
      checkpoints: [
        {
          id: 'exfil-requires-three',
          basis: 'inferred',
          question: '威胁建模时，可以沿哪些条件检查数据外泄路径？',
          answer:
            '沿数据可达性、外发路径与触发事件梳理风险；三项共存表示需要验证的威胁路径，不代表外泄必然成功。触发者可能是模型、用户或自动组件。控制应按具体系统的请求路径和威胁模型选择：用可信主体做对象级授权，限制实际网络出口，并单独检查文件、日志和用户可见输出。提示词与输入标注可降低部分样本的触发概率，但不是授权机制；任何单项控制都需验证覆盖面与绕过路径。',
        },
        {
          id: 'covert-channels',
          basis: 'inferred',
          question: '除了「调用工具发请求」，还有哪些隐蔽的外泄路径？',
          answer:
            '常见的非工具接收路径包括写入可被同步或共享的文件、写入会被外部平台采集的日志，以及输出到调用者可见的响应中。它们是否构成外泄，取决于谁能访问这些接收端及其后续处理；网络出口策略不会覆盖它们。对每条路径分别追踪身份、权限、数据流与保留策略。',
        },
        {
          id: 'csp-browser-request-scope',
          basis: 'documented',
          question: '浏览器 CSP 的 img-src 与 connect-src 分别约束什么？',
          answer:
            'W3C CSP Level 3 将 img-src 定义为限制图片资源 URL 的指令，将 connect-src 用于规范覆盖的脚本连接请求。这些是受页面 CSP 约束的浏览器请求；不能据此证明服务端抓取 URL 也受 CSP 控制。该 W3C 技术报告截至 2026-09-16 标为 Working Draft，兼容性还要按目标浏览器验证。',
          sourceIds: ['w3c-csp3'],
        },
        {
          id: 'ssrf-validate-connection-target',
          basis: 'documented',
          question: '服务端抓取不可信 URL 时，为什么 DNS 检查和最终连接必须一起审查？',
          answer:
            'OWASP SSRF 指南说明，域名可能泄露给外部 DNS resolver，也可能解析到内部 IP；其允许列表示例要求请求连接到已验证的 IP，并建议禁用客户端自动重定向以避免绕过输入校验。只检查一次 DNS、却让 HTTP 客户端之后自行解析或跟随未复核的跳转，不能证明实际连接目标仍满足策略。',
          sourceIds: ['owasp-ssrf-prevention'],
        },
        {
          id: 'anthropic-messages-and-retention-scope',
          basis: 'documented',
          question: 'Anthropic Messages API 的无状态语义能否说明所有上下文都会如何保留？',
          answer:
            '不能。Messages API 文档称多轮对话由应用在请求中提交对话历史；API 和数据保留文档另行列出数据处理安排、功能资格与组织/工作区配置。前者描述该 API 的请求状态模型，不能单独推出服务端保留时长，也不能推广到其他产品或供应商。',
          sourceIds: ['anthropic-working-with-messages', 'anthropic-api-data-retention'],
        },
      ],
      resourceIds: ['twelve-factor-agents', 'ai-engineering-huyen', 'owasp-authorization-cheat-sheet', 'owasp-ssrf-prevention', 'w3c-csp3', 'anthropic-working-with-messages', 'anthropic-api-data-retention'],
    },
    {
      id: 'agent-security/defense-in-depth',
      chapterId: 'agent-security',
      slug: 'defense-in-depth',
      title: '纵深防御：分层降低风险',
      summary: '通过不同控制限制单点失效的影响，并验证它们共享的身份、策略、运行时与审计依赖。',
      estimatedMinutes: 20,
      difficulty: 'expert',
      hasBody: true,
      status: 'drafting',
      keywords: ['defense-in-depth', 'layers'],
      checkpoints: [
        {
          id: 'layers',
          basis: 'inferred',
          question: '一套务实的 agent 安全分层是什么样的？',
          answer:
            '把输入来源标注、模型行为约束、执行时授权与隔离、审计响应组合起来，降低单点失效的影响。执行层是关键强制执行点，但策略覆盖、可信身份、底层权限与运行时安全仍是它的前提；审计能提供观测和追查，不能证明所有控制有效。'
        },
        {
          id: 'owasp-prompt-injection-mitigation',
          basis: 'documented',
          question: 'OWASP 对 prompt injection 的防护边界与缓解方式有哪些明确建议？',
          answer: 'OWASP LLM01:2025 指出 prompt injection 与模型处理输入的方式相关，目前没有 fool-proof 的彻底预防方法；可组合行为约束、输入/输出过滤、最小权限、外部内容隔离与对抗测试来降低影响。',
          sourceIds: ['owasp-llm-prompt-injection'],
        },
        {
          id: 'what-to-do-first',
          basis: 'inferred',
          question: '如果只能做三件事，先做哪三件？',
          answer:
            '**一，按授权、影响、可逆性与恢复能力给动作分级。** 只有符合业务策略的动作才进入人工审批；审批不能弥补越权，低风险动作也要经过授权。**二，收紧权限与出网。** 逐项列出任务必需的资源和目的地，按拒绝默认设计策略，并考虑 DNS/重定向/云元数据等部署风险。**三，建立可用的审计与响应。** 记录允许、拒绝、未知结果和策略故障，限制敏感字段，监控日志管道并指定告警 owner。这三类措施减少对模型服从性的依赖，但仍需针对目标威胁模型测试；更长的提示词不能替代授权、隔离与恢复控制。'
        },
      ],
      resourceIds: ['owasp-llm-prompt-injection', 'owasp-authorization-cheat-sheet', 'twelve-factor-agents', 'claude-agent-sdk'],
    },
    {
      id: 'agent-security/identity-and-tenancy',
      chapterId: 'agent-security',
      slug: 'identity-and-tenancy',
      title: '身份与租户：模型给出的 user_id 不是身份',
      summary: '把已验证 principal、action 与具体 resource 绑定，在每次 Agent 工具执行时强制租户和对象级授权。',
      estimatedMinutes: 28,
      difficulty: 'expert',
      hasBody: true,
      status: 'drafting',
      keywords: ['identity', 'authorization', 'tenant-isolation', 'idor'],
      checkpoints: [
        {
          id: 'authentication-is-not-authorization',
          basis: 'documented',
          question: '用户通过认证后，是否自然拥有每个对象与每个 action 的权限？',
          answer: '不是。认证确认主体身份，授权要判断该主体是否可以对指定资源执行指定操作；具体权限还要按业务策略逐次判定。',
          sourceIds: ['owasp-authorization-cheat-sheet'],
        },
        {
          id: 'tenant-from-trusted-context',
          basis: 'documented',
          question: '授权查询是否可以直接使用模型参数或请求体中的 tenant_id？',
          answer: '不可以。租户应从经过认证并由服务端验证的上下文中取得；请求体字段只是输入，不是身份凭据。对象访问还要在服务端对具体资源执行检查，避免 IDOR/水平越权。',
          sourceIds: ['owasp-authorization-cheat-sheet'],
        },
        {
          id: 'resource-scope-policy',
          basis: 'inferred',
          question: '怎样避免“同租户成员都可访问所有对象”这种过宽权限？',
          answer: '除成员关系和 tenant 约束外，还要根据 action 对 resource 检查 owner、ACL 或业务策略；本地模型把读权限设为同租户、写权限设为 owner，用负向用例验证策略差异。',
          note: '读写策略只是本节的教学例子；实际权限矩阵应由具体业务和威胁模型确定。',
        },
        {
          id: 'rls-is-not-table-privilege-control',
          basis: 'documented',
          question: 'PostgreSQL RLS 是否能限制所有表操作，并自动保护表所有者与完整性检查？',
          answer: '不能。RLS 约束普通行级 SELECT、INSERT、UPDATE、DELETE；TRUNCATE、REFERENCES 不受行策略约束，表所有者通常绕过策略，superuser/BYPASSRLS 总会绕过，外键与唯一性等完整性检查也不受行策略过滤。仍需单独配置 SQL 权限、运行角色与并发安全。',
          sourceIds: ['postgres-row-security'],
        },
        {
          id: 'rls-using-with-check-and-transaction-context',
          basis: 'documented',
          question: 'RLS 更新策略里的 USING 和 WITH CHECK 分别检查什么，事务本地 tenant 设置又保证了什么？',
          answer: 'USING 限定已有行是否可见或可作为更新目标；WITH CHECK 验证插入或更新后的新行。set_config(..., true) 只保证值在当前事务内有效，不验证值是否来自可信身份；tenant 值仍须由可信服务端从已验证 principal 派生，并且 RLS 不能替代对象级授权。',
          sourceIds: ['postgres-create-policy-18', 'postgres-setting-local-18'],
        },
      ],
      resourceIds: ['owasp-authorization-cheat-sheet', 'postgres-row-security', 'postgres-create-policy-18', 'postgres-setting-local-18'],
    },
  ],
  resourceIds: [
    'mcp-docs',
    'mcp-spec-changelog',
    'twelve-factor-agents',
    'ai-engineering-huyen',
    'claude-agent-sdk',
    'anthropic-building-effective-agents',
  ],
  labIds: ['lab-injection-probe'],
  backendMapping: {
    analogy:
      'agent 安全 ≈ 一个对外开放且有写权限的服务：威胁模型变了，但最小权限、纵深防御、审计这套方法论没变',
    transferable: [
      '威胁建模的习惯：先列资产与入口，再看最坏后果',
      '最小权限、专用身份、出网白名单 —— 运维里怎么做，这里就怎么做',
      '供应链治理：锁版本、评审来源、保留移除能力',
    ],
    pitfalls: [
      '把提示注入当成「输出质量」问题，忽略它的下游是真实的动作',
      '只把用户输入当不可信来源，忘了检索内容、工具返回值、代码注释与子 agent 摘要',
      '相信加了分隔标签就能挡住注入 —— 实测对内容操纵无效',
      '把安全重心放在写更严的 system prompt 上，而执行层没有校验',
      '只盯网络出口，忽略写文件、写日志、输出给用户这三条隐蔽路径',
    ],
    cost: 'high',
  },
  status: 'published',
  updatedAt: '2026-10-22',
  verifiedAt: '2026-10-22',
} satisfies Chapter;
