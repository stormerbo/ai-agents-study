import type {
  ContentStatus,
  Difficulty,
  MigrationCost,
  ResourceKind,
  ResourceLang,
  ResourcePriority,
  ResourceStatus,
} from '@/content/curriculum/schema';

/**
 * 枚举值到中文标签的映射，集中一处。
 *
 * 单独放在这里而不是散落在各组件里的原因：这些标签会在章节页、资源库页、
 * 知识地图等多个地方出现，一旦分散，很快就会出现"同一状态两种说法"的情况。
 * 用 Record<Enum, string> 声明还能享受类型系统的保护 —— 以后往 schema 里
 * 加一个枚举值，这里会立刻编译报错，而不是悄悄漏掉一个分支。
 */

export const DIFFICULTY_LABEL: Record<Difficulty, string> = {
  intro: '入门',
  beginner: '初级',
  intermediate: '中级',
  advanced: '进阶',
  expert: '专家',
};

export const RESOURCE_KIND_LABEL: Record<ResourceKind, string> = {
  doc: '官方文档',
  repo: '开源仓库',
  paper: '论文',
  book: '书籍',
  course: '课程',
  video: '视频',
  blog: '博客',
  spec: '规范',
  tool: '工具',
};

export const RESOURCE_LANG_LABEL: Record<ResourceLang, string> = {
  zh: '中文',
  en: '英文',
  multi: '多语言',
};

export const RESOURCE_PRIORITY_LABEL: Record<ResourcePriority, string> = {
  must: '必读',
  recommended: '推荐',
  optional: '选读',
};

export const RESOURCE_STATUS_LABEL: Record<ResourceStatus, string> = {
  active: '有效',
  archived: '已归档',
  deprecated: '已废弃',
};

export const CONTENT_STATUS_LABEL: Record<ContentStatus, string> = {
  planned: '计划中',
  outlined: '大纲完成',
  drafting: '撰写中',
  published: '已完成',
};

export const MIGRATION_COST_LABEL: Record<MigrationCost, string> = {
  low: '低',
  medium: '中',
  high: '高',
};

/** 把分钟数转成人类可读的时长 */
export function formatMinutes(minutes: number): string {
  if (minutes < 60) return `${minutes} 分钟`;
  const hours = Math.floor(minutes / 60);
  const rest = minutes % 60;
  return rest === 0 ? `${hours} 小时` : `${hours} 小时 ${rest} 分`;
}
