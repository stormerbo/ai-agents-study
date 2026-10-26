import { parseUtcTimestampMicros } from './stage5-v7-decision-receipt-conformance.mjs';

const TERMINAL_TYPES = new Set(['consumed', 'aborted', 'failed']);

function reject(code, message) {
  throw Object.assign(new Error(message), { code });
}

function requiredId(value) {
  return typeof value === 'string' && value.length > 0;
}

function decimalUsdMicros(value) {
  if (typeof value !== 'string' || !/^(0|[1-9][0-9]*)(\.[0-9]{1,6})?$/.test(value)) return null;
  const [whole, fraction = ''] = value.split('.');
  return BigInt(whole) * 1_000_000n + BigInt((fraction + '000000').slice(0, 6));
}

function verifyEarlyFailureEvidence(evidence, terminal, envelope) {
  if (!evidence || evidence.source_verification === 'unverified') {
    reject(
      'V7_FAILED_EVIDENCE_UNVERIFIED',
      'required runtime-stop or usage evidence is absent, stale, or unavailable',
    );
  }
  if (evidence.source_verification === 'invalid') {
    reject('V7_FAILED_EVIDENCE_INVALID', 'authenticated early-failure evidence is contradictory');
  }
  const fail = () =>
    reject(
      'V7_FAILED_EVIDENCE_INVALID',
      'failed terminal conflicts with its frozen early-failure policy, evidence, or recomputed bound',
    );
  if (
    evidence.source_verification !== 'valid' ||
    evidence.attempt_set_complete !== false ||
    evidence.scoring_complete !== false ||
    evidence.required_metrics_known !== true
  )
    fail();
  const gate = evidence.failure_gate;
  const allowedGates = {
    budget_violation: { field: 'budget_violation', stopCondition: 'budget' },
    deadline_violation: { field: 'deadline_violation', stopCondition: 'deadline' },
  };
  const selected = allowedGates[gate];
  const spec = envelope.frozen_spec;
  const runtimeStop = evidence.runtime_stop;
  const ledger = evidence.usage_ledger;
  const actual = decimalUsdMicros(ledger?.actual_usd);
  const maximum = decimalUsdMicros(spec?.max_budget_usd);
  const stoppedAt = parseUtcTimestampMicros(runtimeStop?.stopped_at_utc);
  const deadline = parseUtcTimestampMicros(spec?.deadline_utc);
  if (
    !selected ||
    !spec?.early_failure_policy ||
    spec.early_failure_policy[selected.field] !== 'fail-before-scoring' ||
    !Array.isArray(envelope.stop_conditions) ||
    !envelope.stop_conditions.includes(selected.stopCondition) ||
    !runtimeStop ||
    runtimeStop.verified !== true ||
    runtimeStop.processes_terminated !== true ||
    !/^[a-f0-9]{64}$/.test(runtimeStop.record_sha256 ?? '') ||
    !ledger ||
    ledger.verified !== true ||
    ledger.closed !== true ||
    ledger.all_provider_calls_terminal !== true ||
    !Number.isSafeInteger(ledger.closed_sequence) ||
    ledger.closed_sequence < 1 ||
    !/^[a-f0-9]{64}$/.test(ledger.closed_head_sha256 ?? '') ||
    !/^[a-f0-9]{64}$/.test(ledger.ledger_sha256 ?? '') ||
    actual === null ||
    maximum === null ||
    envelope.cost_status !== 'known' ||
    envelope.budget?.authorized_max_usd !== spec.max_budget_usd ||
    envelope.budget?.actual_usd !== ledger.actual_usd ||
    envelope.deadline_utc !== spec.deadline_utc ||
    envelope.runtime_audit_sha256 !== evidence.runtime_audit_sha256 ||
    envelope.usage_ledger_sha256 !== ledger.ledger_sha256 ||
    !/^[a-f0-9]{64}$/.test(evidence.runtime_audit_sha256 ?? '') ||
    !/^[a-f0-9]{64}$/.test(envelope.report_sha256 ?? '') ||
    (envelope.quality_decision !== null && envelope.quality_decision !== 'unverified')
  )
    fail();
  const violated =
    gate === 'budget_violation'
      ? actual > maximum
      : stoppedAt !== null && deadline !== null && stoppedAt > deadline;
  const payload = terminal.payload;
  if (
    !violated ||
    !payload ||
    payload.early_failure_gate !== gate ||
    payload.report_sha256 !== envelope.report_sha256 ||
    payload.runtime_audit_sha256 !== evidence.runtime_audit_sha256 ||
    payload.runtime_stop_record_sha256 !== runtimeStop.record_sha256 ||
    payload.usage_ledger_sha256 !== ledger.ledger_sha256 ||
    payload.usage_ledger_closed_sequence !== ledger.closed_sequence ||
    payload.usage_ledger_closed_head_sha256 !== ledger.closed_head_sha256
  )
    fail();
}

/**
 * Semantic conformance helper for an already signature-verified v7 receipt prefix.
 * It checks lifecycle grammar and report references; it does not verify signatures,
 * identity sources, source freshness, scorer evidence, or the detached decision receipt.
 */
export function verifyV7Lifecycle({ events, envelope, earlyFailureEvidence = null }) {
  if (!Array.isArray(events) || !envelope || typeof envelope !== 'object') {
    reject('V7_INPUT', 'verified event prefix and envelope are required');
  }
  const byId = new Map();
  const sequences = new Set();
  let previousSequence = 0;
  for (const event of events) {
    if (
      !event ||
      !requiredId(event.event_id) ||
      !requiredId(event.event_type) ||
      !Number.isSafeInteger(event.sequence) ||
      event.sequence <= previousSequence ||
      !event.payload ||
      typeof event.payload !== 'object' ||
      Array.isArray(event.payload)
    ) {
      reject('V7_EVENT_SHAPE', 'events must have unique ids, increasing sequences, and payloads');
    }
    if (byId.has(event.event_id) || sequences.has(event.sequence)) {
      reject('V7_EVENT_DUPLICATE', 'event ids and sequences must be unique');
    }
    byId.set(event.event_id, event);
    sequences.add(event.sequence);
    previousSequence = event.sequence;
  }

  const approvals = events.filter((event) => event.event_type === 'assurance-approved');
  const authorizations = events.filter((event) => event.event_type === 'authorized');
  const reservations = events.filter((event) => event.event_type === 'reserved');
  const terminals = events.filter((event) => TERMINAL_TYPES.has(event.event_type));
  const reviews = events.filter((event) => event.event_type === 'handoff-reviewed');
  const revocations = events.filter(
    (event) => event.event_type === 'governance-attestation-revoked',
  );

  if (approvals.length === 0)
    reject('V7_APPROVAL_MISSING', 'assurance approval evidence is absent from the verified prefix');
  if (approvals.length > 1)
    reject('V7_APPROVAL_CARDINALITY', 'assurance approval event is duplicated');
  if (authorizations.length > 1)
    reject('V7_DUPLICATE_AUTHORIZATION', 'authorization event is duplicated');
  if (reservations.length > 1)
    reject('V7_DUPLICATE_RESERVATION', 'reservation event is duplicated');
  if (terminals.length > 1) reject('V7_DUPLICATE_TERMINAL', 'terminal event is duplicated');
  if (reviews.length > 1) reject('V7_DUPLICATE_REVIEW', 'handoff review event is duplicated');

  const approval = approvals[0];
  const approvalDecision = approval.payload.decision;
  if (!['accepted', 'rejected'].includes(approvalDecision)) {
    reject('V7_APPROVAL_DECISION', 'approval event must carry an accepted or rejected decision');
  }
  const authorization = authorizations[0] ?? null;
  const reservation = reservations[0] ?? null;
  const terminal = terminals[0] ?? null;
  const review = reviews[0] ?? null;
  const reviewAttestationId = review?.payload.attestation_id;
  const revocationTargets = new Set();
  for (const revocation of revocations) {
    const targetId = revocation.payload.target_attestation_id;
    const target = [approval, review].find(
      (candidate) => candidate?.payload.attestation_id === targetId,
    );
    if (!target || revocation.sequence <= target.sequence || revocationTargets.has(targetId)) {
      reject(
        'V7_REVOCATION_TARGET',
        'revocation must uniquely target a prior attestation in this run',
      );
    }
    revocationTargets.add(targetId);
  }
  const approvalRevocations = revocations.filter(
    (event) => event.payload.target_attestation_id === approval.payload.attestation_id,
  );
  const approvalRevoked = approvalRevocations.length === 1;

  const governance = envelope.governance;
  if (!governance || !Array.isArray(governance.revocation_event_ids)) {
    reject('V7_EVENT_SHAPE', 'governance event references are malformed');
  }
  if (governance.approval_event_id !== approval.event_id) {
    reject(
      'V7_GOVERNANCE_EVENT_MISSING',
      'referenced assurance approval is not in the verified prefix',
    );
  }
  if (
    governance.revocation_event_ids.length !== revocations.length ||
    governance.revocation_event_ids.some(
      (id) => !revocations.some((event) => event.event_id === id),
    )
  ) {
    reject(
      'V7_GOVERNANCE_REFERENCE_CONTRADICTION',
      'governance revocation references do not exactly cover the verified prefix',
    );
  }
  if (
    approvalRevoked &&
    approvalDecision === 'accepted' &&
    authorization &&
    approvalRevocations[0].sequence < authorization.sequence
  ) {
    reject('V7_AUTHORIZED_AFTER_REVOKED_APPROVAL', 'authorization follows a revoked approval');
  }
  if (approvalDecision === 'rejected' && authorization) {
    reject('V7_AUTHORIZED_AFTER_REJECTED_APPROVAL', 'authorization follows a rejected approval');
  }

  if (!authorization) {
    if (
      reservation ||
      terminal ||
      review ||
      envelope.authorization_event_id !== null ||
      envelope.reservation_event_id !== null ||
      envelope.terminal_event_id !== null ||
      envelope.status !== 'incomplete' ||
      envelope.outcome !== 'incomplete'
    ) {
      reject(
        'V7_NO_START_CONTRADICTION',
        'a no-start run cannot claim execution or a completed outcome',
      );
    }
    return {
      state: 'no-start',
      terminal_event_type: null,
      governance: approvalRevoked
        ? 'revoked'
        : approvalDecision === 'rejected'
          ? 'rejected'
          : 'approved',
    };
  }

  if (
    approvalDecision !== 'accepted' ||
    approvalRevoked ||
    approval.sequence >= authorization.sequence
  ) {
    reject('V7_AUTHORIZATION_ORDER', 'authorization requires a prior accepted, unrevoked approval');
  }
  if (envelope.authorization_event_id !== authorization.event_id) {
    reject('V7_AUTHORIZATION_REFERENCE', 'envelope authorization reference is incorrect');
  }
  if (!reservation) {
    if (
      terminal ||
      review ||
      envelope.reservation_event_id !== null ||
      envelope.terminal_event_id !== null ||
      envelope.status !== 'incomplete' ||
      envelope.outcome !== 'incomplete'
    ) {
      reject('V7_RESERVATION_MISSING', 'authorization without reservation must remain incomplete');
    }
    return {
      state: 'authorized',
      terminal_event_type: null,
      governance: approvalRevoked ? 'revoked' : 'approved',
    };
  }
  if (
    reservation.sequence <= authorization.sequence ||
    envelope.reservation_event_id !== reservation.event_id
  ) {
    reject('V7_RESERVATION_ORDER', 'reservation must follow and match authorization');
  }
  if (!terminal) {
    if (
      review ||
      envelope.terminal_event_id !== null ||
      envelope.status !== 'incomplete' ||
      envelope.outcome !== 'incomplete'
    ) {
      reject('V7_TERMINAL_MISSING', 'a run without a terminal event must remain incomplete');
    }
    return {
      state: 'reserved',
      terminal_event_type: null,
      governance: approvalRevoked ? 'revoked' : 'approved',
    };
  }
  if (
    terminal.sequence <= reservation.sequence ||
    envelope.terminal_event_id !== terminal.event_id
  ) {
    reject('V7_TERMINAL_ORDER', 'terminal must follow and match reservation');
  }
  if (terminal.event_type === 'consumed') {
    if (!['passed', 'failed'].includes(envelope.outcome) || envelope.status !== envelope.outcome) {
      reject(
        'V7_CONSUMED_OUTCOME',
        'consumed requires complete scoring mapped to passed or failed',
      );
    }
  } else if (terminal.event_type === 'aborted') {
    if (envelope.outcome !== 'aborted' || envelope.status !== 'incomplete') {
      reject('V7_ABORTED_OUTCOME', 'aborted terminal requires an incomplete report outcome');
    }
  } else {
    if (envelope.outcome !== 'failed' || envelope.status !== 'failed') {
      reject('V7_FAILED_OUTCOME', 'failed terminal requires a failed report outcome');
    }
    verifyEarlyFailureEvidence(earlyFailureEvidence, terminal, envelope);
  }
  if (review) {
    if (
      review.sequence <= terminal.sequence ||
      governance.review_event_id !== review.event_id ||
      review.payload.terminal_event_id !== terminal.event_id ||
      review.payload.terminal_event_hash !== terminal.event_hash ||
      governance.handoff_core?.terminal_event?.event_id !== terminal.event_id ||
      governance.handoff_core?.terminal_event?.event_hash !== terminal.event_hash
    ) {
      reject(
        'V7_REVIEW_TERMINAL_BINDING',
        'handoff review must follow and bind the exact terminal event',
      );
    }
  } else if (governance.review_event_id !== null) {
    reject('V7_REVIEW_MISSING', 'review reference must resolve to a verified event');
  }
  return {
    state: 'terminal',
    terminal_event_type: terminal.event_type,
    governance:
      approvalRevoked || (reviewAttestationId && revocationTargets.has(reviewAttestationId))
        ? 'revoked'
        : review
          ? 'approved'
          : 'unverified',
  };
}
