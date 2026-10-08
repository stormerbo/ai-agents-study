import { readdirSync, readFileSync } from 'node:fs';
import { join } from 'node:path';

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

/**
 * 所有**由 `<InlineMd>` 渲染**的纯文本字段。
 *
 * 这些字段不走 MDX 管线 —— 它们是 `meta.ts` 里的普通字符串，直接插进 JSX。
 * 一旦里面写了 Markdown 标记，渲染层不认识，星号就会原样显示出来。
 */
const INLINE_MD = /\*\*[^*]+\*\*|`[^`]+`/g;

type PlainField = { where: string; text: string };

function plainTextFields(): PlainField[] {
  const out: PlainField[] = [];
  for (const c of chapters) {
    out.push({ where: `章 ${c.id} 的 summary`, text: c.summary });
    out.push({ where: `章 ${c.id} 的类比`, text: c.backendMapping.analogy });
    for (const t of c.backendMapping.transferable)
      out.push({ where: `章 ${c.id} 的可迁移项`, text: t });
    for (const p of c.backendMapping.pitfalls)
      out.push({ where: `章 ${c.id} 的失效直觉`, text: p });
    for (const l of c.lessons) {
      if (l.summary) out.push({ where: `节 ${l.id} 的 summary`, text: l.summary });
      for (const cp of l.checkpoints ?? []) {
        out.push({ where: `自检项 ${cp.id} 的 question`, text: cp.question });
        out.push({ where: `自检项 ${cp.id} 的 answer`, text: cp.answer });
        if (cp.note) out.push({ where: `自检项 ${cp.id} 的 note`, text: cp.note });
      }
    }
  }
  for (const [id, r] of Object.entries(curriculum.resources)) {
    out.push({ where: `资源 ${id} 的 why`, text: r.why });
  }
  for (const [id, lab] of Object.entries(curriculum.labs)) {
    out.push({ where: `实验 ${id} 的 goal`, text: lab.goal });
    for (const o of lab.objectives) out.push({ where: `实验 ${id} 的目标项`, text: o });
  }
  return out;
}

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

/**
 * 纯文本字段的行内标记。
 *
 * `meta.ts` 里的这些字段不走 MDX 管线，由 `<InlineMd>` 渲染，只认识
 * `**粗体**` 与 `` `代码` ``。写坏的标记不会报错 —— 它会原样显示成星号，
 * 构建通过、页面正常、只有肉眼能看出来（AGENTS.md §4.1 的静默失效家族）。
 *
 * 这里做的是**渲染等价校验**：把 `InlineMd` 能消掉的部分全部消掉，剩下的
 * 必须没有残留标记。这能拦住漏写的闭合 `**`、以及把 `**` 写在 CJK 标点
 * 旁边的写法（MDX 里那类问题由 CommonMark 的闭合规则决定，这里是纯文本，
 * 规则不同，所以两边都要各自防）。
 */
describe('纯文本字段的行内标记', () => {
  it('每处 `**` 都有配对的闭合标记', () => {
    for (const { where, text } of plainTextFields()) {
      // 消掉 InlineMd 能正确渲染的部分，剩下的不应再有裸标记
      const leftover = text.replace(INLINE_MD, '');
      expect(leftover, `${where} 存在未配对的 ** 或反引号：${text}`).not.toMatch(/\*\*|`/);
    }
  });
});

/**
 * 粗体标记的**位置**是否合法。
 *
 * 这一条针对 MDX 正文 —— 那里走 CommonMark 的强调规则：一个 `**` 能不能
 * 起效，取决于它两侧紧邻的字符（"flanking" 规则）。`**` 紧贴 CJK 标点时，
 * 至少有一端不构成合法分隔符，结果是星号被当字面量显示。
 *
 * 实测踩到的两种写法（都已修正）：
 *   - `而**「独立」是关键词**`   开头 `**` 后紧跟 `「` → 开不了
 *   - `采用**子词（subword）**方案` 结尾 `**` 前紧贴 `）` → 合不上
 *
 * 校验方式是先按奇偶位置认出开/闭标记（正文里的粗体不嵌套，所以交替配对
 * 成立），再逐对套用 flanking 规则。代码块、行内代码、Mermaid 组件里的
 * `**` 不是强调，先剔除。
 */
describe('粗体标记的位置（CommonMark flanking）', () => {
  const PUNCT = /[，。：；、！？「」『』（）《》〈〉【】“”‘’—…·,.:;!?()<>[\]{}"']/;
  const isPunct = (c?: string) => !!c && PUNCT.test(c);
  const isWord = (c?: string) => !!c && !/\s/.test(c) && !isPunct(c);

  function emphasisProblems(text: string): string[] {
    const problems: string[] = [];
    const marks: number[] = [];
    for (let i = text.indexOf('**'); i !== -1; i = text.indexOf('**', i + 2)) marks.push(i);

    if (marks.length % 2 !== 0) {
      problems.push(`** 出现 ${marks.length} 次（奇数），有未闭合的标记`);
      return problems;
    }
    for (let k = 0; k + 1 < marks.length; k += 2) {
      const open = marks[k]!;
      const close = marks[k + 1]!;
      // 左闭合失效：`**` 后紧跟标点，而前面又是普通字符
      if (isPunct(text[open + 2]) && isWord(text[open - 1])) {
        problems.push(`开头 ** 后紧跟标点 → …${text.slice(open, open + 12)}…`);
      }
      // 右闭合失效：`**` 前紧贴标点，而后面又是普通字符
      if (isPunct(text[close - 1]) && isWord(text[close + 2])) {
        problems.push(`结尾 ** 前紧贴标点 → …${text.slice(Math.max(0, close - 10), close + 4)}…`);
      }
    }
    return problems;
  }

  it('MDX 正文里的粗体两端都构成合法分隔符', () => {
    const root = join(process.cwd(), 'src/content/chapters');
    const files = readdirSync(root, { recursive: true })
      .map(String)
      .filter((f) => f.endsWith('.mdx'));
    expect(files.length).toBeGreaterThan(10);

    const failures: string[] = [];
    for (const file of files) {
      const raw = readFileSync(join(root, file), 'utf8');
      // 只检查「代码之外」的正文：按反引号切段后取偶数段。
      // 围栏块与行内代码一起被排除，不必分别写正则（早先那样写会跨行误吞正文）。
      const prose = raw
        .replace(/^---[\s\S]*?---/, '') // frontmatter 不渲染
        .split('`')
        .filter((_, i) => i % 2 === 0)
        .join('');
      for (const p of emphasisProblems(prose)) failures.push(`${file}: ${p}`);
    }
    expect(failures, failures.join('\n')).toEqual([]);
  });
});
