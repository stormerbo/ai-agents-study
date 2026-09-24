import { chapters } from '@/content/chapters';

import { glossary } from './glossary';
import { labs } from './labs';
import { projects } from './projects';
import { resources } from './resources';
import type {
  Chapter,
  ChapterId,
  Curriculum,
  Lab,
  LabId,
  Lesson,
  LessonId,
  Project,
  ProjectId,
  Resource,
  ResourceId,
  Stage,
  StageId,
  Term,
  TermId,
} from './schema';
import { stages } from './stages';

export const curriculum: Curriculum = {
  version: '0.1.0',
  updatedAt: '2026-09-24',
  stages,
  chapters,
  resources,
  labs,
  projects,
  glossary,
};

// 导出 schema 的类型与常量（如 CLAIM_BASES），页面与测试都要用
export * from './schema';

// ---------------------------------------------------------------------------
// 派生索引
// 模块加载时算一次，全站复用 —— 这些数据在构建期就固定了，没有理由每次查询重算。
// ---------------------------------------------------------------------------

const chapterById = new Map<ChapterId, Chapter>(chapters.map((c) => [c.id, c]));
const stageById = new Map<StageId, Stage>(stages.map((s) => [s.id, s]));

/** 把全部章节的节按学习顺序展平。「上一节 / 下一节」是跨章连续的。 */
const lessonOrder: { lesson: Lesson; chapter: Chapter }[] = chapters.flatMap((chapter) =>
  chapter.lessons.map((lesson) => ({ lesson, chapter })),
);

const lessonIndexById = new Map<LessonId, number>(
  lessonOrder.map((entry, index) => [entry.lesson.id, index]),
);

// ---------------------------------------------------------------------------
// 查询
// ---------------------------------------------------------------------------

export function getStages(): Stage[] {
  return stages;
}

export function getStage(id: StageId): Stage | undefined {
  return stageById.get(id);
}

export function getChapters(): Chapter[] {
  return chapters;
}

export function getChapter(id: ChapterId): Chapter | undefined {
  return chapterById.get(id);
}

/** 阶段内的章节列表 —— 由 Chapter.stageId 派生，按章序号排序 */
export function getChaptersByStage(stageId: StageId): Chapter[] {
  return chapters.filter((c) => c.stageId === stageId);
}

export function getLesson(id: LessonId): { lesson: Lesson; chapter: Chapter } | undefined {
  const index = lessonIndexById.get(id);
  return index === undefined ? undefined : lessonOrder[index];
}

/**
 * 上一节 / 下一节，跨章连续。
 * 用展平后的全局序号计算，章边界处无需特殊处理。
 */
export function getAdjacentLessons(id: LessonId): {
  prev?: { lesson: Lesson; chapter: Chapter };
  next?: { lesson: Lesson; chapter: Chapter };
} {
  const index = lessonIndexById.get(id);
  if (index === undefined) return {};
  // noUncheckedIndexedAccess 已开启，这里的 undefined 由类型系统强制处理
  return {
    prev: index > 0 ? lessonOrder[index - 1] : undefined,
    next: index < lessonOrder.length - 1 ? lessonOrder[index + 1] : undefined,
  };
}

export function getResource(id: ResourceId): Resource | undefined {
  return resources[id];
}

/** 按 id 列表取资源，自动跳过不存在的 id（引用完整性由 check-content 保证） */
export function getResources(ids: readonly ResourceId[]): Resource[] {
  return ids.map((id) => resources[id]).filter((r): r is Resource => r !== undefined);
}

export function getLab(id: LabId): Lab | undefined {
  return labs[id];
}

export function getLabs(ids: readonly LabId[]): Lab[] {
  return ids.map((id) => labs[id]).filter((l): l is Lab => l !== undefined);
}

export function getProject(id: ProjectId): Project | undefined {
  return projects[id];
}

export function getProjectsByStage(stageId: StageId): Project[] {
  return Object.values(projects).filter((p) => p.stageId === stageId);
}

export function getGlossaryTerm(id: TermId): Term | undefined {
  return glossary[id];
}

// ---------------------------------------------------------------------------
// 派生统计与判定
// ---------------------------------------------------------------------------

export interface CurriculumStats {
  stageCount: number;
  chapterCount: number;
  lessonCount: number;
  resourceCount: number;
  labCount: number;
  projectCount: number;
  /** 已写正文的节数 / 计划中的节数 */
  lessonsWithBody: number;
}

export function getStats(): CurriculumStats {
  const lessons = lessonOrder.map((e) => e.lesson);
  return {
    stageCount: stages.length,
    chapterCount: chapters.length,
    lessonCount: lessons.length,
    resourceCount: Object.keys(resources).length,
    labCount: Object.keys(labs).length,
    projectCount: Object.keys(projects).length,
    lessonsWithBody: lessons.filter((l) => l.hasBody).length,
  };
}

/**
 * 前置依赖的建议，而非硬性封锁。
 *
 * 采用**软解锁**：返回"建议先读哪些章"，但从不阻止访问。
 * 目标读者是有经验的后端工程师 —— 硬锁会让人无法直接跳到真正需要的章节，
 * 那是居高临下的设计。UI 上表现为一条提示，而不是一道墙。
 */
export function getPrerequisiteAdvice(chapterId: ChapterId): ChapterId[] {
  const chapter = chapterById.get(chapterId);
  if (!chapter) return [];
  // 这里返回的是**直接**前置。若将来需要完整闭包，可在此做拓扑展开。
  return chapter.prerequisiteIds.filter((id) => chapterById.has(id));
}

/** 尚未完成的章节（用于"内容建设中"的提示与首页的进度叙事） */
export function getUnwrittenChapters(): Chapter[] {
  return chapters.filter((c) => c.lessons.every((l) => !l.hasBody));
}
