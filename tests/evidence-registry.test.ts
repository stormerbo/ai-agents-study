import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';

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
const experimentSchema = JSON.parse(readFileSync('experiments/schemas/experiment.schema.json', 'utf8'));
const resultSchema = JSON.parse(readFileSync('experiments/schemas/result.schema.json', 'utf8'));
const resultObservationFieldAllowlist = new Set([
  '1', '10', '2', '5', 'anthropic', 'anthropicSdk', 'argumentValidation', 'claimsForOneTask',
  'comparison', 'decisionForFixtureOnly', 'deliveriesAfterLostReceipt', 'fixtureVersion', 'incomplete',
  'inputTokens', 'integrity_check', 'interval', 'intervalWidthPp', 'mcpSdk',
  'model', 'mrtrRequestStateEchoAndTamperChecks', 'openai', 'outputTokens', 'passAt5Percent',
  'passPow5Percent', 'preSendRecoveryDeliveries', 'providerHost', 'providerRequests', 'refusal',
  'retryUsesFreshJsonRpcId', 'rounds', 'sameKeyTaskCount', 'singleSuccessRatePercent', 'status',
  'stopReasons', 'test_restore_required', 'testsFailed', 'testsPassed', 'tokensPerCharacter',
  'toolCalls', 'toolNames', 'toolResults', 'usage', 'widthPpToN',
  'apiProcesses', 'datasetVersion', 'failed', 'migrationVersions', 'passed', 'providerCalls',
  'readinessFailsWhenLatestMigrationIsMissing', 'testCount', 'taskStatus', 'crossProcessTaskRead',
  'crossProcessEventRead', 'fixtureOnly',
  'toolsCall', 'toolsList',
]);
const sensitiveValuePatterns = [
  /\bsk-(?:proj-|live-|ant-)?[A-Za-z0-9_-]{16,}\b/i,
  /\bBearer\s+[A-Za-z0-9._~+/-]{12,}/i,
  /\b(?:postgres(?:ql)?|mysql):\/\/[^\s]+/i,
  /-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----/i,
];

function assertSanitizedObservation(value: unknown, path: string, checkObservationKeys = true) {
  if (Array.isArray(value)) {
    value.forEach((item, index) => assertSanitizedObservation(item, `${path}[${index}]`, checkObservationKeys));
    return;
  }
  if (value && typeof value === 'object') {
    for (const [key, child] of Object.entries(value)) {
      if (checkObservationKeys) {
        expect(resultObservationFieldAllowlist.has(key), `${path}.${key} is not allowlisted`).toBe(true);
        expect(key, `${path}.${key} resembles a secret field`).not.toMatch(/api.?key|authorization|password|secret|dsn|private.?key|credential/i);
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
        expect(curriculum.chapters.some((chapter) => chapter.lessons.some((lesson) => lesson.id === lessonId))).toBe(true);
    for (const item of claims.claims)
      expect(curriculum.chapters.some((chapter) => chapter.lessons.some((lesson) => lesson.id === item.lessonId))).toBe(true);
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
      expect(Boolean(experiment.codeLocator && experiment.codeSha256) || Boolean(experiment.scriptPath && experiment.scriptSha256)).toBe(true);
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
      };
      expect(result.experimentId).toBe(experiment.id);
      expect(result.evidenceType).toBeDefined();
      expect(Object.keys(result.observations).length).toBeGreaterThan(0);
      expect(result.limitations.length).toBeGreaterThan(0);
    }
  });

  it('keeps result observations within the reviewed field allowlist and scans for secrets', () => {
    for (const experiment of experiments.experiments) {
      const result = JSON.parse(readFileSync(experiment.resultPath, 'utf8')) as { observations: unknown };
      assertSanitizedObservation(result.observations, `${experiment.id}.observations`);
      assertSanitizedObservation(result, experiment.id, false);
    }
  });

  it('keeps correction records aligned with the human-readable errata ledger', () => {
    const ledger = readFileSync('docs/ERRATA.md', 'utf8');
    for (const record of errata.records) expect(ledger).toContain(record.id);
    for (const record of errata.records)
      for (const lessonId of record.lessonIds)
        expect(curriculum.chapters.some((chapter) => chapter.lessons.some((lesson) => lesson.id === lessonId))).toBe(true);
  });
});
