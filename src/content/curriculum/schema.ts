/**
 * 课程内容的数据模型 —— 全站唯一真源。
 *
 * 两条硬规则，破坏任何一条都会出问题：
 *
 * 1. 本文件是 **纯类型声明，零运行时依赖**，尤其绝不能 import MDX。
 *    章节树、知识地图、进度组件都是客户端组件，需要导入这里的类型；
 *    一旦本文件（或它所在模块图）引入了 MDX 的 import，整棵内容树的
 *     MDX 编译产物都会被拖进浏览器 bundle。正文的 lazy import 放在
 *    同目录的 body.ts 里，并由 `import 'server-only'` 兜底。
 *
 * 2. 所有 id 用稳定 slug，绝不用数组下标 —— 进度数据会持久化 id，
 *    插入一章就会让全部进度错位。
 */

// ---------------------------------------------------------------------------
// 标识符
// ---------------------------------------------------------------------------

export type StageId = string;
export type ChapterId = string;
/** 形如 `${ChapterId}/${slug}` */
export type LessonId = string;
export type ResourceId = string;
export type LabId = string;
export type ProjectId = string;
export type TermId = string;

// ---------------------------------------------------------------------------
// 枚举
// 一律用 `as const` 数组 + 派生联合类型：既能做类型，也能在运行时
// 渲染筛选器选项、遍历校验。
// ---------------------------------------------------------------------------

export const DIFFICULTIES = ['intro', 'beginner', 'intermediate', 'advanced', 'expert'] as const;
export type Difficulty = (typeof DIFFICULTIES)[number];

/**
 * 正文写作深度：
 * - deep   精写 —— 写到读者能照着写代码
 * - guided 导读 —— 15~20 分钟读完，深度靠延伸阅读
 */
export const DEPTHS = ['deep', 'guided'] as const;
export type Depth = (typeof DEPTHS)[number];

export const RESOURCE_KINDS = [
  'doc',
  'repo',
  'paper',
  'book',
  'course',
  'video',
  'blog',
  'spec',
  'tool',
] as const;
export type ResourceKind = (typeof RESOURCE_KINDS)[number];

export const RESOURCE_LANGS = ['zh', 'en', 'multi'] as const;
export type ResourceLang = (typeof RESOURCE_LANGS)[number];

/** 建议阅读顺序 —— 驱动资源库的默认排序与徽标 */
export const RESOURCE_PRIORITIES = ['must', 'recommended', 'optional'] as const;
export type ResourcePriority = (typeof RESOURCE_PRIORITIES)[number];

/**
 * 资源的存活状态。AI 领域的外链腐化极快（仓库归档、模型下线、
 * 课程过期），显式标出来是这类站点的生命线。
 */
export const RESOURCE_STATUSES = ['active', 'archived', 'deprecated'] as const;
export type ResourceStatus = (typeof RESOURCE_STATUSES)[number];

/** 核实到什么程度 —— 比一个笼统的日期更诚实 */
export const VERIFICATION_LEVELS = ['opened', 'search-only'] as const;
export type VerificationLevel = (typeof VERIFICATION_LEVELS)[number];

export const CONTENT_STATUSES = ['planned', 'outlined', 'drafting', 'published'] as const;
export type ContentStatus = (typeof CONTENT_STATUSES)[number];

/** 后端经验的迁移成本，用于章节卡片上的提示 */
export const MIGRATION_COSTS = ['low', 'medium', 'high'] as const;
export type MigrationCost = (typeof MIGRATION_COSTS)[number];

// ---------------------------------------------------------------------------
// 资源
// ---------------------------------------------------------------------------

export interface Resource {
  id: ResourceId;
  title: string;
  url: string;
  kind: ResourceKind;
  lang: ResourceLang;
  difficulty: Difficulty;
  /**
   * 为什么值得读、该读哪一部分 —— **必填**。
   * 这是本站与「awesome-list 式链接堆砌」的本质区别：读者需要的是
   * 判断依据，不是链接数量。
   */
  why: string;
  priority: ResourcePriority;
  author?: string;
  publisher?: string;
  year?: number;
  /** 预计阅读时长（分钟）。参考书类可缺省，表示按需查阅。 */
  estimatedMinutes?: number;
  access?: 'free' | 'freemium' | 'paid';
  status: ResourceStatus;
  /** 最近一次人工核实链接可用的日期（ISO 8601 date，如 2026-09-24） */
  verifiedAt: string;
  verificationLevel: VerificationLevel;
  /** GitHub star 数。只在构建期拉取缓存，绝不硬编码（手工统计冲突极大）。 */
  stars?: number;
  /** 已知镜像或备用链接 */
  mirrors?: string[];
  tags?: string[];
}

// ---------------------------------------------------------------------------
// 自检项
// ---------------------------------------------------------------------------

/**
 * 章末/节末的自检项，也是进度的第二档粒度。
 * 带参考答案 —— 比「学会了 / 没学会」式的自评有效得多。
 */
/**
 * 一条内容的**依据类型** —— 本站准确性机制的核心。
 *
 * 为什么要有这个字段：AI 领域的技术细节（API 字段名、流式事件格式、
 * 版本行为）变化极快，而错误的断言与正确的断言在语气上没有任何区别。
 * 读者无法分辨，作者（包括 AI）也会在长文里不自觉地把推断写成事实。
 *
 * 所以每一条自检答案都必须显式声明自己的依据，不允许有"没说清"的中间态：
 * - documented  已被官方文档或规范明确说明 —— **必须有 sourceIds**
 * - inferred    基于工程经验的判断，不是可查证的事实
 * - unverified  我无法核实，但认为值得保留 —— UI 上会显式警示
 */
export const CLAIM_BASES = ['documented', 'inferred', 'unverified'] as const;
export type ClaimBasis = (typeof CLAIM_BASES)[number];

export interface Checkpoint {
  /** 节内唯一。完整 key 为 `${LessonId}#${id}` */
  id: string;
  question: string;
  /** 参考答案要点，UI 上默认折叠 */
  answer: string;
  /** 这个答案的依据类型。必填 —— 强制作者对每条答案的来源有意识。 */
  basis: ClaimBasis;
  /**
   * basis 为 documented 时必填。
   *
   * 只能引用资源库里的条目，不接受任意 URL：这样每一条依据都必然
   * 经过了链接巡检与核实标注，不会出现"引用了某个记不清的链接"的情况。
   * 需要引用新来源时，先把它加进 resources.ts。
   */
  sourceIds?: ResourceId[];
  /**
   * 补充说明：依据的版本与时效，或 unverified 的具体原因。
   * 「我核实不了」这句话本身也是信息，不要沉默地略过。
   */
  note?: string;
  /** 没答出来时回哪一节复习 */
  reviewLessonId?: LessonId;
  /** 没答出来时看哪篇外部资料 */
  resourceIds?: ResourceId[];
}

// ---------------------------------------------------------------------------
// 模型与实验
// ---------------------------------------------------------------------------

export interface ModelRef {
  provider: ProviderId;
  model: string;
  label?: string;
}

/**
 * 已知厂商。同时允许任意字符串，用于 OpenAI 兼容端点，
 * 但服务端会对模型名做白名单二次校验。
 */
export const KNOWN_PROVIDERS = ['anthropic', 'openai', 'deepseek'] as const;
export type ProviderId = (typeof KNOWN_PROVIDERS)[number] | (string & {});

/** 消息内容块 —— 基于 block 而非纯字符串，因为它是 Anthropic 与 OpenAI 的最小公共上界 */
export type ContentBlock =
  | { type: 'text'; text: string }
  | { type: 'image'; mediaType: string; dataBase64: string }
  | { type: 'tool_use'; id: string; name: string; input: unknown }
  | { type: 'tool_result'; toolUseId: string; content: string; isError?: boolean }
  | { type: 'thinking'; text: string; signature?: string };

export interface AgentMessage {
  role: 'user' | 'assistant';
  content: ContentBlock[];
}

export interface ToolSpec {
  name: string;
  description: string;
  /** JSON Schema。适配层负责转成 Anthropic 的 input_schema / OpenAI 的 function.parameters */
  inputSchema: Record<string, unknown>;
}

export const LAB_CAPABILITIES = ['streaming', 'tools', 'multi-turn', 'vision', 'json'] as const;
export type LabCapability = (typeof LAB_CAPABILITIES)[number];

export interface LabPreset {
  label: string;
  hint?: string;
  messages: AgentMessage[];
}

export interface Lab {
  id: LabId;
  chapterId: ChapterId;
  lessonId?: LessonId;
  title: string;
  /** 这个实验要验证什么 */
  goal: string;
  /** inline = 内嵌在正文里；standalone = 另有 /labs/[id] 独立页（可分享链接） */
  surface: 'inline' | 'standalone';
  /** 服务端白名单的二次来源：客户端传来的 model 必须落在这里 */
  allowedModels: ModelRef[];
  defaultModel: ModelRef;
  system?: { content: string; locked: boolean };
  /** 预置任务卡片，消除「不知道输入什么」的空白焦虑 */
  presets?: LabPreset[];
  defaults?: { temperature?: number; maxTokens?: number };
  /** **教学关键**：明确写出「你应该观察到什么现象」，否则跑完也不知道学到了什么 */
  objectives: string[];
  /** 学习者一定会撞上的报错及排查方向 */
  troubleshooting?: { symptom: string; cause: string; fix: string }[];
  capabilities?: LabCapability[];
  /** 是否展示原始上游 SSE 事件（第 1 章强烈建议打开） */
  showRawEvents?: boolean;
  estimatedMinutes: number;
}

// ---------------------------------------------------------------------------
// 实战作业
// ---------------------------------------------------------------------------

export interface RubricItem {
  id: string;
  criteria: string;
  /** 权重，用于汇总自评分 */
  weight: number;
  /** 0~3 分的分档描述 */
  levels: { score: 0 | 1 | 2 | 3; descriptor: string }[];
}

export interface ProjectMilestone {
  id: string;
  title: string;
  detail: string;
}

/** 多语言实现指引 —— 直接对应 Java/Python/Go 背景的读者 */
export interface ProjectTrack {
  lang: 'typescript' | 'python' | 'java' | 'go';
  notes?: string;
  starterUrl?: string;
}

export interface Project {
  id: ProjectId;
  stageId: StageId;
  title: string;
  /** 一句话交付目标 */
  brief: string;
  /** 用户视角的验收场景 */
  requirements: string[];
  /** 硬性约束：语言、依赖、禁止使用的框架 */
  constraints: string[];
  milestones: ProjectMilestone[];
  rubric: RubricItem[];
  /** 必须全部满足、不能由其他 rubric 分数抵消的安全与状态不变量。 */
  hardGates?: string[];
  referenceImpl?: {
    repo?: string;
    command?: string;
    walkthroughLessonId?: LessonId;
    notes: string;
  };
  starter?: { url: string; notes?: string };
  tracks?: ProjectTrack[];
  requires: ChapterId[];
  /** [下限, 上限] 小时 */
  estimatedHours: [number, number];
  difficulty: Difficulty;
}

// ---------------------------------------------------------------------------
// 后端视角对照 —— 全站差异化主线，必填
// ---------------------------------------------------------------------------

/**
 * 目标读者是有经验的后端工程师。他们已有的并发、幂等、持久化、
 * 可观测性经验，大部分可以迁移；但有一小部分直觉在这里会**反过来咬人**。
 * 后者才是真正需要讲清楚的东西。
 */
export interface BackendMapping {
  /** 一句话类比：这相当于后端的什么 */
  analogy: string;
  /** 哪些已有的后端经验可以直接迁移过来 */
  transferable: string[];
  /** 哪些后端直觉在这里会失效 —— 最容易踩坑的地方 */
  pitfalls: string[];
  cost: MigrationCost;
}

// ---------------------------------------------------------------------------
// 节 / 章 / 阶段
// ---------------------------------------------------------------------------

export interface Lesson {
  id: LessonId;
  chapterId: ChapterId;
  /** URL 段、body.ts 的 key、MDX 文件名前缀，三者必须一致 */
  slug: string;
  title: string;
  summary?: string;
  estimatedMinutes: number;
  difficulty: Difficulty;
  /** body.ts 中是否存在对应的 MDX。false = 只有大纲，UI 应明确标注 */
  hasBody: boolean;
  status: ContentStatus;
  updatedAt?: string;
  keywords?: string[];
  checkpoints?: Checkpoint[];
  labIds?: LabId[];
  /** 节级资源（章级资源在 Chapter.resourceIds） */
  resourceIds?: ResourceId[];
}

export interface Chapter {
  id: ChapterId;
  stageId: StageId;
  /** 阶段内顺序 */
  order: number;
  title: string;
  subtitle?: string;
  summary: string;
  /** 学完能做到什么 —— 可验证的行为描述，比「了解 / 掌握」有用得多 */
  outcomes: string[];
  depth: Depth;
  difficulty: Difficulty;
  /** 正文 + 实验 + 作业的预计总时长（分钟） */
  estimatedMinutes: number;
  tags: string[];
  /** 前置章节。反向边（谁依赖我）由 selector 计算，不手写。 */
  prerequisiteIds: ChapterId[];
  lessons: Lesson[];
  resourceIds: ResourceId[];
  labIds?: LabId[];
  projectIds?: ProjectId[];
  backendMapping: BackendMapping;
  status: ContentStatus;
  updatedAt: string;
  /** 最近一次人工核实本章外链与事实的日期 */
  verifiedAt: string;
  /** 第一版重点章，首页与地图高亮 */
  flagship?: boolean;
}

export interface Stage {
  id: StageId;
  order: number;
  title: string;
  tagline: string;
  summary: string;
  /** 进入本阶段前应具备的知识 —— 帮读者自我定位 */
  assumedKnowledge: string[];
  /** 出阶段时可展示的作品 */
  capstone: string;
  /** 对应 globals.css 里 @theme 定义的 --color-stage-N */
  colorToken: string;
  /**
   * 注意这里**没有** chapterIds / projectIds。
   *
   * 阶段与章节的关系只在 Chapter.stageId 上表达一次，阶段内的章节列表
   * 由 `getChaptersByStage()` 派生。两处都存同一关系必然会不同步 ——
   * 加了新章却忘了往阶段里补 id，是这类结构最经典的 bug。
   */
}

// ---------------------------------------------------------------------------
// 术语表 —— 中文技术内容的质量分水岭
// ---------------------------------------------------------------------------

/**
 * 同一概念多种译法（agent / 智能体 / 代理）是中文技术内容最常见的败笔。
 * 正文里用 <Term id="..." /> 渲染，强制与术语表对齐。
 */
export interface Term {
  id: TermId;
  en: string;
  zh: string;
  definition: string;
  /** 曾经出现过但不推荐使用的译法 */
  discouraged?: string[];
  resourceIds?: ResourceId[];
}

// ---------------------------------------------------------------------------
// 根
// ---------------------------------------------------------------------------

export interface Curriculum {
  version: string;
  updatedAt: string;
  stages: Stage[];
  chapters: Chapter[];
  resources: Record<ResourceId, Resource>;
  labs: Record<LabId, Lab>;
  projects: Record<ProjectId, Project>;
  glossary: Record<TermId, Term>;
}
