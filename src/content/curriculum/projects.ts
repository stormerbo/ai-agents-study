import type { Project } from './schema';

function rubric(prefix: string, rows: [string, string, string, string, string][]) {
  return rows.map(([criteria, none, weak, adequate, strong], index) => ({
    id: `${prefix}-${index + 1}`,
    criteria,
    weight: 1,
    levels: [
      { score: 0 as const, descriptor: none },
      { score: 1 as const, descriptor: weak },
      { score: 2 as const, descriptor: adequate },
      { score: 3 as const, descriptor: strong },
    ],
  }));
}

/**
 * 实战作业注册表。
 *
 * 每个阶段一个可交付的项目。设计原则：**作业必须只依赖该阶段及更早章节的知识**，
 * 否则会变成"逼读者去查还没学的东西"，而不是检验学习成果。
 *
 * 评分清单（rubric）是自评用的 —— 每项都写成"能观察到什么"，而不是"做得好不好"。
 */
export const projects: Record<string, Project> = {
  'p1-reliable-extraction': {
    id: 'p1-reliable-extraction',
    stageId: 'stage-1-foundation',
    title: '可靠的结构化抽取器',
    brief:
      '从售后订单消息中抽取诉求、订单号和证据，交付一个面对脏数据也能解释失败原因的结构化抽取 CLI。',
    requirements: [
      '输入：合成的售后订单消息，含缺字段、错别字、多个诉求和互相矛盾的描述',
      '输出：售后订单号、诉求类型、用户请求、原文证据片段和不确定字段；不得补造文本中没有的订单事实',
      '提供命令行或 HTTP 接口，能对同一段文本重复调用',
      '对每一份输出，附带一个自评的置信度或"哪些字段没把握"的说明',
      '准备至少 10 段测试文本，其中至少 3 段是刻意构造的边界情况（内容残缺、格式混乱、包含干扰信息）',
      '冻结 prompt、schema 与数据集版本；每次提示修改都在同一批样本上配对复跑，分别报告结构成功率、逐字段精确率和全字段 exact-match，并保留失败样本。只用离线 fixture 时须标为控制流/评分器验证，不能宣称提示质量提升。',
    ],
    constraints: [
      '不得使用任何 agent 框架（LangChain / LlamaIndex 等）',
      '不得使用厂商强制 Schema；本阶段练习提示设计与代码校验。',
      '必须自己实现重试与失败降级，不能把异常直接抛给调用方',
      '必须记录每次调用的 token 用量，并在程序结束时汇总',
    ],
    milestones: [
      { id: 'm1', title: '跑通一次调用', detail: '能对一段文本产出结构化结果，先不管稳定性' },
      {
        id: 'm2',
        title: '设计 schema 与提示',
        detail: '把输出结构定下来，写清字段含义与边界，并在提示里给出示例',
      },
      { id: 'm3', title: '加上校验与重试', detail: '解析失败时带上具体错误信息重试，次数有上限' },
      { id: 'm4', title: '跑 10 段测试集', detail: '记录成功率、失败模式分类，以及 token 成本' },
      {
        id: 'm5',
        title: '写一份失败分析',
        detail: '哪些失败是提示问题、哪些是任务本身不适合这样做',
      },
      {
        id: 'm6',
        title: '运行 Prompt 回归对照',
        detail:
          '冻结 prompt/schema 与样本版本，比较修改前后的逐字段结果；使用 examples/prompt-regression 检查散列、分母和退化样本。',
      },

    ],
    rubric: [
      {
        id: 'r1',
        criteria: '10 段测试文本的解析成功率',
        weight: 3,
        levels: [
          { score: 0, descriptor: '不到一半能跑通' },
          { score: 1, descriptor: '过半，但边界情况基本全挂' },
          { score: 2, descriptor: '常规样本全通过，边界情况有部分能处理' },
          { score: 3, descriptor: '边界情况也有明确处理策略，失败时不崩溃' },
        ],
      },
      {
        id: 'r2',
        criteria: '失败时是否有可解释的降级路径',
        weight: 3,
        levels: [
          { score: 0, descriptor: '直接抛异常' },
          { score: 1, descriptor: '重试固定次数后抛异常' },
          { score: 2, descriptor: '重试时带上错误信息，仍失败则返回部分结果并标注' },
          { score: 3, descriptor: '明确区分格式失败与内容失败，分别有不同处理，且有测试覆盖' },
        ],
      },
      {
        id: 'r3',
        criteria: '是否测量并报告了成本',
        weight: 2,
        levels: [
          { score: 0, descriptor: '没有统计' },
          { score: 1, descriptor: '统计了调用次数' },
          { score: 2, descriptor: '统计了输入输出 token 数与总成本' },
          { score: 3, descriptor: '还能说出成本的主要来源，以及哪一步优化收益最大' },
        ],
      },
      {
        id: 'r4',
        criteria: '对"为什么仍然会失败"的理解',
        weight: 2,
        levels: [
          { score: 0, descriptor: '归因为"模型不行"' },
          { score: 1, descriptor: '能列举失败现象，但未区分原因层次' },
          { score: 2, descriptor: '能区分提示问题、任务设计问题与任务本身不适合' },
          {
            score: 3,
            descriptor: '能指出如果换一种任务设计（例如让代码而非模型提供事实），哪类失败会消失',
          },
        ],
      },
      {
        id: 'r5',
        criteria: 'Prompt 回归与逐字段评分',
        weight: 2,
        levels: [
          { score: 0, descriptor: '只凭个别输出声称提示变好' },
          { score: 1, descriptor: '有测试样本，但版本、分母或运行条件不一致' },
          { score: 2, descriptor: '冻结同一数据集与 schema，分别报告结构成功率、字段精确率和 exact-match' },
          { score: 3, descriptor: '逐样本定位回归与改进，失败仍计入分母；无在线证据时明确标记未验证' },
        ],
      },
    ],
    referenceImpl: {
      repo: 'examples/prompt-regression',
      command:
        'python3 examples/prompt-regression/compare.py --dataset examples/prompt-regression/dataset.json --before examples/prompt-regression/results-before.json --after examples/prompt-regression/results-after.json',
      notes:
        '示例运行数据为合成 fixture，用于验证同一数据集 hash、固定分母、逐字段精确率与回归定位。真实 prompt 改善需要在冻结任务集上重新调用目标模型，并另行保存模型/provider/参数与 usage 证据。',
    },
    tracks: [
      {
        lang: 'python',
        notes:
          '建议用 pydantic 做校验层，它对"期望类型 vs 实际类型"的报错信息写得最清楚，便于直接回传给孩子模型纠错。',
      },
      {
        lang: 'typescript',
        notes:
          '建议用 zod。注意 ZodError 直接序列化会比较啰嗦，最好自己映射成一句人类可读的描述再回传。',
      },
      {
        lang: 'go',
        notes:
          '标准库的 encoding/json 需要额外处理"字段类型不符"的情况，可以借此体会一下强类型语言在这层的摩擦。',
      },
    ],
    requires: ['llm-api-basics', 'prompt-engineering', 'context-engineering'],
    estimatedHours: [4, 8],
    difficulty: 'beginner',
  },
  'p2-grounded-support': {
    id: 'p2-grounded-support',
    stageId: 'stage-2-primitives',
    title: '有依据的售后政策答复',
    brief: '实现一个售后订单政策检索程序，只能根据找到的有效条款生成带出处的答复。',
    requirements: [
      '使用版本化的合成售后政策与订单 fixture，记录文档 id、版本、片段和有效时间。',
      '返回候选片段与可定位出处；把检索召回与最终回答正确性分开评估。',
      '政策没有覆盖问题时明确报告证据不足，不让模型补充未提供的政策。',
      '覆盖更新、删除和过期条款的测试，说明索引切换前后读者会看到什么。',
      '专题选修（多模态文档）：单独提交图像/PDF 路径实验记录；固定输入及版本，标明采用原生 PDF、页图或文本抽取路径，逐字段对照来源并记录误差和不确定项。该实验与文本检索交付分开；无真实模型运行证据时标为未验证。选择该专题时此项为必做；未选择时 `p2-4` 标记为不适用，不计入共同毕业判定。'
    ],
    constraints: [
      '基础路径必须可离线运行，使用词法基线与固定合成数据集。',
      '真实 embedding 作为独立的在线或本地模型实验；哈希向量仅用于验证管线控制流，不可报告成真实语义检索效果。',
      '不得先把无权访问的候选片段交给模型再过滤最终答案。',
    ],
    milestones: [
      { id: 'm1', title: '建立政策语料', detail: '定义稳定文档 id、版本、有效期和删除标记。' },
      {
        id: 'm2',
        title: '实现检索与引用',
        detail: '返回可定位片段，不把相似度分数伪装成答案置信度。',
      },
      { id: 'm3', title: '拆分评估', detail: '分别计算候选召回、引用支持度和答案正确性。' },
      { id: 'm4', title: '验证更新与拒答', detail: '用旧政策、撤回条款和无答案问题做负向测试。' },
      {
        id: 'm5',
        title: '提交多模态文档实验（专题选修）',
        detail:
          '使用 lab-vision-extract 或实际支持的 PDF 路径，固定输入版本并逐字段对照原始来源；未运行的路径标为未验证。',
      },
    ],
    rubric: rubric('p2', [
      [
        '引用可定位性',
        '没有出处',
        '只有文档标题',
        '能定位文档与片段',
        '还能定位版本并验证原文支持答案',
      ],
      [
        '证据不足处理',
        '无依据也作答',
        '偶尔标注不确定',
        '无证据时稳定 abstain',
        '负向测试覆盖边界与冲突条款',
      ],
      [
        '评估设计',
        '只看最终答案',
        '只有一个混合总分',
        '分开报告召回与回答',
        '评分规则、数据版本与已知限制均可复现',
      ],
      [
        '多模态路径实验',
        '没有固定输入或把视觉结果写成检索结果',
        '只描述模型输出，未对照原始来源或记录实际路径',
        '固定输入版本，记录 PDF/页图/文本路径并逐字段对照来源和错误',
        '区分转换与模型错误、保存原始输出和不确定项；未支持路径明确标为未验证，不外推真实模型能力',
      ],
    ]),
    referenceImpl: {
      repo: 'examples/p2-grounded-support',
      command:
        'PYTHONDONTWRITEBYTECODE=1 python3 examples/p2-grounded-support/grounded_support.py --evaluate',
      notes:
        '可离线运行的词法检索基线，返回带文档版本的原文证据并在无证据时 abstain；固定合成集分别报告候选召回和引用精确度。它不生成模型答案、不实现真实 embedding，也不证明语义检索质量。',
    },
    requires: ['retrieval', 'structured-output'],
    estimatedHours: [6, 10],
    difficulty: 'intermediate',
  },
  'p3-controlled-agent': {
    id: 'p3-controlled-agent',
    stageId: 'stage-3-orchestration',
    title: '受控的售后 Agent',
    brief: '交付一个真模型驱动的售后订单 CLI Agent，只能通过只读 MCP 工具查询合成订单和售后政策。',
    requirements: [
      '至少完成一次真实模型工具往返；离线 fixture 结果单独标为控制流验证。',
      '模型可选择查询订单或政策，但工具参数必须经本地 schema 校验后才能执行。',
      '记录每轮 stop reason、工具名、参数校验结果、usage 和任务终止状态。',
      '将 provider 传输失败、MCP 客户端/发现失败、工具业务错误、协议错误、拒绝、截断与预算终止分别记入轨迹；MCP 调用异常时标记执行结果未知，不自动重放。缺失或格式错误的 usage 必须保持 unknown。',
      '通过可配置的最大轮数与输出上限终止循环；工具错误不能被回填成成功数据。',
      '提交架构决策记录：说明哪些步骤使用 Agent、哪些保留为确定性 workflow；比较手写循环与已学框架的状态/失败处理/可观测边界，并给出不采用 Agent 的替代方案。结论引用本项目证据，不以 star 数替代评估。',
      '专题选修（多智能体）：完成受限的单 Agent / 多 Agent 对照。先用离线替身注入 worker 超时、无效结果和拒答，验证交接与失败处理；若报告真实模型质量差异，必须对同一冻结任务集配对运行同一模型版本和生成参数，并记录每个角色的输入输出、交接、调用数、usage、耗时、失败与评分规则。无在线证据时将质量比较标为未验证；离线结果只评价编排。不选择该专题时 `p3-5` 标记为不适用，不计入共同项目评价。'
    ],
    constraints: [
      '只接入只读 MCP server，不访问真实客户数据、文件系统或发送接口。',
      '必须区分协议错误、模型传输错误、工具业务错误和正常终止。',
      '工具客户端异常不等于工具业务拒绝；调用已发出但没有响应时，不得推断为“未执行”或自动重试。',
      '不实现审批恢复、分布式 worker 或生产任务 API；这些由阶段 4 项目负责。',
    ],
    milestones: [
      {
        id: 'm1',
        title: '验证 MCP 对接',
        detail: '运行 client/server 两个进程并检查 tools/list 与 tools/call。',
      },
      {
        id: 'm2',
        title: '接入模型循环',
        detail: '把 stop reason 映射到继续、工具执行、截断和结束分支。',
      },
      {
        id: 'm3',
        title: '加上预算与输入校验',
        detail: '工具 allowlist、参数 schema、最大轮数和输出 token 上限全部可观测。',
      },
      {
        id: 'm4',
        title: '分开离线与在线报告',
        detail: '离线测控制流；在线记录端点、模型、usage 与重复次数。',
      },
      {
        id: 'm5',
        title: '提交架构决策记录',
        detail: '用本项目轨迹和失败测试比较 Agent、确定性 workflow 与手写/框架实现，写明取舍和退出条件。',
      },
      {
        id: 'm6',
        title: '完成多智能体对照实验（专题选修）',
        detail: '先运行 examples/multi-agent-comparison/README.md 中的离线参考练习，再在 P3 任务上提交同一冻结集的对照；替身固定响应并注入 worker 失败，分别报告编排轨迹与模型质量边界。'
      },
    ],
    rubric: rubric('p3', [
      [
        '工具往返轨迹',
        '只有最终答案',
        '手工伪造一次调用',
        '轨迹可复查',
        '官方 MCP peer 互操作和真实模型调用分别有证据',
      ],
      [
        '停止与错误语义',
        '无限循环或吞错',
        '有最大轮数但状态混淆',
        '常见停止与错误分开',
        '还区分 provider 与 MCP 客户端异常、工具业务错误和未知执行结果；缺失 usage 保持 unknown，不自动重放',
      ],
      [
        '预算与安全',
        '无预算或可调用任意工具',
        '只限制一项资源',
        '工具只读且有输出/轮数限制',
        '还验证非法参数与未知工具不会产生副作用',
      ],
      [
        '架构决策记录',
        '没有选型理由，或把 Agent 当默认解',
        '只列框架名称、热度或个人偏好',
        '按任务不确定性、状态、失败路径和可观测性比较手写循环与框架',
        '还比较确定性 workflow/不用 Agent 的方案，引用项目轨迹与故障证据，写明取舍和退出条件',
      ],
      [
        '多智能体对照实验',
        '没有单 Agent 基线或无法复查结果',
        '分别运行两种方案但任务、模型或参数不一致，或只报最终答案',
        '同一任务集和固定模型/参数，记录角色交接、调用数、usage、耗时及失败',
        '再用离线替身注入超时/无效结果/拒答，分析收益与成本，并明确离线编排结果不能证明真实模型质量提升',
      ],
    ]),
    referenceImpl: {
      repo: 'examples/p3-controlled-agent',
      command:
        'uv sync --project examples/p3-controlled-agent && uv run --project examples/p3-controlled-agent python examples/p3-controlled-agent/cli.py --mcp-smoke',
      notes:
        '包含可复查的 MCP stdio 双进程协议检查、9 项离线控制流测试和受预算限制的 Anthropic Messages API 真模型循环。单 Agent / 多 Agent 配对实验参考 examples/multi-agent-comparison/README.md 与离线替身；仅证明编排轨迹和失败处理。在线报告单独保存在 gitignored 的 verify-output/stage3-mcp/live.json；端点可能只部分支持 Anthropic 工具协议，报告状态必须结合模型与端点阅读。'
    },
    requires: ['agent-loop', 'agent-paradigms', 'agent-frameworks', 'mcp', 'tool-calling'],
    estimatedHours: [8, 14],
    difficulty: 'intermediate',
  },
  'p4-durable-support': {
    id: 'p4-durable-support',
    stageId: 'stage-4-production',
    title: '可恢复的售后支持服务',
    brief: '把受控的售后订单 Agent 包进带身份授权、持久任务、审批和外部动作对账的服务。',
    requirements: [
      '提供任务 API、PostgreSQL 和独立 worker；重复提交幂等键返回同一任务。',
      '审批冻结参数 hash、资源版本、policy version、审批人和期限；服务重启后能恢复原动作。',
      '提供审批详情接口 GET /v1/approvals/{id}/review：仅当前被指定的 approver 可查看；返回来自可信工具登记表的动作名/允许展示参数、资源与策略版本、请求者、期限和参数 hash；预览与冻结快照不一致时拒绝展示。',
      '使用 outbox 向本地 HTTP 投递接收服务发消息；网络结果未知时进入 reconciling。',
      '实现租户隔离、权限过滤、事件续读和可撤销的任务查询。',
      '提供跨进程重启、并发审批、租约接管、撤权竞争和外部回执丢失的集成测试。',
      '运行离线控制流与真实 PostgreSQL 多进程集成门禁；把两类证据分开登记，真模型质量和独立交接留给阶段 5。',
      '通过租户预算账户在发送前原子预留 token/tool 上限，收到可信 usage 后核销；usage 未知时保留整笔预留并阻止超过账户额度。',
      '限制任务队列、worker 与 provider 并发；重试次数、Retry-After 和整体 deadline 都有上限。',
    ],
    constraints: [
      '禁止向真实客户发信、退款或修改真实订单；投递仅到项目自带的本地接收服务。',
      '离线 fixture 只能证明状态机与故障路径，不可标成在线模型能力验证。',
      '本地 SQLite 模型不替代本阶段 PostgreSQL 集成验收。',
    ],
    milestones: [
      {
        id: 'm1',
        title: '建立任务与身份边界',
        detail: '租户来自认证 principal，不采信请求体中的 tenant_id。',
      },
      {
        id: 'm2',
        title: '实现 worker 与审批恢复',
        detail: '任务领取受租约和 epoch 保护，审批恢复不重放整段模型历史。',
      },
      {
        id: 'm3',
        title: '实现 outbox 与本地接收端',
        detail: '稳定 external key、接收端持久去重和未知状态对账同时可观察。',
      },
      {
        id: 'm4',
        title: '运行多进程故障演练',
        detail: '杀 worker、重启服务并验证数据库轨迹和接收端真实副作用计数。',
      },
      {
        id: 'm5',
        title: '执行阶段 4 验收门禁',
        detail:
          '运行离线检查与 PostgreSQL 多进程集成套件，登记代码/锁文件 hash、fixture 版本、结果和限制；缺少 Docker 或数据库时必须失败。',
      },
    ],
    rubric: rubric('p4', [
      [
        '跨租户安全',
        '信任用户 tenant_id',
        '只检查部分接口',
        '查询与工具都按 principal 隔离',
        '越权检索、事件、审批和投递均有负向集成测试',
      ],
      [
        '任务恢复',
        '只靠进程内存',
        '重启后从头规划',
        '从检查点和冻结动作恢复',
        '租约过期后接管且旧 epoch 被拒绝',
      ],
      [
        '外部副作用',
        '网络请求成功就报完成',
        '有重试但无对账',
        'outbox、稳定幂等键和 unknown 状态齐全',
        '故障演练验证接收端副作用与对账证据',
      ],
      [
        '预算与容量约束',
        '无队列/并发上限或成本预算，耗尽后仍继续派发',
        '只有单个静态上限，并发预留可能超额',
        '限制队列与 provider 并发；发送前预留 token/tool 预算，超额拒绝，未知用量保留预留',
        '集成测试覆盖并发竞争、耗尽拒绝、未知用量和释放；报告区分 usage、预留与货币成本',
      ],
      [
        '审批信息可审阅性',
        '动作无授权或模型自行标记已批准',
        '只提供 approval id/status，审批者看不到将执行的动作',
        '指定审批者能查看可信 allowlist 构造的工具、参数、资源版本、请求者和期限摘要',
        '测试非指定身份/跨租户拒绝、参数或版本与 hash 不匹配时 fail closed，并验证拒绝/过期审批不会产生副作用',
      ],
    ]),
    hardGates: [
      '跨租户读取或检索必须全部被拒绝，且无越权资料进入模型上下文。',
      '未审批或参数 hash 已变化的动作不得投递。',
      '外部结果未知时不得谎报 completed，也不得无条件重复执行。',
      'PostgreSQL 集成证据必须来自本机真实数据库和独立进程；离线 fixture 与供应商行为分开报告。',
    ],
    referenceImpl: {
      repo: 'examples/p4-durable-support',
      command:
        "uv sync --frozen && uv run pytest -m 'not integration' -q && uv run pytest -m integration -q",
      notes:
        '提供 PostgreSQL 持久任务 API、lease/epoch worker、审批恢复与只向指定审批者提供的合成动作详情、ACL 前置过滤、有界队列与 provider 并发、token/tool 预算预留和核销、transactional outbox、本地合成 sink 与 unknown 对账。离线测试只证明 fixture/control-flow；集成命令需要 Docker，启动 PostgreSQL 与独立 API 进程，缺依赖会失败。审批详情端点只展示合成 send_notice 的 allowlist 参数，不含生产 UI、敏感字段脱敏策略或真实责任流程。预算账本不核对真实 provider 货币账单，也不证明目标环境的持续吞吐。尚未调用真实模型，因此不证明 provider 能力、答案质量或真实客户系统授权；真模型验收、独立交接、发布/回滚与 holdout 评测属于阶段 5。',
    },
    requires: ['agent-security', 'human-in-the-loop', 'agent-deployment', 'mcp', 'retrieval', 'cost-and-latency'],
    estimatedHours: [20, 35],
    difficulty: 'advanced',
  },
  'p5-agent-delivery': {
    id: 'p5-agent-delivery',
    stageId: 'stage-5-practice',
    title: '售后 Agent 可交付系统',
    brief: '交付可由他人从干净环境部署、评测、故障演练并接手的售后订单 Agent 项目。',
    requirements: [
      '从空环境按文档安装、迁移数据库、启动服务、连接一个已验证真模型端点并完成任务。',
      '冻结 dev/holdout 数据版本和评分器；报告质量、成本、延迟及未知 usage，不混成单一成功率。',
      '正式 blind holdout 必须绑定冻结候选、镜像、scorer 和单次授权记录；仓库公开 fixture 不能代替隐藏集。',
      '完成端点迁移契约评测、审批后重启、撤权竞态、重复提交和外部状态未知的故障演练。',
      '提交架构说明、威胁边界、已知限制、发布单、回滚方式和独立接手记录。',
      '对设计答辩：哪些步骤是固定 workflow、谁有授权、如何判断检索失败，以及为何未知动作不能直接重试。',
      '专题选修（Coding Agent 与源码研读）：在不含真实凭据和真实客户数据的隔离副本中完成限定任务；提交任务说明、权限边界、最终 diff、测试结果和人工复核记录；验证仓库中的不可信文本不能扩大任务范围；越界改动必须撤销后重新验收。选择该专题时此项为必做；未选择时 `p5-4` 标记为不适用，不计入共同毕业判定。',
      '专题选修（计算机使用安全）：按 `examples/computer-use-safety/TASK.md` 在本地合成发票页面完成范围受限的 GUI 任务；记录前后状态和动作顺序，忽略页面数据中的越权指令，只保存草稿并在独立审批边界停止。不得使用真实账号、凭据或客户数据。选择该专题时此项为必做；未选择时 `p5-5` 标记为不适用，不计入共同毕业判定。',
    ],
    constraints: [
      '评测集不得包含真实个人信息；最终 holdout 在规则和 prompt 冻结后只运行一次并记录版本。',
      '在线模型证据与 fixture 回归分开归档；无 Key 的构建仍应完整运行离线检查。',
      '本地 acceptance matrix 只核对结构与来源字段，不认证外部 registry、真实执行或 reviewer 身份；需单独保留人工签署。',
      '不允许用加权 rubric 分数抵消任何 hard gate 失败。',
    ],
    milestones: [
      {
        id: 'm1',
        title: '冻结发布候选',
        detail: '锁定代码、依赖、prompt、工具 schema、模型标识和评分器。',
      },
      {
        id: 'm2',
        title: '完成在线契约与质量评测',
        detail: '记录端点范围、请求参数、模型响应、usage 和统计限制。',
      },
      {
        id: 'm3',
        title: '执行恢复演练',
        detail: '由独立接手者按步骤完成重启、租约接管和未知动作核对。',
      },
      {
        id: 'm4',
        title: '完成交接答辩',
        detail: '以日志、测试和部署产物回答验收问题，而不只演示成功路径。',
      },
      {
        id: 'm5',
        title: '签署验收矩阵与发布决定',
        detail:
          '逐项核对 19 个 gate 的状态和证据；外部 holdout、独立 reviewer 或发布/回滚责任人缺失时保持未通过。',
      },
      {
        id: 'm6',
        title: '完成 Coding Agent 安全任务（专题选修）',
        detail:
          '在隔离副本中执行有范围约束的编码任务，审查 diff 与测试，并记录对仓库不可信文本的处理。',
      },
      {
        id: 'm7',
        title: '完成计算机使用安全任务（专题选修）',
        detail:
          '在本地合成页面中完成限定 GUI 操作，保存状态与动作记录，并在独立审批边界停止。',
      },
    ],
    rubric: rubric('p5', [
      [
        '干净环境交付',
        '无法启动',
        '作者机器可运行但步骤缺失',
        '按文档可部署并完成任务',
        '独立接手者无需作者私有文件即可复现',
      ],
      [
        '评测与迁移证据',
        '只报总分',
        '有质量分但无数据版本',
        '质量、成本、延迟分开且记录版本',
        '含端点迁移差异、区间和未验证边界',
      ],
      [
        '运营与响应',
        '没有恢复手册',
        '有告警但无演练',
        '完成审批恢复与未知动作演练',
        '发布、回滚、对账和负责人交接均有记录',
      ],
      [
        'Coding Agent 安全协作',
        '越出任务范围且未复核，或运行环境可访问真实凭据',
        '任务完成但没有权限边界、完整 diff 或测试证据',
        '在无真实凭据的隔离副本中完成限定任务，复核所有改动并运行相关测试',
        '还验证不可信仓库文本未扩大任务范围，提交工具/文件变更记录；越界时撤销并从干净副本重新验收',
      ],
      [
        '计算机使用安全',
        '操作错目标、服从页面中的越权指令，或越过审批边界提交',
        '任务完成但没有前后状态、动作顺序或停止条件证据',
        '只修改指定合成发票，记录动作并保存草稿后停止',
        '还证明范围外对象不变、页面数据未改变任务，提交尝试被拒绝且外部副作用为零',
      ],
    ]),
    referenceImpl: {
      repo: 'examples/coding-agent-safety',
      command: 'python3 examples/coding-agent-safety/verify.py',
      notes:
        '提供一个故意有缺陷的 priority starter、范围受限任务说明、含不可信指令的合成工单和参考实现。直接验收命令针对 starter 应先失败；verify.py 针对参考实现通过。它不自动验证 Coding Agent 的工具权限或 diff 范围，需按任务说明人工检查隔离设置、工具记录和完整 diff。计算机使用安全专题的本地 GUI 任务、隔离要求和启动方式见 examples/computer-use-safety/TASK.md。',
    },
    hardGates: [
      '任何跨租户访问、未授权写操作或未审批投递均为项目不通过。',
      '外部副作用未知时必须进入可查询的对账路径，不得宣称恰好一次。',
      '真模型在线验收缺凭据时标为 blocked/unverified，不得用 fixture 结果替代。',
      '正式 blind holdout 必须由外部 append-only registry 记录，并经独立 reviewer 核对候选、镜像、scorer 与单次授权；本地结构矩阵不能替代该签署。',
    ],
    requires: ['agent-deployment', 'evaluation', 'capstone', 'continuous-evolution'],
    estimatedHours: [30, 50],
    difficulty: 'expert',
  },
};
