const PHASE_ORDER = new Map([
  ['preflight', 0],
  ['record-time', 1],
]);

function reject(code, message) {
  throw Object.assign(new Error(message), { code });
}

function nonemptyString(value) {
  return typeof value === 'string' && value.length > 0;
}

/**
 * Reference conformance check for identity-decision coverage in a v7 governance object.
 * `verifiedEvents` must already come from a cryptographically verified receipt chain.
 * `recordTimeDecisions` must contain fresh, schema-checked source responses whose digests
 * were recomputed from their canonical JCS preimages by the caller.
 */
export function verifyIdentityDecisionCoverage({
  governance,
  events: verifiedEvents,
  recordTimeDecisions,
  expectedIdentitySourceId,
}) {
  if (!governance || !Array.isArray(verifiedEvents) || !(recordTimeDecisions instanceof Map)) {
    reject(
      'IDENTITY_INPUT',
      'verified governance, event chain, and record-time decisions are required',
    );
  }
  if (!nonemptyString(expectedIdentitySourceId)) {
    reject('IDENTITY_SOURCE', 'the expected identity source must be verifier-configured');
  }

  const governanceEventIds = [
    governance.approval_event_id,
    governance.review_event_id,
    ...(Array.isArray(governance.revocation_event_ids) ? governance.revocation_event_ids : []),
  ];
  if (
    governanceEventIds.length < 2 ||
    governanceEventIds.some((id) => !nonemptyString(id)) ||
    new Set(governanceEventIds).size !== governanceEventIds.length
  ) {
    reject('IDENTITY_GOVERNANCE_EVENTS', 'governance event ids must be present and unique');
  }

  const eventsById = new Map();
  const usedSequences = new Set();
  for (const event of verifiedEvents) {
    if (
      !event ||
      !nonemptyString(event.event_id) ||
      !Number.isSafeInteger(event.sequence) ||
      event.sequence < 1 ||
      !nonemptyString(event.event_type) ||
      !event.payload ||
      typeof event.payload !== 'object' ||
      Array.isArray(event.payload) ||
      !nonemptyString(event.recorded_at_utc)
    ) {
      reject(
        'IDENTITY_EVENT_SHAPE',
        'verified events must include id, type, sequence, time, and payload',
      );
    }
    if (eventsById.has(event.event_id) || usedSequences.has(event.sequence)) {
      reject('IDENTITY_EVENT_DUPLICATE', 'verified event ids and sequences must be unique');
    }
    eventsById.set(event.event_id, event);
    usedSequences.add(event.sequence);
  }

  const expectedTypes = new Map([
    [governance.approval_event_id, 'assurance-approved'],
    [governance.review_event_id, 'handoff-reviewed'],
    ...(governance.revocation_event_ids ?? []).map((id) => [id, 'governance-attestation-revoked']),
  ]);
  for (const eventId of governanceEventIds) {
    const event = eventsById.get(eventId);
    if (!event)
      reject('IDENTITY_EVENT_MISSING', `governance event ${eventId} is absent from verified chain`);
    if (event.event_type !== expectedTypes.get(eventId)) {
      reject('IDENTITY_EVENT_TYPE', `governance event ${eventId} has the wrong event type`);
    }
  }
  if (
    recordTimeDecisions.size !== governanceEventIds.length ||
    [...recordTimeDecisions.keys()].some((eventId) => !governanceEventIds.includes(eventId))
  ) {
    reject(
      'IDENTITY_RECORD_TIME_COVERAGE',
      'record-time source results must exactly cover governance events',
    );
  }

  const expected = governanceEventIds
    .map((eventId) => eventsById.get(eventId))
    .sort((left, right) => left.sequence - right.sequence)
    .flatMap((event) => [
      { event, phase: 'preflight' },
      { event, phase: 'record-time' },
    ]);
  const entries = governance.identity_decisions;
  if (!Array.isArray(entries)) {
    reject('IDENTITY_COVERAGE', 'identity decision entries must be an array');
  }

  const entryKeys = new Set();
  const decisionRefs = new Set();
  for (const entry of entries) {
    if (
      !entry ||
      !nonemptyString(entry.event_id) ||
      !PHASE_ORDER.has(entry.phase) ||
      !nonemptyString(entry.source_id) ||
      !nonemptyString(entry.decision_ref) ||
      !/^[a-f0-9]{64}$/.test(entry.decision_sha256 ?? '')
    ) {
      reject('IDENTITY_ENTRY_SHAPE', 'identity decision entries must match the strict wire schema');
    }
    const pairKey = `${entry.event_id}\u0000${entry.phase}`;
    if (entryKeys.has(pairKey))
      reject('IDENTITY_DUPLICATE', 'identity decision phase is duplicated');
    if (decisionRefs.has(entry.decision_ref))
      reject('IDENTITY_DUPLICATE_REF', 'identity decision references must be unique');
    if (entry.source_id !== expectedIdentitySourceId) {
      reject('IDENTITY_SOURCE', 'identity decision source differs from verifier configuration');
    }
    entryKeys.add(pairKey);
    decisionRefs.add(entry.decision_ref);
  }
  if (entries.length !== expected.length) {
    reject(
      'IDENTITY_COVERAGE',
      'each governance event must have exactly one entry for each identity phase',
    );
  }

  for (let index = 0; index < expected.length; index += 1) {
    const { event, phase } = expected[index];
    const entry = entries[index];
    if (entry.event_id !== event.event_id || entry.phase !== phase) {
      reject(
        'IDENTITY_ORDER',
        'entries must follow verified event sequence, preflight before record-time',
      );
    }
    if (phase === 'preflight') {
      if (
        entry.decision_ref !== event.payload.identity_preflight_ref ||
        entry.decision_sha256 !== event.payload.identity_preflight_sha256
      ) {
        reject(
          'IDENTITY_PREFLIGHT_BINDING',
          'preflight reference and digest differ from signed event payload',
        );
      }
      continue;
    }

    const decision = recordTimeDecisions.get(event.event_id);
    if (
      !decision ||
      entry.source_id !== decision.source_id ||
      entry.decision_ref !== decision.decision_ref ||
      entry.decision_sha256 !== decision.decision_sha256 ||
      decision.authority_sequence !== event.sequence ||
      decision.authority_recorded_at !== event.recorded_at_utc
    ) {
      reject(
        'IDENTITY_RECORD_TIME_BINDING',
        'record-time reference must match the fresh source result and verified event time',
      );
    }
  }

  return { valid: true };
}
