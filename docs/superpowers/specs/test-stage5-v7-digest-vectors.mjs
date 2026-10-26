import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import canonicalize from 'canonicalize';

const document = JSON.parse(
  await readFile(new URL('stage5-v7-digest-vectors-v1.json', import.meta.url), 'utf8'),
);

function digest(value) {
  return createHash('sha256').update(canonicalize(value), 'utf8').digest('hex');
}

function reportPreimage(envelope) {
  const report = structuredClone(envelope);
  report.schema = 'official-blind-holdout-evidence-envelope-v5';
  for (const field of [
    'gate_id',
    'kind',
    'status',
    'release_id',
    'blind',
    'registry',
    'report_sha256',
    'trust_bundle',
    'trust_bundle_root_signature',
    'trust_bundle_sha256',
    'governance',
  ]) {
    delete report[field];
  }
  return report;
}

test('v7 digest vectors are explicitly synthetic and record all four preimages', () => {
  assert.equal(document.schema, 'stage5-v7-digest-vectors-v1');
  assert.equal(document.test_only, true);
  assert.deepEqual(Object.keys(document.expected).sort(), [
    'evidence_envelope_sha256',
    'handoff_core_sha256',
    'handoff_evidence_sha256',
    'report_sha256',
  ]);
});

test('v7 report, handoff, and outer-envelope digest preimages match the shared vectors', () => {
  const { envelope } = document;
  const preimages = {
    report_sha256: reportPreimage(envelope),
    handoff_core_sha256: envelope.governance.handoff_core,
    handoff_evidence_sha256: envelope.governance,
    evidence_envelope_sha256: envelope,
  };
  for (const [name, preimage] of Object.entries(preimages)) {
    assert.equal(canonicalize(preimage), document.canonical_preimages[name]);
    assert.equal(digest(preimage), document.expected[name]);
  }
});

test('v7 digest boundaries isolate report, handoff core, governance evidence, and receipt chain', () => {
  const { envelope } = document;
  const baseline = {
    report: digest(reportPreimage(envelope)),
    core: digest(envelope.governance.handoff_core),
    evidence: digest(envelope.governance),
    outer: digest(envelope),
  };

  const receiptChanged = structuredClone(envelope);
  receiptChanged.registry.receipt_chain.push({ event_id: 'evt-next', signature: 'test-signature' });
  assert.equal(digest(reportPreimage(receiptChanged)), baseline.report);
  assert.equal(digest(receiptChanged.governance), baseline.evidence);
  assert.notEqual(digest(receiptChanged), baseline.outer);

  const identityDecisionChanged = structuredClone(envelope);
  identityDecisionChanged.governance.identity_decisions.push({
    event_id: 'evt-next',
    phase: 'preflight',
  });
  assert.equal(digest(reportPreimage(identityDecisionChanged)), baseline.report);
  assert.equal(digest(identityDecisionChanged.governance.handoff_core), baseline.core);
  assert.notEqual(digest(identityDecisionChanged.governance), baseline.evidence);
  assert.notEqual(digest(identityDecisionChanged), baseline.outer);

  const coreChanged = structuredClone(envelope);
  coreChanged.governance.handoff_core.incident_contact = 'updated';
  assert.equal(digest(reportPreimage(coreChanged)), baseline.report);
  assert.notEqual(digest(coreChanged.governance.handoff_core), baseline.core);
  assert.notEqual(digest(coreChanged.governance), baseline.evidence);
  assert.notEqual(digest(coreChanged), baseline.outer);

  const reportChanged = structuredClone(envelope);
  reportChanged.run_id = 'run-other';
  assert.notEqual(digest(reportPreimage(reportChanged)), baseline.report);
  assert.notEqual(digest(reportChanged), baseline.outer);
});
