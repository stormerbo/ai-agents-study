import { existsSync, readdirSync, readFileSync } from 'node:fs';
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

describe('W6 全节复核清单', () => {
  it('keeps the recorded pass list unique and covered by the review tracker', () => {
    const plan = readFileSync(
      new URL('../docs/superpowers/plans/2026-10-19-curriculum-reliability.md', import.meta.url),
      'utf8',
    );
    const passLine = plan
      .split('\n')
      .find((line) => line.startsWith('**Recorded W6 full-lesson scope passes'));
    expect(passLine).toBeDefined();
    const lessonIds = [...passLine!.matchAll(/\x60([^\x60]+\/[^\x60]+)\x60/g)].map(([, id]) => id);
    const uniqueIds = new Set(lessonIds);
    const tracker = readFileSync(
      new URL('../docs/CURRICULUM-REVIEW-TRACKER.md', import.meta.url),
      'utf8',
    );

    expect(lessonIds).toHaveLength(144);
    expect(uniqueIds.size).toBe(lessonIds.length);
    expect(passLine).toContain('144/144 unique lessons (100.00%)');
    expect(passLine).toContain('W6 whole-lesson scope review is complete');
    expect(uniqueIds.has('tooling/orchestration-stack')).toBe(true);
    expect(uniqueIds.has('retrieval/why-retrieval')).toBe(true);
    expect(uniqueIds.has('reading-source/compare')).toBe(true);
    expect(uniqueIds.has('reading-source/outputs')).toBe(true);
    expect(uniqueIds.has('reading-source/picking-projects')).toBe(true);
    expect(uniqueIds.has('reading-source/trace-one-task')).toBe(true);
    expect(uniqueIds.has('reading-source/why-and-how')).toBe(true);
    expect([...uniqueIds].every((id) => tracker.includes('| `' + id + '` |'))).toBe(true);
  });

  it('keeps W6 and per-lesson status summaries aligned with the current tracker', () => {
    const tracker = readFileSync(
      new URL('../docs/CURRICULUM-REVIEW-TRACKER.md', import.meta.url),
      'utf8',
    );
    const audit = readFileSync(
      new URL('../docs/CURRICULUM-ACCURACY-AUDIT-2026-10-20.md', import.meta.url),
      'utf8',
    );
    const statuses = (text: string) =>
      text
        .split('\n')
        .flatMap((line) => {
          const match = line.match(/^\| `([^`]+)` \| (corrected|reviewed-ok|in-review) \|/);
          return match ? [[match[1], match[2]] as const] : [];
        });
    const currentStatuses = statuses(tracker);
    const reportStatuses = statuses(audit);
    const counts = Object.fromEntries(
      ['corrected', 'reviewed-ok', 'in-review'].map((status) => [
        status,
        currentStatuses.filter(([, value]) => value === status).length,
      ]),
    );

    expect(currentStatuses).toHaveLength(144);
    expect(reportStatuses).toEqual(currentStatuses);
    expect(counts).toEqual({ corrected: 37, 'reviewed-ok': 0, 'in-review': 107 });
    expect(tracker.split('\n')[2]).toContain('144/144');
    expect(audit.split('\n')[2]).toContain('144/144');
  });

  it('makes model rights a documented deployment gate for local models', () => {
    const localModels = curriculum.chapters
      .flatMap((chapter) => chapter.lessons)
      .find((lesson) => lesson.id === 'tooling/local-models');

    expect(
      localModels?.checkpoints?.some(
        (checkpoint) =>
          checkpoint.id === 'model-rights' &&
          checkpoint.basis === 'documented' &&
          checkpoint.sourceIds?.includes('osi-open-source-ai-definition') &&
          checkpoint.sourceIds?.includes('huggingface-model-card-guides'),
      ),
    ).toBe(true);
  });

  it('keeps the retrieval latency comparison on equal top-k and repeat counts', () => {
    const retrieval = curriculum.chapters
      .flatMap((chapter) => chapter.lessons)
      .find((lesson) => lesson.id === 'tooling/retrieval-stack');
    const checkpoint = retrieval?.checkpoints?.find((item) => item.id === 'benchmark-top-k');
    const lesson = readFileSync(
      new URL('../src/content/chapters/tooling/01-retrieval-stack.mdx', import.meta.url),
      'utf8',
    );

    expect(checkpoint?.basis).toBe('documented');
    expect(checkpoint?.sourceIds).toContain('chroma-python-collection-query');
    expect(lesson).toContain('n_results=1');
    expect(lesson).toContain('chroma_query_time(Vs, ids_s, qs, n=11)');
    expect(lesson).toContain('NumPy 返回 top-1、Chroma 返回 top-5');
    expect(lesson).toContain('逐次测量没有归档');
  });

  it('qualifies retrieval cost and paraphrase recall claims', () => {
    const lesson = readFileSync(
      new URL('../src/content/chapters/retrieval/01-why-retrieval.mdx', import.meta.url),
      'utf8',
    );

    expect(lesson).toContain('不能把「多取一条」直接等同于固定增加一笔费用');
    expect(lesson).toContain('不能保证所有换说法的查询都能召回');
    expect(lesson).not.toContain('每多取一条，就是每轮多付一条的钱');
  });

  it('scopes MCP schema generation to the illustrated server implementation', () => {
    const compare = curriculum.chapters
      .flatMap((chapter) => chapter.lessons)
      .find((lesson) => lesson.id === 'reading-source/compare');
    const checkpoint = compare?.checkpoints?.find((item) => item.id === 'mcp-schema-generation-source');
    const lesson = readFileSync(
      new URL('../src/content/chapters/reading-source/04-compare.mdx', import.meta.url),
      'utf8',
    );

    expect(checkpoint?.basis).toBe('documented');
    expect(checkpoint?.sourceIds).toContain('mcp-python-sdk-tools');
    expect(lesson).toContain('不规定 server 必须手写 schema');
    expect(lesson).toContain('官方 Python SDK 的 `@mcp.tool()` 会从函数类型标注生成 schema');
    expect(lesson).not.toContain('B、C 里 schema 是另外维护的数据');
    const pythonFence = lesson.split('```python')[1]?.split('```')[0] ?? '';
    const longLines = pythonFence
      .split('\n')
      .flatMap((line, lineIndex) =>
        line.length > 88
          ? ['line ' + (lineIndex + 1) + ': ' + line.length]
          : [],
      );
    expect(Math.max(...pythonFence.split('\n').map((line) => line.length))).toBeLessThanOrEqual(80);
    expect(longLines).toEqual([]);
  });


  it('traces the model-visible LangChain schema through the pinned constructor path', () => {
    const lesson = readFileSync(
      new URL('../src/content/chapters/reading-source/03-trace-one-task.mdx', import.meta.url),
      'utf8',
    );
    const trace = curriculum.chapters
      .flatMap((chapter) => chapter.lessons)
      .find((item) => item.id === 'reading-source/trace-one-task');
    const checkpoint = trace?.checkpoints?.find(
      (item) => item.id === 'langchain-tool-call-schema-path',
    );

    expect(checkpoint?.basis).toBe('documented');
    expect(checkpoint?.sourceIds).toContain('langchain-core-063-tool-structured');
    expect(checkpoint?.sourceIds).toContain('pydantic-json-schema');
    expect(lesson).toContain('StructuredTool.from_function');
    expect(lesson).toContain('BaseTool.tool_call_schema（base.py:464）');
    expect(lesson).toContain('_get_filtered_args`（base.py:95）');
    expect(lesson).toContain('只有定义，没有被 `create_schema_from_function` 或 `tool_call_schema` 调用');
    expect(lesson).toContain('return t.tool_call_schema.model_json_schema()');
    expect(lesson).not.toContain('前四跳都只是透传');
    expect(lesson).not.toContain('上面三组对照');
  });

  it('grounds the source-reading lesson in the actual LangChain schema path', () => {
    const lesson = readFileSync(
      new URL('../src/content/chapters/reading-source/01-why-and-how.mdx', import.meta.url),
      'utf8',
    );
    const entry = curriculum.chapters
      .flatMap((chapter) => chapter.lessons)
      .find((item) => item.id === 'reading-source/why-and-how');
    const checkpoint = entry?.checkpoints?.find(
      (item) => item.id === 'langchain-docstring-schema-boundary',
    );

    expect(checkpoint?.basis).toBe('documented');
    expect(checkpoint?.sourceIds).toContain('langchain-core-063-tool-structured');
    expect(checkpoint?.sourceIds).toContain('pydantic-json-schema');
    expect(lesson).toContain('tool_call_schema.model_json_schema()');
    expect(lesson).toContain('它没有把参数说明解析成字段 description');
    expect(lesson).toContain('_get_filtered_args');
    expect(lesson).not.toContain('结果它连读都没读');
    expect(lesson).not.toContain('tool_.args_schema.model_json_schema()');
  });

  it('does not imply that a version-pinned script detects upstream changes automatically', () => {
    const lesson = readFileSync(
      new URL('../src/content/chapters/reading-source/05-outputs.mdx', import.meta.url),
      'utf8',
    );

    expect(lesson).toContain('在目标版本环境中更新依赖快照并重跑断言');
    expect(lesson).toContain('不能自动发现上游行为变化');
    expect(lesson).not.toContain('它会在新版本上重新跑，自动发现结论是否还成立');
    const pythonFence = lesson.split('```python')[1]?.split('```')[0] ?? '';
    const longestLine = Math.max(...pythonFence.split('\n').map((line) => line.length));
    expect(longestLine).toBeLessThanOrEqual(70);
  });


  it('separates LangChain schema construction from provider request dispatch', () => {
    const lesson = readFileSync(
      new URL('../src/content/chapters/reading-source/02-picking-projects.mdx', import.meta.url),
      'utf8',
    );
    const picking = curriculum.chapters
      .flatMap((chapter) => chapter.lessons)
      .find((item) => item.id === 'reading-source/picking-projects');
    const checkpoint = picking?.checkpoints?.find(
      (item) => item.id === 'langchain-provider-integration-boundary',
    );

    expect(checkpoint?.basis).toBe('documented');
    expect(checkpoint?.sourceIds).toContain('langchain-python-integrations');
    expect(lesson).toContain('工具 schema：应用代码 → langchain_core.tools → Pydantic schema');
    expect(lesson).toContain('模型请求：  Agent/应用 → provider integration → provider SDK → HTTP transport');
    expect(lesson).not.toContain('→ httpx / anthropic（真正发请求的）');
    expect(lesson).toContain('BASE_FILE=');
    expect(lesson).toContain('rg -n "_get_filtered_args" "$BASE_FILE"');
    const bashFence = lesson.split('```bash')[1]?.split('```')[0] ?? '';
    const longestBashLine = Math.max(...bashFence.split('\n').map((line) => line.length));
    expect(longestBashLine).toBeLessThanOrEqual(70);
  });

  it('keeps the local-model executable example within an 88-character line width', () => {
    const lesson = readFileSync(
      new URL('../src/content/chapters/tooling/03-local-models.mdx', import.meta.url),
      'utf8',
    );
    const fences = [...lesson.matchAll(/^\x60{3}[^\n]*\n([\s\S]*?)^\x60{3}/gm)].map(([, body]) => body ?? '');
    const longLines = fences.flatMap((fence, fenceIndex) =>
      fence.split('\n').flatMap((line, lineIndex) =>
        line.length > 88
          ? ['fence ' + (fenceIndex + 1) + ', line ' + (lineIndex + 1) + ': ' + line.length]
          : [],
      ),
    );

    expect(longLines).toEqual([]);
  });
});

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

  /**
   * 章状态必须与正文完成度一致。
   *
   * 这个字段驱动章节页上的「正文状态」徽章，但它**要手工维护** ——
   * 于是必然漂移：2026-10-08 发现四个已经写完的章，徽章还停在
   * 「撰写中」甚至「大纲完成」，读者会以为正文没写完。
   *
   * 用规则代替自律：有几节写完了正文，就对应哪个状态。
   */
  it('章状态与正文完成度一致', () => {
    for (const chapter of chapters) {
      const total = chapter.lessons.length;
      const written = chapter.lessons.filter((l) => l.hasBody).length;
      const expected = written === 0 ? 'outlined' : written === total ? 'published' : 'drafting';
      expect(
        chapter.status,
        `章 ${chapter.id}：${written}/${total} 节有正文，status 应为 '${expected}'，实际是 '${chapter.status}'`,
      ).toBe(expected);
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


describe('教程能力追踪矩阵', () => {
  const matrix = readFileSync(join(process.cwd(), 'docs/CURRICULUM-CAPABILITY-MATRIX.md'), 'utf8');

  it('映射的课程节与实验都在注册表中', () => {
    const lessonIds = new Set(chapters.flatMap((chapter) => chapter.lessons.map((lesson) => lesson.id)));
    const lessonRefs = Array.from(
      matrix.matchAll(/\[`([^`]+)`\]\(\.\.\/src\/content\/chapters\/[^)]+\)/g),
      (match) => match[1]!,
    );
    expect(lessonRefs.length).toBeGreaterThan(0);
    for (const id of lessonRefs) {
      expect(lessonIds.has(id as (typeof chapters)[number]['lessons'][number]['id']), `能力矩阵引用了不存在的课程节 ${id}`).toBe(true);
    }
    const coveredChapterIds = new Set(
      Array.from(matrix.matchAll(/\(\.\.\/src\/content\/chapters\/([^/]+)\/meta\.ts\)/g), (match) => match[1]!),
    );
    for (const chapter of chapters) {
      expect(coveredChapterIds.has(chapter.id), `能力矩阵没有覆盖章节 ${chapter.id}`).toBe(true);
    }

    const labIds = new Set(Object.keys(curriculum.labs));
    const labRefs = new Set(Array.from(matrix.matchAll(/`(lab-[a-z0-9-]+)`/g), (match) => match[1]!));
    expect(labRefs.size).toBeGreaterThan(0);
    for (const id of labRefs) {
      expect(labIds.has(id), `能力矩阵引用了不存在的实验 ${id}`).toBe(true);
    }
  });

  it('每个能力域引用的项目至少映射一个真实 rubric 条目', () => {
    const capabilityRows = matrix
      .split('\n')
      .filter((line) => /^\| [^|]+ \/ [0-3] \|/.test(line));
    expect(capabilityRows).toHaveLength(16);

    const projectIds = {
      1: 'p1-reliable-extraction',
      2: 'p2-grounded-support',
      3: 'p3-controlled-agent',
      4: 'p4-durable-support',
      5: 'p5-agent-delivery',
    } as const;
    for (const row of capabilityRows) {
      const projectCell = row.split('|')[4] ?? '';
      for (const [, number] of projectCell.matchAll(/\bP([1-5])\b/g)) {
        const project = curriculum.projects[projectIds[Number(number) as keyof typeof projectIds]];
        expect(project, `能力矩阵引用了不存在的 P${number}`).toBeDefined();
        expect(
          project!.rubric.some((item) => row.includes(`\`${item.id}\``)),
          `能力矩阵的 P${number} 没有映射真实 rubric ID：${row}`,
        ).toBe(true);
      }
    }
  });
});


describe('阶段 4 项目预算与容量验收', () => {
  it('把并发容量与 token/tool 预算核算纳入评分', () => {
    const project = curriculum.projects['p4-durable-support']!;
    expect(project.requires).toContain('cost-and-latency');
    expect(project.requirements.some((item) => item.includes('token') && item.includes('tool'))).toBe(true);
    expect(project.rubric.some((item) => item.criteria === '预算与容量约束')).toBe(true);
  });
});

describe('阶段 1 Prompt 回归验收', () => {
  it('要求冻结数据集并对提示变更做逐字段配对评分', () => {
    const project = curriculum.projects['p1-reliable-extraction']!;
    expect(project.requirements.some((item) =>
      item.includes('冻结') && item.includes('prompt') && item.includes('逐字段')),
    ).toBe(true);
    expect(project.rubric.some((item) => item.criteria === 'Prompt 回归与逐字段评分')).toBe(true);
  });
});

describe('阶段 2 多模态文档专题验收', () => {
  it('提供与文本检索项目分开的视觉/文档路径实验和评分', () => {
    const project = curriculum.projects['p2-grounded-support']!;
    expect(project.requirements.some((item) =>
      item.includes('专题选修') && item.includes('多模态') && item.includes('图像/PDF')),
    ).toBe(true);
    expect(project.rubric.some((item) => item.id === 'p2-4' && item.criteria === '多模态路径实验')).toBe(true);
  });
});


describe('阶段 3 项目架构选型验收', () => {
  it('要求读者提交有证据边界的架构决策记录', () => {
    const project = curriculum.projects['p3-controlled-agent']!;
    expect(project.requires).toContain('agent-paradigms');
    expect(project.requires).toContain('agent-frameworks');
    expect(project.requirements.some((item) => item.includes('架构决策记录'))).toBe(true);
    expect(project.milestones.some((item) => item.title === '提交架构决策记录')).toBe(true);
    expect(project.rubric.some((item) => item.criteria === '架构决策记录')).toBe(true);
  });
});

describe('阶段 3 失败轨迹验收', () => {
  it('要求分开记录 provider/MCP/工具失败和未知执行结果', () => {
    const project = curriculum.projects['p3-controlled-agent']!;
    expect(project.requirements.some((item) =>
      item.includes('MCP 客户端/发现失败') && item.includes('执行结果未知') && item.includes('不自动重放'),
    )).toBe(true);
    expect(project.constraints.some((item) =>
      item.includes('不等于工具业务拒绝') && item.includes('不得推断为“未执行”'),
    )).toBe(true);
    expect(project.rubric.some((item) =>
      item.criteria === '停止与错误语义' && item.levels[3]?.descriptor.includes('未知执行结果'),
    )).toBe(true);
  });
});

describe('阶段 3 多智能体对照验收', () => {
  it('要求在同一任务集上比较单 Agent 与多 Agent 并记录失败和成本', () => {
    const project = curriculum.projects['p3-controlled-agent']!;
    expect(project.requirements.some((item) => item.includes('单 Agent') && item.includes('多 Agent'))).toBe(true);
    expect(project.requirements.some((item) => item.includes('专题选修'))).toBe(true);
    expect(project.requirements.some((item) => item.includes('p3-5') && item.includes('不计入共同项目评价'))).toBe(true);
    expect(project.milestones.some((item) => item.title.includes('完成多智能体对照实验'))).toBe(true);
    expect(project.rubric.some((item) => item.criteria === '多智能体对照实验')).toBe(true);
  });
});


describe('阶段 4 审批可审阅性验收', () => {
  it('要求授权审批者查看绑定到冻结动作的安全摘要', () => {
    const project = curriculum.projects['p4-durable-support']!;
    expect(project.requirements.some((item) => item.includes('审批详情接口'))).toBe(true);
    expect(project.rubric.some((item) => item.criteria === '审批信息可审阅性')).toBe(true);
  });
});

describe('阶段 5 Coding Agent 安全协作验收', () => {
  it('要求在隔离环境完成有范围约束和差异复核的编码任务', () => {
    const project = curriculum.projects['p5-agent-delivery']!;
    expect(project.requirements.some((item) =>
      item.includes('Coding Agent') && item.includes('隔离') && item.includes('diff')),
    ).toBe(true);
    expect(project.requirements.some((item) => item.includes('Coding Agent') && item.includes('专题选修'))).toBe(true);
    expect(project.requirements.some((item) => item.includes('p5-4') && item.includes('不计入共同毕业判定'))).toBe(true);
    expect(project.milestones.some((item) => item.title.includes('完成 Coding Agent 安全任务'))).toBe(true);
    expect(project.rubric.some((item) => item.criteria === 'Coding Agent 安全协作')).toBe(true);
  });
});

describe('阶段 5 计算机使用安全专题验收', () => {
  it('把本地合成 GUI 任务作为可选专项，不扩张共同毕业门槛', () => {
    const project = curriculum.projects['p5-agent-delivery']!;
    expect(project.requirements.some((item) => item.includes('p5-5') && item.includes('不计入共同毕业判定'))).toBe(true);
    expect(project.requirements.some((item) => item.includes('examples/computer-use-safety/TASK.md'))).toBe(true);
    expect(project.milestones.some((item) => item.id === 'm7' && item.title.includes('计算机使用安全'))).toBe(true);
    expect(project.rubric.some((item) => item.id === 'p5-5' && item.criteria === '计算机使用安全')).toBe(true);
    expect(project.referenceImpl?.notes).toContain('examples/computer-use-safety/TASK.md');
    expect(project.hardGates).toHaveLength(4);
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

  it('Mermaid 图表里没有 Markdown 标记（图表不解析 markdown）', () => {
    // chart={`...`} 的内容由 mermaid 渲染，不是 markdown —— 写了 `**粗体**`
    // 会原样显示成星号，而上面那条「按反引号切段」的规则恰好把这段排除了。
    const root = join(process.cwd(), 'src/content/chapters');
    const files = readdirSync(root, { recursive: true })
      .map(String)
      .filter((f) => f.endsWith('.mdx'));

    const failures: string[] = [];
    for (const file of files) {
      const raw = readFileSync(join(root, file), 'utf8');
      for (const chart of raw.matchAll(/chart=\{`([\s\S]*?)`\}/g)) {
        for (const line of (chart[1] ?? '').split('\n')) {
          if (line.includes('**')) failures.push(`${file}: ${line.trim()}`);
        }
      }
    }
    expect(failures, `Mermaid 图表里出现了 Markdown 标记：\n${failures.join('\n')}`).toEqual([]);
  });
});

/**
 * Markdown 表格的列数一致性。
 *
 * 表格不是 CommonMark 的一部分，它来自 remark-gfm（见 next.config.ts）。GFM 要求
 * **分隔行的单元格数与表头行完全相等** —— 多一格、少一格都不报错，整张表会退化成
 * 一段普通文字，页面上显示成一串竖线，而构建、typecheck、lint 全绿
 * （AGENTS.md §4.1 的静默失效家族：构建通过、页面正常、只是内容错了）。
 *
 * 实测踩到过一处：表头 4 列、分隔行 5 列，页面渲染出
 * `| 路线 | 做法 | 全部命中 | 总 token | |---|---|---:|:--:|---:|`。
 * 这类错误肉眼极难发现 —— 源码里两种写法看起来都像表格。
 */
describe('Markdown 表格的列数一致性', () => {
  const cells = (line: string) =>
    line
      .trim()
      .replace(/^\|/, '')
      .replace(/\|$/, '')
      .split(/(?<!\\)\|/)
      .map((s) => s.trim());

  const isDelimiterRow = (line: string) => /^\|[\s:|-]*$/.test(line.trim()) && /-/.test(line);

  /** 返回坏表格的描述（文件内行号从 1 开始）。围栏代码块里的竖线不算表格。 */
  function brokenTables(md: string): string[] {
    const lines = md.split('\n');
    const problems: string[] = [];
    let inFence = false;
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i] ?? '';
      if (/^\s*(```|~~~)/.test(line)) {
        inFence = !inFence;
        continue;
      }
      if (inFence) continue;
      if (!line.trim().startsWith('|')) continue;
      const next = lines[i + 1] ?? '';
      if (!isDelimiterRow(next)) continue;
      const header = cells(line).length;
      const delimiter = cells(next).length;
      if (header !== delimiter) {
        problems.push(
          `第 ${i + 1} 行：表头 ${header} 列、分隔行 ${delimiter} 列 → ${line.trim().slice(0, 60)}`,
        );
      }
    }
    return problems;
  }

  it('检查器本身认得出坏表格（防止这条断言退化成空转）', () => {
    const good = '| 路线 | 做法 |\n|---|---:|\n| A | 1 |\n';
    const bad = '| 路线 | 做法 |\n|---|---:|---:|\n| A | 1 |\n';
    expect(brokenTables(good)).toEqual([]);
    expect(brokenTables(bad)).toHaveLength(1);
  });

  it('正文与译文的表格列数一致', () => {
    const roots = [
      join(process.cwd(), 'src/content/chapters'),
      join(process.cwd(), 'src/content/reading'),
    ];
    const files = roots.flatMap((root) =>
      readdirSync(root, { recursive: true })
        .map(String)
        .filter((f) => f.endsWith('.mdx') || f.endsWith('.md'))
        .map((f) => ({ root, file: f })),
    );
    expect(files.length).toBeGreaterThan(100);

    const failures: string[] = [];
    for (const { root, file } of files) {
      for (const p of brokenTables(readFileSync(join(root, file), 'utf8'))) {
        failures.push(`${file}: ${p}`);
      }
    }
    expect(failures, `表格分隔行列数与表头不一致（表格不会渲染）：\n${failures.join('\n')}`).toEqual(
      [],
    );
  });
});

/**
 * 正文登记的四方一致性。
 *
 * 一节正文要真正出现在页面上，需要**四处**同时写对：
 *   1. meta.ts 里 `hasBody: true`
 *   2. 该章 body.ts 里有 `'<slug>': () => import('./NN-<slug>.mdx')`
 *   3. 磁盘上有对应的 `.mdx` 文件
 *   4. `src/lib/content/body.ts` 的 REGISTRY 里注册了该章
 *
 * 漏掉任何一处都**不会报错**：`getLessonBody` 找不到时返回 undefined，
 * 页面静默退回「这一节的正文还在撰写中」占位 —— 构建通过、测试全绿、
 * 只有人去点开那一页才发现。这属于 §4.1 / §4.8 的静默失效家族，
 * 靠自律守不住，交给机器。
 */
describe('正文登记一致性', () => {
  const root = join(process.cwd(), 'src/content/chapters');
  const registrySrc = readFileSync(join(process.cwd(), 'src/lib/content/body.ts'), 'utf8');
  const registeredChapters = new Set(
    // 注意：引号是可选的 —— prettier 的 quoteProps 默认是 "as-needed"，
    // 会把 `'retrieval': x` 规范成 `retrieval: x`。
    // 这个正则若写死引号，一次 pnpm format 就会让本条测试误报「章 retrieval 没注册」。
    [...registrySrc.matchAll(/^\s*'?([a-z0-9-]+)'?:\s*\w+Bodies,/gm)].map((m) => m[1]!),
  );

  it('每章 body.ts 的 key 与 hasBody 的节完全一一对应', () => {
    for (const chapter of chapters) {
      const dir = join(root, chapter.id);
      const bodyPath = join(dir, 'body.ts');
      const hasBodySlugs = chapter.lessons.filter((l) => l.hasBody).map((l) => l.slug);
      const hasBodyFile = existsSync(bodyPath);

      expect(
        hasBodyFile,
        `章 ${chapter.id} 有 ${hasBodySlugs.length} 节标了 hasBody，却没有 body.ts`,
      ).toBe(hasBodySlugs.length > 0);

      const src = hasBodyFile ? readFileSync(bodyPath, 'utf8') : '';
      // key 允许带引号或不带引号 —— 两种写法在 JS 里等价，不能因为风格差异漏判
      const entries = [
        ...src.matchAll(/['"]?([a-z0-9-]+)['"]?:\s*\(\)\s*=>\s*import\('([^']+)'\)/g),
      ].map((m) => ({ key: m[1]!, target: m[2]! }));

      expect(
        entries.map((e) => e.key).sort(),
        `章 ${chapter.id} 的 body.ts key 与 hasBody 的节不一致`,
      ).toEqual([...hasBodySlugs].sort());

      for (const entry of entries) {
        expect(
          existsSync(join(dir, entry.target)),
          `章 ${chapter.id} 的 body.ts 引用了不存在的文件 ${entry.target}`,
        ).toBe(true);
      }

      const mdx = readdirSync(dir).filter((f) => f.endsWith('.mdx'));
      const bySlug = new Map<string, string[]>();
      for (const file of mdx) {
        const m = /^\d+-([a-z0-9-]+)\.mdx$/.exec(file);
        expect(m, `章 ${chapter.id} 的正文文件名不符合 <编号>-<slug>.mdx：${file}`).not.toBeNull();
        const slug = m![1]!;
        bySlug.set(slug, [...(bySlug.get(slug) ?? []), file]);
      }
      for (const [slug, files] of bySlug) {
        expect(files.length, `章 ${chapter.id} 的 ${slug} 有多个正文文件`).toBe(1);
        expect(
          chapter.lessons.some((l) => l.slug === slug),
          `章 ${chapter.id} 的正文文件 ${files[0]} 没有对应的节`,
        ).toBe(true);
      }
      for (const slug of hasBodySlugs) {
        expect(bySlug.has(slug), `节 ${chapter.id}/${slug} 标了 hasBody 但磁盘上没有 .mdx`).toBe(
          true,
        );
      }
    }
  });

  it('有正文的章必须在 src/lib/content/body.ts 的 REGISTRY 里注册', () => {
    for (const chapter of chapters) {
      const hasBody = chapter.lessons.some((l) => l.hasBody);
      expect(
        registeredChapters.has(chapter.id),
        hasBody
          ? `章 ${chapter.id} 有正文，却没在 REGISTRY 里注册 —— 页面会静默显示「撰写中」`
          : `章 ${chapter.id} 没有正文，却注册进了 REGISTRY`,
      ).toBe(hasBody);
    }
  });
});
