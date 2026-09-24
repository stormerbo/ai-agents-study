import { describe, expect, it } from 'vitest';

import { CLAIM_BASES, curriculum, getChapters, getStages } from '@/content/curriculum';

/**
 * 内容完整性校验。
 *
 * 这些断言的作用是**守住内容质量的下限**：一个写错的 resourceId、一个
 * 指向不存在章节的前置依赖、一个成环的依赖图，如果不在这里被拦下，
 * 就会在某个页面上表现为莫名其妙的空白或死循环。
 *
 * 靠自律检查 19 章、上百个引用是不现实的 —— 交给机器。
 */

const chapters = getChapters();
const stages = getStages();

describe('章节结构', () => {
  it('章 id 唯一', () => {
    const ids = chapters.map((c) => c.id);
    expect(new Set(ids).size).toBe(ids.length);
  });

  it('章 order 唯一', () => {
    const orders = chapters.map((c) => c.order);
    expect(new Set(orders).size).toBe(orders.length);
  });

  it('每章的 stageId 都指向存在的阶段', () => {
    const stageIds = new Set(stages.map((s) => s.id));
    for (const chapter of chapters) {
      expect(stageIds.has(chapter.stageId), `章 ${chapter.id} 的 stageId 无效`).toBe(true);
    }
  });

  it('阶段 id 唯一', () => {
    const ids = stages.map((s) => s.id);
    expect(new Set(ids).size).toBe(ids.length);
  });

  it('每章至少有一节', () => {
    for (const chapter of chapters) {
      expect(chapter.lessons.length, `章 ${chapter.id} 没有节`).toBeGreaterThan(0);
    }
  });

  it('章都必须填写后端视角对照（本站的差异化主线）', () => {
    for (const chapter of chapters) {
      expect(chapter.backendMapping.analogy.length, `章 ${chapter.id} 缺 analogy`).toBeGreaterThan(
        0,
      );
      expect(
        chapter.backendMapping.pitfalls.length,
        `章 ${chapter.id} 的 pitfalls 不能为空 —— 这是最值钱的部分`,
      ).toBeGreaterThan(0);
    }
  });
});

describe('节', () => {
  it('节 id 格式为 `${chapterId}/${slug}`', () => {
    for (const chapter of chapters) {
      for (const lesson of chapter.lessons) {
        expect(lesson.id).toBe(`${chapter.id}/${lesson.slug}`);
        expect(lesson.chapterId).toBe(chapter.id);
      }
    }
  });

  it('节 id 全局唯一', () => {
    const ids = chapters.flatMap((c) => c.lessons.map((l) => l.id));
    expect(new Set(ids).size).toBe(ids.length);
  });

  it('章内 slug 唯一', () => {
    for (const chapter of chapters) {
      const slugs = chapter.lessons.map((l) => l.slug);
      expect(new Set(slugs).size, `章 ${chapter.id} 内有重复 slug`).toBe(slugs.length);
    }
  });

  it('已写正文的节，状态不能还是 planned', () => {
    for (const chapter of chapters) {
      for (const lesson of chapter.lessons) {
        if (lesson.hasBody) {
          expect(lesson.status, `节 ${lesson.id} 标了 hasBody 但状态是 planned`).not.toBe(
            'planned',
          );
        }
      }
    }
  });
});

describe('前置依赖', () => {
  it('前置章节都真实存在', () => {
    const ids = new Set(chapters.map((c) => c.id));
    for (const chapter of chapters) {
      for (const prereq of chapter.prerequisiteIds) {
        expect(ids.has(prereq), `章 ${chapter.id} 的前置 ${prereq} 不存在`).toBe(true);
      }
    }
  });

  it('不存在自引用', () => {
    for (const chapter of chapters) {
      expect(chapter.prerequisiteIds).not.toContain(chapter.id);
    }
  });

  it('依赖图无环', () => {
    const byId = new Map(chapters.map((c) => [c.id, c]));
    const state = new Map<string, 'visiting' | 'done'>();

    const visit = (id: string, path: string[]): void => {
      const mark = state.get(id);
      if (mark === 'done') return;
      if (mark === 'visiting') {
        throw new Error(`前置依赖成环: ${[...path, id].join(' → ')}`);
      }
      state.set(id, 'visiting');
      for (const prereq of byId.get(id)?.prerequisiteIds ?? []) {
        visit(prereq, [...path, id]);
      }
      state.set(id, 'done');
    };

    for (const chapter of chapters) visit(chapter.id, []);
  });

  it('前置章节的学习顺序早于当前章', () => {
    for (const chapter of chapters) {
      for (const prereqId of chapter.prerequisiteIds) {
        const prereq = chapters.find((c) => c.id === prereqId);
        expect(prereq!.order, `章 ${chapter.id} 的前置 ${prereqId} 排在了它后面`).toBeLessThan(
          chapter.order,
        );
      }
    }
  });
});

describe('引用完整性', () => {
  const resourceIds = new Set(Object.keys(curriculum.resources));
  const labIds = new Set(Object.keys(curriculum.labs));
  const projectIds = new Set(Object.keys(curriculum.projects));
  const chapterIds = new Set(chapters.map((c) => c.id));

  it('所有 resourceIds 都存在', () => {
    for (const chapter of chapters) {
      for (const id of chapter.resourceIds) {
        expect(resourceIds.has(id), `章 ${chapter.id} 引用了不存在的资源 ${id}`).toBe(true);
      }
      for (const lesson of chapter.lessons) {
        for (const id of lesson.resourceIds ?? []) {
          expect(resourceIds.has(id), `节 ${lesson.id} 引用了不存在的资源 ${id}`).toBe(true);
        }
        for (const cp of lesson.checkpoints ?? []) {
          for (const id of cp.resourceIds ?? []) {
            expect(resourceIds.has(id), `自检项 ${cp.id} 引用了不存在的资源 ${id}`).toBe(true);
          }
        }
      }
    }
  });

  it('所有 labIds 都存在，且 lab 反向指回正确的章', () => {
    for (const chapter of chapters) {
      for (const id of chapter.labIds ?? []) {
        expect(labIds.has(id), `章 ${chapter.id} 引用了不存在的实验 ${id}`).toBe(true);
        expect(curriculum.labs[id]!.chapterId).toBe(chapter.id);
      }
    }
  });

  it('每个实验的 chapterId 都指向存在的章', () => {
    for (const lab of Object.values(curriculum.labs)) {
      expect(chapterIds.has(lab.chapterId), `实验 ${lab.id} 的 chapterId 无效`).toBe(true);
    }
  });

  it('每个实验至少声明一个允许的模型，且默认模型在白名单内', () => {
    for (const lab of Object.values(curriculum.labs)) {
      expect(lab.allowedModels.length, `实验 ${lab.id} 没有允许的模型`).toBeGreaterThan(0);
      const match = lab.allowedModels.some(
        (m) => m.provider === lab.defaultModel.provider && m.model === lab.defaultModel.model,
      );
      expect(match, `实验 ${lab.id} 的默认模型不在白名单内`).toBe(true);
    }
  });

  it('每个实验都声明了"应该观察到什么"', () => {
    for (const lab of Object.values(curriculum.labs)) {
      expect(
        lab.objectives.length,
        `实验 ${lab.id} 没有 objectives —— 跑完不知道学到了什么就等于没做`,
      ).toBeGreaterThan(0);
    }
  });

  it('章引用的 projectIds 都存在', () => {
    for (const chapter of chapters) {
      for (const id of chapter.projectIds ?? []) {
        expect(projectIds.has(id), `章 ${chapter.id} 引用了不存在的作业 ${id}`).toBe(true);
      }
    }
  });

  it('作业的前置章节都存在', () => {
    for (const project of Object.values(curriculum.projects)) {
      for (const id of project.requires) {
        expect(chapterIds.has(id), `作业 ${project.id} 依赖了不存在的章 ${id}`).toBe(true);
      }
      expect(project.rubric.length, `作业 ${project.id} 没有评分清单`).toBeGreaterThan(0);
    }
  });

  it('自检项的 reviewLessonId 都存在', () => {
    const lessonIds = new Set(chapters.flatMap((c) => c.lessons.map((l) => l.id)));
    for (const chapter of chapters) {
      for (const lesson of chapter.lessons) {
        for (const cp of lesson.checkpoints ?? []) {
          if (cp.reviewLessonId) {
            expect(lessonIds.has(cp.reviewLessonId), `自检项 ${cp.id} 的回看目标不存在`).toBe(true);
          }
        }
      }
    }
  });
});

/**
 * 准确性机制。
 *
 * 这组断言不检查"内容对不对"——那需要人工核实，机器做不到。
 * 它检查的是**作者有没有对每条答案的来源保持诚实**：
 * 声称有文档依据的必须给出依据，声称核实不了的必须说明原因。
 * 这拦不住我写错，但能拦住我含糊其辞。
 */
describe('内容依据（准确性机制）', () => {
  const resourceIds = new Set(Object.keys(curriculum.resources));

  const allCheckpoints = () =>
    chapters.flatMap((c) =>
      c.lessons.flatMap((l) => (l.checkpoints ?? []).map((cp) => ({ chapter: c, lesson: l, cp }))),
    );

  it('每条自检项都声明了依据类型', () => {
    for (const { lesson, cp } of allCheckpoints()) {
      expect(CLAIM_BASES, `节 ${lesson.id} 的自检项 ${cp.id} 缺 basis`).toContain(cp.basis);
    }
  });

  it('标为 documented 的必须有来源', () => {
    for (const { lesson, cp } of allCheckpoints()) {
      if (cp.basis !== 'documented') continue;
      expect(
        cp.sourceIds?.length ?? 0,
        `自检项 ${lesson.id}#${cp.id} 声称有文档依据，却没有给出 sourceIds`,
      ).toBeGreaterThan(0);
    }
  });

  it('标为 unverified 的必须说明核实不了的原因', () => {
    for (const { lesson, cp } of allCheckpoints()) {
      if (cp.basis !== 'unverified') continue;
      expect(
        cp.note?.length ?? 0,
        `自检项 ${lesson.id}#${cp.id} 标为未核实，却没有说明原因 —— 「我核实不了」本身就是信息`,
      ).toBeGreaterThan(0);
    }
  });

  it('来源只能是资源库里的条目（不接受任意 URL）', () => {
    for (const { lesson, cp } of allCheckpoints()) {
      for (const id of cp.sourceIds ?? []) {
        expect(resourceIds.has(id), `自检项 ${lesson.id}#${cp.id} 的依据 ${id} 不在资源库中`).toBe(
          true,
        );
      }
    }
  });

  it('非 documented 的不应该塞来源（避免用来源伪装权威）', () => {
    for (const { lesson, cp } of allCheckpoints()) {
      if (cp.basis === 'documented') continue;
      expect(
        cp.sourceIds?.length ?? 0,
        `自检项 ${lesson.id}#${cp.id} 标为 ${cp.basis}，却带了 sourceIds`,
      ).toBe(0);
    }
  });
});

describe('资源质量', () => {
  it('每条资源都有 why —— 这是本站与链接堆砌的本质区别', () => {
    for (const resource of Object.values(curriculum.resources)) {
      expect(resource.why.length, `资源 ${resource.id} 缺 why`).toBeGreaterThan(10);
    }
  });

  it('资源 URL 都是 https', () => {
    for (const resource of Object.values(curriculum.resources)) {
      expect(resource.url, `资源 ${resource.id} 不是 https`).toMatch(/^https:\/\//);
    }
  });

  it('资源都有核实日期与核实方式', () => {
    for (const resource of Object.values(curriculum.resources)) {
      expect(resource.verifiedAt, `资源 ${resource.id} 缺 verifiedAt`).toMatch(
        /^\d{4}-\d{2}-\d{2}$/,
      );
      expect(['opened', 'search-only']).toContain(resource.verificationLevel);
    }
  });

  it('资源 id 与它的 key 一致', () => {
    for (const [key, resource] of Object.entries(curriculum.resources)) {
      expect(resource.id).toBe(key);
    }
  });

  it('没有硬编码 star 数', () => {
    for (const resource of Object.values(curriculum.resources)) {
      expect(
        resource.stars,
        `资源 ${resource.id} 硬编码了 star 数 —— 手工统计的 star 数出入极大，应由构建期拉取`,
      ).toBeUndefined();
    }
  });
});

describe('术语表', () => {
  it('术语 id 与 key 一致，且都有中英对照', () => {
    for (const [key, term] of Object.entries(curriculum.glossary)) {
      expect(term.id).toBe(key);
      expect(term.en.length).toBeGreaterThan(0);
      expect(term.zh.length).toBeGreaterThan(0);
      expect(term.definition.length).toBeGreaterThan(10);
    }
  });
});
