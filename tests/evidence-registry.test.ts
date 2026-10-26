import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { isAbsolute, resolve, sep } from 'node:path';

import { describe, expect, it } from 'vitest';
import Ajv2020 from 'ajv/dist/2020.js';

import { curriculum } from '@/content/curriculum';

type Experiment = {
  id: string;
  lessonIds: string[];
  codeLocator?: { path: string; fence: number; role: string };
  codeSha256?: string;
  scriptPath?: string;
  scriptSha256?: string;
  resultPath: string;
  status: string;
  reviewedAt: string | null;
};
type Claim = {
  id: string;
  lessonId: string;
  sourcePath: string;
  text: string;
  textSha256: string;
  sourceIds: string[];
  experimentIds: string[];
  errataIds: string[];
  reviewStatus: string;
};

const experiments = JSON.parse(readFileSync('experiments/registry.json', 'utf8')) as {
  experiments: Experiment[];
};
const claims = JSON.parse(readFileSync('experiments/claims.json', 'utf8')) as { claims: Claim[] };
const errata = JSON.parse(readFileSync('experiments/errata.json', 'utf8')) as {
  records: { id: string; lessonIds: string[]; experimentIds: string[] }[];
};
const mdxFences = (path: string) =>
  [...readFileSync(path, 'utf8').matchAll(/^```[^\n]*\n([\s\S]*?)^```\s*$/gm)].map((m) => m[1]);
const sha256 = (value: string) => createHash('sha256').update(value).digest('hex');
const ajv = new Ajv2020({ allErrors: true, strict: false });
const claimSchema = JSON.parse(readFileSync('experiments/schemas/claim.schema.json', 'utf8'));
const experimentSchema = JSON.parse(
  readFileSync('experiments/schemas/experiment.schema.json', 'utf8'),
);
const resultSchema = JSON.parse(readFileSync('experiments/schemas/result.schema.json', 'utf8'));

function readBoundSource(path: string): string {
  const repoRoot = resolve(process.cwd());
  const absolutePath = resolve(repoRoot, path);
  expect(isAbsolute(path)).toBe(false);
  expect(absolutePath.startsWith(`${repoRoot}${sep}`)).toBe(true);
  return readFileSync(absolutePath, 'utf8');
}
const resultObservationFieldAllowlist = new Set([
  '1',
  '10',
  '2',
  '5',
  'anthropic',
  'anthropicSdk',
  'argumentValidation',
  'claimsForOneTask',
  'comparison',
  'coveragePercent',
  'duplicateJsonKeysRejected',
  'remainingLessons',
  'pythonMaxLineLength',
  'textFenceMaxLineLength',
  'decisionForFixtureOnly',
  'deliveriesAfterLostReceipt',
  'emptyRequiredSetDecision',
  'fixtureVersion',
  'fixtureSha256',
  'headingAttachedToFirstParagraph',
  'incomplete',
  'inputTokens',
  'integrity_check',
  'interval',
  'intervalWidthPp',
  'mcpSdk',
  'model',
  'mrtrRequestStateEchoAndTamperChecks',
  'openai',
  'outputTokens',
  'completeFixtureDecision',
  'passAt5Percent',
  'passPow5Percent',
  'preSendRecoveryDeliveries',
  'providerHost',
  'providerRequests',
  'postgresImage',
  'restoredAppState',
  'sinkOperationCount',
  'stdoutMatchesPublishedOutput',
  'refusal',
  'retryUsesFreshJsonRpcId',
  'rounds',
  'sameKeyTaskCount',
  'singleSuccessRatePercent',
  'singleDigitMutationsDetected',
  'status',
  'stopReasons',
  'test_restore_required',
  'testsFailed',
  'testsPassed',
  'sqliteTestsFailed',
  'sqliteTestsPassed',
  'tokensPerCharacter',
  'toolBatchDispatchesOnMalformedIds',
  'toolCalls',
  'toolNames',
  'toolResults',
  'usage',
  'widthPpToN',
  'apiProcesses',
  'datasetVersion',
  'failed',
  'migrationVersions',
  'oldReviewServerRequests',
  'passed',
  'providerCalls',
  'readinessFailsWhenLatestMigrationIsMissing',
  'testCount',
  'taskStatus',
  'crossProcessTaskRead',
  'crossProcessEventRead',
  'fixtureOnly',
  'checks',
  'checksPassed',
  'fraction',
  'percent',
  'remaining',
  'uniqueLessonIds',
  'uniqueW6Lessons',
  'totalLessons',
  'historicalBenchmarksRerun',
  'mcpClientExceptionsRecorded',
  'unknownToolCallNotReplayed',
  'implementationAssertionPropagates',
  'historicalFixture',
  'pythonDemoExecuted',
  'pydanticStrictRejectsStringInteger',
  'decisionHelperBranchesTested',
  'externalNetworkCalls',
  'officialSourcesReviewed',
  'localDemoOutput',
  'firstLoopExecuted',
  'chapterCount',
  'pythonFencesCompiled',
  'serverRequestsChecked',
  'deselected',
  'durationSeconds',
  'sinkReadinessFailsWhenLatestMigrationIsMissing',
  'toolsCall',
  'toolsList',
  'pythonFencesCompiled',
  'serverRequestsChecked',
  'discoverAndToolsListCacheHints',
  'mrtrInputRequiredAndRetry',
  'unsupportedVersionAndMissingMetadata',
  'subscriptionMessagesParsed',
  'subscriptionFilterAckAndIdCorrelation',
  'modernOnlyVersionAdvertisement',
  'langgraphVersion',
  'trace',
  'next',
  'step',
  'checkpointChannels',
  'checkpointValuesMatchFinalState',
  'weakScoreFalsePositiveFixtures',
  'planExecutorCopiesChecked',
  'structuredScorerCopiesChecked',
  'usageCounterCopiesChecked',
  'productionBuildPages',
  'pagefindIndexedPages',
  'pagefindWords',
  'visualViewportWidth',
  'articleWidth',
  'documentScrollWidth',
  'mermaidRendered',
  'browserConsoleErrors',
  'lightScreenshot',
  'darkScreenshot',
  'screenshotDimensions',
]);
const sensitiveValuePatterns = [
  /\bsk-(?:proj-|live-|ant-)?[A-Za-z0-9_-]{16,}\b/i,
  /\bBearer\s+[A-Za-z0-9._~+/-]{12,}/i,
  /\b(?:postgres(?:ql)?|mysql):\/\/[^\s]+/i,
  /-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----/i,
];

function assertSanitizedObservation(value: unknown, path: string, checkObservationKeys = true) {
  if (Array.isArray(value)) {
    value.forEach((item, index) =>
      assertSanitizedObservation(item, `${path}[${index}]`, checkObservationKeys),
    );
    return;
  }
  if (value && typeof value === 'object') {
    for (const [key, child] of Object.entries(value)) {
      if (checkObservationKeys) {
        expect(resultObservationFieldAllowlist.has(key), `${path}.${key} is not allowlisted`).toBe(
          true,
        );
        expect(key, `${path}.${key} resembles a secret field`).not.toMatch(
          /api.?key|authorization|password|secret|dsn|private.?key|credential/i,
        );
      }
      assertSanitizedObservation(child, `${path}.${key}`, checkObservationKeys);
    }
    return;
  }
  if (typeof value === 'string')
    for (const pattern of sensitiveValuePatterns)
      expect(value, `${path} contains a sensitive value`).not.toMatch(pattern);
}

describe('evidence registry', () => {
  it('validates claims, experiment records and result records against their JSON Schemas', () => {
    const validateClaim = ajv.compile(claimSchema);
    const validateExperiment = ajv.compile(experimentSchema);
    const validateResult = ajv.compile(resultSchema);
    for (const claim of claims.claims)
      expect(validateClaim(claim), JSON.stringify(validateClaim.errors)).toBe(true);
    for (const experiment of experiments.experiments) {
      expect(validateExperiment(experiment), JSON.stringify(validateExperiment.errors)).toBe(true);
      if (experiment.status === 'needs-review') expect(experiment.reviewedAt).toBeNull();
      else expect(experiment.reviewedAt).toMatch(/^\d{4}-\d{2}-\d{2}$/);
      const result = JSON.parse(readFileSync(experiment.resultPath, 'utf8'));
      expect(validateResult(result), JSON.stringify(validateResult.errors)).toBe(true);
    }
  });

  it('uses unique experiment and claim ids with valid lesson references', () => {
    const experimentIds = experiments.experiments.map((item) => item.id);
    const claimIds = claims.claims.map((item) => item.id);
    expect(new Set(experimentIds).size).toBe(experimentIds.length);
    expect(new Set(claimIds).size).toBe(claimIds.length);
    for (const item of experiments.experiments)
      for (const lessonId of item.lessonIds)
        expect(
          curriculum.chapters.some((chapter) =>
            chapter.lessons.some((lesson) => lesson.id === lessonId),
          ),
        ).toBe(true);
    for (const item of claims.claims)
      expect(
        curriculum.chapters.some((chapter) =>
          chapter.lessons.some((lesson) => lesson.id === item.lessonId),
        ),
      ).toBe(true);
  });

  it('keeps claim text hashes, source ids, experiment links and errata links current', () => {
    const experimentIds = new Set(experiments.experiments.map((item) => item.id));
    const errataIds = new Set(errata.records.map((item) => item.id));
    for (const claim of claims.claims) {
      const body = readFileSync(claim.sourcePath, 'utf8');
      expect(body).toContain(claim.text);
      expect(sha256(claim.text)).toBe(claim.textSha256);
      for (const sourceId of claim.sourceIds) expect(curriculum.resources[sourceId]).toBeDefined();
      for (const id of claim.experimentIds) expect(experimentIds.has(id)).toBe(true);
      for (const id of claim.errataIds) expect(errataIds.has(id)).toBe(true);
    }
  });

  it('pins registered code fences by SHA-256 and points to existing result records', () => {
    for (const experiment of experiments.experiments) {
      expect(
        Boolean(experiment.codeLocator && experiment.codeSha256) ||
          Boolean(experiment.scriptPath && experiment.scriptSha256),
      ).toBe(true);
      if (experiment.codeLocator && experiment.codeSha256) {
        const code = experiment.codeLocator.path.endsWith('.mdx')
          ? mdxFences(experiment.codeLocator.path)[experiment.codeLocator.fence]
          : readFileSync(experiment.codeLocator.path, 'utf8');
        expect(code, `${experiment.id} code locator exists`).toBeDefined();
        expect(sha256(code!)).toBe(experiment.codeSha256);
      }
      if (experiment.scriptPath && experiment.scriptSha256)
        expect(sha256(readFileSync(experiment.scriptPath, 'utf8'))).toBe(experiment.scriptSha256);
      const result = JSON.parse(readFileSync(experiment.resultPath, 'utf8')) as {
        experimentId: string;
        evidenceType: string;
        observations: object;
        limitations: string[];
        sourceBindings?: { path: string; sha256: string; role: string }[];
      };
      expect(result.experimentId).toBe(experiment.id);
      expect(result.evidenceType).toBeDefined();
      expect(Object.keys(result.observations).length).toBeGreaterThan(0);
      expect(result.limitations.length).toBeGreaterThan(0);
      for (const binding of result.sourceBindings ?? []) {
        expect(sha256(readBoundSource(binding.path))).toBe(binding.sha256);
      }
      if (experiment.scriptPath && experiment.scriptSha256 && result.sourceBindings) {
        expect(
          result.sourceBindings.find(({ path }) => path === experiment.scriptPath)?.sha256,
        ).toBe(experiment.scriptSha256);
      }
    }
  });

  it('binds new P3 failure-trace evidence to the tested implementation and test sources', () => {
    const experiment = experiments.experiments.find(
      (item) => item.id === 'exp-stage3-mcp-client-errors-20261023',
    );
    expect(experiment).toBeDefined();
    const result = JSON.parse(readFileSync(experiment!.resultPath, 'utf8')) as {
      sourceBindings?: { path: string; sha256: string; role: string }[];
    };
    const bindings = result.sourceBindings ?? [];
    expect(bindings).toHaveLength(5);
    expect(new Set(bindings.map(({ path }) => path))).toEqual(new Set([
      'examples/support_agent/runtime.py',
      'examples/support_agent/providers.py',
      'examples/support_agent/tool_gateway.py',
      'examples/p3-controlled-agent/controlled_agent.py',
      'examples/p3-controlled-agent/test_controlled_agent.py',
    ]));
    expect(bindings.some(({ role }) => role === 'implementation')).toBe(true);
    expect(bindings.some(({ role }) => role === 'test')).toBe(true);
    expect(bindings.find(({ path }) => path === experiment!.scriptPath)?.sha256).toBe(
      experiment!.scriptSha256,
    );
  });

  it('keeps result observations within the reviewed field allowlist and scans for secrets', () => {
    for (const experiment of experiments.experiments) {
      const result = JSON.parse(readFileSync(experiment.resultPath, 'utf8')) as {
        observations: unknown;
      };
      assertSanitizedObservation(result.observations, `${experiment.id}.observations`);
      assertSanitizedObservation(result, experiment.id, false);
    }
  });

  it('validates the independent handoff template and rejects invalid record shapes', () => {
    const template = JSON.parse(
      readFileSync('examples/p5-agent-delivery/HANDOFF-RECORD.template.json', 'utf8'),
    );
    const schema = JSON.parse(
      readFileSync('examples/p5-agent-delivery/HANDOFF-RECORD.schema.json', 'utf8'),
    );
    const validate = ajv.compile(schema);
    expect(validate(template), JSON.stringify(validate.errors)).toBe(true);

    const invalidState = JSON.parse(JSON.stringify(template));
    invalidState.holdout.registry_state = 'completed';
    expect(validate(invalidState)).toBe(false);

    const extraField = JSON.parse(JSON.stringify(template));
    extraField.unreviewed_field = true;
    expect(validate(extraField)).toBe(false);

    const numericBudget = JSON.parse(JSON.stringify(template));
    numericBudget.holdout.maximum_spend = 12.5;
    expect(validate(numericBudget)).toBe(false);

    const recordedSecret = JSON.parse(JSON.stringify(template));
    recordedSecret.operator.credential_value_recorded = true;
    expect(validate(recordedSecret)).toBe(false);
  });

  it('keeps correction records aligned with the human-readable errata ledger', () => {
    const ledger = readFileSync('docs/ERRATA.md', 'utf8');
    for (const record of errata.records) expect(ledger).toContain(record.id);
    for (const record of errata.records)
      for (const lessonId of record.lessonIds)
        expect(
          curriculum.chapters.some((chapter) =>
            chapter.lessons.some((lesson) => lesson.id === lessonId),
          ),
        ).toBe(true);
  });
});

describe('computer-use/what-differs evidence boundaries', () => {
  const lesson = readFileSync('src/content/chapters/computer-use/01-what-differs.mdx', 'utf8');

  it('limits claims to the screenshot-coordinate adapter and keeps the sample proposal-only', () => {
    expect(lesson).toContain('自建截图/坐标适配器');
    expect(lesson).toContain('browser-use');
    expect(lesson).toContain('可访问性树');
    expect(lesson).toContain('示例只请求动作提议');
    expect(lesson).toContain('不执行点击或输入');
    expect(lesson).not.toContain('这三个动作能表达任何界面操作');
    expect(lesson).not.toContain('三次运行三次成功');
  });
});

describe('context-engineering/kv-cache evidence boundaries', () => {
  const lesson = readFileSync('src/content/chapters/context-engineering/07-kv-cache.mdx', 'utf8');
  const resources = readFileSync('src/content/curriculum/resources.ts', 'utf8');

  it('distinguishes DeepSeek current context caching from its Responses API parameter support and historical observations', () => {
    expect(resources).toContain("'deepseek-context-caching'");
    expect(lesson).toContain('固定 token 间隔');
    expect(lesson).toContain('尽力而为');
    expect(lesson).toContain('不支持');
    expect(lesson).toContain('不能据此反推 2026-10-08');
    expect(lesson).toContain('原始逐次响应未归档');
  });
});

describe('context-engineering/context-is-finite evidence boundaries', () => {
  const lesson = readFileSync('src/content/chapters/context-engineering/01-context-is-finite.mdx', 'utf8');
  const meta = readFileSync('src/content/chapters/context-engineering/meta.ts', 'utf8');
  const resources = readFileSync('src/content/curriculum/resources.ts', 'utf8');
  const data = readFileSync('docs/DATA.md', 'utf8');

  it('separates the chapter-zero baseline from current lesson reruns and labels historical summaries', () => {
    expect(lesson).toContain('第 0 章的机械标记');
    expect(lesson).toContain('本节未重测');
    expect(lesson).toContain('原始逐次请求/响应');
    expect(lesson).toContain('不能独立复核');
    expect(data).toContain('逐次请求/响应、精确模型版本、样本映射与评分器未归档');
  });

  it('requires a final exact answer match and does not count incomplete responses as correct', () => {
    expect(lesson).toContain('def score_answer');
    expect(lesson).toContain('re.fullmatch');
    expect(lesson).toContain('stop != "end_turn"');
    expect(lesson).not.toContain('if ANSWER in text');
    expect(lesson).toContain('不要在评分循环里自动重试');
  });

  it('cites primary sources for Lost in the Middle, context rot, stop reasons, and endpoint compatibility', () => {
    expect(resources).toContain("'chroma-context-rot'");
    expect(resources).toContain("'deepseek-anthropic-api'");
    expect(meta).toContain("'chroma-context-rot'");
    expect(meta).toContain("'anthropic-stop-reasons'");
    expect(meta).toContain("'deepseek-anthropic-api'");
  });
});

describe('context-engineering/just-in-time evidence boundaries', () => {
  const lesson = readFileSync('src/content/chapters/context-engineering/03-just-in-time.mdx', 'utf8');
  const meta = readFileSync('src/content/chapters/context-engineering/meta.ts', 'utf8');
  const data = readFileSync('docs/DATA.md', 'utf8');

  it('does not turn a sparse historical crossover into a universal selection threshold', () => {
    expect(lesson).toContain('不是可迁移阈值');
    expect(lesson).toContain('不验证两条路线是否给出同等正确答案');
    expect(lesson).toContain('token 总量不能直接当成账单');
    expect(data).toContain('20% 交叉点只是稀疏单次样本的插值');
  });

  it('fails closed on incomplete tool-loop responses and assigns access checks to the host', () => {
    expect(lesson).toContain('resp.stop_reason != "end_turn"');
    expect(lesson).toContain('按需路线达到工具轮次上限');
    expect(lesson).toContain('没有可处理的本地 read_doc 调用');
    expect(lesson).toContain('权限必须在目录生成和每次读取时由宿主校验');
  });

  it('documents provider-specific cache usage semantics', () => {
    expect(meta).toContain("sourceIds: ['deepseek-context-caching', 'claude-prompt-caching', 'anthropic-stop-reasons']");
    expect(meta).toContain('prompt_cache_hit_tokens');
    expect(meta).toContain('cache_read_input_tokens');
  });
});
