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
      '写一个小工具，从非结构化的中文文本里抽取结构化数据；要求它在面对脏数据时不崩溃，并给出可解释的失败原因。',
    requirements: [
      '输入：一段任意长度的中文文本（招聘启事、会议纪要、商品描述均可）',
      '输出：一个结构化的 JSON 对象，字段由你自己定义，但要覆盖该文本类型的关键信息',
      '提供命令行或 HTTP 接口，能对同一段文本重复调用',
      '对每一份输出，附带一个自评的置信度或"哪些字段没把握"的说明',
      '准备至少 10 段测试文本，其中至少 3 段是刻意构造的边界情况（内容残缺、格式混乱、包含干扰信息）',
    ],
    constraints: [
      '不得使用任何 agent 框架（LangChain / LlamaIndex 等）',
      '不得使用厂商的 schema 强制模式或约束解码 —— 这一阶段要练的是提示设计加代码校验',
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
    ],
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
  'p4-durable-support': {
    id: 'p4-durable-support',
    stageId: 'stage-4-production',
    title: '可恢复的售后支持服务',
    brief: '把受控的售后订单 Agent 包进带身份授权、持久任务、审批和外部动作对账的服务。',
    requirements: [
      '提供任务 API、PostgreSQL 和独立 worker；重复提交幂等键返回同一任务。',
      '审批冻结参数 hash、资源版本、policy version、审批人和期限；服务重启后能恢复原动作。',
      '使用 outbox 向本地 HTTP 投递接收服务发消息；网络结果未知时进入 reconciling。',
      '实现租户隔离、权限过滤、事件续读和可撤销的任务查询。',
      '提供跨进程重启、并发审批、租约接管、撤权竞争和外部回执丢失的集成测试。',
      '运行离线控制流与真实 PostgreSQL 多进程集成门禁；把两类证据分开登记，真模型质量和独立交接留给阶段 5。',
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
        detail: '运行离线检查与 PostgreSQL 多进程集成套件，登记代码/锁文件 hash、fixture 版本、结果和限制；缺少 Docker 或数据库时必须失败。',
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
    ]),
    hardGates: [
      '跨租户读取或检索必须全部被拒绝，且无越权资料进入模型上下文。',
      '未审批或参数 hash 已变化的动作不得投递。',
      '外部结果未知时不得谎报 completed，也不得无条件重复执行。',
      'PostgreSQL 集成证据必须来自本机真实数据库和独立进程；离线 fixture 与供应商行为分开报告。',
    ],
    referenceImpl: {
      repo: 'examples/p4-durable-support',
      command: 'uv sync --frozen && uv run pytest -m \'not integration\' -q && uv run pytest -m integration -q',
      notes:
        '提供 PostgreSQL 持久任务 API、lease/epoch worker、审批恢复、ACL 前置过滤、共享限制、transactional outbox、本地合成 sink 与 unknown 对账。离线测试只证明 fixture/control-flow；集成命令需要 Docker，启动 PostgreSQL 与独立 API 进程，缺依赖会失败。尚未调用真实模型，因此不证明 provider 能力、答案质量或真实客户系统授权；真模型验收、独立交接、发布/回滚与 holdout 评测属于阶段 5。',
    },
    requires: ['agent-security', 'human-in-the-loop', 'agent-deployment', 'mcp', 'retrieval'],
    estimatedHours: [20, 35],
    difficulty: 'advanced',
  },
};
