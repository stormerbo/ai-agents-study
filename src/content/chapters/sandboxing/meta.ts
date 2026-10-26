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
      title: '隔离解决什么问题',
      summary: '提示和工具注册表都不保证执行环境的可达范围；隔离用来缩小潜在影响边界。',
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
            '隔离是纵深防御的一种：它不判断模型意图，而是限制进程实际可达的文件、网络与资源。提示注入可能尝试影响后续行为；模型输出也可能不符合任务要求；重试或实现缺陷还可能造成意外动作。是否发生以及影响多大取决于模型、上下文、宿主身份、挂载、网络出口和执行器配置，必须在目标部署环境验证。',
        },
        {
          id: 'capability-decides-isolation',
          basis: 'inferred',
          question: '隔离级别该由什么决定？',
          answer:
            '由**能力组合和威胁模型**决定，而不是由「这个 agent 重不重要」决定。只有在无敏感数据、无外部副作用且输出范围受控时，才可以考虑不增加独立执行隔离；仍须由宿主执行对象级授权和资源限制。能执行不可信代码时，应评估 OS/运行时边界；能访问内部网络且能读取外部内容时，还要单独限制网络出口和数据外传。判断顺序是先列出它实际需要的能力（读什么、写什么、连什么网、用谁的凭据），再问「如果这一项被滥用，最坏会怎样」，并验证宿主配置是否真的能把影响限制在可接受范围。',
        },
        {
          id: 'authorization-versus-isolation',
          basis: 'documented',
          question: '身份认证、工具授权、对象级授权和隔离分别检查什么？',
          answer: '身份认证确认主体；授权需要在请求时检查主体是否可执行动作、访问具体对象；隔离限制进程实际可达资源。OWASP 建议默认拒绝并对每次请求验证权限，不能用工具名或难猜 ID 代替对象级授权。',
          sourceIds: ['owasp-authorization-cheat-sheet'],
        },
        {
          id: 'ssrf-is-not-sandboxing',
          basis: 'documented',
          question: '为什么隔离执行环境不能单独防住 SSRF？',
          answer: 'SSRF 是服务端按不可信目标发起请求的问题；需在连接层验证目标、处理 DNS 与重定向。进程隔离可以限制出口，但不能替代请求目标策略。',
          sourceIds: ['owasp-ssrf-prevention'],
        },
        {
          id: 'path-resolution-races',
          basis: 'documented',
          question: '为什么 realpath 检查后再 open 仍可能有竞态？',
          answer: '路径检查与打开是分开的操作；并发变化可能使最终打开对象不同于先前检查对象。Linux openat2 提供路径解析约束，但实际可用性取决于内核与部署。',
          sourceIds: ['linux-openat2-path-lookup'],
        },
        {
          id: 'temporary-fixture-cleanup',
          basis: 'documented',
          question: '使用 tempfile.mkdtemp 创建目录时，如何确保 fixture 被清理？',
          answer: 'mkdtemp 返回唯一目录，但调用方负责清理；示例通过进程退出处理删除临时目录，并由 verifier 检查不会删除 TMPDIR 中的其他文件。',
          sourceIds: ['python-tempfile'],
        },
      ],
      resourceIds: ['twelve-factor-agents', 'ai-engineering-huyen', 'owasp-authorization-cheat-sheet', 'owasp-ssrf-prevention', 'linux-openat2-path-lookup', 'python-tempfile'],
    },
    {
      id: 'sandboxing/isolation-levels',
      chapterId: 'sandboxing',
      slug: 'isolation-levels',
      title: '隔离的层级',
      summary: '从进程内限制到容器与虚拟机边界；按威胁模型和爆炸半径选型。',
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
            '可把隔离讨论为五个层级：**L0 进程内**没有独立边界；**L1 语言层限制**只降低误用风险，不是安全边界；**L2 独立进程**可限制部分资源与墙钟时间，但不自动收窄文件、网络或进程树；**L3 容器**共享宿主内核，依配置使用 namespace、挂载、cgroup、capabilities 与安全策略；**L4 VM/microVM**增加 guest kernel 与 hypervisor 边界，但仍依赖 hypervisor、设备模型与宿主配置。层级不是绝对安全排名，选择取决于代码信任、暴露的数据/副作用、租户模型、延迟与运行时能力。模型生成代码需要宿主强制的隔离边界；具体采用容器或 microVM 应按威胁模型验证，不能只按层级名称推断安全。',
        },
        {
          id: 'escape-surface',
          basis: 'inferred',
          question: '容器隔离最容易在哪几个地方漏？',
          answer:
            '三个需要按部署条件检查的暴露面。**挂载**：若把范围过大的宿主目录以读写方式挂入，容器内进程可在该挂载范围内读写其权限允许的文件；实际可见内容还取决于挂载范围和宿主权限。**网络**：默认网络配置可能允许访问外部或已连接网络中的目标，但可达性取决于路由、防火墙、Docker 配置及目标服务；只有任务代码能够发出请求、目标可达且响应/数据进入可外传路径时，才构成相应的数据外泄路径。**凭据**：若 secret 值被放入容器内进程可见的环境变量，能读取该环境的代码就可能读到它；应避免向不可信任务进程注入不需要的凭据。它们是需分别验证的边界，某一层配置良好不能替代其余边界的检查。',
        },
        {
          id: 'python-resource-limit-scope',
          basis: 'documented',
          question: 'Python 子进程的资源限制和超时会自动覆盖哪些范围？',
          answer:
            '`resource` 模块及各个限制的可用性依 Unix 平台而异；`RLIMIT_CPU` 限制进程 CPU 时间。`subprocess` 的超时处理针对被调用子进程，不自动证明其派生进程树已终止；执行器须依据目标平台另外实现并验证进程组/作业对象清理。',
          sourceIds: ['python-resource-limits', 'python-subprocess'],
        },
        {
          id: 'container-and-runtime-boundaries',
          basis: 'documented',
          question: 'Docker、gVisor 与 Firecracker 分别提供什么配置或执行边界？',
          answer:
            'Docker 文档列出的只读文件系统、挂载、网络、用户和 capability 等参数用于配置容器，不代表宿主威胁已自动覆盖。gVisor 使用用户态 application kernel；Firecracker 提供基于 KVM 的 microVM。二者架构不同，具体安全边界仍需按各自文档和目标部署验证。',
          sourceIds: ['docker-run-container', 'gvisor-security', 'firecracker-microvm-design'],
        },
        {
          id: 'docker-none-network',
          basis: 'documented',
          question: 'Docker 的 none 网络与 loopback 有什么关系？',
          answer:
            '`--network none` 不把容器接入外部 Docker 网络，并保留 loopback；是否存在额外接口名、默认路由或宿主侧出口策略，应在目标运行时实测。官方说明不能替代具体部署检查。',
          sourceIds: ['docker-none-network'],
        },
      ],
      resourceIds: ['claude-agent-sdk', 'openhands', 'docker-run-container', 'docker-none-network', 'python-resource-limits', 'python-subprocess', 'gvisor-security', 'firecracker-microvm-design'],
    },
    {
      id: 'sandboxing/least-privilege',
      chapterId: 'sandboxing',
      slug: 'least-privilege',
      title: '文件系统与网络的最小权限',
      summary: '最小权限要按威胁模型具体落实到文件、连接目标与 OS 边界。',
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
            '**默认最小化读写权限**：能读的目录按任务需要限定，可写目录单独隔离并按生命周期清理，敏感路径通过权限和 OS 策略隔离。路径前缀字符串比较不可靠；realpath 能说明 `..`/符号链接的解析问题，但 realpath、类型检查与 open 分步进行时存在 TOCTOU 竞态。对可被并发修改的目录，应采用 OS sandbox、受限目录句柄 API，或 Linux `openat2` 的解析约束；还要限制单次读取大小。',
        },
        {
          id: 'network-policy',
          basis: 'inferred',
          question: '如何按任务边界配置最小网络权限？',
          answer:
            '网络权限要按任务威胁模型设置：已知服务调用采用精确 host/IP、端口与协议 allowlist，由连接层/出口策略强制；若处理任意用户 URL，则需在连接时检查目标 IP、处理 DNS 重绑定，并禁用或重新校验 redirect。公网抓取通常应阻止 loopback、link-local、组织私网和云元数据，但这不是所有内部服务调用都适用的统一规则。本站离线 fixture 只验证 URL policy 分支，没有发 DNS 或 HTTP 请求。',
        },
        {
          id: 'openat2-path-resolution-boundary',
          basis: 'documented',
          question: 'Linux openat2 的 RESOLVE_BENEATH 与 RESOLVE_IN_ROOT 如何约束路径解析？',
          answer:
            '`RESOLVE_BENEATH` 拒绝解析到起始目录之外的路径；`RESOLVE_IN_ROOT` 将给定目录句柄当作本次解析的 root。它们是单次 openat2 路径解析的约束选项，行为、其他 flags 和内核支持需按目标 Linux 版本核验；不能据此声称文件内容授权或所有文件类型/副作用都已受限。',
          sourceIds: ['linux-openat2-manpage', 'linux-openat2-path-lookup'],
        },
        {
          id: 'protected-hardlinks-scope',
          basis: 'documented',
          question: 'Linux fs.protected_hardlinks 是否能代替文件权限和隔离？',
          answer:
            '内核文档说明 `protected_hardlinks=1` 时，用户不能对自己不拥有、且没有读写权限的源文件创建硬链接；设为 0 时行为不受此项限制。它只约束一类硬链接创建情形，是否存在及当前值依系统配置，不能代替文件权限、独立文件系统或 OS sandbox。',
          sourceIds: ['linux-fs-protected-hardlinks'],
        },
        {
          id: 'ssrf-target-validation',
          basis: 'documented',
          question: '服务端抓取 URL 时，为什么校验 DNS 后还要控制实际连接？',
          answer:
            'OWASP SSRF 指南区分已知可信目标 allowlist 与任意外部地址；对允许的目标，应校验实际 IP 并让客户端连接该验证地址，处理 DNS rebinding，并禁用自动重定向或对每次跳转重新执行完整校验。Python `ipaddress.is_global` 按 IANA 特殊用途登记分类，且其结果曾在 Python 3.13 调整；它不能单独表达组织自有地址策略。本站代码只运行固定 DNS fixture，不执行 DNS 或 HTTP。',
          sourceIds: ['owasp-ssrf-prevention', 'python-ipaddress'],
        },
      ],
      resourceIds: ['owasp-ssrf-prevention', 'python-ipaddress', 'linux-openat2-path-lookup', 'linux-openat2-manpage', 'linux-fs-protected-hardlinks'],
    },
    {
      id: 'sandboxing/secrets',
      chapterId: 'sandboxing',
      slug: 'secrets',
      title: '凭据不该进入上下文',
      summary: '凭据离开可信边界后，暴露面取决于请求、日志与会话的具体实现。',
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
            '如果凭据进入模型可见数据，它会被发送给该次请求使用的 API 提供方；是否进入应用/代理日志、是否在后续请求重发、如何保留，则取决于消息构造、日志配置和提供方政策。模型也可能输出或转发看到的内容。应让凭据值留在模型不可见的可信边界，并对日志做字段白名单与脱敏测试。请求头和请求体都可能被记录，不能笼统地把某一种位置称为安全。',
        },
        {
          id: 'secret-hygiene',
          basis: 'inferred',
          question: '除了不放进上下文，凭据管理还有哪几条要做到？',
          answer:
            '四条：**权限最小** —— 凭据只具备当前任务所需权限；**生命周期受控** —— 能移除或替换时优先采用短期凭据，静态凭据按类型、风险和下游能力安排轮换，暴露时可撤销；**主体可归因** —— 专用服务身份只能标识服务，最终用户身份应由可信宿主从认证上下文单独记录；以及**日志最小化** —— 使用字段白名单，在应用、SDK、代理与导出边界验证敏感字段不会落盘，模式扫描只是补充。',
        },
        {
          id: 'short-lived-credentials-and-rotation',
          basis: 'documented',
          question: '官方 secrets 管理指南如何建议减少长期凭据风险？',
          answer:
            'AWS Well-Architected SEC02-BP03 建议优先移除不再需要的 secret，能替换时用短期凭据；仍需长期凭据时放入专用 secrets manager，并在支持时配置自动轮换。OWASP Secrets Management Cheat Sheet 同时强调生命周期、最小权限与按凭据用途安排轮换；这不构成所有凭据都采用同一固定周期的依据。',
          sourceIds: ['aws-well-architected-secrets', 'owasp-secrets-management'],
        },
        {
          id: 'secrets-must-not-enter-logs',
          basis: 'documented',
          question: '应用日志应如何处理密码、访问令牌和 API key？',
          answer:
            'OWASP Logging Cheat Sheet 将 authentication passwords、access tokens、encryption keys 等列为通常不应直接记录的敏感数据；若业务确需关联，应采用适当的移除、掩码、哈希或加密，并控制访问与保留。单一正则不能证明所有日志路径和秘密格式都被覆盖。',
          sourceIds: ['owasp-logging-cheat-sheet'],
        },
        {
          id: 'authorization-is-per-request',
          basis: 'documented',
          question: '为什么不能以模型提供的租户 ID 或资源 ID 作为授权证明？',
          answer:
            'OWASP Authorization Cheat Sheet 建议默认拒绝，并在每次访问时验证权限；访问具体对象时应执行 object-level authorization。请求中的租户/资源标识只是定位输入，不是可信主体或授权决定。',
          sourceIds: ['owasp-authorization-cheat-sheet'],
        },
      ],
      resourceIds: ['owasp-secrets-management', 'aws-well-architected-secrets', 'owasp-logging-cheat-sheet', 'owasp-authorization-cheat-sheet'],
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
            '按威胁模型记录足以关联事件的最小字段：可信主体、任务/请求关联 ID、工具动作、授权结果与规则、受影响目标的安全摘要、执行结果（成功、失败或未知）及触发来源。不要默认记录完整参数；它们可能含密钥、个人信息或攻击者控制的内容。使用字段白名单、长度限制和安全编码，并定义访问控制、保留期与日志接收失败策略。',
        },
        {
          id: 'authorization-default-deny',
          basis: 'documented',
          question: '授权没有命中规则时该如何处理，权限应多久验证一次？',
          answer:
            'OWASP 建议访问默认拒绝，并在每个请求上验证权限；应用应审查每条访问路径，避免遗漏的检查形成旁路。',
          sourceIds: ['owasp-authorization-cheat-sheet'],
        },
        {
          id: 'audit-sensitive-fields',
          basis: 'documented',
          question: '审计日志应如何处理访问令牌、密钥和不可信字段？',
          answer:
            'OWASP Logging 建议不要直接记录访问令牌、认证密码和主要密钥；应对事件数据进行清理，防止 CR/LF 与分隔符造成日志注入，并按输出格式编码。',
          sourceIds: ['owasp-logging-cheat-sheet'],
        },
        {
          id: 'cgroup-controller-availability',
          basis: 'documented',
          question: '声明了 cgroup v2 资源上限后，如何确认控制器实际可用并已启用？',
          answer:
            '`cgroup.controllers` 列出当前 cgroup 可启用的控制器；控制器默认不启用，需通过 `cgroup.subtree_control` 配置，而且子层级受父层级启用状态约束。部署检查必须读取目标主机与层级的真实状态。',
          sourceIds: ['linux-cgroup-v2'],
        },
        {
          id: 'subprocess-timeout-cleanup',
          basis: 'documented',
          question: '`Popen.communicate(timeout=...)` 超时后，调用方还要做什么？',
          answer:
            '等待超时会抛出 `TimeoutExpired`，但不会自动杀死子进程；调用方应显式终止子进程并再次 `communicate()` 完成清理。捕获的输出会缓存在内存，不能用它承接无界输出。',
          sourceIds: ['python-subprocess'],
        },
      ],
      resourceIds: ['claude-agent-sdk', 'openhands', 'owasp-authorization-cheat-sheet', 'owasp-logging-cheat-sheet', 'linux-cgroup-v2', 'python-subprocess'],
    },
  ],
  resourceIds: [
    'claude-agent-sdk',
    'twelve-factor-agents',
    'openhands',
    'mcp-docs',
    'ai-engineering-huyen',
  ],
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
