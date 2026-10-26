import { verifyV7Lifecycle } from './stage5-v7-lifecycle-conformance.mjs';
import { verifyV7DecisionReceiptClaims } from './stage5-v7-decision-receipt-conformance.mjs';

const EVIDENCE_STATES = new Set(['valid', 'invalid', 'unverified']);
const GOVERNANCE_STATES = new Set(['approved', 'rejected', 'revoked', 'unverified']);
const HOLDOUT_STATES = new Set(['passed', 'failed', 'invalid', 'unverified']);
const LIFECYCLE_STATES = new Set([
  'no-start',
  'authorized',
  'reserved',
  'terminal',
  'unverified',
  'invalid',
]);

function invalidInput(message) {
  throw Object.assign(new TypeError(message), { code: 'V7_DECISION_INPUT' });
}

/**
 * Derive the four v7 decision dimensions from already-verified subsystem results.
 * This helper does not authenticate those inputs, build/sign a detached receipt,
 * or replace the acceptance verifier.
 */
export function deriveV7DecisionDimensions({
  evidenceIntegrity,
  governanceAuthorization,
  holdoutOutcome,
  lifecycleState,
  governanceError = null,
}) {
  if (
    !EVIDENCE_STATES.has(evidenceIntegrity) ||
    !GOVERNANCE_STATES.has(governanceAuthorization) ||
    !HOLDOUT_STATES.has(holdoutOutcome) ||
    !LIFECYCLE_STATES.has(lifecycleState) ||
    ![null, 'invalid'].includes(governanceError)
  ) {
    invalidInput('v7 decision inputs contain an unsupported derived state');
  }

  const terminalContradiction =
    lifecycleState !== 'terminal' && ['passed', 'failed'].includes(holdoutOutcome);
  const invalid =
    evidenceIntegrity === 'invalid' ||
    holdoutOutcome === 'invalid' ||
    lifecycleState === 'invalid' ||
    governanceError === 'invalid' ||
    terminalContradiction;

  let acceptanceReadiness;
  if (invalid) {
    acceptanceReadiness = 'invalid-report';
  } else if (
    evidenceIntegrity === 'unverified' ||
    holdoutOutcome === 'unverified' ||
    governanceAuthorization === 'unverified' ||
    lifecycleState !== 'terminal'
  ) {
    acceptanceReadiness = 'unverified';
  } else if (
    holdoutOutcome === 'failed' ||
    governanceAuthorization === 'rejected' ||
    governanceAuthorization === 'revoked'
  ) {
    acceptanceReadiness = 'not-eligible';
  } else {
    acceptanceReadiness = 'ready-for-human-acceptance';
  }

  return {
    evidence_integrity: evidenceIntegrity,
    governance_authorization: governanceAuthorization,
    holdout_outcome: holdoutOutcome,
    acceptance_readiness: acceptanceReadiness,
  };
}

const MISSING_LIFECYCLE_EVIDENCE = new Set([
  'V7_APPROVAL_MISSING',
  'V7_GOVERNANCE_EVENT_MISSING',
  'V7_REVIEW_MISSING',
  'V7_TERMINAL_MISSING',
  'V7_RESERVATION_MISSING',
]);

/**
 * Compose the local lifecycle, dimension, and receipt-claims contracts. The event
 * chain, subsystem statuses, receipt schema/signature, and source expiry inputs must
 * already have been independently verified by the caller.
 */
export function deriveAndVerifyV7Decision({
  events,
  envelope,
  earlyFailureEvidence = null,
  evidenceIntegrity,
  governanceAuthorization,
  holdoutOutcome,
  governanceError = null,
  receiptBindings,
  freshnessExpiries,
  decisionReceipt,
}) {
  if (!receiptBindings || typeof receiptBindings !== 'object' || Array.isArray(receiptBindings)) {
    invalidInput('expected detached-receipt bindings must be an object');
  }
  let lifecycle;
  let lifecycleState;
  let lifecycleError = null;
  let derivedEvidenceIntegrity = evidenceIntegrity;
  let derivedHoldoutOutcome = holdoutOutcome;
  try {
    lifecycle = verifyV7Lifecycle({ events, envelope, earlyFailureEvidence });
    lifecycleState = lifecycle.state;
  } catch (error) {
    if (
      !error ||
      typeof error.code !== 'string' ||
      !error.code.startsWith('V7_') ||
      ['V7_INPUT', 'V7_EVENT_SHAPE'].includes(error.code)
    )
      throw error;
    lifecycleError = error.code;
    if (error.code === 'V7_FAILED_EVIDENCE_UNVERIFIED') {
      lifecycleState = 'terminal';
      derivedEvidenceIntegrity = 'unverified';
      derivedHoldoutOutcome = 'unverified';
    } else if (error.code === 'V7_FAILED_EVIDENCE_INVALID') {
      lifecycleState = 'invalid';
      derivedHoldoutOutcome = 'invalid';
    } else {
      lifecycleState = MISSING_LIFECYCLE_EVIDENCE.has(error.code) ? 'unverified' : 'invalid';
    }
  }
  const dimensions = deriveV7DecisionDimensions({
    evidenceIntegrity: derivedEvidenceIntegrity,
    governanceAuthorization,
    holdoutOutcome: derivedHoldoutOutcome,
    lifecycleState,
    governanceError,
  });
  for (const [key, value] of Object.entries(dimensions)) {
    if (Object.hasOwn(receiptBindings, key) && receiptBindings[key] !== value) {
      reject('V7_DECISION_BINDING', `receipt context ${key} conflicts with the derived decision`);
    }
  }
  const expectedBindings = { ...receiptBindings, ...dimensions };
  verifyV7DecisionReceiptClaims(decisionReceipt, expectedBindings, freshnessExpiries);
  return {
    ...dimensions,
    lifecycle_state: lifecycleState,
    lifecycle_error: lifecycleError,
  };
}
