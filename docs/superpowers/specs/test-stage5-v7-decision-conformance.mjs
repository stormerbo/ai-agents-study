import assert from 'node:assert/strict';
import test from 'node:test';
import {
  deriveAndVerifyV7Decision,
  deriveV7DecisionDimensions,
} from './stage5-v7-decision-conformance.mjs';

function decision(overrides = {}) {
  return deriveV7DecisionDimensions({
    evidenceIntegrity: 'valid',
    governanceAuthorization: 'approved',
    holdoutOutcome: 'passed',
    lifecycleState: 'terminal',
    governanceError: null,
    ...overrides,
  });
}

test('only valid, approved, passed, terminal evidence becomes ready for human acceptance', () => {
  assert.deepEqual(decision(), {
    evidence_integrity: 'valid',
    governance_authorization: 'approved',
    holdout_outcome: 'passed',
    acceptance_readiness: 'ready-for-human-acceptance',
  });
});

test('invalid evidence or state contradiction has priority over an independently passing holdout', () => {
  assert.equal(decision({ evidenceIntegrity: 'invalid' }).acceptance_readiness, 'invalid-report');
  assert.equal(decision({ lifecycleState: 'invalid' }).acceptance_readiness, 'invalid-report');
  assert.equal(decision({ holdoutOutcome: 'invalid' }).acceptance_readiness, 'invalid-report');
  assert.equal(
    decision({ lifecycleState: 'reserved', holdoutOutcome: 'passed' }).acceptance_readiness,
    'invalid-report',
  );
});

test('missing sources preserve unverified status even when governance already rejected', () => {
  const result = decision({
    evidenceIntegrity: 'unverified',
    governanceAuthorization: 'rejected',
    holdoutOutcome: 'unverified',
  });
  assert.equal(result.governance_authorization, 'rejected');
  assert.equal(result.acceptance_readiness, 'unverified');
});

test('valid holdout pass remains visible when governance identity is unavailable', () => {
  const result = decision({ governanceAuthorization: 'unverified' });
  assert.equal(result.holdout_outcome, 'passed');
  assert.equal(result.acceptance_readiness, 'unverified');
});

test('a conclusive holdout failure is not eligible, while unavailable holdout remains unverified', () => {
  assert.equal(decision({ holdoutOutcome: 'failed' }).acceptance_readiness, 'not-eligible');
  assert.equal(decision({ holdoutOutcome: 'unverified' }).acceptance_readiness, 'unverified');
});

test('signed governance rejection or revocation blocks a terminal verified run', () => {
  assert.equal(
    decision({ governanceAuthorization: 'rejected' }).acceptance_readiness,
    'not-eligible',
  );
  assert.equal(
    decision({ governanceAuthorization: 'revoked' }).acceptance_readiness,
    'not-eligible',
  );
});

test('rejection does not hide unresolved execution after revocation', () => {
  const result = decision({
    governanceAuthorization: 'revoked',
    lifecycleState: 'reserved',
    holdoutOutcome: 'unverified',
  });
  assert.equal(result.governance_authorization, 'revoked');
  assert.equal(result.acceptance_readiness, 'unverified');
});

test('known invalid governance signature is not mislabeled as a signed rejection', () => {
  const result = decision({
    governanceAuthorization: 'unverified',
    governanceError: 'invalid',
  });
  assert.equal(result.governance_authorization, 'unverified');
  assert.equal(result.acceptance_readiness, 'invalid-report');
});

test('no-start, authorized-only, and reserved-only runs cannot be acceptance-ready', () => {
  for (const lifecycleState of ['no-start', 'authorized', 'reserved']) {
    assert.equal(
      decision({ lifecycleState, holdoutOutcome: 'unverified' }).acceptance_readiness,
      'unverified',
    );
  }
});

test('binds the derived decision dimensions to a detached receipt after lifecycle verification', () => {
  const input = decisionPackageFixture();
  const result = deriveAndVerifyV7Decision(input);
  assert.equal(result.acceptance_readiness, 'ready-for-human-acceptance');
  assert.equal(result.lifecycle_state, 'terminal');
});

test('turns a contradictory verified lifecycle into invalid-report and verifies that receipt binding', () => {
  const input = decisionPackageFixture();
  input.events[4].payload.terminal_event_id = 'other-terminal';
  input.decisionReceipt.acceptance_readiness = 'invalid-report';
  const result = deriveAndVerifyV7Decision(input);
  assert.equal(result.acceptance_readiness, 'invalid-report');
  assert.equal(result.lifecycle_state, 'invalid');
  assert.equal(result.lifecycle_error, 'V7_REVIEW_TERMINAL_BINDING');
});

test('rejects a detached receipt whose dimension disagrees with the composed verifier result', () => {
  const input = decisionPackageFixture();
  input.decisionReceipt.holdout_outcome = 'unverified';
  assert.throws(() => deriveAndVerifyV7Decision(input), { code: 'V7_DECISION_BINDING' });
});

function decisionPackageFixture() {
  const digest = 'a'.repeat(64);
  const event = (event_id, event_type, sequence, payload = {}) => ({
    event_id,
    event_type,
    sequence,
    event_hash: String(sequence).padStart(64, '0'),
    payload,
  });
  const events = [
    event('approval', 'assurance-approved', 1, { attestation_id: 'att-01', decision: 'accepted' }),
    event('authorized', 'authorized', 2),
    event('reserved', 'reserved', 3),
    event('terminal', 'consumed', 4),
    event('review', 'handoff-reviewed', 5, {
      attestation_id: 'att-02',
      terminal_event_id: 'terminal',
      terminal_event_hash: '0000000000000000000000000000000000000000000000000000000000000004',
    }),
  ];
  const envelope = {
    authorization_event_id: 'authorized',
    reservation_event_id: 'reserved',
    terminal_event_id: 'terminal',
    status: 'passed',
    outcome: 'passed',
    governance: {
      approval_event_id: 'approval',
      review_event_id: 'review',
      revocation_event_ids: [],
      handoff_core: {
        terminal_event: {
          event_id: 'terminal',
          event_hash: '0000000000000000000000000000000000000000000000000000000000000004',
        },
      },
    },
  };
  const receiptBindings = {
    schema: 'stage5-acceptance-decision-v1',
    decision_id: 'decision-01',
    evidence_envelope_sha256: digest,
    report_sha256: 'b'.repeat(64),
    run_id: 'run-01',
    frozen_spec_sha256: 'c'.repeat(64),
    assurance_profile: 'single-authority-v1',
    trust_bundle_sha256: 'd'.repeat(64),
    key_status_sequence: 7,
    usage_trust_bundle_sha256: 'e'.repeat(64),
    usage_key_status_sequence: 8,
    usage_ledger_closed_sequence: 9,
    usage_ledger_closed_head_sha256: 'f'.repeat(64),
    identity_decisions_sha256: '1'.repeat(64),
    verifier_policy_id: 'policy-01',
    verifier_build_sha256: '2'.repeat(64),
    signature_profile: 'ed25519-jcs-stage5-decision-v1',
    verifier_key_id: 'verifier-01',
  };
  const dimensions = {
    evidence_integrity: 'valid',
    governance_authorization: 'approved',
    holdout_outcome: 'passed',
    acceptance_readiness: 'ready-for-human-acceptance',
  };
  return {
    events,
    envelope,
    evidenceIntegrity: 'valid',
    governanceAuthorization: 'approved',
    holdoutOutcome: 'passed',
    receiptBindings,
    freshnessExpiries: ['2026-10-23T10:04:00Z', '2026-10-23T10:05:00Z'],
    decisionReceipt: {
      ...receiptBindings,
      ...dimensions,
      verified_at_utc: '2026-10-23T10:00:00Z',
      valid_until_utc: '2026-10-23T10:04:00Z',
      signature: 'A'.repeat(86),
    },
  };
}

test('keeps missing approval evidence unverified instead of treating absence as contradiction', () => {
  const input = decisionPackageFixture();
  input.events = input.events.filter((event) => event.event_type !== 'assurance-approved');
  input.governanceAuthorization = 'unverified';
  input.holdoutOutcome = 'unverified';
  input.decisionReceipt.governance_authorization = 'unverified';
  input.decisionReceipt.holdout_outcome = 'unverified';
  input.decisionReceipt.acceptance_readiness = 'unverified';
  const result = deriveAndVerifyV7Decision(input);
  assert.equal(result.lifecycle_state, 'unverified');
  assert.equal(result.lifecycle_error, 'V7_APPROVAL_MISSING');
  assert.equal(result.acceptance_readiness, 'unverified');
});

test('maps unavailable early-failure evidence to an unverified terminal result', () => {
  const input = decisionPackageFixture();
  input.events[3].event_type = 'failed';
  input.envelope.status = 'failed';
  input.envelope.outcome = 'failed';
  input.earlyFailureEvidence = { source_verification: 'unverified' };
  input.evidenceIntegrity = 'valid';
  input.holdoutOutcome = 'failed';
  input.decisionReceipt.evidence_integrity = 'unverified';
  input.decisionReceipt.holdout_outcome = 'unverified';
  input.decisionReceipt.acceptance_readiness = 'unverified';
  const result = deriveAndVerifyV7Decision(input);
  assert.equal(result.lifecycle_state, 'terminal');
  assert.equal(result.lifecycle_error, 'V7_FAILED_EVIDENCE_UNVERIFIED');
  assert.equal(result.evidence_integrity, 'unverified');
  assert.equal(result.holdout_outcome, 'unverified');
  assert.equal(result.acceptance_readiness, 'unverified');
});

test('does not produce a decision receipt for malformed lifecycle input', () => {
  const input = decisionPackageFixture();
  input.events[0].sequence = '1';
  assert.throws(() => deriveAndVerifyV7Decision(input), { code: 'V7_EVENT_SHAPE' });
});
