import assert from 'node:assert/strict';
import test from 'node:test';
import { verifyV7DecisionReceiptClaims } from './stage5-v7-decision-receipt-conformance.mjs';

const digest = 'a'.repeat(64);
const bindings = {
  schema: 'stage5-acceptance-decision-v1',
  decision_id: 'decision-01',
  evidence_envelope_sha256: digest,
  report_sha256: 'b'.repeat(64),
  run_id: 'run-01',
  frozen_spec_sha256: 'c'.repeat(64),
  assurance_profile: 'single-authority-v1',
  evidence_integrity: 'valid',
  governance_authorization: 'approved',
  holdout_outcome: 'passed',
  acceptance_readiness: 'ready-for-human-acceptance',
  trust_bundle_sha256: 'd'.repeat(64),
  key_status_sequence: 7,
  usage_trust_bundle_sha256: 'e'.repeat(64),
  usage_key_status_sequence: 11,
  usage_ledger_closed_sequence: 33,
  usage_ledger_closed_head_sha256: 'f'.repeat(64),
  identity_decisions_sha256: '1'.repeat(64),
  verifier_policy_id: 'policy-01',
  verifier_build_sha256: '2'.repeat(64),
  signature_profile: 'ed25519-jcs-stage5-decision-v1',
  verifier_key_id: 'verifier-01',
};

function receipt(overrides = {}) {
  return {
    ...bindings,
    verified_at_utc: '2026-10-23T10:00:00Z',
    valid_until_utc: '2026-10-23T10:04:00Z',
    ...overrides,
  };
}

const expiries = ['2026-10-23T10:10:00Z', '2026-10-23T10:04:00Z', '2026-10-23T10:05:00Z'];

test('accepts an exact decision receipt binding with the earliest source expiry', () => {
  assert.deepEqual(verifyV7DecisionReceiptClaims(receipt(), bindings, expiries), { valid: true });
});

test('rejects any receipt dimension or evidence binding that differs from verifier output', () => {
  assert.throws(
    () =>
      verifyV7DecisionReceiptClaims(receipt({ holdout_outcome: 'unverified' }), bindings, expiries),
    { code: 'V7_DECISION_BINDING' },
  );
  assert.throws(
    () =>
      verifyV7DecisionReceiptClaims(
        receipt({ evidence_envelope_sha256: '9'.repeat(64) }),
        bindings,
        expiries,
      ),
    { code: 'V7_DECISION_BINDING' },
  );
});

test('rejects expiry later than the earliest verified trust-source expiry', () => {
  assert.throws(
    () =>
      verifyV7DecisionReceiptClaims(
        receipt({ valid_until_utc: '2026-10-23T10:05:00Z' }),
        bindings,
        expiries,
      ),
    { code: 'V7_DECISION_EXPIRY' },
  );
});

test('rejects a receipt that is already expired when verified', () => {
  assert.throws(
    () =>
      verifyV7DecisionReceiptClaims(
        receipt({
          verified_at_utc: '2026-10-23T10:04:00.000001Z',
          valid_until_utc: '2026-10-23T10:04:00Z',
        }),
        bindings,
        expiries,
      ),
    { code: 'V7_DECISION_EXPIRY' },
  );
});

test('uses microsecond ordering when selecting the freshness boundary', () => {
  const exact = receipt({ valid_until_utc: '2026-10-23T10:04:00.000002Z' });
  assert.deepEqual(
    verifyV7DecisionReceiptClaims(exact, bindings, [
      '2026-10-23T10:04:00.000003Z',
      '2026-10-23T10:04:00.000002Z',
    ]),
    { valid: true },
  );
});

test('rejects malformed and impossible UTC freshness timestamps', () => {
  for (const timestamp of [
    '2026-02-29T10:00:00Z',
    '2026-10-23T10:00:60Z',
    '2026-10-23T10:00:00+00:00',
  ]) {
    assert.throws(
      () =>
        verifyV7DecisionReceiptClaims(receipt({ valid_until_utc: timestamp }), bindings, expiries),
      { code: 'V7_DECISION_EXPIRY' },
    );
  }
});
