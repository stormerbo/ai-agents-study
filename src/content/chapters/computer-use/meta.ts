import type { Chapter } from '@/content/curriculum/schema';

export const chapter = {
  id: 'computer-use',
  stageId: 'stage-2-primitives',
  order: 9,
  title: '计算机使用',
  subtitle: '让模型操作界面',
  summary:
    '从自建截图/坐标适配器出发，理解 GUI 自动化的观测、动作与结果边界，并区分 browser-use、computer-use、业务 API 等路线；再学习失败模式、权限边界与选型。',
  outcomes: [
    '能限定自建截图/坐标适配器与语义化 API 的差异，并识别 browser-use 等结构化页面观测路线',
    '能为一个界面自动化任务设计出「每步重新观测」的循环与停止条件',
    '能判断一个任务该走 API 还是走界面，并给出理由',
  ],
  depth: 'deep',
  difficulty: 'advanced',
  estimatedMinutes: 90,
  tags: ['computer-use', 'gui', 'automation'],
  prerequisiteIds: ['tool-calling', 'multimodal'],
  lessons: [
    {
      id: 'computer-use/what-differs',
      chapterId: 'computer-use',
      slug: 'what-differs',
      title: '它和工具调用的三点区别',
      summary: '以自建截图/坐标适配器为例，对照语义化 API 与 browser-use，理解观测、动作和结果反馈的差异。',
      estimatedMinutes: 20,
      difficulty: 'intermediate',
      hasBody: true,
      status: 'drafting',
      keywords: ['computer-use', 'tool-use'],
      checkpoints: [
        {
          id: 'three-differences',
          basis: 'inferred',
          question: '计算机使用与函数调用，本质差别在哪三点？',
          answer:
            '本节讨论的是自建截图/坐标适配器：它把截图作为观测，并给模型一组 click/type 等原语提议；这些动作不携带业务语义，宿主必须验证、授权、执行并检查业务后置条件。该描述不适用于所有 computer-use 工具集：Anthropic computer use 是由宿主执行并回传结果的成员工具集，支持批量动作；browser use 还提供页面结构、可访问性树和元素引用。执行失败可通过协议结果反馈，但工具调用成功不等于业务任务成功。应按实际接口与应用状态判断，而不是把差异归结为“API 封闭、GUI 开放”或认为错误信号天生缺失。',
        },
        {
          id: 'api-redirect-boundary',
          question: '为什么本节携带 API Key 的 urllib 请求拒绝自动重定向？',
          answer:
            'urllib 的默认 HTTP 重定向处理器会将 POST 改为 GET，并可能把普通请求头带到重定向目标。请求含 x-api-key 时，示例使用自定义处理器在 30x 处停止；应核对可信 endpoint，而不是自动向新 URL 重发凭据。',
          basis: 'documented',
          sourceIds: ['python-urllib-request'],
          note: '此处只约束 Python urllib 客户端的自动跳转；不替代对 base URL、DNS、代理、TLS 或服务端目标的安全校验。',
        },
        {
          id: 'why-general-purpose-is-harder',
          basis: 'inferred',
          question: '为什么「动作更通用」反而让它更难做对？',
          answer:
            '点击坐标可做范围、窗口和目标区域校验，但通常缺少“这个控件代表哪项业务操作”的语义约束；页面变化还可能改变同一坐标的含义。这个风险来自具体适配器和宿主权限，不代表所有通用动作都无法校验，也不代表每次动作都必须立刻重发整张截图。应选择适合任务的新鲜观测（页面结构、截图或应用 API），执行前做授权与副作用控制，执行后检查独立业务判据。',
        },
      ],
      resourceIds: ['anthropic-computer-use', 'anthropic-browser-use', 'anthropic-tool-combinations', 'claude-messages-api', 'twelve-factor-agents', 'python-urllib-request'],
    },
    {
      id: 'computer-use/observe-act-loop',
      chapterId: 'computer-use',
      slug: 'observe-act-loop',
      title: '观测-动作循环',
      summary: '根据动作影响获取足够新鲜的观测，并用任务级判据决定继续、停止或交给人工。',
      estimatedMinutes: 20,
      difficulty: 'intermediate',
      hasBody: true,
      status: 'drafting',
      keywords: ['loop', 'screenshot'],
      checkpoints: [
        {
          id: 'must-reobserve',
          basis: 'inferred',
          question: '什么情况下动作后应重新截图或查询应用状态？',
          answer:
            '当下一步依赖动作可能改变的界面状态时，应取得足够新鲜的观测；可以是截图、DOM/可访问性信息、设备状态或应用 API，具体取决于适配器能提供什么。旧观测不能证明动作已生效，也不能确认异步变化。无需把“每次动作后必须发整屏截图”当成所有工具的协议要求；本节的截图/坐标循环只是其中一种做法。',
        },
        {
          id: 'credential-redirect-boundary',
          basis: 'documented',
          question: 'API 请求携带 key 时，怎样防止 HTTP 重定向把凭据带到跳转目标？',
          answer:
            '对携带凭据的请求，默认拒绝自动重定向，除非已明确验证目标与凭据转发策略。Python urllib 可用自定义 HTTPRedirectHandler 让 redirect_request 返回 None，并通过该 opener 发请求；这只阻止自动跟随，不替代对原始 base URL、TLS、代理和凭据来源的信任配置。',
          sourceIds: ['python-urllib-request'],
        },
        {
          id: 'loop-termination',
          basis: 'inferred',
          question: '这个循环的终止条件，和普通 agent 循环有什么不同？',
          answer:
            '至少分清三种结果：任务成功（由应用状态或独立判据确认）、安全/预算停止（步数或成本上限）、以及未确认完成的退出（模型请求 done、连续无进展或错误）。相同截图只能作为启发式停滞信号，不是成功证据；具体阈值需根据界面动态、哈希碰撞和任务风险评估。界面操作也可能使用 API stop reason，但该协议状态不等于业务任务成功。',
        },
      ],
      resourceIds: ['anthropic-context-engineering', 'claude-messages-api', 'anthropic-computer-use', 'deepseek-vision', 'python-urllib-request'],
    },
    {
      id: 'computer-use/failure-modes',
      chapterId: 'computer-use',
      slug: 'failure-modes',
      title: '失败模式',
      summary: '界面动作可能落空、重复执行，或产生未满足业务后置条件的结果；需按适配器反馈与任务风险设计独立验收。',
      estimatedMinutes: 22,
      difficulty: 'advanced',
      hasBody: true,
      status: 'drafting',
      keywords: ['failure-modes', 'reliability'],
      checkpoints: [
        {
          id: 'silent-failures',
          basis: 'inferred',
          question: '如何分类界面自动化的失败，并确认任务结果？',
          answer:
            '界面动作至少要区分未命中/未生效、状态未知、作用对象或业务结果不符等情况。严重度取决于副作用与权限，不能一概说静默错误总比可见错误危险。可用语义定位、适配器反馈、独立后置条件与风险匹配的审批来降低风险；坐标漂移只是可能的失败模式之一。',
        },
        {
          id: 'state-unknown',
          basis: 'inferred',
          question: '「点了但不知道有没有生效」这种情况该怎么处理？',
          answer:
            '这是界面场景里的**状态未知**问题。重复下单、发送等动作可能带来重复副作用，因此在重试前应优先查询新鲜状态或使用去重机制；如能确认未生效，可按任务策略重试。若状态仍无法确认，应保留 unknown/failed_unconfirmed 结果，并按风险、授权和补偿能力决定等待、人工介入或后续处理。',
        },
      ],
      resourceIds: ['twelve-factor-agents', 'claude-messages-api', 'deepseek-anthropic-api']
    },
    {
      id: 'computer-use/safety-and-scope',
      chapterId: 'computer-use',
      slug: 'safety-and-scope',
      title: '权限与活动范围',
      summary: '界面自动化使用通用坐标动作，需由可信宿主限制可执行动作、预算与授权，并核验业务结果。',
      estimatedMinutes: 20,
      difficulty: 'advanced',
      hasBody: true,
      status: 'drafting',
      keywords: ['permissions', 'safety'],
      checkpoints: [
        {
          id: 'scope-definition',
          basis: 'inferred',
          question: '为一个界面 agent 划定活动范围，具体要限制哪些东西？',
          answer:
            '可从**调用者身份与凭据、目标资源、动作和参数、数据范围**四方面定义策略，但还要结合应用权限与执行器能力。身份和动作类型不能单独构成通用的“最小安全集”：授权应在可信宿主按每次请求校验，并绑定调用者、目标和参数；默认拒绝未声明动作。站点/页面白名单与坐标安全区只约束部分导航或点击路径，不证明目标语义正确，也不替代应用侧授权。可逆性是风险因素之一，是否需要审批应按影响、用户授权和恢复能力决定。数据范围还应覆盖读取、进入模型上下文、日志留存与外发。'
        },
        {
          id: 'python-bool-inheritance',
          basis: 'documented',
          question: '为什么预算输入不能只用 isinstance(value, int) 校验？',
          answer:
            'Python 内置类型文档将 bool 定义为 int 的子类；True 和 False 在数值上下文中分别表现为 1 和 0，因此只用 isinstance(value, int) 会把布尔值当成预算整数。边界校验应显式排除 bool。',
          sourceIds: ['python-built-in-types'],
        },
        {
          id: 'budget-input-boundaries',
          basis: 'inferred',
          question: '本地预算闸门应如何验证预留量和实际 usage？',
          answer:
            '请求前预留量与响应后 usage 都应校验为非负整数；预算阈值与文本限制也应拒绝类型不符和越界值。预留只针对当前进程的教学模型，不能代替并发场景下的原子共享预算。',
        },
        {
          id: 'irreversible-actions',
          basis: 'inferred',
          question: '对不可逆动作，确认点应该放在哪一层？',
          answer:
            '高影响或授权不足的动作应由可信宿主在副作用发生前执行授权决策；模型不能批准自己提出的动作。授权应绑定已验证的调用者、任务、目标与参数，并处理有效期、一次性消费、并发和撤销。额外人工确认是基于影响与恢复能力选择的控制，不是所有不可逆动作都必须采用的唯一方案。若使用 UI 确认，应展示足够的目标和参数供用户核对。提示注入是威胁来源之一，不能靠提示词或弹窗本身解决；还要验证执行身份、应用权限和实际授权覆盖路径。',
        },
      ],
      resourceIds: ['twelve-factor-agents', 'claude-agent-sdk', 'anthropic-handle-tool-calls', 'owasp-authorization-cheat-sheet', 'owasp-logging-cheat-sheet', 'python-built-in-types'],
    },
    {
      id: 'computer-use/when-not-to-use',
      chapterId: 'computer-use',
      slug: 'when-not-to-use',
      title: '什么时候别用它',
      summary: '按任务语义、授权、反馈、恢复与总成本比较 API、CLI、网页结构化工具和整桌面操作；旧 token 对照不构成有效端到端 benchmark。',
      estimatedMinutes: 18,
      difficulty: 'intermediate',
      hasBody: true,
      status: 'drafting',
      keywords: ['trade-offs'],
      checkpoints: [
        {
          id: 'api-first',
          basis: 'inferred',
          question: '选择 API、CLI、DOM/accessibility 或截图/坐标界面路线时，应比较哪些条件？',
          answer:
            '旧对照中 API 臂只生成 tool_use 参数，未执行工具；GUI 臂只更新本地模拟表单，done 仅检查字段非空。因此 14.4 倍 token 比值和 5 次往返不是统一后置条件下的端到端成本对照，历史原始响应缺失也无法独立复算。选型应先找满足任务语义、真实授权、状态反馈和恢复要求的最窄接口，再用同一任务验收标准比较 executor、延迟、usage、失败/未知结果和维护成本；不能因其被称为 API 就预设便宜或安全。',
        },
        {
          id: 'api-harness-redirect-boundary',
          basis: 'documented',
          question: '为什么带有 API key 的 urllib 请求不应默认跟随重定向？',
          answer:
            'Python urllib.request 文档说明，HTTPRedirectHandler.redirect_request 可以返回 None 来拒绝自动重定向；默认处理会对 POST 的 301/302 自动跳转并改成 GET。拒绝自动跳转能阻止这个客户端把带凭据的请求继续发往未经验证的目标，但不替代可信 base URL、TLS、代理与凭据配置。',
          sourceIds: ['python-urllib-request'],
        },
        {
          id: 'when-gui-is-right',
          basis: 'inferred',
          question: '哪些约束下可以考虑网页或桌面 UI 路线？',
          answer:
            '先按环境区分路线：网页任务可比较业务 API、CLI、DOM/accessibility locator、browser agent 和人工操作；Anthropic 当前 browser-use 文档描述了结合页面结构、元素引用与截图的浏览器路线。确需整桌面输入、跨应用操作或视觉验收时，再评估 computer-use 或人工流程。遗留系统和一次性任务也不自动意味着 GUI 更合算，需把工程集成、授权、失败恢复、总运行成本和维护纳入比较。若高频可靠任务长期只能依赖不稳定 UI，应评估提供 API 或更强应用状态接口。',
        },
      ],
      resourceIds: ['mcp-docs', 'twelve-factor-agents', 'anthropic-computer-use', 'anthropic-tool-combinations', 'anthropic-browser-use', 'playwright-locators', 'python-urllib-request'],
    },
  ],
  resourceIds: [
    'claude-messages-api',
    'twelve-factor-agents',
    'mcp-docs',
    'anthropic-context-engineering',
    'claude-agent-sdk',
  ],
  backendMapping: {
    analogy:
      '界面自动化 ≈ 用坐标代替接口：动作空间更通用，但没有类型约束、没有错误码、也没有幂等语义',
    transferable: [
      '你写过 UI 自动化测试 —— 等待、重试、选择器稳定性是同一套问题',
      '幂等与「状态未知」的处理经验：先观测再决定，不要盲目重试',
      '权限最小化：专用账号 + 白名单，把事故半径压到最小',
    ],
    pitfalls: [
      '把截图/坐标 adapter 的反馈局限推广到所有网页和桌面自动化路线；browser、DOM、CLI 和业务 API 的观察与错误信号各不相同',
      '复用上一步的截图或坐标继续推理，让模型基于过期画面做决策',
      '用提示词约束不可逆动作，而不是在执行层拦',
      '把旧的不等价 API / 合成 GUI harness 用量比推广成任意路线的成本规律',
      '在状态未知时自动重试，造成重复提交',
    ],
    cost: 'high',
  },
  status: 'published',
  updatedAt: '2026-10-08',
  verifiedAt: '2026-10-08',
} satisfies Chapter;
