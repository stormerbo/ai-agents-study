import assert from 'node:assert/strict';
import test from 'node:test';
import { verifyIdentityDecisionCoverage } from './stage5-governance-conformance.mjs';

const digest = 'a'.repeat(64);
const sourceId = 'identity-source-01';

function fixture({ includeRevocation = false } = {}) {
  const events = [
    {
      event_id: 'evt-approval',
      event_type: 'assurance-approved',
      sequence: 1,
      recorded_at_utc: '2026-10-23T10:00:01Z',
      payload: {
        identity_preflight_ref: 'identity:preflight:approval',
        identity_preflight_sha256: digest,
      },
    },
    {
      event_id: 'evt-authorized',
      event_type: 'authorized',
      sequence: 2,
      recorded_at_utc: '2026-10-23T10:00:02Z',
      payload: {},
    },
    {
      event_id: 'evt-reserved',
      event_type: 'reserved',
      sequence: 3,
      recorded_at_utc: '2026-10-23T10:00:03Z',
      payload: {},
    },
    {
      event_id: 'evt-terminal',
      event_type: 'consumed',
      sequence: 4,
      recorded_at_utc: '2026-10-23T10:00:04Z',
      payload: {},
    },
    {
      event_id: 'evt-review',
      event_type: 'handoff-reviewed',
      sequence: 5,
      recorded_at_utc: '2026-10-23T10:00:05Z',
      payload: {
        identity_preflight_ref: 'identity:preflight:review',
        identity_preflight_sha256: 'b'.repeat(64),
      },
    },
  ];
  if (includeRevocation) {
    events.push({
      event_id: 'evt-revocation',
      event_type: 'governance-attestation-revoked',
      sequence: 6,
      recorded_at_utc: '2026-10-23T10:00:06Z',
      payload: {
        identity_preflight_ref: 'identity:preflight:revocation',
        identity_preflight_sha256: 'c'.repeat(64),
      },
    });
  }

  const governanceEventIds = [
    'evt-approval',
    'evt-review',
    ...(includeRevocation ? ['evt-revocation'] : []),
  ];
  const recordTimeDecisions = new Map();
  const identityDecisions = [];
  for (const eventId of governanceEventIds) {
    const event = events.find((candidate) => candidate.event_id === eventId);
    const suffix = eventId.slice(4);
    const preflightRef = event.payload.identity_preflight_ref;
    const preflightDigest = event.payload.identity_preflight_sha256;
    identityDecisions.push({
      event_id: eventId,
      phase: 'preflight',
      source_id: sourceId,
      decision_ref: preflightRef,
      decision_sha256: preflightDigest,
    });
    const recordTime = {
      event_id: eventId,
      phase: 'record-time',
      source_id: sourceId,
      decision_ref: `identity:record-time:${suffix}`,
      decision_sha256: digest,
    };
    identityDecisions.push(recordTime);
    recordTimeDecisions.set(eventId, {
      source_id: sourceId,
      decision_ref: recordTime.decision_ref,
      decision_sha256: recordTime.decision_sha256,
      authority_sequence: event.sequence,
      authority_recorded_at: event.recorded_at_utc,
    });
  }

  return {
    governance: {
      approval_event_id: 'evt-approval',
      review_event_id: 'evt-review',
      revocation_event_ids: includeRevocation ? ['evt-revocation'] : [],
      identity_decisions: identityDecisions,
    },
    events,
    recordTimeDecisions,
    expectedIdentitySourceId: sourceId,
  };
}

test('accepts complete governance identity decisions in verified receipt order', () => {
  const input = fixture({ includeRevocation: true });
  assert.deepEqual(verifyIdentityDecisionCoverage(input), { valid: true });
});

test('rejects missing or duplicate preflight/record-time phase entries', () => {
  const missing = fixture();
  missing.governance.identity_decisions.pop();
  assert.throws(() => verifyIdentityDecisionCoverage(missing), { code: 'IDENTITY_COVERAGE' });

  const duplicate = fixture();
  duplicate.governance.identity_decisions.push({
    ...duplicate.governance.identity_decisions[0],
  });
  assert.throws(() => verifyIdentityDecisionCoverage(duplicate), { code: 'IDENTITY_DUPLICATE' });
});

test('rejects unsorted, orphaned, and incorrectly bound decision references', () => {
  const unsorted = fixture();
  [unsorted.governance.identity_decisions[0], unsorted.governance.identity_decisions[2]] = [
    unsorted.governance.identity_decisions[2],
    unsorted.governance.identity_decisions[0],
  ];
  assert.throws(() => verifyIdentityDecisionCoverage(unsorted), { code: 'IDENTITY_ORDER' });

  const orphaned = fixture();
  orphaned.governance.review_event_id = 'evt-not-in-chain';
  assert.throws(() => verifyIdentityDecisionCoverage(orphaned), { code: 'IDENTITY_EVENT_MISSING' });

  const extraRecord = fixture();
  extraRecord.recordTimeDecisions.set('evt-not-in-governance', {
    source_id: sourceId,
    decision_ref: 'identity:record-time:extra',
    decision_sha256: digest,
    authority_sequence: 6,
    authority_recorded_at: '2026-10-23T10:00:06Z',
  });
  assert.throws(() => verifyIdentityDecisionCoverage(extraRecord), {
    code: 'IDENTITY_RECORD_TIME_COVERAGE',
  });

  const wrongPreflight = fixture();
  wrongPreflight.governance.identity_decisions[0].decision_sha256 = 'f'.repeat(64);
  assert.throws(() => verifyIdentityDecisionCoverage(wrongPreflight), {
    code: 'IDENTITY_PREFLIGHT_BINDING',
  });

  const wrongRecordTime = fixture();
  wrongRecordTime.recordTimeDecisions.get('evt-approval').authority_sequence = 8;
  assert.throws(() => verifyIdentityDecisionCoverage(wrongRecordTime), {
    code: 'IDENTITY_RECORD_TIME_BINDING',
  });
});
