import assert from 'node:assert/strict';
import test from 'node:test';
import { verifyV7Lifecycle } from './stage5-v7-lifecycle-conformance.mjs';

function event(event_id, event_type, sequence, payload = {}) {
  return { event_id, event_type, sequence, event_hash: `${sequence}`.padStart(64, '0'), payload };
}

function fixture() {
  const events = [
    event('approval', 'assurance-approved', 1, { attestation_id: 'att-1', decision: 'accepted' }),
    event('authorized', 'authorized', 2),
    event('reserved', 'reserved', 3),
    event('terminal', 'consumed', 4),
    event('review', 'handoff-reviewed', 5, {
      terminal_event_id: 'terminal',
      terminal_event_hash: '0000000000000000000000000000000000000000000000000000000000000004',
    }),
  ];
  return {
    events,
    envelope: {
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
    },
  };
}

test('accepts the ordered approval-authorize-reserve-terminal-review lifecycle', () => {
  assert.deepEqual(verifyV7Lifecycle(fixture()), {
    state: 'terminal',
    terminal_event_type: 'consumed',
    governance: 'approved',
  });
});

test('rejects duplicate authorization events as a contradictory lifecycle', () => {
  const input = fixture();
  input.events.splice(2, 0, event('authorized-2', 'authorized', 3));
  input.events.slice(3).forEach((item, index) => {
    item.sequence = index + 4;
  });
  assert.throws(() => verifyV7Lifecycle(input), { code: 'V7_DUPLICATE_AUTHORIZATION' });
});

test('classifies a valid pre-start approval revocation as a no-start run', () => {
  const input = fixture();
  input.events = [
    event('approval', 'assurance-approved', 1, { attestation_id: 'att-1', decision: 'accepted' }),
    event('revoked', 'governance-attestation-revoked', 2, {
      target_attestation_id: 'att-1',
    }),
  ];
  input.envelope.authorization_event_id = null;
  input.envelope.reservation_event_id = null;
  input.envelope.terminal_event_id = null;
  input.envelope.outcome = 'incomplete';
  input.envelope.status = 'incomplete';
  input.envelope.governance.revocation_event_ids = ['revoked'];
  assert.deepEqual(verifyV7Lifecycle(input), {
    state: 'no-start',
    terminal_event_type: null,
    governance: 'revoked',
  });
});

test('rejects authorization after an approval rejection or prior revocation', () => {
  const rejected = fixture();
  rejected.events[0].payload.decision = 'rejected';
  assert.throws(() => verifyV7Lifecycle(rejected), {
    code: 'V7_AUTHORIZED_AFTER_REJECTED_APPROVAL',
  });

  const revoked = fixture();
  revoked.events.splice(
    1,
    0,
    event('revoked', 'governance-attestation-revoked', 2, {
      target_attestation_id: 'att-1',
    }),
  );
  revoked.events.slice(2).forEach((item, index) => {
    item.sequence = index + 3;
  });
  revoked.envelope.governance.revocation_event_ids = ['revoked'];
  assert.throws(() => verifyV7Lifecycle(revoked), { code: 'V7_AUTHORIZED_AFTER_REVOKED_APPROVAL' });
});

test('preserves a reserved run without terminal evidence as incomplete', () => {
  const input = fixture();
  input.events = input.events.slice(0, 3);
  input.envelope.terminal_event_id = null;
  input.envelope.outcome = 'incomplete';
  input.envelope.status = 'incomplete';
  input.envelope.governance.review_attestation = null;
  input.envelope.governance.review_event_id = null;
  input.envelope.governance.handoff_core = null;
  input.envelope.governance.handoff_core_sha256 = null;
  input.envelope.governance.identity_decisions = [];
  assert.deepEqual(verifyV7Lifecycle(input), {
    state: 'reserved',
    terminal_event_type: null,
    governance: 'approved',
  });
});

test('rejects a review that names a different terminal event', () => {
  const input = fixture();
  input.events[4].payload.terminal_event_id = 'another-run-terminal';
  assert.throws(() => verifyV7Lifecycle(input), { code: 'V7_REVIEW_TERMINAL_BINDING' });
});

test('accepts consumed terminal for either complete scorer pass or fail', () => {
  const failedScore = fixture();
  failedScore.envelope.status = 'failed';
  failedScore.envelope.outcome = 'failed';
  assert.equal(verifyV7Lifecycle(failedScore).terminal_event_type, 'consumed');
});

test('maps aborted terminal only to an incomplete outcome', () => {
  const input = fixture();
  input.events[3].event_type = 'aborted';
  input.envelope.status = 'incomplete';
  input.envelope.outcome = 'aborted';
  assert.equal(verifyV7Lifecycle(input).terminal_event_type, 'aborted');
  input.envelope.outcome = 'passed';
  assert.throws(() => verifyV7Lifecycle(input), { code: 'V7_ABORTED_OUTCOME' });
});

function failedFixture({
  failureGate = 'budget_violation',
  actualUsd = '5.01',
  stoppedAtUtc = '2026-10-23T12:00:01Z',
  earlyFailurePolicy = 'fail-before-scoring',
  attemptSetComplete = false,
  scoringComplete = false,
  requiredMetricsKnown = true,
} = {}) {
  const input = fixture();
  input.events[3].event_type = 'failed';
  const runtimeAuditSha256 = '3'.repeat(64);
  const runtimeStopRecordSha256 = '4'.repeat(64);
  const usageLedgerSha256 = '5'.repeat(64);
  const usageLedgerClosedHeadSha256 = '6'.repeat(64);
  const reportSha256 = '7'.repeat(64);
  input.events[3].payload = {
    report_sha256: reportSha256,
    early_failure_gate: failureGate,
    runtime_audit_sha256: runtimeAuditSha256,
    runtime_stop_record_sha256: runtimeStopRecordSha256,
    usage_ledger_sha256: usageLedgerSha256,
    usage_ledger_closed_sequence: 12,
    usage_ledger_closed_head_sha256: usageLedgerClosedHeadSha256,
  };
  input.envelope.status = 'failed';
  input.envelope.outcome = 'failed';
  input.envelope.quality_decision = 'unverified';
  input.envelope.report_sha256 = reportSha256;
  input.envelope.deadline_utc = '2026-10-23T12:00:00Z';
  input.envelope.runtime_audit_sha256 = runtimeAuditSha256;
  input.envelope.usage_ledger_sha256 = usageLedgerSha256;
  input.envelope.cost_status = 'known';
  input.envelope.stop_conditions = ['budget', 'deadline'];
  input.envelope.budget = { authorized_max_usd: '5.00', actual_usd: actualUsd };
  input.envelope.frozen_spec = {
    max_budget_usd: '5.00',
    deadline_utc: '2026-10-23T12:00:00Z',
    early_failure_policy: {
      budget_violation: earlyFailurePolicy,
      deadline_violation: earlyFailurePolicy,
    },
  };
  input.earlyFailureEvidence = {
    source_verification: 'valid',
    runtime_audit_sha256: runtimeAuditSha256,
    failure_gate: failureGate,
    attempt_set_complete: attemptSetComplete,
    scoring_complete: scoringComplete,
    required_metrics_known: requiredMetricsKnown,
    runtime_stop: {
      verified: true,
      processes_terminated: true,
      record_sha256: runtimeStopRecordSha256,
      stopped_at_utc: stoppedAtUtc,
    },
    usage_ledger: {
      verified: true,
      closed: true,
      all_provider_calls_terminal: true,
      ledger_sha256: usageLedgerSha256,
      closed_sequence: 12,
      closed_head_sha256: usageLedgerClosedHeadSha256,
      actual_usd: actualUsd,
    },
  };
  return input;
}

test('rejects failed terminal without independently verified early-failure evidence', () => {
  const input = fixture();
  input.events[3].event_type = 'failed';
  input.envelope.status = 'failed';
  input.envelope.outcome = 'failed';
  input.envelope.quality_decision = 'unverified';
  assert.throws(() => verifyV7Lifecycle(input), { code: 'V7_FAILED_EVIDENCE_UNVERIFIED' });
});

test('accepts early budget failure only when authenticated cost exceeds its frozen bound', () => {
  assert.equal(verifyV7Lifecycle(failedFixture()).terminal_event_type, 'failed');
  assert.throws(() => verifyV7Lifecycle(failedFixture({ actualUsd: '5.00' })), {
    code: 'V7_FAILED_EVIDENCE_INVALID',
  });
});

test('accepts early deadline failure only when trusted stop time exceeds the frozen deadline', () => {
  const valid = failedFixture({ failureGate: 'deadline_violation', actualUsd: '4.00' });
  assert.equal(verifyV7Lifecycle(valid).terminal_event_type, 'failed');
  assert.throws(
    () =>
      verifyV7Lifecycle(
        failedFixture({
          failureGate: 'deadline_violation',
          actualUsd: '4.00',
          stoppedAtUtc: '2026-10-23T12:00:00Z',
        }),
      ),
    { code: 'V7_FAILED_EVIDENCE_INVALID' },
  );
});

test('rejects early failure when scoring is complete or any required metric is unknown', () => {
  assert.throws(() => verifyV7Lifecycle(failedFixture({ scoringComplete: true })), {
    code: 'V7_FAILED_EVIDENCE_INVALID',
  });
  assert.throws(() => verifyV7Lifecycle(failedFixture({ requiredMetricsKnown: false })), {
    code: 'V7_FAILED_EVIDENCE_INVALID',
  });
});

test('rejects early failure if frozen policy disables the claimed path or receipt bindings differ', () => {
  assert.throws(() => verifyV7Lifecycle(failedFixture({ earlyFailurePolicy: 'disabled' })), {
    code: 'V7_FAILED_EVIDENCE_INVALID',
  });
  const wrongReceipt = failedFixture();
  wrongReceipt.events[3].payload.usage_ledger_closed_head_sha256 = '9'.repeat(64);
  assert.throws(() => verifyV7Lifecycle(wrongReceipt), { code: 'V7_FAILED_EVIDENCE_INVALID' });
});
