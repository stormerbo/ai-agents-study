import type { Project } from './schema';

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
};
