import assert from 'node:assert/strict';
import { createHash, createPublicKey, verify } from 'node:crypto';
import { readFile, readdir } from 'node:fs/promises';
import canonicalize from 'canonicalize';
import test from 'node:test';
import Ajv2020 from 'ajv/dist/2020.js';

const directory = new URL('.', import.meta.url);
const utcTimestampMicroseconds = (timestamp) => {
  if (typeof timestamp !== 'string' || !timestamp.endsWith('Z')) return null;
  const dateTimeFields = timestamp.slice(0, -1).split('T');
  if (dateTimeFields.length !== 2) return null;
  const [datePart, timePart] = dateTimeFields;
  const dateFields = datePart.split('-');
  const clockFields = timePart.split('.');
  if (dateFields.length !== 3 || clockFields.length > 2) return null;
  const timeFields = clockFields[0].split(':');
  if (timeFields.length !== 3) return null;
  const [yearText, monthText, dayText] = dateFields;
  const [hourText, minuteText, secondText] = timeFields;
  if (
    yearText.length !== 4 ||
    monthText.length !== 2 ||
    dayText.length !== 2 ||
    hourText.length !== 2 ||
    minuteText.length !== 2 ||
    secondText.length !== 2
  ) {
    return null;
  }
  const digitsOnly = (value) => [...value].every((char) => char >= '0' && char <= '9');
  if (![yearText, monthText, dayText, hourText, minuteText, secondText].every(digitsOnly)) {
    return null;
  }
  const year = Number(yearText);
  const month = Number(monthText);
  const day = Number(dayText);
  const hour = Number(hourText);
  const minute = Number(minuteText);
  const second = Number(secondText);
  if (year < 1 || month < 1 || month > 12 || hour > 23 || minute > 59 || second > 59) {
    return null;
  }
  const isLeapYear = year % 4 === 0 && (year % 100 !== 0 || year % 400 === 0);
  const daysPerMonth = [31, isLeapYear ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
  if (day < 1 || day > daysPerMonth[month - 1]) return null;
  const fraction = clockFields[1] ?? '';
  if (
    (clockFields.length === 2 && (fraction.length < 1 || fraction.length > 6)) ||
    !digitsOnly(fraction)
  ) {
    return null;
  }
  const wholeSecondEpochMs = Date.parse(`${datePart}T${clockFields[0]}Z`);
  if (!Number.isFinite(wholeSecondEpochMs)) return null;
  const fractionMicros = BigInt(fraction.padEnd(6, '0') || '0');
  return BigInt(wholeSecondEpochMs) * 1000n + fractionMicros;
};
const sourceProbeRecordSha256 = (scope, probe) => {
  const { probe_record_sha256, ...probeContent } = probe;
  const preimage = {
    schema: 'stage5-source-probe-journal-entry-v1',
    environment_id: scope.environment_id,
    source_id: scope.source_id,
    monitor_service_id: scope.monitor_service_id,
    probe: probeContent,
  };
  return createHash('sha256').update(canonicalize(preimage), 'utf8').digest('hex');
};
const attestationSchema = JSON.parse(
  await readFile(new URL('stage5-governance-attestation-v1.schema.json', directory), 'utf8'),
);
const eventSchema = JSON.parse(
  await readFile(new URL('stage5-governance-event-payloads-v1.schema.json', directory), 'utf8'),
);
const decisionSchema = JSON.parse(
  await readFile(new URL('stage5-acceptance-decision-v1.schema.json', directory), 'utf8'),
);
const handoffCoreSchema = JSON.parse(
  await readFile(new URL('stage5-handoff-core-v1.schema.json', directory), 'utf8'),
);
const governanceObjectSchema = JSON.parse(
  await readFile(new URL('stage5-governance-object-v1.schema.json', directory), 'utf8'),
);
const identityDecisionSchema = JSON.parse(
  await readFile(new URL('stage5-identity-decision-v1.schema.json', directory), 'utf8'),
);
const identityRoleChangeSchema = await readFile(
  new URL('stage5-identity-role-change-v1.schema.json', directory),
  'utf8',
).then(JSON.parse, () => null);
const identityRoleChangePolicySchema = await readFile(
  new URL('stage5-identity-role-change-policy-v1.schema.json', directory),
  'utf8',
).then(JSON.parse, () => null);
const identityRoleChangePolicyTransitionSchema = await readFile(
  new URL('stage5-identity-role-change-policy-transition-v1.schema.json', directory),
  'utf8',
).then(JSON.parse, () => null);
const identityRoleHistoryPackageSchema = await readFile(
  new URL('stage5-identity-role-history-package-v1.schema.json', directory),
  'utf8',
).then(JSON.parse, () => null);
const decisionCommonSchema = JSON.parse(
  await readFile(new URL('stage5-decision-consumption-common-v1.schema.json', directory), 'utf8'),
);
const humanAcceptanceSchema = JSON.parse(
  await readFile(new URL('stage5-human-acceptance-v1.schema.json', directory), 'utf8'),
);
const releaseAuthorizationSchema = JSON.parse(
  await readFile(new URL('stage5-release-authorization-v1.schema.json', directory), 'utf8'),
);
const decisionChallengeEventsSchema = JSON.parse(
  await readFile(new URL('stage5-decision-challenge-events-v1.schema.json', directory), 'utf8'),
);
const decisionChallengeEventsV2Schema = JSON.parse(
  await readFile(new URL('stage5-decision-challenge-events-v2.schema.json', directory), 'utf8'),
);
const sourceOutageEpisodeSchema = JSON.parse(
  await readFile(new URL('stage5-source-outage-episode-v1.schema.json', directory), 'utf8'),
);
const sourceProbeJournalPageSchema = JSON.parse(
  await readFile(new URL('stage5-source-probe-journal-page-v1.schema.json', directory), 'utf8'),
);
const decisionConsumptionPolicySchema = JSON.parse(
  await readFile(new URL('stage5-decision-consumption-policy-v1.schema.json', directory), 'utf8'),
);
const decisionConsumptionPolicyV2Schema = JSON.parse(
  await readFile(new URL('stage5-decision-consumption-policy-v2.schema.json', directory), 'utf8'),
);
const deploymentOperationSchema = JSON.parse(
  await readFile(new URL('stage5-deployment-operation-v1.schema.json', directory), 'utf8'),
);
const decisionConsumerIdentitySchema = JSON.parse(
  await readFile(
    new URL('stage5-decision-consumer-identity-decision-v1.schema.json', directory),
    'utf8',
  ),
);
const v7EnvelopeSchema = JSON.parse(
  await readFile(
    new URL('official-blind-holdout-evidence-envelope-v7.schema.json', directory),
    'utf8',
  ),
);
const ajv = new Ajv2020({ allErrors: true, strict: true, strictRequired: false });
ajv.addSchema(decisionCommonSchema);
if (identityRoleChangeSchema) ajv.addSchema(identityRoleChangeSchema);
const validateAttestation = ajv.compile(attestationSchema);
const validateEvent = ajv.compile(eventSchema);
const validateDecision = ajv.compile(decisionSchema);
const validateHandoffCore = ajv.compile(handoffCoreSchema);
const validateGovernanceObject = ajv.compile(governanceObjectSchema);
const validateIdentityDecision = ajv.compile(identityDecisionSchema);
const validateIdentityRoleChange = identityRoleChangeSchema
  ? ajv.compile(identityRoleChangeSchema)
  : () => false;
const validateIdentityRoleChangePolicy = identityRoleChangePolicySchema
  ? ajv.compile(identityRoleChangePolicySchema)
  : () => false;
const validateIdentityRoleChangePolicyTransition = identityRoleChangePolicyTransitionSchema
  ? ajv.compile(identityRoleChangePolicyTransitionSchema)
  : () => false;
const validateIdentityRoleHistoryPackage = identityRoleHistoryPackageSchema
  ? ajv.compile(identityRoleHistoryPackageSchema)
  : () => false;
const validateHumanAcceptance = ajv.compile(humanAcceptanceSchema);
const validateReleaseAuthorization = ajv.compile(releaseAuthorizationSchema);
const validateDecisionChallengeEvent = ajv.compile(decisionChallengeEventsSchema);
const validateDecisionChallengeEventV2 = ajv.compile(decisionChallengeEventsV2Schema);
const validateSourceOutageEpisode = ajv.compile(sourceOutageEpisodeSchema);
const validateSourceProbeJournalPage = ajv.compile(sourceProbeJournalPageSchema);
const validateDecisionConsumptionPolicy = ajv.compile(decisionConsumptionPolicySchema);
const validateDecisionConsumptionPolicyV2 = ajv.compile(decisionConsumptionPolicyV2Schema);
const isDecisionConsumptionPolicyV2SemanticallyValid = (policy) => {
  const monitoring = policy.challenge_monitoring;
  const requiredDetectionDelay = [
    BigInt(monitoring.full_reconciliation_interval_seconds) +
      BigInt(monitoring.full_reconciliation_duration_bound_seconds),
    BigInt(monitoring.notification_delivery_bound_seconds) +
      BigInt(monitoring.target_fanout_duration_bound_seconds),
    BigInt(monitoring.source_unavailability_threshold_seconds) +
      2n *
        (BigInt(monitoring.source_probe_interval_seconds) +
          BigInt(monitoring.source_probe_timeout_bound_seconds)) +
      BigInt(monitoring.target_fanout_duration_bound_seconds),
  ].reduce((maximum, candidate) => (candidate > maximum ? candidate : maximum), 0n);
  return BigInt(monitoring.maximum_detection_delay_seconds) >= requiredDetectionDelay;
};
const validateDeploymentOperation = ajv.compile(deploymentOperationSchema);
const validateDecisionConsumerIdentity = ajv.compile(decisionConsumerIdentitySchema);
const validateV7Envelope = ajv.compile(v7EnvelopeSchema);

const digest = 'a'.repeat(64);
const commonAttestation = {
  attestation_id: 'att-01',
  decision: 'accepted',
  subject_id: 'person-01',
  frozen_spec_sha256: digest,
  assurance_profile: 'single-authority-v1',
  approval_policy_id: 'policy-01',
  signed_at_utc: '2026-10-23T10:00:00Z',
  expires_at_utc: '2026-10-24T10:00:00Z',
  trust_domains: {
    append_authority_domain: 'registry',
    key_custodian_domain: 'custodian',
  },
  compromise_in_scope: false,
  signature_profile: 'ed25519-jcs-governance-attestation-v1',
  signing_key_id: 'person-key-01',
  signature: 'A'.repeat(86),
};

const approval = {
  schema: 'stage5-assurance-approval-v1',
  ...commonAttestation,
  required_role: 'stage5_risk_owner',
};
const review = {
  schema: 'stage5-handoff-review-v1',
  ...commonAttestation,
  required_role: 'stage5_independent_reviewer',
  handoff_core_sha256: digest,
};

const approvalEvent = {
  attestation_id: 'att-01',
  attestation_sha256: digest,
  subject_id: 'person-01',
  required_role: 'stage5_risk_owner',
  decision: 'accepted',
  frozen_spec_sha256: digest,
  assurance_profile: 'single-authority-v1',
  approval_policy_id: 'policy-01',
  identity_preflight_ref: 'identity:decision:01',
  identity_preflight_sha256: digest,
  trust_domains_sha256: digest,
  compromise_in_scope: false,
};
const reviewEvent = {
  attestation_id: 'att-02',
  attestation_sha256: digest,
  subject_id: 'person-02',
  required_role: 'stage5_independent_reviewer',
  decision: 'accepted',
  frozen_spec_sha256: digest,
  handoff_core_sha256: digest,
  terminal_event_id: 'evt-terminal',
  terminal_event_hash: digest,
  approval_policy_id: 'policy-01',
  identity_preflight_ref: 'identity:decision:02',
  identity_preflight_sha256: digest,
};
const revocationEvent = {
  revocation_id: 'rev-01',
  target_kind: 'assurance-approval',
  target_attestation_id: 'att-01',
  target_attestation_sha256: digest,
  subject_id: 'person-01',
  required_role: 'stage5_risk_owner',
  reason_code: 'signer-withdrawal',
  approval_policy_id: 'policy-01',
  identity_preflight_ref: 'identity:decision:03',
  identity_preflight_sha256: digest,
};
const preflightIdentityDecision = {
  schema: 'stage5-identity-preflight-decision-v1',
  source_id: 'identity-source-01',
  decision_ref: 'identity:preflight:01',
  environment_id: 'stage5-prod',
  log_id: 'holdout-log-01',
  run_id: 'run-01',
  attestation_sha256: digest,
  subject_id: 'person-01',
  signing_key_id: 'person-key-01',
  required_role: 'stage5_risk_owner',
  approval_policy_id: 'policy-01',
  challenge_nonce: 'nonce-01-a-valid-single-use-random-challenge',
  verified_subject_id: 'person-01',
  key_fingerprint_sha256: digest,
  role_grant_id: 'grant-01',
  role_valid_now: true,
  credential_state_now: 'active',
  revocation_sequence: 12,
  decision: 'allow',
  issued_at_utc: '2026-10-23T10:00:00Z',
  valid_until_utc: '2026-10-23T10:00:30Z',
  policy_version: 'identity-policy-3',
  decision_sha256: digest,
};
const recordTimeIdentityDecision = {
  ...preflightIdentityDecision,
  schema: 'stage5-identity-record-time-decision-v1',
  decision_ref: 'identity:record-time:01',
  authority_sequence: 4,
  authority_recorded_at: '2026-10-23T10:00:10Z',
  evaluated_at_utc: '2026-10-23T10:00:11Z',
  role_valid_at_record_time: true,
};
delete recordTimeIdentityDecision.challenge_nonce;
delete recordTimeIdentityDecision.issued_at_utc;
delete recordTimeIdentityDecision.valid_until_utc;
delete recordTimeIdentityDecision.role_valid_now;

const v7FrozenSpec = {
  hash_profile: 'jcs-rfc8785-v1',
  holdout_version: 'holdout-v1',
  run_id: 'run-01',
  authorization_event_id: 'evt-authorized',
  owner_id: 'person-01',
  executor_id: 'agent-01',
  recovery_operator_id: 'operator-01',
  candidate_sha256: digest,
  image_digest: `sha256:${digest}`,
  dataset_sha256: digest,
  scorer_sha256: digest,
  executor_sha256: digest,
  max_budget_usd: '5.00',
  early_failure_policy: {
    budget_violation: 'fail-before-scoring',
    deadline_violation: 'fail-before-scoring',
  },
  max_cases: 12,
  minimum_task_count: 12,
  minimum_pass_rate_bps: 10000,
  require_all_tasks_pass: true,
  max_output_bytes: 100000,
  deadline_utc: '2026-10-23T12:00:00Z',
  stop_conditions: [
    'budget',
    'deadline',
    'side-effect',
    'permission-boundary',
    'evidence-missing',
    'label-leak',
    'identity-mismatch',
  ],
  registry_environment_id: 'stage5-prod',
  registry_log_id: 'holdout-log-01',
  permitted_signer_key_id: 'registry-key-01',
  trust_bundle_sha256: digest,
  receipt_hash_profile: 'jcs-rfc8785-v1',
  receipt_signature_profile: 'ed25519-jcs-receipt-v1',
  max_status_age_seconds: 600,
  clock_skew_seconds: 30,
  verifier_input_limits_sha256: digest,
  assurance_profile: 'single-authority-v1',
  append_authority_domain_id: 'registry-domain',
  signing_key_custodian_domain_id: 'key-custodian-domain',
  witness_authority_domain_id: null,
  witness_root_fingerprint_sha256: null,
};
const v7EventSummary = {
  type: 'authorized',
  event_id: 'evt-authorized',
  actor_id: 'person-01',
  actor_role: 'owner',
  previous_event_id: null,
  holdout_version: 'holdout-v1',
  candidate_sha256: digest,
  image_digest: `sha256:${digest}`,
  dataset_sha256: digest,
  scorer_sha256: digest,
  executor_sha256: digest,
  hash_profile: 'jcs-rfc8785-v1',
  frozen_spec_sha256: digest,
  run_id: 'run-01',
  appended_at: '2026-10-23T10:00:00Z',
};
const v7EventEnvelope = {
  schema: 'stage5-registry-event-envelope-v1',
  hash_profile: 'jcs-rfc8785-v1',
  run_id: 'run-01',
  sequence: 1,
  event_id: 'evt-authorized',
  previous_event_hash: '0'.repeat(64),
  event_type: 'authorized',
  actor_subject_id: 'person-01',
  actor_role: 'owner',
  registry_recorded_at: '2026-10-23T10:00:00Z',
  actor_asserted_at: null,
  payload_sha256: digest,
  payload: v7EventSummary,
  event_hash: digest,
};
const v7Receipt = {
  schema: 'stage5-append-receipt-v1',
  hash_profile: 'jcs-rfc8785-v1',
  environment_id: 'stage5-prod',
  log_id: 'holdout-log-01',
  run_id: 'run-01',
  sequence: 1,
  event_id: 'evt-authorized',
  previous_event_hash: '0'.repeat(64),
  event_hash: digest,
  registry_recorded_at: '2026-10-23T10:00:00Z',
  signature_profile: 'ed25519-jcs-receipt-v1',
  signature_algorithm: 'Ed25519',
  key_id: 'registry-key-01',
  signature: 'A'.repeat(86),
};
function makeV7Envelope(governance) {
  return {
    schema: 'official-blind-holdout-evidence-envelope-v7',
    hash_profile: 'jcs-rfc8785-v1',
    gate_id: 'official_blind_holdout',
    kind: 'holdout',
    status: 'passed',
    release_id: 'release-01',
    run_id: 'run-01',
    blind: true,
    holdout_version: 'holdout-v1',
    candidate_sha256: digest,
    image_digest: `sha256:${digest}`,
    scorer_sha256: digest,
    executor_sha256: digest,
    authorization_event_id: 'evt-authorized',
    reservation_event_id: 'evt-reserved',
    terminal_event_id: 'evt-consumed',
    frozen_spec: v7FrozenSpec,
    frozen_spec_sha256: digest,
    results_sha256: digest,
    output_sha256: digest,
    output_seal_id: 'seal-01',
    metrics: {
      task_count: 12,
      passed_tasks: 12,
      pass_rate_bps: 10000,
      quality_criteria: {
        minimum_task_count: 12,
        minimum_pass_rate_bps: 10000,
        require_all_tasks_pass: true,
      },
      token_usage: { input_tokens: 120, output_tokens: 80 },
      cost_usd: '1.25',
    },
    metrics_sha256: digest,
    independent_task_count: 12,
    sample_size: 12,
    passed_tasks: 12,
    pass_rate_bps: 10000,
    quality_criteria: {
      minimum_task_count: 12,
      minimum_pass_rate_bps: 10000,
      require_all_tasks_pass: true,
    },
    quality_decision: 'passed',
    token_usage: { input_tokens: 120, output_tokens: 80 },
    case_limit: 12,
    max_output_bytes: 100000,
    deadline_utc: '2026-10-23T12:00:00Z',
    executed_at: '2026-10-23T10:00:00Z',
    outcome: 'passed',
    cost_status: 'known',
    budget: { authorized_max_usd: '5.00', actual_usd: '1.25' },
    stop_conditions: v7FrozenSpec.stop_conditions,
    registry: {
      registry_id: 'holdout-registry-01',
      append_only: true,
      receipt_chain: [{ event: v7EventEnvelope, receipt: v7Receipt }],
    },
    trust_bundle: {
      schema: 'stage5-receipt-trust-bundle-v1',
      bundle_id: 'bundle-01',
      hash_profile: 'jcs-rfc8785-v1',
      signature_profile: 'ed25519-jcs-receipt-v1',
      environment_id: 'stage5-prod',
      log_id: 'holdout-log-01',
      issued_at_utc: '2026-10-23T09:00:00Z',
      keys: [
        {
          key_id: 'registry-key-01',
          algorithm: 'Ed25519',
          public_key: 'A'.repeat(43),
          state: 'active',
          not_before_utc: '2026-10-23T09:00:00Z',
          not_after_utc: '2027-01-23T00:00:00Z',
        },
      ],
    },
    trust_bundle_root_signature: {
      schema: 'stage5-trust-root-signature-v1',
      root_key_id: 'root-01',
      profile: 'ed25519-jcs-trust-bundle-v1',
      signature: 'A'.repeat(86),
    },
    trust_bundle_sha256: digest,
    report_sha256: digest,
    governance,
  };
}

const verifierDecision = {
  schema: 'stage5-acceptance-decision-v1',
  decision_id: 'decision-01',
  evidence_envelope_sha256: digest,
  report_sha256: digest,
  run_id: 'run-01',
  frozen_spec_sha256: digest,
  assurance_profile: 'single-authority-v1',
  evidence_integrity: 'valid',
  governance_authorization: 'approved',
  holdout_outcome: 'passed',
  acceptance_readiness: 'ready-for-human-acceptance',
  trust_bundle_sha256: digest,
  key_status_sequence: 7,
  usage_trust_bundle_sha256: digest,
  usage_key_status_sequence: 11,
  usage_ledger_closed_sequence: 33,
  usage_ledger_closed_head_sha256: digest,
  identity_decisions_sha256: digest,
  verifier_policy_id: 'policy-01',
  verifier_build_sha256: digest,
  verified_at_utc: '2026-10-23T10:00:00Z',
  valid_until_utc: '2026-10-23T10:05:00Z',
  signature_profile: 'ed25519-jcs-stage5-decision-v1',
  verifier_key_id: 'verifier-key-01',
  signature: 'A'.repeat(86),
};

const handoffCore = {
  schema: 'stage5-handoff-core-v1',
  run_id: 'run-01',
  frozen_spec_sha256: digest,
  assurance_profile: 'single-authority-v1',
  compromise_in_scope: false,
  trust_domains: {
    append_authority_domain: 'registry',
    key_custodian_domain: 'custodian',
  },
  terminal_event: {
    event_id: 'evt-terminal',
    event_hash: digest,
    sequence: 3,
    event_type: 'consumed',
  },
  deployment_facts: [
    'deployment-topology',
    'identity-ownership',
    'registry-operations',
    'rollback-procedure',
    'retention-policy',
    'incident-response',
  ].map((fact_id) => ({
    fact_id,
    evidence_ref: `evidence:${fact_id}`,
    evidence_sha256: digest,
  })),
  residual_risks: [
    {
      risk_id: 'risk-01',
      severity: 'medium',
      statement: 'Provider usage may be delayed.',
      disposition: 'mitigated',
      owner_subject_id: 'person-01',
    },
  ],
  required_subjects: {
    risk_owner_subject_id: 'person-01',
    independent_reviewer_subject_id: 'person-02',
  },
};

const governanceObject = {
  schema: 'stage5-governance-evidence-v1',
  approval_attestation: approval,
  approval_event_id: 'evt-approval',
  review_attestation: review,
  review_event_id: 'evt-review',
  revocation_event_ids: [],
  handoff_core: handoffCore,
  handoff_core_sha256: digest,
  identity_decisions: [
    {
      event_id: 'evt-approval',
      phase: 'preflight',
      source_id: 'identity-source-01',
      decision_ref: 'identity:preflight:01',
      decision_sha256: digest,
    },
    {
      event_id: 'evt-approval',
      phase: 'record-time',
      source_id: 'identity-source-01',
      decision_ref: 'identity:record:01',
      decision_sha256: digest,
    },
    {
      event_id: 'evt-review',
      phase: 'preflight',
      source_id: 'identity-source-01',
      decision_ref: 'identity:preflight:02',
      decision_sha256: digest,
    },
    {
      event_id: 'evt-review',
      phase: 'record-time',
      source_id: 'identity-source-01',
      decision_ref: 'identity:record:02',
      decision_sha256: digest,
    },
  ],
};

test('validates bounded verifier protocol errors without leaking input', async () => {
  const schema = JSON.parse(
    await readFile(new URL('stage5-verifier-protocol-error-v1.schema.json', directory), 'utf8'),
  );
  const validate = new Ajv2020({ allErrors: true, strict: true, strictRequired: false }).compile(
    schema,
  );
  const limitError = {
    schema: 'stage5-verifier-protocol-error-v1',
    request_id: 'request-01',
    error_code: 'input-limit-exceeded',
    limit_dimension: 'decompressed-input-bytes',
    retryable: false,
  };
  assert.equal(validate(limitError), true, JSON.stringify(validate.errors));
  const busyError = {
    ...limitError,
    error_code: 'capacity-exhausted',
    limit_dimension: null,
    retryable: true,
    retry_after_seconds: 3,
  };
  assert.equal(validate(busyError), true, JSON.stringify(validate.errors));
  const notReadyError = {
    ...busyError,
    error_code: 'verifier-not-ready',
    retry_after_seconds: 5,
  };
  assert.equal(validate(notReadyError), true, JSON.stringify(validate.errors));
  assert.ok(
    Buffer.byteLength(JSON.stringify({ ...busyError, request_id: 'a'.repeat(128) })) < 1024,
  );
  assert.equal(validate({ ...busyError, retry_after_seconds: 0 }), false);
  assert.equal(validate({ ...notReadyError, retryable: false }), false);
  assert.equal(validate({ ...limitError, retry_after_seconds: 3 }), false);
  assert.ok(
    Buffer.byteLength(JSON.stringify({ ...limitError, request_id: 'a'.repeat(128) })) < 1024,
  );
  assert.equal(validate({ ...limitError, limit_dimension: null }), false);
  assert.equal(validate({ ...limitError, limit_dimension: 'parse-cpu' }), true);
  assert.equal(validate({ ...limitError, limit_dimension: 'global-concurrency' }), false);
  assert.equal(
    validate({ ...limitError, error_code: 'malformed-input', limit_dimension: null }),
    true,
  );
  assert.equal(
    validate({ ...limitError, error_code: 'unsupported-content-encoding', limit_dimension: null }),
    true,
  );
  assert.equal(
    validate({
      ...limitError,
      error_code: 'unsupported-content-encoding',
      limit_dimension: 'json-depth',
    }),
    false,
  );
  assert.equal(validate({ ...limitError, retryable: true }), false);
  assert.equal(validate({ ...limitError, body_fragment: 'secret' }), false);
});

test('validates externally pinned parser resource-limit profiles', async () => {
  const schema = JSON.parse(
    await readFile(new URL('stage5-verifier-input-limits-v1.schema.json', directory), 'utf8'),
  );
  const validate = new Ajv2020({ allErrors: true, strict: true }).compile(schema);
  const profile = {
    schema: 'stage5-verifier-input-limits-v1',
    profile_id: 'stage5-prod-parser-limits-v1',
    accepted_content_encodings: ['identity', 'gzip'],
    max_compressed_input_bytes: 8_000_000,
    max_decompressed_input_bytes: 64_000_000,
    max_json_depth: 64,
    max_total_tokens: 2_000_000,
    max_object_members: 256,
    max_array_items: 100_000,
    max_decoded_string_bytes: 4_000_000,
    max_number_token_bytes: 128,
    max_canonical_output_bytes: 64_000_000,
    max_parse_wall_ms: 2_000,
    max_parse_cpu_ms: 1_000,
    max_parser_memory_bytes: 256_000_000,
    max_total_parser_memory_bytes: 1_000_000_000,
    max_concurrent_verification_jobs: 3,
    max_concurrent_jobs_per_principal: 1,
    max_queued_verification_jobs: 12,
    max_queued_jobs_per_principal: 4,
  };
  const profileIsConsistent = (candidate) =>
    validate(candidate) &&
    BigInt(candidate.max_concurrent_verification_jobs) *
      BigInt(candidate.max_parser_memory_bytes) <=
      BigInt(candidate.max_total_parser_memory_bytes) &&
    candidate.max_concurrent_jobs_per_principal <= candidate.max_concurrent_verification_jobs &&
    candidate.max_queued_jobs_per_principal <= candidate.max_queued_verification_jobs;
  assert.equal(profileIsConsistent(profile), true);
  assert.equal(profileIsConsistent({ ...profile, max_total_parser_memory_bytes: 100 }), false);
  assert.equal(profileIsConsistent({ ...profile, max_concurrent_jobs_per_principal: 4 }), false);
  assert.equal(profileIsConsistent({ ...profile, max_queued_jobs_per_principal: 13 }), false);
  assert.equal(validate({ ...profile, max_json_depth: 129 }), false);
  assert.equal(validate({ ...profile, max_number_token_bytes: 257 }), false);
  assert.equal(validate({ ...profile, max_parse_cpu_ms: 0 }), false);
  assert.equal(validate({ ...profile, max_concurrent_verification_jobs: 1025 }), false);
  assert.equal(validate({ ...profile, max_queued_verification_jobs: 10001 }), false);
  assert.equal(validate({ ...profile, max_parser_memory_bytes: 0 }), false);
  assert.equal(validate({ ...profile, accepted_content_encodings: ['identity', 'br'] }), false);
  assert.equal(
    validate({ ...profile, accepted_content_encodings: ['identity', 'identity'] }),
    false,
  );
  assert.equal(validate({ ...profile, operator_override: true }), false);
});

test('matches exact integer raw-token interoperability vectors', async () => {
  const vectors = JSON.parse(
    await readFile(new URL('stage5-jcs-number-token-vectors-v1.json', directory), 'utf8'),
  );
  const maximum = BigInt(vectors.maximum_absolute_integer);
  const classify = (token) => {
    const match = /^(-?)(0|[1-9][0-9]*)(?:\.([0-9]+))?(?:[eE]([+-]?[0-9]+))?$/.exec(token);
    if (!match) return { expected: 'reject', reason: 'invalid-json-number' };
    const [, sign, integer, fraction = '', exponentText = '0'] = match;
    let coefficient = BigInt(`${sign}${integer}${fraction}`);
    if (coefficient === 0n) return { expected: 'accept', canonical_number_token: '0' };
    const exponent = Number(exponentText);
    if (!Number.isSafeInteger(exponent) || Math.abs(exponent) > 1000) {
      return exponent > 0
        ? { expected: 'reject', reason: 'outside-safe-integer-range' }
        : { expected: 'reject', reason: 'not-an-exact-integer' };
    }
    const scale = fraction.length - exponent;
    if (scale > 0) {
      const divisor = 10n ** BigInt(scale);
      if (coefficient % divisor !== 0n)
        return { expected: 'reject', reason: 'not-an-exact-integer' };
      coefficient /= divisor;
    } else if (-scale > 20) {
      return { expected: 'reject', reason: 'outside-safe-integer-range' };
    } else {
      coefficient *= 10n ** BigInt(-scale);
    }
    if (coefficient < -maximum || coefficient > maximum) {
      return { expected: 'reject', reason: 'outside-safe-integer-range' };
    }
    return { expected: 'accept', canonical_number_token: coefficient.toString() };
  };
  for (const vector of vectors.cases) {
    assert.deepEqual(
      classify(vector.raw_number_token),
      {
        expected: vector.expected,
        ...(vector.expected === 'accept'
          ? { canonical_number_token: vector.canonical_number_token }
          : { reason: vector.reason }),
      },
      vector.id,
    );
  }
});

test('demonstrates raw decimal precision is lost before schema validation', () => {
  const rounded = JSON.parse('{"value":9007199254740991.1}');
  assert.equal(rounded.value, 9007199254740991);
  assert.equal(Number.isSafeInteger(rounded.value), true);
});

test('requires exact JCS-safe numeric fields in versioned wire schemas', async () => {
  const files = (await readdir(new URL('.', import.meta.url))).filter((file) =>
    file.endsWith('.schema.json'),
  );
  const violations = [];
  const visit = (value, file, path = '$') => {
    if (Array.isArray(value)) {
      value.forEach((item, index) => visit(item, file, `${path}[${index}]`));
      return;
    }
    if (!value || typeof value !== 'object') return;
    if (value.type === 'number' || (Array.isArray(value.type) && value.type.includes('number'))) {
      violations.push(
        `${file}:${path} permits floating-point JSON numbers; use a bounded integer or decimal string`,
      );
    }
    const integerType =
      value.type === 'integer' || (Array.isArray(value.type) && value.type.includes('integer'));
    if (integerType && (!Number.isSafeInteger(value.maximum) || value.maximum > 9007199254740991)) {
      violations.push(`${file}:${path} has no safe integer maximum`);
    }
    for (const [key, child] of Object.entries(value)) visit(child, file, `${path}.${key}`);
  };
  for (const file of files) {
    visit(JSON.parse(await readFile(new URL(file, directory), 'utf8')), file);
  }
  assert.deepEqual(violations, []);
});

test('accepts approval and review attestation shapes', () => {
  assert.equal(validateAttestation(approval), true, JSON.stringify(validateAttestation.errors));
  assert.equal(validateAttestation(review), true, JSON.stringify(validateAttestation.errors));
});

test('rejects role substitution, unknown fields, and circular approval bindings', () => {
  assert.equal(validateAttestation({ ...approval, unexpected: true }), false);
  assert.equal(
    validateAttestation({ ...approval, required_role: 'stage5_independent_reviewer' }),
    false,
  );
  assert.equal(validateAttestation({ ...approval, handoff_core_sha256: digest }), false);
});

test('requires complete witness binding only for dual-witness attestations', () => {
  const dualWitnessApproval = {
    ...approval,
    assurance_profile: 'dual-witness-v1',
    trust_domains: {
      ...approval.trust_domains,
      independent_witness_domain: 'witness',
    },
    witness_authority_id: 'witness-01',
    witness_root_sha256: digest,
  };
  assert.equal(
    validateAttestation(dualWitnessApproval),
    true,
    JSON.stringify(validateAttestation.errors),
  );
  assert.equal(
    validateAttestation({ ...dualWitnessApproval, trust_domains: approval.trust_domains }),
    false,
  );
});

test('accepts the versioned handoff core and requires all six deployment fact classes', () => {
  assert.equal(validateHandoffCore(handoffCore), true, JSON.stringify(validateHandoffCore.errors));
  assert.equal(
    validateHandoffCore({
      ...handoffCore,
      deployment_facts: handoffCore.deployment_facts.filter(
        (item) => item.fact_id !== 'retention-policy',
      ),
    }),
    false,
  );
  assert.equal(validateHandoffCore({ ...handoffCore, extra_claim: true }), false);
});

test('requires a witness domain when the handoff threat model includes authority compromise', () => {
  const dualWitnessCore = {
    ...handoffCore,
    assurance_profile: 'dual-witness-v1',
    compromise_in_scope: true,
    trust_domains: {
      ...handoffCore.trust_domains,
      independent_witness_domain: 'witness',
    },
  };
  assert.equal(
    validateHandoffCore(dualWitnessCore),
    true,
    JSON.stringify(validateHandoffCore.errors),
  );
  assert.equal(
    validateHandoffCore({ ...dualWitnessCore, trust_domains: handoffCore.trust_domains }),
    false,
  );
  assert.equal(validateHandoffCore({ ...handoffCore, compromise_in_scope: true }), false);
});

test('accepts explicit preflight and record-time identity source decision records', () => {
  assert.equal(
    validateIdentityDecision(preflightIdentityDecision),
    true,
    JSON.stringify(validateIdentityDecision.errors),
  );
  assert.equal(
    validateIdentityDecision(recordTimeIdentityDecision),
    true,
    JSON.stringify(validateIdentityDecision.errors),
  );
  assert.equal(
    validateIdentityDecision({ ...recordTimeIdentityDecision, challenge_nonce: 'not-allowed' }),
    false,
  );
});

test('rejects incomplete or unbounded identity decision records', () => {
  assert.equal(
    validateIdentityDecision({ ...preflightIdentityDecision, challenge_nonce: '' }),
    false,
  );
  assert.equal(
    validateIdentityDecision({ ...recordTimeIdentityDecision, authority_sequence: 0 }),
    false,
  );
});

const identityRoleChange = {
  schema: 'stage5-identity-role-change-v1',
  source_id: 'identity-source-01',
  role_change_id: 'role-change-01',
  sequence: 12,
  previous_record_sha256: digest,
  environment_id: 'stage5-prod',
  log_id: 'holdout-log-01',
  action: 'role-granted',
  target_subject_id: 'person-02',
  role: 'stage5_risk_owner',
  signing_key_id: null,
  key_fingerprint_sha256: null,
  actor_subject_id: 'identity-admin-01',
  approver_subject_id: 'identity-admin-02',
  approval: {
    approval_id: 'role-change-approval-01',
    approval_policy_id: 'role-change-policy-01',
    approval_policy_sha256: digest,
    approval_policy_revision: 4,
    approver_subject_id: 'identity-admin-02',
    approver_signing_key_id: 'identity-admin-key-02',
    approved_change_sha256: digest,
    signed_at_utc: '2026-10-23T08:59:00Z',
    signature_profile: 'ed25519-jcs-identity-role-change-approval-v1',
    signature: 'A'.repeat(86),
  },
  effective_at_utc: '2026-10-23T09:00:00Z',
  recorded_at_utc: '2026-10-23T09:00:05Z',
  reason_code: 'approved-role-assignment',
  record_sha256: digest,
  signature_profile: 'ed25519-jcs-identity-role-change-v1',
  signature_key_id: 'identity-audit-key-01',
  signature: 'A'.repeat(86),
};

test('accepts signed, scope-bound identity role-change audit records', () => {
  assert.equal(identityRoleChangeSchema !== null, true, 'identity role-change schema is missing');
  assert.equal(
    validateIdentityRoleChange(identityRoleChange),
    true,
    JSON.stringify(validateIdentityRoleChange.errors),
  );
});

test('rejects missing role-change approvers or invalid action bindings', () => {
  assert.equal(
    validateIdentityRoleChange({ ...identityRoleChange, approver_subject_id: '' }),
    false,
  );
  const { approval: _approval, ...withoutApproval } = identityRoleChange;
  assert.equal(validateIdentityRoleChange(withoutApproval), false);
  assert.equal(
    validateIdentityRoleChange({
      ...identityRoleChange,
      approval: { ...identityRoleChange.approval, approved_change_sha256: 'not-a-digest' },
    }),
    false,
  );
  assert.equal(
    validateIdentityRoleChange({
      ...identityRoleChange,
      approval: { ...identityRoleChange.approval, approval_policy_sha256: 'not-a-digest' },
    }),
    false,
  );
  assert.equal(
    validateIdentityRoleChange({
      ...identityRoleChange,
      approval: { ...identityRoleChange.approval, approval_policy_revision: 0 },
    }),
    false,
  );
  assert.equal(
    validateIdentityRoleChange({
      ...identityRoleChange,
      signature: `${'A'.repeat(85)}E`,
    }),
    false,
  );
  assert.equal(
    validateIdentityRoleChange({ ...identityRoleChange, action: 'role-granted', role: null }),
    false,
  );
  assert.equal(
    validateIdentityRoleChange({
      ...identityRoleChange,
      action: 'key-bound',
      role: 'stage5_risk_owner',
    }),
    false,
  );
  assert.equal(
    validateIdentityRoleChange({ ...identityRoleChange, credential: 'must-not-ship' }),
    false,
  );
});

test('requires key-change records to bind exactly one subject key and no role', () => {
  const keyBinding = {
    ...identityRoleChange,
    action: 'key-bound',
    role: null,
    signing_key_id: 'person-key-02',
    key_fingerprint_sha256: digest,
  };
  assert.equal(
    validateIdentityRoleChange(keyBinding),
    true,
    JSON.stringify(validateIdentityRoleChange.errors),
  );
  assert.equal(
    validateIdentityRoleChange({ ...keyBinding, action: 'role-revoked', role: null }),
    false,
  );
  assert.equal(validateIdentityRoleChange({ ...keyBinding, role: 'stage5_risk_owner' }), false);
});

const identityRoleHistoryPackage = {
  schema: 'stage5-identity-role-history-package-v1',
  source_id: 'identity-source-01',
  environment_id: 'stage5-prod',
  log_id: 'holdout-log-01',
  query: {
    subject_id: 'person-02',
    role: 'stage5_risk_owner',
    signing_key_id: null,
    challenge_nonce: 'A'.repeat(43),
  },
  history_mode: 'complete-from-genesis-v1',
  events: [
    {
      ...identityRoleChange,
      sequence: 1,
      previous_record_sha256: '0'.repeat(64),
    },
  ],
  history_head: {
    sequence: 1,
    record_sha256: digest,
    query_sha256: digest,
    observed_at_utc: '2026-10-23T09:01:00Z',
    signature_profile: 'ed25519-jcs-identity-role-history-head-v1',
    signature_key_id: 'identity-audit-key-01',
    signature: 'A'.repeat(86),
  },
};

test('accepts complete-from-genesis identity role-history package shape', () => {
  assert.equal(
    identityRoleHistoryPackageSchema !== null,
    true,
    'identity role-history package schema is missing',
  );
  assert.equal(
    validateIdentityRoleHistoryPackage(identityRoleHistoryPackage),
    true,
    JSON.stringify(validateIdentityRoleHistoryPackage.errors),
  );
});

test('rejects malformed or unsupported identity role-history package shapes', () => {
  assert.equal(
    validateIdentityRoleHistoryPackage({
      ...identityRoleHistoryPackage,
      history_head: { ...identityRoleHistoryPackage.history_head, sequence: -1 },
    }),
    false,
  );
  assert.equal(
    validateIdentityRoleHistoryPackage({
      ...identityRoleHistoryPackage,
      history_mode: 'filtered-current-state-only',
    }),
    false,
  );
  assert.equal(
    validateIdentityRoleHistoryPackage({
      ...identityRoleHistoryPackage,
      query: { ...identityRoleHistoryPackage.query, challenge_nonce: 'short' },
    }),
    false,
  );
  assert.equal(
    validateIdentityRoleHistoryPackage({
      ...identityRoleHistoryPackage,
      query: {
        ...identityRoleHistoryPackage.query,
        challenge_nonce: `${'A'.repeat(42)}B`,
      },
    }),
    false,
  );
  assert.equal(
    validateIdentityRoleHistoryPackage({ ...identityRoleHistoryPackage, cached_success: true }),
    false,
  );
});

const identityRoleChangePolicy = {
  schema: 'stage5-identity-role-change-policy-v1',
  policy_id: 'role-change-policy-01',
  version: 1,
  environment_id: 'stage5-prod',
  log_id: 'holdout-log-01',
  rules: [
    {
      action: 'role-granted',
      role: 'stage5_risk_owner',
      actor_roles: ['stage5_governance_administrator'],
      approver_roles: ['stage5_risk_owner'],
    },
    {
      action: 'role-revoked',
      role: 'stage5_risk_owner',
      actor_roles: ['stage5_governance_administrator'],
      approver_roles: ['stage5_risk_owner'],
    },
    {
      action: 'key-bound',
      role: null,
      actor_roles: ['stage5_governance_administrator'],
      approver_roles: ['stage5_risk_owner'],
    },
    {
      action: 'key-revoked',
      role: null,
      actor_roles: ['stage5_governance_administrator'],
      approver_roles: ['stage5_risk_owner'],
    },
  ],
  controls: {
    actor_approver_must_differ: true,
    target_must_differ_from_actor_and_approver: true,
    approval_must_bind_expected_head: true,
  },
  bootstrap: {
    bootstrap_record_id: 'identity-policy-bootstrap-01',
    authority_subject_id: 'root-owner-01',
    authority_key_id: 'root-owner-key-01',
    approval_sha256: digest,
    approved_at_utc: '2026-10-23T08:00:00Z',
    initial_role_changes: [
      {
        sequence: 1,
        role_change_id: 'bootstrap-admin-grant-01',
        action: 'role-granted',
        target_subject_id: 'governance-admin-01',
        role: 'stage5_governance_administrator',
        signing_key_id: null,
        key_fingerprint_sha256: null,
      },
      {
        sequence: 2,
        role_change_id: 'bootstrap-risk-owner-grant-01',
        action: 'role-granted',
        target_subject_id: 'risk-owner-01',
        role: 'stage5_risk_owner',
        signing_key_id: null,
        key_fingerprint_sha256: null,
      },
      {
        sequence: 3,
        role_change_id: 'bootstrap-risk-owner-key-01',
        action: 'key-bound',
        target_subject_id: 'risk-owner-01',
        role: null,
        signing_key_id: 'risk-owner-key-01',
        key_fingerprint_sha256: digest,
      },
    ],
  },
};

test('accepts a verifier-pinned identity role-change policy shape', () => {
  assert.equal(
    identityRoleChangePolicySchema !== null,
    true,
    'identity role-change policy schema is missing',
  );
  assert.equal(
    validateIdentityRoleChangePolicy(identityRoleChangePolicy),
    true,
    JSON.stringify(validateIdentityRoleChangePolicy.errors),
  );
});

test('rejects identity role-change policy shapes that weaken separation or action bindings', () => {
  assert.equal(
    validateIdentityRoleChangePolicy({
      ...identityRoleChangePolicy,
      controls: { ...identityRoleChangePolicy.controls, actor_approver_must_differ: false },
    }),
    false,
  );
  assert.equal(
    validateIdentityRoleChangePolicy({
      ...identityRoleChangePolicy,
      rules: [{ ...identityRoleChangePolicy.rules[0], role: null }],
    }),
    false,
  );
  assert.equal(
    validateIdentityRoleChangePolicy({
      ...identityRoleChangePolicy,
      rules: [{ ...identityRoleChangePolicy.rules[0], approver_roles: [] }],
    }),
    false,
  );
  assert.equal(
    validateIdentityRoleChangePolicy({
      ...identityRoleChangePolicy,
      bootstrap: {
        ...identityRoleChangePolicy.bootstrap,
        initial_role_changes: [
          ...identityRoleChangePolicy.bootstrap.initial_role_changes.slice(0, 2),
          {
            ...identityRoleChangePolicy.bootstrap.initial_role_changes[2],
            action: 'role-revoked',
          },
        ],
      },
    }),
    false,
  );
  assert.equal(
    validateIdentityRoleChangePolicy({
      ...identityRoleChangePolicy,
      bootstrap: {
        ...identityRoleChangePolicy.bootstrap,
        initial_role_changes: identityRoleChangePolicy.bootstrap.initial_role_changes.map(
          (change) =>
            change.action === 'key-bound'
              ? { ...change, action: 'role-granted', role: 'stage5_independent_reviewer' }
              : change,
        ),
      },
    }),
    false,
  );
  const { initial_role_changes: _initialRoleChanges, ...bootstrapWithoutInitial } =
    identityRoleChangePolicy.bootstrap;
  assert.equal(
    validateIdentityRoleChangePolicy({
      ...identityRoleChangePolicy,
      bootstrap: bootstrapWithoutInitial,
    }),
    false,
  );
  assert.equal(
    validateIdentityRoleChangePolicy({ ...identityRoleChangePolicy, unreviewed: true }),
    false,
  );
  assert.equal(
    validateIdentityRoleChangePolicy({ ...identityRoleChangePolicy, version: 2 }),
    false,
  );
  assert.equal(
    validateIdentityRoleChangePolicy({
      ...identityRoleChangePolicy,
      version: 2,
      supersedes_policy_sha256: digest,
      transition_record_id: 'policy-transition-02',
      transition_approval_sha256: digest,
    }),
    true,
  );
});

const identityRoleChangePolicyTransition = {
  schema: 'stage5-identity-role-change-policy-transition-v1',
  transition_id: 'policy-transition-02',
  environment_id: 'stage5-prod',
  log_id: 'holdout-log-01',
  policy_id: 'role-change-policy-01',
  previous_policy_version: 1,
  previous_policy_sha256: digest,
  next_policy_version: 2,
  next_policy_sha256: 'b'.repeat(64),
  expected_pin_revision: 4,
  previous_pin_sha256: digest,
  actor_subject_id: 'pin-operator-01',
  transition_approval: {
    approval_id: 'policy-transition-approval-02',
    approver_subject_id: 'risk-owner-01',
    approver_signing_key_id: 'risk-owner-key-01',
    approved_intent_sha256: 'c'.repeat(64),
    signed_at_utc: '2026-10-23T10:00:00Z',
    signature_profile: 'ed25519-jcs-identity-policy-transition-approval-v1',
    signature: 'A'.repeat(86),
  },
  pin_update: {
    pin_authority_id: 'verifier-pin-authority-01',
    pin_revision: 5,
    transition_record_id: 'policy-transition-02',
    transition_approval_sha256: 'c'.repeat(64),
    previous_pin_sha256: digest,
    next_pin_sha256: 'b'.repeat(64),
    applied_at_utc: '2026-10-23T10:00:05Z',
    signature_profile: 'ed25519-jcs-verifier-policy-pin-update-v1',
    signing_key_id: 'verifier-pin-key-01',
    signature: `${'A'.repeat(85)}Q`,
  },
  recorded_at_utc: '2026-10-23T10:00:06Z',
  record_sha256: 'd'.repeat(64),
  signature_profile: 'ed25519-jcs-identity-policy-transition-v1',
  signing_key_id: 'identity-audit-key-01',
  signature: `${'A'.repeat(85)}w`,
};

test('accepts signed policy transition and separately authorized verifier pin update shapes', () => {
  assert.equal(
    identityRoleChangePolicyTransitionSchema !== null,
    true,
    'policy transition schema is missing',
  );
  assert.equal(
    validateIdentityRoleChangePolicyTransition(identityRoleChangePolicyTransition),
    true,
    JSON.stringify(validateIdentityRoleChangePolicyTransition.errors),
  );
});

test('rejects incomplete policy transition or verifier pin update shapes', () => {
  assert.equal(
    validateIdentityRoleChangePolicyTransition({
      ...identityRoleChangePolicyTransition,
      transition_approval: {
        ...identityRoleChangePolicyTransition.transition_approval,
        signature_profile: 'unbound',
      },
    }),
    false,
  );
  assert.equal(
    validateIdentityRoleChangePolicyTransition({
      ...identityRoleChangePolicyTransition,
      pin_update: { ...identityRoleChangePolicyTransition.pin_update, next_pin_sha256: 'bad' },
    }),
    false,
  );
  assert.equal(
    validateIdentityRoleChangePolicyTransition({
      ...identityRoleChangePolicyTransition,
      pin_update: {
        ...identityRoleChangePolicyTransition.pin_update,
        signature: `${'A'.repeat(85)}E`,
      },
    }),
    false,
  );
  const { pin_update: _pinUpdate, ...withoutPinUpdate } = identityRoleChangePolicyTransition;
  assert.equal(validateIdentityRoleChangePolicyTransition(withoutPinUpdate), false);
  assert.equal(
    validateIdentityRoleChangePolicyTransition({
      ...identityRoleChangePolicyTransition,
      untrusted_payload: true,
    }),
    false,
  );
});

test('accepts the strict governance object and identity decision references', () => {
  assert.equal(
    validateGovernanceObject(governanceObject),
    true,
    JSON.stringify(validateGovernanceObject.errors),
  );
  assert.equal(
    validateGovernanceObject({
      ...governanceObject,
      identity_decisions: governanceObject.identity_decisions.map((entry) =>
        entry.phase === 'preflight' ? { ...entry, credential: 'must-not-ship' } : entry,
      ),
    }),
    false,
  );
});

test('requires every identity decision reference to have a strict, credential-free shape', () => {
  assert.equal(
    validateGovernanceObject({
      ...governanceObject,
      identity_decisions: governanceObject.identity_decisions.slice(1),
    }),
    false,
  );
  assert.equal(
    validateGovernanceObject({
      ...governanceObject,
      identity_decisions: governanceObject.identity_decisions.map((entry) =>
        entry.phase === 'preflight' ? { ...entry, phase: 'post-commit' } : entry,
      ),
    }),
    false,
  );
});

test('accepts approval, review, and revocation event payloads', () => {
  for (const event of [approvalEvent, reviewEvent, revocationEvent]) {
    assert.equal(validateEvent(event), true, JSON.stringify(validateEvent.errors));
  }
});

test('rejects unknown event fields and unbounded revocation reason text', () => {
  assert.equal(validateEvent({ ...approvalEvent, unexpected: true }), false);
  assert.equal(validateEvent({ ...revocationEvent, reason_code: 'free-form narrative' }), false);
  assert.equal(validateEvent({ ...revocationEvent, reason_code: 'key-compromise' }), false);
});

test('accepts the complete v7 evidence envelope and rejects unknown or derived fields', () => {
  const envelope = makeV7Envelope(governanceObject);
  assert.equal(validateV7Envelope(envelope), true, JSON.stringify(validateV7Envelope.errors));
  const withoutLimitsBinding = { ...envelope.frozen_spec };
  delete withoutLimitsBinding.verifier_input_limits_sha256;
  assert.equal(validateV7Envelope({ ...envelope, frozen_spec: withoutLimitsBinding }), false);
  assert.equal(validateV7Envelope({ ...envelope, producer_note: 'unbound' }), false);
  assert.equal(
    validateV7Envelope({ ...envelope, acceptance_readiness: 'ready-for-human-acceptance' }),
    false,
  );
  assert.equal(
    validateV7Envelope({ ...envelope, schema: 'official-blind-holdout-evidence-envelope-v6' }),
    false,
  );
  assert.equal(
    validateV7Envelope({
      ...envelope,
      registry: { ...envelope.registry, arbitrary_event_metadata: true },
    }),
    false,
  );
  assert.equal(
    validateV7Envelope({
      ...envelope,
      registry: { ...envelope.registry, events: [v7EventSummary] },
    }),
    false,
  );
  assert.equal(
    validateV7Envelope({
      ...envelope,
      registry: {
        ...envelope.registry,
        receipt_chain: [
          {
            ...envelope.registry.receipt_chain[0],
            event: {
              ...v7EventEnvelope,
              event_type: 'reserved',
            },
          },
        ],
      },
    }),
    false,
  );
});

test('requires a frozen early-failure policy for budget and deadline claims', () => {
  const envelope = makeV7Envelope(governanceObject);
  assert.equal(validateV7Envelope(envelope), true, JSON.stringify(validateV7Envelope.errors));
  const withoutEarlyFailurePolicy = { ...envelope.frozen_spec };
  delete withoutEarlyFailurePolicy.early_failure_policy;
  assert.equal(validateV7Envelope({ ...envelope, frozen_spec: withoutEarlyFailurePolicy }), false);
  assert.equal(
    validateV7Envelope({
      ...envelope,
      frozen_spec: {
        ...envelope.frozen_spec,
        early_failure_policy: { budget_violation: 'fail-before-scoring' },
      },
    }),
    false,
  );
});

test('requires failed terminal receipts to bind frozen gate and closed runtime evidence', () => {
  const envelope = makeV7Envelope(governanceObject);
  const failedEvent = {
    ...v7EventEnvelope,
    sequence: 3,
    event_id: 'evt-failed',
    event_type: 'failed',
    payload: {
      ...v7EventSummary,
      type: 'failed',
      report_sha256: digest,
      early_failure_gate: 'budget_violation',
      runtime_audit_sha256: digest,
      runtime_stop_record_sha256: digest,
      usage_ledger_sha256: digest,
      usage_ledger_closed_sequence: 3,
      usage_ledger_closed_head_sha256: digest,
    },
  };
  const failedReceipt = {
    ...v7Receipt,
    sequence: 3,
    event_id: 'evt-failed',
    event_hash: digest,
  };
  envelope.registry.receipt_chain = [{ event: failedEvent, receipt: failedReceipt }];
  assert.equal(validateV7Envelope(envelope), true, JSON.stringify(validateV7Envelope.errors));
  delete failedEvent.payload.usage_ledger_closed_head_sha256;
  assert.equal(validateV7Envelope(envelope), false);
});

test('accepts an incomplete v7 run with no terminal review or handoff core', () => {
  const envelope = makeV7Envelope(governanceObject);
  envelope.status = 'incomplete';
  envelope.outcome = 'incomplete';
  envelope.authorization_event_id = 'evt-authorized';
  envelope.reservation_event_id = 'evt-reserved';
  envelope.terminal_event_id = null;
  envelope.results_sha256 = null;
  envelope.output_sha256 = null;
  envelope.output_seal_id = null;
  envelope.metrics = null;
  envelope.metrics_sha256 = null;
  envelope.independent_task_count = null;
  envelope.sample_size = null;
  envelope.passed_tasks = null;
  envelope.pass_rate_bps = null;
  envelope.quality_decision = 'unverified';
  envelope.token_usage = null;
  envelope.executed_at = null;
  envelope.cost_status = 'unknown';
  envelope.budget.actual_usd = null;
  envelope.governance.review_attestation = null;
  envelope.governance.review_event_id = null;
  envelope.governance.handoff_core = null;
  envelope.governance.handoff_core_sha256 = null;
  envelope.governance.identity_decisions = envelope.governance.identity_decisions.filter(
    (entry) => entry.event_id === envelope.governance.approval_event_id,
  );
  assert.equal(validateV7Envelope(envelope), true, JSON.stringify(validateV7Envelope.errors));
});

test('accepts a signed verifier decision receipt shape', async () => {
  assert.equal(validateDecision(verifierDecision), true, JSON.stringify(validateDecision.errors));
  const vectorDocument = JSON.parse(
    await readFile(new URL('stage5-decision-signature-vectors-v1.json', directory), 'utf8'),
  );
  assert.equal(
    validateDecision({
      ...vectorDocument.vector.message,
      signature: vectorDocument.vector.signature_base64url,
    }),
    true,
    JSON.stringify(validateDecision.errors),
  );
  assert.equal(
    validateDecision({
      ...verifierDecision,
      governance_authorization: 'revoked',
      acceptance_readiness: 'not-eligible',
    }),
    true,
    JSON.stringify(validateDecision.errors),
  );
});

test('allows audit receipts with unavailable sources but requires trust heads for eligible decisions', () => {
  const unverified = {
    ...verifierDecision,
    governance_authorization: 'unverified',
    acceptance_readiness: 'unverified',
    key_status_sequence: null,
    usage_trust_bundle_sha256: null,
    usage_key_status_sequence: null,
    usage_ledger_closed_sequence: null,
    usage_ledger_closed_head_sha256: null,
  };
  assert.equal(validateDecision(unverified), true, JSON.stringify(validateDecision.errors));

  const unavailableDualWitness = {
    ...unverified,
    assurance_profile: 'dual-witness-v1',
  };
  assert.equal(
    validateDecision(unavailableDualWitness),
    true,
    JSON.stringify(validateDecision.errors),
  );

  const missingKeyStatus = { ...verifierDecision, key_status_sequence: null };
  assert.equal(validateDecision(missingKeyStatus), false);
  assert.equal(
    validateDecision({ ...verifierDecision, usage_ledger_closed_head_sha256: null }),
    false,
  );
  assert.equal(validateDecision({ ...verifierDecision, usage_key_status_sequence: null }), false);
  assert.equal(validateDecision({ ...verifierDecision, usage_trust_bundle_sha256: null }), false);
  assert.equal(
    validateDecision({ ...verifierDecision, usage_ledger_closed_sequence: null }),
    false,
  );

  const dualWitnessDecision = {
    ...verifierDecision,
    assurance_profile: 'dual-witness-v1',
    witness_head_sha256: digest,
  };
  assert.equal(
    validateDecision(dualWitnessDecision),
    true,
    JSON.stringify(validateDecision.errors),
  );
  assert.equal(validateDecision({ ...dualWitnessDecision, witness_head_sha256: undefined }), false);
  assert.equal(
    validateDecision({
      ...dualWitnessDecision,
      acceptance_readiness: 'not-eligible',
      witness_head_sha256: undefined,
    }),
    false,
  );
  assert.equal(
    validateDecision({ ...dualWitnessDecision, governance_authorization: 'trusted' }),
    false,
  );
  assert.equal(
    validateDecision({ ...verifierDecision, assurance_profile: 'local-reference' }),
    false,
  );
  assert.equal(
    validateDecision({
      ...verifierDecision,
      assurance_profile: 'local-reference',
      acceptance_readiness: 'not-eligible',
    }),
    false,
  );
  assert.equal(
    validateDecision({
      ...verifierDecision,
      assurance_profile: 'local-reference',
      acceptance_readiness: 'unverified',
      governance_authorization: 'unverified',
      usage_trust_bundle_sha256: null,
      usage_key_status_sequence: null,
      usage_ledger_closed_sequence: null,
      usage_ledger_closed_head_sha256: null,
    }),
    true,
  );
  assert.equal(validateDecision({ ...verifierDecision, extra: 'accepted' }), false);
});

test('validates scoped identity-source decisions for downstream acceptance and release', () => {
  const identityDecision = {
    schema: 'stage5-decision-consumer-identity-decision-v1',
    source_id: 'identity-source',
    decision_ref: 'identity:consumer-decision:01',
    decision_log_id: 'decision-log',
    record_type: 'human-acceptance',
    record_id: 'acceptance-01',
    environment_id: 'stage5-prod',
    authorization_intent_sha256: digest,
    subject_id: 'subject-acceptor',
    signing_key_id: 'acceptor-key',
    key_fingerprint_sha256: digest,
    required_role: 'stage5_acceptance_authority',
    role_grant_id: 'grant-acceptor',
    role_valid_now: true,
    credential_state_now: 'active',
    revocation_sequence: 5,
    decision: 'allow',
    challenge_nonce: 'nonce-with-more-than-128-bits-randomness',
    policy_version: 'identity-policy-v1',
    issued_at_utc: '2026-10-23T10:00:00Z',
    valid_until_utc: '2026-10-23T10:00:30Z',
    decision_sha256: digest,
  };
  assert.equal(
    validateDecisionConsumerIdentity(identityDecision),
    true,
    JSON.stringify(validateDecisionConsumerIdentity.errors),
  );
  assert.equal(validateDecisionConsumerIdentity({ ...identityDecision, decision: 'deny' }), false);
  assert.equal(
    validateDecisionConsumerIdentity({
      ...identityDecision,
      authorization_intent_sha256: undefined,
    }),
    false,
  );
  assert.equal(
    validateDecisionConsumerIdentity({ ...identityDecision, challenge_nonce: 'short' }),
    false,
  );
  assert.equal(validateDecisionConsumerIdentity({ ...identityDecision, extra: 'unbound' }), false);
});

test('validates the strict candidate build-provenance statement shape', async () => {
  const schema = JSON.parse(
    await readFile(new URL('p5-build-provenance-v1.schema.json', directory), 'utf8'),
  );
  const validate = new Ajv2020({ allErrors: true, strict: true }).compile(schema);
  const sha256 = 'a'.repeat(64);
  const statement = {
    build_id: 'build-01',
    repository_id: 'https://example.invalid/repo',
    source_commit: 'b'.repeat(40),
    source_tree_sha256: sha256,
    materials: [{ uri: 'repo://src/main.py', kind: 'source-file', sha256 }],
    materials_sha256: sha256,
    build_recipe_sha256: sha256,
    invocation_sha256: sha256,
    builder_id: 'ci://builder/prod',
    builder_image_digest: `sha256:${sha256}`,
    target_platform: { os: 'linux', architecture: 'amd64' },
    oci_index_digest: `sha256:${sha256}`,
    platform_manifest_digest: `sha256:${sha256}`,
    started_at_utc: '2026-10-23T10:00:00Z',
    finished_at_utc: '2026-10-23T10:01:00Z',
    hash_profile: 'jcs-rfc8785-v1',
    signature_profile: 'ed25519-jcs-p5-build-provenance-v1',
    signing_key_id: 'builder-key-01',
  };
  const envelope = {
    schema: 'p5-build-provenance-envelope-v1',
    statement,
    signature: 'A'.repeat(86),
  };
  assert.equal(validate(envelope), true, JSON.stringify(validate.errors));
  assert.equal(validate({ ...envelope, extra: true }), false);
  assert.equal(
    validate({
      ...envelope,
      statement: {
        ...statement,
        materials: [{ uri: 'repo://source file', kind: 'source-file', sha256 }],
      },
    }),
    false,
  );
  assert.equal(
    validate({
      ...envelope,
      statement: { ...statement, materials: [{ uri: 'repo://src/main.py', sha256 }] },
    }),
    false,
  );
  assert.equal(
    validate({ ...envelope, statement: { ...statement, hash_profile: 'unknown' } }),
    false,
  );
});

test('validates the signed runtime image-admission statement shape', async () => {
  const schema = JSON.parse(
    await readFile(new URL('p5-runtime-image-admission-v1.schema.json', directory), 'utf8'),
  );
  const validate = new Ajv2020({ allErrors: true, strict: true }).compile(schema);
  const sha256 = 'a'.repeat(64);
  const admission = {
    admission_id: 'image-admission-01',
    preflight_request_id: 'image-preflight-req-01',
    preflight_nonce: 'abcdefghijklmnopqrstuvwx12345678',
    run_id: 'holdout-run-01',
    candidate_hash: sha256,
    frozen_spec_sha256: sha256,
    build_provenance_sha256: sha256,
    runtime_id: 'isolated-runtime-01',
    target_platform: { os: 'linux', architecture: 'amd64' },
    oci_index_digest: `sha256:${sha256}`,
    platform_manifest_digest: `sha256:${sha256}`,
    resolved_at_utc: '2026-10-23T10:00:00Z',
    valid_until_utc: '2026-10-23T10:00:30Z',
    signature_profile: 'ed25519-jcs-p5-runtime-image-admission-v1',
    signing_key_id: 'runtime-supervisor-key-01',
  };
  const envelope = {
    schema: 'p5-runtime-image-admission-envelope-v1',
    admission,
    signature: 'A'.repeat(86),
  };
  assert.equal(validate(envelope), true, JSON.stringify(validate.errors));
  assert.equal(validate({ ...envelope, extra: true }), false);
  assert.equal(
    validate({ ...envelope, admission: { ...admission, preflight_nonce: 'short' } }),
    false,
  );
  assert.equal(
    validate({
      ...envelope,
      admission: { ...admission, signature_profile: 'unknown-profile' },
    }),
    false,
  );
  assert.equal(
    validate({
      ...envelope,
      admission: {
        ...admission,
        target_platform: { os: 'linux', architecture: 'amd64', extra: true },
      },
    }),
    false,
  );
});

test('validates the strict holdout session redemption request shape', async () => {
  const schema = JSON.parse(
    await readFile(new URL('p5-holdout-session-open-request-v1.schema.json', directory), 'utf8'),
  );
  const capabilityGrantSchema = JSON.parse(
    await readFile(new URL('p5-holdout-capability-grant-v1.schema.json', directory), 'utf8'),
  );
  const ajv = new Ajv2020({ allErrors: true, strict: true });
  ajv.addSchema(capabilityGrantSchema);
  const validate = ajv.compile(schema);
  const validateGrant = ajv.getSchema(capabilityGrantSchema.$id);
  const sha256 = 'a'.repeat(64);
  const grant = {
    capability_id: 'cap-01',
    token_sha256: sha256,
    run_id: 'holdout-run-01',
    reservation_event_id: 'reserve-01',
    frozen_spec_sha256: sha256,
    candidate_hash: sha256,
    build_provenance_sha256: sha256,
    runtime_admission_sha256: sha256,
    platform_manifest_digest: `sha256:${sha256}`,
    runtime_id: 'isolated-runtime-01',
    runtime_subject: 'spiffe://stage5/runtime/01',
    custodian_audience: 'holdout-custodian-prod',
    dataset_sha256: sha256,
    session_policy_sha256: sha256,
    capability_expires_at_utc: '2026-10-23T10:10:00Z',
    max_attempts: 12,
    operation: 'read_next_attempt',
    scope_sha256: sha256,
    issued_at_utc: '2026-10-23T10:00:00Z',
    signature_profile: 'ed25519-jcs-p5-holdout-capability-grant-v1',
    signing_key_id: 'registry-capability-key-01',
  };
  const capabilityGrant = {
    schema: 'p5-holdout-capability-grant-envelope-v1',
    grant,
    signature: 'A'.repeat(86),
  };
  assert.equal(validateGrant(capabilityGrant), true);
  assert.equal(
    validateGrant({ ...capabilityGrant, grant: { ...grant, signature_profile: 'unknown' } }),
    false,
  );
  assert.equal(
    validateGrant({ ...capabilityGrant, grant: { ...grant, token_sha256: 'bad' } }),
    false,
  );
  assert.equal(validateGrant({ ...capabilityGrant, extra: true }), false);
  const redemption = {
    capability_id: 'cap-01',
    capability_token: 'A'.repeat(43),
    capability_grant: capabilityGrant,
    redeem_request_id: 'redeem-01',
    run_id: 'holdout-run-01',
    reservation_event_id: 'reserve-01',
    frozen_spec_sha256: sha256,
    candidate_hash: sha256,
    build_provenance_sha256: sha256,
    runtime_admission_sha256: sha256,
    platform_manifest_digest: `sha256:${sha256}`,
    runtime_id: 'isolated-runtime-01',
    runtime_subject: 'spiffe://stage5/runtime/01',
    custodian_audience: 'holdout-custodian-prod',
    dataset_sha256: sha256,
    session_policy_sha256: sha256,
    capability_expires_at_utc: '2026-10-23T10:10:00Z',
    max_attempts: 12,
    operation: 'read_next_attempt',
    scope_sha256: sha256,
  };
  const request = { schema: 'p5-holdout-session-open-request-v1', redemption };
  assert.equal(validate(request), true, JSON.stringify(validate.errors));
  assert.equal(validate({ ...request, extra: true }), false);
  assert.equal(
    validate({ ...request, redemption: { ...redemption, capability_token: 'short' } }),
    false,
  );
  assert.equal(
    validate({ ...request, redemption: { ...redemption, capability_token: `${'A'.repeat(42)}B` } }),
    false,
  );
  assert.equal(
    validate({ ...request, redemption: { ...redemption, operation: 'read_labels' } }),
    false,
  );
  assert.equal(validate({ ...request, redemption: { ...redemption, max_attempts: 0 } }), false);
  assert.equal(
    validate({ ...request, redemption: { ...redemption, candidate_hash: 'bad' } }),
    false,
  );
});

test('validates the signed custodian capability lifecycle event shapes', async () => {
  const schema = JSON.parse(
    await readFile(new URL('p5-holdout-custodian-event-v1.schema.json', directory), 'utf8'),
  );
  const validate = new Ajv2020({
    allErrors: true,
    strict: true,
    strictRequired: false,
  }).compile(schema);
  const sha256 = 'a'.repeat(64);
  const baseEvent = {
    event_id: 'custodian-event-01',
    event_type: 'capability-redeemed',
    custodian_id: 'holdout-custodian-prod',
    custodian_log_id: 'holdout-log-01',
    environment_id: 'stage5-prod',
    run_id: 'holdout-run-01',
    reservation_event_id: 'reserve-01',
    capability_id: 'cap-01',
    capability_grant_sha256: sha256,
    scope_sha256: sha256,
    runtime_id: 'isolated-runtime-01',
    runtime_subject: 'spiffe://stage5/runtime/01',
    session_id: 'session-01',
    redeem_request_id: 'redeem-01',
    sequence: 1,
    previous_event_sha256: '0'.repeat(64),
    recorded_at_utc: '2026-10-23T10:01:00Z',
    signature_profile: 'ed25519-jcs-p5-holdout-custodian-event-v1',
    signing_key_id: 'custodian-key-01',
  };
  const envelope = {
    schema: 'p5-holdout-custodian-event-envelope-v1',
    event: baseEvent,
    signature: 'A'.repeat(86),
  };
  assert.equal(validate(envelope), true, JSON.stringify(validate.errors));
  const unredeemedBase = Object.fromEntries(
    Object.entries(baseEvent).filter(
      ([key]) => key !== 'session_id' && key !== 'redeem_request_id',
    ),
  );
  const revoked = {
    ...envelope,
    event: {
      ...unredeemedBase,
      event_type: 'capability-revoked',
      revocation_request_id: 'revoke-01',
      reason_code: 'recovery-no-start',
    },
  };
  assert.equal(validate(revoked), true, JSON.stringify(validate.errors));
  const expired = {
    ...envelope,
    event: { ...unredeemedBase, event_type: 'capability-expired', reason_code: 'run-deadline' },
  };
  assert.equal(validate(expired), true, JSON.stringify(validate.errors));
  assert.equal(
    validate({ ...expired, event: { ...expired.event, reason_code: 'attempt-limit-reached' } }),
    false,
  );
  assert.equal(
    validate({
      ...revoked,
      event: { ...revoked.event, reason_code: 'normal-completion' },
    }),
    false,
  );
  assert.equal(
    validate({ ...envelope, event: { ...baseEvent, event_type: 'capability-revoked' } }),
    false,
  );
  assert.equal(validate({ ...envelope, event: { ...baseEvent, sequence: 0 } }), false);
  assert.equal(
    validate({ ...envelope, event: { ...baseEvent, capability_token: 'leaked' } }),
    false,
  );
  assert.equal(validate({ ...envelope, event: { ...baseEvent, reason_code: 'arbitrary' } }), false);
});

test('requires a stable close request id for custodian session closure', async () => {
  const schema = JSON.parse(
    await readFile(new URL('p5-holdout-custodian-event-v1.schema.json', directory), 'utf8'),
  );
  const validate = new Ajv2020({
    allErrors: true,
    strict: true,
    strictRequired: false,
  }).compile(schema);
  const sha256 = 'c'.repeat(64);
  const event = {
    event_id: 'custodian-event-closed',
    event_type: 'session-closed',
    custodian_id: 'holdout-custodian-prod',
    custodian_log_id: 'holdout-log-01',
    environment_id: 'stage5-prod',
    run_id: 'holdout-run-01',
    reservation_event_id: 'reserve-01',
    capability_id: 'cap-01',
    capability_grant_sha256: sha256,
    scope_sha256: sha256,
    runtime_id: 'isolated-runtime-01',
    runtime_subject: 'spiffe://stage5/runtime/01',
    session_id: 'session-01',
    close_request_id: 'close-01',
    reason_code: 'normal-completion',
    sequence: 3,
    previous_event_sha256: sha256,
    recorded_at_utc: '2026-10-23T10:04:00Z',
    signature_profile: 'ed25519-jcs-p5-holdout-custodian-event-v1',
    signing_key_id: 'custodian-key-01',
  };
  const envelope = {
    schema: 'p5-holdout-custodian-event-envelope-v1',
    event,
    signature: 'A'.repeat(86),
  };
  assert.equal(validate(envelope), true, JSON.stringify(validate.errors));
  assert.equal(
    validate({
      ...envelope,
      event: Object.fromEntries(
        Object.entries(event).filter(([key]) => key !== 'close_request_id'),
      ),
    }),
    false,
  );
});

test('validates the signed output seal binding to closed session, runtime, and usage ledger', async () => {
  const schema = JSON.parse(
    await readFile(new URL('p5-holdout-output-seal-v1.schema.json', directory), 'utf8'),
  );
  const validate = new Ajv2020({
    allErrors: true,
    strict: true,
    strictRequired: false,
  }).compile(schema);
  const sha256 = 'b'.repeat(64);
  const envelope = {
    schema: 'p5-holdout-output-seal-envelope-v1',
    output_seal: {
      seal_id: 'seal-01',
      close_request_id: 'close-01',
      custodian_id: 'holdout-custodian-prod',
      custodian_log_id: 'holdout-log-01',
      environment_id: 'stage5-prod',
      run_id: 'holdout-run-01',
      reservation_event_id: 'reserve-01',
      frozen_spec_sha256: sha256,
      candidate_sha256: sha256,
      runtime_admission_sha256: sha256,
      runtime_image_sha256: sha256,
      dataset_sha256: sha256,
      capability_id: 'cap-01',
      capability_grant_sha256: sha256,
      scope_sha256: sha256,
      runtime_id: 'isolated-runtime-01',
      runtime_subject: 'spiffe://stage5/runtime/01',
      session_id: 'session-01',
      session_closed_event_sha256: sha256,
      runtime_stop_record_sha256: sha256,
      usage_ledger_id: 'usage-ledger-01',
      usage_closure_sha256: sha256,
      usage_ledger_closed_sequence: 8,
      usage_ledger_closed_head_sha256: sha256,
      output_manifest_sha256: sha256,
      attempt_count: 12,
      sealed_at_utc: '2026-10-23T10:05:00Z',
      signature_profile: 'ed25519-jcs-p5-holdout-output-seal-v1',
      signing_key_id: 'custodian-key-01',
    },
    signature: 'A'.repeat(86),
  };
  assert.equal(validate(envelope), true, JSON.stringify(validate.errors));
  assert.equal(
    validate({
      ...envelope,
      output_seal: { ...envelope.output_seal, usage_ledger_closed_sequence: -1 },
    }),
    false,
  );
  assert.equal(
    validate({
      ...envelope,
      output_seal: { ...envelope.output_seal, output_manifest_sha256: 'bad' },
    }),
    false,
  );
  assert.equal(
    validate({
      ...envelope,
      output_seal: { ...envelope.output_seal, leaked_capability: 'secret' },
    }),
    false,
  );
});

test('validates immutable runtime provider-call usage transitions', async () => {
  const schema = JSON.parse(
    await readFile(new URL('p5-runtime-usage-entry-v1.schema.json', directory), 'utf8'),
  );
  const validate = new Ajv2020({
    allErrors: true,
    strict: true,
    strictRequired: false,
  }).compile(schema);
  const sha256 = 'd'.repeat(64);
  const entry = {
    entry_id: 'usage-entry-01',
    idempotency_key: 'usage-idem-01',
    environment_id: 'stage5-prod',
    usage_ledger_id: 'usage-ledger-01',
    run_id: 'holdout-run-01',
    reservation_event_id: 'reserve-01',
    frozen_spec_sha256: sha256,
    candidate_sha256: sha256,
    runtime_admission_sha256: sha256,
    runtime_image_sha256: sha256,
    dataset_sha256: sha256,
    runtime_id: 'runtime-01',
    runtime_subject: 'spiffe://stage5/runtime/01',
    supervisor_subject: 'spiffe://stage5/supervisor/01',
    attempt_id: 'attempt-01',
    provider_call_id: 'provider-call-01',
    provider_id: 'provider-a',
    model_id: 'model-a',
    state: 'prepared',
    transition_basis: 'durable-before-dispatch',
    request_sha256: sha256,
    sequence: 1,
    previous_entry_sha256: '0'.repeat(64),
    committed_at_utc: '2026-10-23T10:01:00Z',
    signature_profile: 'ed25519-jcs-p5-runtime-usage-entry-v1',
    signing_key_id: 'usage-key-01',
  };
  const envelope = {
    schema: 'p5-runtime-usage-entry-envelope-v1',
    entry,
    signature: 'A'.repeat(86),
  };
  assert.equal(validate(envelope), true, JSON.stringify(validate.errors));
  const responded = {
    ...envelope,
    entry: {
      ...entry,
      entry_id: 'usage-entry-03',
      idempotency_key: 'usage-idem-03',
      state: 'responded',
      previous_call_state: 'unknown',
      transition_basis: 'authoritative-reconciliation',
      terminalization_phase: 'post-stop',
      runtime_stop_record_sha256: sha256,
      response_sha256: sha256,
      usage_status: 'known',
      usage: { input_tokens: '120', output_tokens: '42' },
      duration: {
        clock_id: 'supervisor-boot-01',
        start_monotonic_ns: '500000000',
        end_monotonic_ns: '900000000',
      },
      reconciles_entry_id: 'usage-entry-02',
      sequence: 3,
      previous_entry_sha256: sha256,
    },
  };
  assert.equal(validate(responded), true, JSON.stringify(validate.errors));
  assert.equal(
    validate({
      ...responded,
      entry: {
        ...responded.entry,
        previous_call_state: 'sent',
        transition_basis: 'timeout-or-crash',
      },
    }),
    false,
  );
  assert.equal(validate({ ...envelope, entry: { ...entry, state: 'sent' } }), false);
  const postStopWithoutProof = {
    ...responded,
    entry: Object.fromEntries(
      Object.entries(responded.entry).filter(([key]) => key !== 'runtime_stop_record_sha256'),
    ),
  };
  assert.equal(validate(postStopWithoutProof), false);
  const cancelled = {
    ...envelope,
    entry: {
      ...entry,
      entry_id: 'usage-entry-02',
      idempotency_key: 'usage-idem-02',
      state: 'cancelled',
      previous_call_state: 'prepared',
      transition_basis: 'proof-not-sent',
      terminalization_phase: 'pre-stop',
      sequence: 2,
      previous_entry_sha256: sha256,
    },
  };
  assert.equal(validate(cancelled), true, JSON.stringify(validate.errors));
  const notExecuted = {
    ...envelope,
    entry: {
      ...entry,
      entry_id: 'usage-entry-03',
      idempotency_key: 'usage-idem-03',
      state: 'confirmed-not-executed',
      previous_call_state: 'unknown',
      transition_basis: 'authoritative-no-execution',
      terminalization_phase: 'pre-stop',
      response_sha256: sha256,
      usage_status: 'not-applicable',
      reconciles_entry_id: 'usage-entry-02',
      sequence: 3,
      previous_entry_sha256: sha256,
    },
  };
  assert.equal(validate(notExecuted), true, JSON.stringify(validate.errors));
});

test('validates usage closure binding and operation completeness state', async () => {
  const schema = JSON.parse(
    await readFile(new URL('p5-runtime-usage-closure-v1.schema.json', directory), 'utf8'),
  );
  const validate = new Ajv2020({
    allErrors: true,
    strict: true,
    strictRequired: false,
  }).compile(schema);
  const sha256 = 'e'.repeat(64);
  const envelope = {
    schema: 'p5-runtime-usage-closure-envelope-v1',
    closure: {
      closure_id: 'usage-close-01',
      environment_id: 'stage5-prod',
      usage_ledger_id: 'usage-ledger-01',
      run_id: 'holdout-run-01',
      reservation_event_id: 'reserve-01',
      frozen_spec_sha256: sha256,
      candidate_sha256: sha256,
      runtime_admission_sha256: sha256,
      runtime_image_sha256: sha256,
      dataset_sha256: sha256,
      runtime_id: 'runtime-01',
      runtime_subject: 'spiffe://stage5/runtime/01',
      supervisor_subject: 'spiffe://stage5/supervisor/01',
      operation_state: 'all-terminal',
      provider_call_count: 4,
      terminal_provider_call_count: 4,
      unresolved_provider_call_count: 0,
      closed_sequence: 12,
      closed_head_sha256: sha256,
      runtime_stop_record_sha256: sha256,
      closed_at_utc: '2026-10-23T10:05:00Z',
      signature_profile: 'ed25519-jcs-p5-runtime-usage-closure-v1',
      signing_key_id: 'usage-key-01',
    },
    signature: 'A'.repeat(86),
  };
  assert.equal(validate(envelope), true, JSON.stringify(validate.errors));
  assert.equal(
    validate({
      ...envelope,
      closure: { ...envelope.closure, unresolved_provider_call_count: 1 },
    }),
    false,
  );
  assert.equal(
    validate({
      ...envelope,
      closure: {
        ...envelope.closure,
        operation_state: 'incomplete',
        unresolved_provider_call_count: 0,
      },
    }),
    false,
  );
  assert.equal(
    validate({
      ...envelope,
      closure: {
        ...envelope.closure,
        closed_sequence: 0,
        closed_head_sha256: sha256,
      },
    }),
    false,
  );
});

test('validates trusted runtime-stop record shape and provider-call inventory', async () => {
  const schema = JSON.parse(
    await readFile(new URL('p5-runtime-stop-record-v1.schema.json', directory), 'utf8'),
  );
  const validate = new Ajv2020({
    allErrors: true,
    strict: true,
    strictRequired: false,
  }).compile(schema);
  const sha256 = 'f'.repeat(64);
  const envelope = {
    schema: 'p5-runtime-stop-record-envelope-v1',
    runtime_stop: {
      stop_record_id: 'runtime-stop-01',
      stop_request_id: 'stop-request-01',
      environment_id: 'stage5-prod',
      usage_ledger_id: 'usage-ledger-01',
      run_id: 'holdout-run-01',
      reservation_event_id: 'reserve-01',
      frozen_spec_sha256: sha256,
      candidate_sha256: sha256,
      runtime_admission_sha256: sha256,
      runtime_image_sha256: sha256,
      dataset_sha256: sha256,
      runtime_id: 'runtime-01',
      runtime_subject: 'spiffe://stage5/runtime/01',
      supervisor_subject: 'spiffe://stage5/supervisor/01',
      stop_reason: 'normal-completion',
      termination_status: 'confirmed',
      egress_status: 'fenced',
      egress_policy_sha256: sha256,
      process_inventory_sha256: sha256,
      observed_process_count: 2,
      terminated_process_count: 2,
      provider_call_inventory: [
        {
          provider_call_id: 'provider-call-01',
          last_state: 'unknown',
          last_entry_sha256: sha256,
        },
      ],
      usage_ledger_head_sequence: 7,
      usage_ledger_head_sha256: sha256,
      started_at_utc: '2026-10-23T10:00:00Z',
      stopped_at_utc: '2026-10-23T10:05:00Z',
      signature_profile: 'ed25519-jcs-p5-runtime-stop-record-v1',
      signing_key_id: 'supervisor-key-01',
    },
    signature: 'A'.repeat(86),
  };
  assert.equal(validate(envelope), true, JSON.stringify(validate.errors));
  assert.equal(
    validate({
      ...envelope,
      runtime_stop: { ...envelope.runtime_stop, egress_status: 'open' },
    }),
    false,
  );
  assert.equal(
    validate({
      ...envelope,
      runtime_stop: {
        ...envelope.runtime_stop,
        provider_call_inventory: [
          {
            provider_call_id: 'provider-call-01',
            last_state: 'unknown',
            last_entry_sha256: 'bad',
          },
        ],
      },
    }),
    false,
  );
});

test('validates bootstrap root pin rollover and emergency recovery record shapes', async () => {
  const schema = JSON.parse(
    await readFile(
      new URL('stage5-identity-bootstrap-root-pin-update-v1.schema.json', directory),
      'utf8',
    ),
  );
  const validate = new Ajv2020({ allErrors: true, strict: true, strictRequired: false }).compile(
    schema,
  );
  const sha256 = 'a'.repeat(64);
  const signature = 'A'.repeat(86);
  const base = {
    schema: 'stage5-identity-bootstrap-root-pin-update-v1',
    update_id: 'root-pin-update-02',
    update_kind: 'planned-root-rollover',
    environment_id: 'stage5-prod',
    previous_scope: {
      log_id: 'identity-log-01',
      policy_id: 'identity-policy-01',
      policy_sha256: sha256,
      policy_version: 1,
      history_head_sequence: 3,
      history_head_sha256: sha256,
    },
    next_scope: {
      log_id: 'identity-log-01',
      policy_id: 'identity-policy-01',
      policy_sha256: 'b'.repeat(64),
      policy_version: 2,
      history_head_sequence: 3,
      history_head_sha256: sha256,
    },
    previous_history_anchor: {
      anchor_id: 'identity-history-anchor-03',
      anchor_record_sha256: sha256,
    },
    previous_root_pin_revision: 4,
    next_root_pin_revision: 5,
    previous_root_pin: {
      subject_id: 'root-owner-01',
      key_id: 'root-key-01',
      key_fingerprint_sha256: sha256,
    },
    next_root_pin: {
      subject_id: 'root-owner-02',
      key_id: 'root-key-02',
      key_fingerprint_sha256: 'b'.repeat(64),
    },
    approved_intent_sha256: sha256,
    policy_transition: {
      record_id: 'policy-transition-02',
      record_sha256: 'c'.repeat(64),
    },
    old_root_approval: {
      subject_id: 'root-owner-01',
      key_id: 'root-key-01',
      approved_intent_sha256: sha256,
      signed_at_utc: '2026-10-23T10:00:00Z',
      signature_profile: 'ed25519-jcs-identity-bootstrap-root-approval-v1',
      signature,
    },
    next_root_proof: {
      subject_id: 'root-owner-02',
      key_id: 'root-key-02',
      approved_intent_sha256: sha256,
      signed_at_utc: '2026-10-23T10:00:00Z',
      signature_profile: 'ed25519-jcs-identity-bootstrap-root-possession-v1',
      signature,
    },
    pin_authority_id: 'verifier-config-01',
    pin_authority_key_id: 'verifier-config-key-01',
    recorded_at_utc: '2026-10-23T10:00:01Z',
    record_sha256: sha256,
    signature_profile: 'ed25519-jcs-identity-bootstrap-root-pin-update-v1',
    signature_key_id: 'verifier-config-key-01',
    signature,
  };
  assert.equal(validate(base), true, JSON.stringify(validate.errors));
  assert.equal(validate({ ...base, old_root_approval: undefined }), false);
  assert.equal(validate({ ...base, policy_transition: null }), false);
  assert.equal(
    validate({
      ...base,
      previous_history_anchor: { ...base.previous_history_anchor, anchor_record_sha256: 'bad' },
    }),
    false,
  );
  const recovery = {
    ...base,
    update_kind: 'emergency-recovery',
    policy_transition: null,
    next_scope: {
      ...base.next_scope,
      log_id: 'identity-log-02',
      policy_id: 'identity-policy-02',
      policy_version: 1,
      history_head_sequence: 0,
      history_head_sha256: '0'.repeat(64),
    },
    old_root_approval: undefined,
    recovery_approvals: [
      {
        authority_id: 'recovery-01',
        key_id: 'recovery-key-01',
        approved_intent_sha256: sha256,
        signed_at_utc: '2026-10-23T10:00:00Z',
        signature_profile: 'ed25519-jcs-identity-bootstrap-recovery-approval-v1',
        signature,
      },
      {
        authority_id: 'recovery-02',
        key_id: 'recovery-key-02',
        approved_intent_sha256: sha256,
        signed_at_utc: '2026-10-23T10:00:00Z',
        signature_profile: 'ed25519-jcs-identity-bootstrap-recovery-approval-v1',
        signature,
      },
    ],
  };
  assert.equal(validate(recovery), true, JSON.stringify(validate.errors));
  assert.equal(
    validate({ ...recovery, recovery_approvals: recovery.recovery_approvals.slice(0, 1) }),
    false,
  );
  assert.equal(validate({ ...recovery, old_root_approval: base.old_root_approval }), false);
  assert.equal(validate({ ...recovery, policy_transition: base.policy_transition }), false);
  assert.equal(
    validate({
      ...base,
      next_root_proof: { ...base.next_root_proof, signature: `${'A'.repeat(85)}E` },
    }),
    false,
  );
});

test('validates atomic verifier pin bundle commit receipts', async () => {
  const schema = JSON.parse(
    await readFile(new URL('stage5-verifier-pin-bundle-commit-v1.schema.json', directory), 'utf8'),
  );
  const validate = new Ajv2020({ allErrors: true, strict: true, strictRequired: false }).compile(
    schema,
  );
  const sha256 = 'a'.repeat(64);
  const base = {
    schema: 'stage5-verifier-pin-bundle-commit-v1',
    bundle_id: 'pin-bundle-05',
    update_kind: 'planned-root-rollover',
    environment_id: 'stage5-prod',
    previous_configuration_revision: 7,
    next_configuration_revision: 8,
    previous_policy_pin_revision: 10,
    next_policy_pin_revision: 11,
    previous_bundle_state_sha256: sha256,
    next_bundle_state_sha256: 'f'.repeat(64),
    previous_policy_pin: {
      policy_id: 'identity-policy-01',
      policy_sha256: sha256,
      policy_version: 1,
    },
    next_policy_pin: {
      policy_id: 'identity-policy-01',
      policy_sha256: 'b'.repeat(64),
      policy_version: 2,
    },
    previous_root_pin_revision: 4,
    next_root_pin_revision: 5,
    previous_root_pin: {
      subject_id: 'root-owner-01',
      key_id: 'root-key-01',
      key_fingerprint_sha256: sha256,
    },
    next_root_pin: {
      subject_id: 'root-owner-02',
      key_id: 'root-key-02',
      key_fingerprint_sha256: 'b'.repeat(64),
    },
    root_pin_update: { record_id: 'root-update-02', record_sha256: 'c'.repeat(64) },
    policy_transition: { record_id: 'policy-transition-02', record_sha256: 'd'.repeat(64) },
    idempotency_key: 'pin-bundle-request-05',
    pin_authority_id: 'verifier-config-01',
    pin_authority_key_id: 'verifier-config-key-01',
    applied_at_utc: '2026-10-23T11:00:00Z',
    record_sha256: sha256,
    signature_profile: 'ed25519-jcs-verifier-pin-bundle-commit-v1',
    signature_key_id: 'verifier-config-key-01',
    signature: 'A'.repeat(86),
  };
  assert.equal(validate(base), true, JSON.stringify(validate.errors));
  assert.equal(validate({ ...base, policy_transition: null }), false);
  const { next_policy_pin_revision: _nextPolicyPinRevision, ...missingPolicyRevision } = base;
  assert.equal(validate(missingPolicyRevision), false);
  const recovery = {
    ...base,
    update_kind: 'emergency-recovery',
    previous_configuration_revision: 8,
    next_configuration_revision: 9,
    previous_policy_pin_revision: 11,
    next_policy_pin_revision: 12,
    previous_policy_pin: base.next_policy_pin,
    next_policy_pin: {
      policy_id: 'identity-policy-02',
      policy_sha256: 'e'.repeat(64),
      policy_version: 1,
    },
    previous_root_pin_revision: 5,
    next_root_pin_revision: 6,
    previous_root_pin: base.next_root_pin,
    next_root_pin: {
      subject_id: 'root-owner-03',
      key_id: 'root-key-03',
      key_fingerprint_sha256: 'e'.repeat(64),
    },
    root_pin_update: { record_id: 'root-recovery-03', record_sha256: 'f'.repeat(64) },
    policy_transition: null,
    idempotency_key: 'pin-bundle-request-06',
  };
  assert.equal(validate(recovery), true, JSON.stringify(validate.errors));
  assert.equal(validate({ ...recovery, policy_transition: base.policy_transition }), false);
  assert.equal(validate({ ...base, untrusted_override: true }), false);
  assert.equal(validate({ ...base, previous_configuration_revision: 0 }), false);
});

test('validates complete witnessed verifier pin history packages', async () => {
  const schema = JSON.parse(
    await readFile(
      new URL('stage5-verifier-pin-bundle-history-package-v1.schema.json', directory),
      'utf8',
    ),
  );
  const validate = new Ajv2020({ allErrors: true, strict: true, strictRequired: false }).compile(
    schema,
  );
  const sha256 = 'a'.repeat(64);
  const entry = {
    entry_id: 'witness-entry-01',
    sequence: 1,
    previous_entry_sha256: '0'.repeat(64),
    bundle_id: 'pin-bundle-01',
    commit_receipt_sha256: sha256,
    previous_configuration_revision: 1,
    next_configuration_revision: 2,
    previous_policy_pin_revision: 1,
    next_policy_pin_revision: 2,
    previous_root_pin_revision: 1,
    next_root_pin_revision: 2,
    previous_bundle_state_sha256: 'b'.repeat(64),
    next_bundle_state_sha256: 'c'.repeat(64),
    recorded_at_utc: '2026-10-23T12:00:00Z',
  };
  const packageValue = {
    schema: 'stage5-verifier-pin-bundle-history-package-v1',
    witness_id: 'pin-witness-01',
    environment_id: 'stage5-prod',
    challenge_nonce: 'A'.repeat(43),
    query_sha256: sha256,
    proof_scheme: 'complete-from-genesis-v1',
    entries: [{ ...entry, entry_sha256: 'd'.repeat(64) }],
    head: {
      sequence: 1,
      entry_sha256: 'd'.repeat(64),
      observed_at_utc: '2026-10-23T12:00:01Z',
      signature_profile: 'ed25519-jcs-verifier-pin-witness-head-v1',
      signature_key_id: 'pin-witness-key-01',
      signature: 'A'.repeat(86),
    },
  };
  assert.equal(validate(packageValue), true, JSON.stringify(validate.errors));
  assert.equal(validate({ ...packageValue, challenge_nonce: 'A'.repeat(42) }), false);
  assert.equal(validate({ ...packageValue, challenge_nonce: `${'A'.repeat(42)}F` }), false);
  assert.equal(validate({ ...packageValue, proof_scheme: 'partial-checkpoint-v1' }), false);
  assert.equal(
    validate({
      ...packageValue,
      entries: [{ ...packageValue.entries[0], sequence: 9007199254740992 }],
    }),
    false,
  );
  assert.equal(
    validate({ ...packageValue, head: { ...packageValue.head, sequence: 9007199254740992 } }),
    false,
  );
  assert.equal(
    validate({
      ...packageValue,
      entries: [{ ...packageValue.entries[0], next_root_pin_revision: 9007199254740992 }],
    }),
    false,
  );
  assert.equal(
    validate({
      ...packageValue,
      entries: [{ ...entry, entry_sha256: 'd'.repeat(64), extra: true }],
    }),
    false,
  );
  assert.equal(validate({ ...packageValue, unverified_head: true }), false);
  assert.equal(
    validate({
      ...packageValue,
      entries: [],
      head: { ...packageValue.head, sequence: 0, entry_sha256: '0'.repeat(64) },
    }),
    true,
  );
});

test('validates downstream human acceptance and release record shapes', () => {
  const snapshot = {
    schema: 'stage5-decision-source-snapshot-v1',
    snapshot_id: 'snapshot-01',
    environment_id: 'stage5-prod',
    assurance_profile: 'single-authority-v1',
    snapshot_started_at_utc: '2026-10-23T10:00:00Z',
    snapshot_completed_at_utc: '2026-10-23T10:00:03Z',
    maximum_snapshot_skew_seconds: 10,
    registry: {
      source_id: 'registry-source',
      trust_bundle_sha256: digest,
      key_status_sequence: 7,
      log_head_sequence: 12,
      log_head_sha256: digest,
      observed_at_utc: '2026-10-23T10:00:01Z',
    },
    usage_ledger: {
      source_id: 'usage-source',
      ledger_id: 'usage-ledger',
      trust_bundle_sha256: digest,
      key_status_sequence: 4,
      closed_sequence: 8,
      closed_head_sha256: digest,
      observed_at_utc: '2026-10-23T10:00:02Z',
    },
    governance: {
      source_id: 'governance-source',
      log_id: 'governance-log',
      log_head_sequence: 6,
      log_head_sha256: digest,
      revocation_sequence: 2,
      observed_at_utc: '2026-10-23T10:00:02Z',
    },
    identity_source: {
      source_id: 'identity-source',
      decisions: [
        {
          decision_ref: 'identity:decision:accept-01',
          decision_sha256: digest,
          authorization_intent_sha256: digest,
          decision_log_id: 'decision-log',
          record_type: 'human-acceptance',
          record_id: 'acceptance-01',
          environment_id: 'stage5-prod',
          subject_id: 'subject-acceptor',
          required_role: 'stage5_acceptance_authority',
          decision: 'allow',
          revocation_sequence: 5,
          policy_version: 'identity-policy-v1',
          observed_at_utc: '2026-10-23T10:00:02Z',
        },
      ],
      observed_at_utc: '2026-10-23T10:00:02Z',
    },

    witness: null,
  };
  const appendReceipt = {
    schema: 'stage5-decision-consumption-receipt-v1',
    decision_log_id: 'decision-log',
    record_type: 'human-acceptance',
    record_id: 'acceptance-01',
    sequence: 1,
    previous_record_sha256: '0'.repeat(64),
    record_sha256: digest,
    recorded_at_utc: '2026-10-23T10:00:04Z',
    key_id: 'decision-log-key',
    signature_profile: 'ed25519-jcs-decision-consumption-receipt-v1',
    signature: 'A'.repeat(86),
  };
  const acceptance = {
    schema: 'stage5-human-acceptance-v1',
    attestation: {
      acceptance_id: 'acceptance-01',
      authorization_intent_sha256: digest,
      decision: 'accepted',
      decision_id: 'decision-01',
      decision_receipt_sha256: digest,
      evidence_envelope_sha256: digest,
      report_sha256: digest,
      frozen_spec_sha256: digest,
      subject_id: 'subject-acceptor',
      required_role: 'stage5_acceptance_authority',
      acceptance_policy_id: 'acceptance-policy-v1',
      acceptance_policy_sha256: digest,
      consistency_profile: 'bounded-snapshot-v1',
      source_snapshot: snapshot,
      idempotency_key: 'acceptance-request-01',
      signed_at_utc: '2026-10-23T10:00:04Z',
      signature_profile: 'ed25519-jcs-stage5-human-acceptance-v1',
      signing_key_id: 'acceptor-key',
      signature: 'A'.repeat(86),
    },
    append_receipt: appendReceipt,
  };
  assert.equal(
    validateHumanAcceptance(acceptance),
    true,
    JSON.stringify(validateHumanAcceptance.errors),
  );
  assert.equal(
    validateHumanAcceptance({
      ...acceptance,
      attestation: { ...acceptance.attestation, consistency_profile: 'globally-atomic-v1' },
    }),
    false,
  );
  assert.equal(
    validateHumanAcceptance({
      ...acceptance,
      append_receipt: { ...appendReceipt, record_type: 'release-authorization' },
    }),
    false,
  );
  assert.equal(
    validateHumanAcceptance({
      ...acceptance,
      attestation: { ...acceptance.attestation, required_role: 'stage5_risk_owner' },
    }),
    false,
  );
  assert.equal(
    validateHumanAcceptance({
      ...acceptance,
      attestation: {
        ...acceptance.attestation,
        source_snapshot: {
          ...snapshot,
          identity_source: { ...snapshot.identity_source, decisions: [] },
        },
      },
    }),
    false,
  );
  assert.equal(
    validateHumanAcceptance({
      ...acceptance,
      attestation: {
        ...acceptance.attestation,
        source_snapshot: {
          ...snapshot,
          identity_source: {
            ...snapshot.identity_source,
            decisions: snapshot.identity_source.decisions.map((decision) => ({
              ...decision,
              decision: 'deny',
            })),
          },
        },
      },
    }),
    false,
  );
  assert.equal(
    validateHumanAcceptance({
      ...acceptance,
      attestation: {
        ...acceptance.attestation,
        source_snapshot: {
          ...snapshot,
          identity_source: {
            ...snapshot.identity_source,
            decisions: snapshot.identity_source.decisions.map(
              ({ required_role, ...decision }) => decision,
            ),
          },
        },
      },
    }),
    false,
  );

  const releaseSnapshot = {
    ...snapshot,
    identity_source: {
      ...snapshot.identity_source,
      decisions: snapshot.identity_source.decisions.map((entry) => ({
        ...entry,
        record_type: 'release-authorization',
        record_id: 'release-01',
        subject_id: 'subject-releaser',
        required_role: 'stage5_release_authority',
      })),
    },
  };
  const release = {
    schema: 'stage5-release-authorization-v1',
    attestation: {
      release_id: 'release-01',
      authorization_intent_sha256: digest,
      deployment_operation_id: 'deploy-op-01',
      acceptance_id: 'acceptance-01',
      acceptance_record_sha256: digest,
      decision_id: 'decision-01',
      decision_receipt_sha256: digest,
      evidence_envelope_sha256: digest,
      report_sha256: digest,
      frozen_spec_sha256: digest,
      target_environment_id: 'prod',
      artifact_sha256: digest,
      image_digest: `sha256:${digest}`,
      subject_id: 'subject-releaser',
      required_role: 'stage5_release_authority',
      release_policy_id: 'release-policy-v1',
      release_policy_sha256: digest,
      consistency_profile: 'bounded-snapshot-v1',
      idempotency_key: 'release-request-01',
      source_snapshot: releaseSnapshot,
      signed_at_utc: '2026-10-23T10:00:05Z',
      signature_profile: 'ed25519-jcs-stage5-release-authorization-v1',
      signing_key_id: 'releaser-key',
      signature: 'A'.repeat(86),
    },
    append_receipt: {
      ...appendReceipt,
      record_type: 'release-authorization',
      record_id: 'release-01',
    },
  };
  assert.equal(
    validateReleaseAuthorization(release),
    true,
    JSON.stringify(validateReleaseAuthorization.errors),
  );
  assert.equal(
    validateReleaseAuthorization({
      ...release,
      attestation: { ...release.attestation, image_digest: digest },
    }),
    false,
  );
  assert.equal(
    validateReleaseAuthorization({
      ...release,
      attestation: { ...release.attestation, consistency_profile: 'globally-atomic-v1' },
    }),
    false,
  );
  assert.equal(
    validateReleaseAuthorization({
      ...release,
      attestation: Object.fromEntries(
        Object.entries(release.attestation).filter(([key]) => key !== 'deployment_operation_id'),
      ),
    }),
    false,
  );
  assert.equal(validateReleaseAuthorization({ ...release, extra: 'not-bound' }), false);
});

test('validates append-only challenge and resolution event payload shapes', () => {
  const challengePayload = {
    event_type: 'decision-challenged',
    challenge_id: 'challenge-01',
    target_record_type: 'human-acceptance',
    target_record_id: 'acceptance-01',
    target_record_sha256: digest,
    reason_code: 'identity-revoked',
    observed_at_utc: '2026-10-23T10:00:00Z',
    initiator: { kind: 'service', service_id: 'identity-monitor' },
    trigger: {
      kind: 'source-state',
      source_id: 'identity-source-01',
      source_sequence: 42,
      source_head_sha256: digest,
    },
  };
  assert.equal(
    validateDecisionChallengeEvent({
      schema: 'stage5-decision-challenge-v1',
      event: challengePayload,
      idempotency_key: 'challenge-op-01',
      append_receipt: {
        schema: 'stage5-decision-consumption-receipt-v1',
        decision_log_id: 'decision-log',
        record_type: 'decision-challenged',
        record_id: challengePayload.challenge_id,
        sequence: 3,
        previous_record_sha256: digest,
        record_sha256: digest,
        recorded_at_utc: '2026-10-23T10:00:00Z',
        key_id: 'decision-log-key',
        signature_profile: 'ed25519-jcs-decision-consumption-receipt-v1',
        signature: 'A'.repeat(86),
      },
    }),
    true,
    JSON.stringify(validateDecisionChallengeEvent.errors),
  );
  assert.equal(
    validateDecisionChallengeEvent({
      schema: 'stage5-decision-challenge-v1',
      event: {
        ...challengePayload,
        trigger: { ...challengePayload.trigger, source_head_sha256: 'not-a-digest' },
      },
      idempotency_key: 'challenge-op-01',
      append_receipt: {
        schema: 'stage5-decision-consumption-receipt-v1',
        decision_log_id: 'decision-log',
        record_type: 'decision-challenged',
        record_id: challengePayload.challenge_id,
        sequence: 3,
        previous_record_sha256: digest,
        record_sha256: digest,
        recorded_at_utc: '2026-10-23T10:00:00Z',
        key_id: 'decision-log-key',
        signature_profile: 'ed25519-jcs-decision-consumption-receipt-v1',
        signature: 'A'.repeat(86),
      },
    }),
    false,
  );
  assert.equal(
    validateDecisionChallengeEvent({
      schema: 'stage5-decision-challenge-v1',
      event: challengePayload,
      idempotency_key: 'challenge-op-01',
      append_receipt: {
        schema: 'stage5-decision-consumption-receipt-v1',
        decision_log_id: 'decision-log',
        record_type: 'human-acceptance',
        record_id: challengePayload.challenge_id,
        sequence: 3,
        previous_record_sha256: digest,
        record_sha256: digest,
        recorded_at_utc: '2026-10-23T10:00:00Z',
        key_id: 'decision-log-key',
        signature_profile: 'ed25519-jcs-decision-consumption-receipt-v1',
        signature: 'A'.repeat(86),
      },
    }),
    false,
  );
  assert.equal(
    validateDecisionChallengeEvent({
      schema: 'stage5-decision-challenge-v1',
      event: { ...challengePayload, extra: true },
      idempotency_key: 'challenge-op-01',
      append_receipt: {},
    }),
    false,
  );

  const resolvedPayload = {
    event_type: 'decision-challenge-resolved',
    resolution_id: 'resolution-01',
    challenge_id: challengePayload.challenge_id,
    challenge_event_sha256: digest,
    target_record_type: challengePayload.target_record_type,
    target_record_id: challengePayload.target_record_id,
    target_record_sha256: challengePayload.target_record_sha256,
    fresh_decision_id: 'decision-02',
    fresh_decision_receipt_sha256: digest,
    resolution_evidence_sha256: digest,
    initiator: {
      kind: 'human',
      subject_id: 'subject-reviewer',
      required_role: 'stage5_decision_challenger',
      identity_decision_ref: 'identity:challenge:01',
      identity_decision_sha256: digest,
    },
  };
  assert.equal(
    validateDecisionChallengeEvent({
      schema: 'stage5-decision-challenge-resolved-v1',
      event: resolvedPayload,
      idempotency_key: 'resolution-op-01',
      append_receipt: {
        schema: 'stage5-decision-consumption-receipt-v1',
        decision_log_id: 'decision-log',
        record_type: 'decision-challenge-resolved',
        record_id: resolvedPayload.resolution_id,
        sequence: 4,
        previous_record_sha256: digest,
        record_sha256: digest,
        recorded_at_utc: '2026-10-23T10:00:01Z',
        key_id: 'decision-log-key',
        signature_profile: 'ed25519-jcs-decision-consumption-receipt-v1',
        signature: 'A'.repeat(86),
      },
    }),
    true,
    JSON.stringify(validateDecisionChallengeEvent.errors),
  );
  assert.equal(
    validateDecisionChallengeEvent({
      schema: 'stage5-decision-challenge-resolved-v1',
      event: { ...resolvedPayload, challenge_event_sha256: '0'.repeat(63) },
      idempotency_key: 'resolution-op-01',
      append_receipt: {},
    }),
    false,
  );
  assert.equal(
    validateDecisionChallengeEvent({
      schema: 'stage5-decision-challenge-resolved-v1',
      event: { ...resolvedPayload, event_type: 'decision-challenged' },
      idempotency_key: 'resolution-op-01',
      append_receipt: {},
    }),
    false,
  );
});

test('binds v2 challenge events to trigger evidence and validates sustained outage episodes', () => {
  assert.equal(
    utcTimestampMicroseconds('2024-02-29T12:00:00.000001Z') -
      utcTimestampMicroseconds('2024-02-29T12:00:00.000000Z'),
    1n,
  );
  assert.equal(utcTimestampMicroseconds('2026-02-29T12:00:00Z'), null);
  assert.equal(utcTimestampMicroseconds('2026-02-30T12:00:00Z'), null);
  assert.equal(utcTimestampMicroseconds('2026-10-23T25:00:00Z'), null);
  assert.equal(utcTimestampMicroseconds('2026-10-23T10:00:00T11:00:00Z'), null);

  const challengeEvent = {
    event_type: 'decision-challenged',
    challenge_id: 'challenge-v2-01',
    target_record_type: 'human-acceptance',
    target_record_id: 'acceptance-01',
    target_record_sha256: digest,
    reason_code: 'source-state-advanced',
    observed_at_utc: '2026-10-23T10:01:00Z',
    initiator: { kind: 'service', service_id: 'challenge-monitor' },
    trigger: {
      kind: 'source-state',
      source_id: 'registry-source-01',
      source_sequence: 43,
      source_head_sha256: digest,
    },
    trigger_evidence_sha256: digest,
  };
  const challengeRecord = {
    schema: 'stage5-decision-challenge-v2',
    event: challengeEvent,
    idempotency_key: 'challenge-v2-op-01',
    append_receipt: {
      schema: 'stage5-decision-consumption-receipt-v1',
      decision_log_id: 'decision-log',
      record_type: 'decision-challenged',
      record_id: challengeEvent.challenge_id,
      sequence: 5,
      previous_record_sha256: digest,
      record_sha256: digest,
      recorded_at_utc: '2026-10-23T10:01:00Z',
      key_id: 'decision-log-key',
      signature_profile: 'ed25519-jcs-decision-consumption-receipt-v1',
      signature: 'A'.repeat(86),
    },
  };
  assert.equal(
    validateDecisionChallengeEventV2(challengeRecord),
    true,
    JSON.stringify(validateDecisionChallengeEventV2.errors),
  );
  assert.equal(
    validateDecisionChallengeEventV2({
      ...challengeRecord,
      event: { ...challengeEvent, trigger_evidence_sha256: undefined },
    }),
    false,
  );
  const resolutionRecord = {
    schema: 'stage5-decision-challenge-resolved-v2',
    event: {
      event_type: 'decision-challenge-resolved',
      resolution_id: 'resolution-v2-01',
      challenge_id: challengeEvent.challenge_id,
      challenge_event_sha256: digest,
      target_record_type: challengeEvent.target_record_type,
      target_record_id: challengeEvent.target_record_id,
      target_record_sha256: challengeEvent.target_record_sha256,
      fresh_decision_id: 'fresh-decision-01',
      fresh_decision_receipt_sha256: digest,
      resolution_evidence_sha256: digest,
      initiator: { kind: 'service', service_id: 'challenge-monitor' },
    },
    idempotency_key: 'resolution-v2-op-01',
    append_receipt: {
      ...challengeRecord.append_receipt,
      record_type: 'decision-challenge-resolved',
      record_id: 'resolution-v2-01',
      sequence: 6,
    },
  };
  assert.equal(
    validateDecisionChallengeEventV2(resolutionRecord),
    true,
    JSON.stringify(validateDecisionChallengeEventV2.errors),
  );

  const episode = {
    schema: 'stage5-source-outage-episode-v1',
    episode_id: 'outage-episode-01',
    environment_id: 'prod',
    decision_log_id: 'decision-log',
    source_id: 'identity-source-01',
    monitor_service_id: 'challenge-monitor',
    policy_id: 'release-policy-v2',
    rule_id: 'source-unavailable-identity-01',
    first_failure_at_utc: '2026-10-23T10:00:00Z',
    confirmed_at_utc: '2026-10-23T10:00:30Z',
    threshold_seconds: 30,
    probes: [
      {
        started_at_utc: '2026-10-23T09:59:58Z',
        completed_at_utc: '2026-10-23T10:00:00Z',
        probe_sequence: 40,
        previous_probe_record_sha256: digest,
        probe_record_sha256: digest,
        request_id: 'probe-01',
        outcome: 'availability-failure',
        failure_class: 'timeout',
      },
      {
        started_at_utc: '2026-10-23T10:00:29Z',
        completed_at_utc: '2026-10-23T10:00:30Z',
        probe_sequence: 41,
        previous_probe_record_sha256: digest,
        probe_record_sha256: digest,
        request_id: 'probe-02',
        outcome: 'availability-failure',
        failure_class: 'connection-refused',
      },
    ],
    signature_profile: 'ed25519-jcs-stage5-source-outage-episode-v1',
    signing_key_id: 'monitor-key-01',
    signature: 'A'.repeat(86),
  };
  const probeScope = {
    environment_id: 'prod',
    source_id: 'identity-source-01',
    monitor_service_id: 'challenge-monitor',
  };
  episode.probes[0].probe_record_sha256 = sourceProbeRecordSha256(probeScope, episode.probes[0]);
  assert.equal(
    episode.probes[0].probe_record_sha256,
    'b7629ab442fb63e62fe6cda32019dbd4ee2b94b103771d90d5109c2ca3ab74e4',
  );
  episode.probes[1].previous_probe_record_sha256 = episode.probes[0].probe_record_sha256;
  episode.probes[1].probe_record_sha256 = sourceProbeRecordSha256(probeScope, episode.probes[1]);
  const outagePolicy = {
    source_id: 'identity-source-01',
    monitor_service_id: 'challenge-monitor',
    policy_id: 'release-policy-v2',
    rule_id: 'source-unavailable-identity-01',
    threshold_seconds: 30,
    source_probe_interval_seconds: 30,
    source_probe_timeout_bound_seconds: 2,
  };
  const outageJournalAnchorSha256 = digest;
  const rehashProbeSequence = (probes) => {
    let previousProbeRecordSha256 = outageJournalAnchorSha256;
    return probes.map((probe) => {
      const nextProbe = {
        ...probe,
        previous_probe_record_sha256: previousProbeRecordSha256,
      };
      nextProbe.probe_record_sha256 = sourceProbeRecordSha256(probeScope, nextProbe);
      previousProbeRecordSha256 = nextProbe.probe_record_sha256;
      return nextProbe;
    });
  };
  const outageIsSemanticallyValid = (
    candidate,
    policy = outagePolicy,
    journalAnchorSha256 = outageJournalAnchorSha256,
  ) => {
    if (!validateSourceOutageEpisode(candidate)) return false;
    const starts = candidate.probes.map((probe) => utcTimestampMicroseconds(probe.started_at_utc));
    const completions = candidate.probes.map((probe) =>
      utcTimestampMicroseconds(probe.completed_at_utc),
    );
    if ([...starts, ...completions].some((time) => time === null)) return false;
    if (candidate.probes[0].previous_probe_record_sha256 !== journalAnchorSha256) return false;
    const scope = {
      environment_id: candidate.environment_id,
      source_id: candidate.source_id,
      monitor_service_id: candidate.monitor_service_id,
    };
    if (
      candidate.probes.some(
        (probe) => probe.probe_record_sha256 !== sourceProbeRecordSha256(scope, probe),
      )
    ) {
      return false;
    }
    if (
      candidate.probes.some(
        (probe, index) =>
          index > 0 &&
          (probe.probe_sequence !== candidate.probes[index - 1].probe_sequence + 1 ||
            probe.previous_probe_record_sha256 !== candidate.probes[index - 1].probe_record_sha256),
      )
    ) {
      return false;
    }
    if (
      candidate.probes.some(
        (probe, index) =>
          completions[index] <= starts[index] ||
          completions[index] - starts[index] >
            BigInt(policy.source_probe_timeout_bound_seconds) * 1_000_000n ||
          (index > 0 &&
            (starts[index] < completions[index - 1] ||
              starts[index] - completions[index - 1] >
                BigInt(policy.source_probe_interval_seconds) * 1_000_000n)),
      )
    ) {
      return false;
    }
    return (
      candidate.probes.every((probe) => probe.outcome === 'availability-failure') &&
      candidate.probes[0].completed_at_utc === candidate.first_failure_at_utc &&
      candidate.probes.at(-1).completed_at_utc === candidate.confirmed_at_utc &&
      completions.at(-1) - completions[0] >= BigInt(policy.threshold_seconds) * 1_000_000n &&
      candidate.source_id === policy.source_id &&
      candidate.monitor_service_id === policy.monitor_service_id &&
      candidate.policy_id === policy.policy_id &&
      candidate.rule_id === policy.rule_id &&
      candidate.threshold_seconds === policy.threshold_seconds
    );
  };
  assert.equal(
    validateSourceOutageEpisode(episode),
    true,
    JSON.stringify(validateSourceOutageEpisode.errors),
  );
  assert.equal(outageIsSemanticallyValid(episode), true);
  const oneMicrosecondTimeoutOver = {
    ...episode,
    first_failure_at_utc: '2026-10-23T10:00:00.000001Z',
    confirmed_at_utc: '2026-10-23T10:00:30.000001Z',
    probes: rehashProbeSequence([
      {
        ...episode.probes[0],
        completed_at_utc: '2026-10-23T10:00:00.000001Z',
      },
      {
        ...episode.probes[1],
        started_at_utc: '2026-10-23T10:00:29.000001Z',
        completed_at_utc: '2026-10-23T10:00:30.000001Z',
      },
    ]),
  };
  assert.equal(outageIsSemanticallyValid(oneMicrosecondTimeoutOver), false);
  const oneMicrosecondThresholdShort = {
    ...episode,
    confirmed_at_utc: '2026-10-23T10:00:29.999999Z',
    probes: rehashProbeSequence([
      episode.probes[0],
      {
        ...episode.probes[1],
        started_at_utc: '2026-10-23T10:00:29.999998Z',
        completed_at_utc: '2026-10-23T10:00:29.999999Z',
      },
    ]),
  };
  assert.equal(outageIsSemanticallyValid(oneMicrosecondThresholdShort), false);
  assert.equal(
    outageIsSemanticallyValid({
      ...episode,
      probes: [{ ...episode.probes[0], failure_class: 'dns-failure' }, episode.probes[1]],
    }),
    false,
  );
  assert.equal(outageIsSemanticallyValid(episode, outagePolicy, 'c'.repeat(64)), false);
  assert.equal(
    outageIsSemanticallyValid(episode, { ...outagePolicy, source_probe_timeout_bound_seconds: 1 }),
    false,
  );
  assert.equal(
    outageIsSemanticallyValid(episode, { ...outagePolicy, source_probe_interval_seconds: 28 }),
    false,
  );
  const skippedSequenceProbes = rehashProbeSequence([
    episode.probes[0],
    { ...episode.probes[1], probe_sequence: 42 },
  ]);
  assert.equal(outageIsSemanticallyValid({ ...episode, probes: skippedSequenceProbes }), false);
  const brokenChainProbe = {
    ...episode.probes[1],
    previous_probe_record_sha256: 'b'.repeat(64),
  };
  brokenChainProbe.probe_record_sha256 = sourceProbeRecordSha256(probeScope, brokenChainProbe);
  assert.equal(
    outageIsSemanticallyValid({
      ...episode,
      probes: [episode.probes[0], brokenChainProbe],
    }),
    false,
  );
  assert.equal(outageIsSemanticallyValid({ ...episode, rule_id: 'other-source' }), false);
  assert.equal(
    outageIsSemanticallyValid({
      ...episode,
      probes: rehashProbeSequence([
        episode.probes[0],
        {
          ...episode.probes[1],
          started_at_utc: '2026-10-23T10:00:28Z',
          completed_at_utc: '2026-10-23T10:00:29Z',
        },
      ]),
      confirmed_at_utc: '2026-10-23T10:00:29Z',
    }),
    false,
  );
  assert.equal(
    outageIsSemanticallyValid({
      ...episode,
      probes: rehashProbeSequence([
        episode.probes[0],
        {
          started_at_utc: '2026-10-23T10:00:29Z',
          completed_at_utc: '2026-10-23T10:00:30Z',
          probe_sequence: 41,
          previous_probe_record_sha256: episode.probes[0].probe_record_sha256,
          probe_record_sha256: digest,
          request_id: 'probe-02',
          outcome: 'authenticated-current-read',
          source_head_sequence: 44,
          source_head_sha256: digest,
        },
      ]),
    }),
    false,
  );
  assert.equal(
    validateSourceOutageEpisode({
      ...episode,
      probes: [episode.probes[0]],
    }),
    false,
  );
  assert.equal(
    validateSourceOutageEpisode({
      ...episode,
      probes: [episode.probes[0], { ...episode.probes[1], failure_class: 'bad-signature' }],
    }),
    false,
  );
});

test('validates nonce-bound monitor probe journal page shapes and range continuity', () => {
  const page = {
    schema: 'stage5-source-probe-journal-page-v1',
    environment_id: 'prod',
    source_id: 'identity-source-01',
    monitor_service_id: 'challenge-monitor',
    query_nonce: 'A'.repeat(43),
    requested_from_sequence: 40,
    requested_to_sequence: 41,
    entries: [
      {
        started_at_utc: '2026-10-23T09:59:58Z',
        completed_at_utc: '2026-10-23T10:00:00Z',
        probe_sequence: 40,
        previous_probe_record_sha256: digest,
        probe_record_sha256: digest,
        request_id: 'probe-01',
        outcome: 'availability-failure',
        failure_class: 'timeout',
      },
      {
        started_at_utc: '2026-10-23T10:00:29Z',
        completed_at_utc: '2026-10-23T10:00:30Z',
        probe_sequence: 41,
        previous_probe_record_sha256: digest,
        probe_record_sha256: digest,
        request_id: 'probe-02',
        outcome: 'availability-failure',
        failure_class: 'connection-refused',
      },
    ],
    current_head_sequence: 41,
    current_head_sha256: digest,
    observed_at_utc: '2026-10-23T10:00:31Z',
    signature_profile: 'ed25519-jcs-stage5-source-probe-journal-page-v1',
    signing_key_id: 'monitor-key-01',
    signature: 'A'.repeat(86),
  };
  const pageProbeScope = {
    environment_id: page.environment_id,
    source_id: page.source_id,
    monitor_service_id: page.monitor_service_id,
  };
  page.entries[0].probe_record_sha256 = sourceProbeRecordSha256(pageProbeScope, page.entries[0]);
  page.entries[1].previous_probe_record_sha256 = page.entries[0].probe_record_sha256;
  page.entries[1].probe_record_sha256 = sourceProbeRecordSha256(pageProbeScope, page.entries[1]);
  page.current_head_sha256 = page.entries[1].probe_record_sha256;
  const pageIsSemanticallyValid = (candidate, query) =>
    validateSourceProbeJournalPage(candidate) &&
    candidate.environment_id === query.environment_id &&
    candidate.source_id === query.source_id &&
    candidate.monitor_service_id === query.monitor_service_id &&
    candidate.query_nonce === query.query_nonce &&
    candidate.requested_from_sequence === query.from_sequence &&
    candidate.requested_to_sequence === query.to_sequence &&
    candidate.entries.length === query.to_sequence - query.from_sequence + 1 &&
    JSON.stringify(candidate.entries) === JSON.stringify(query.expected_probes) &&
    candidate.entries[0].previous_probe_record_sha256 === query.previous_record_sha256 &&
    candidate.entries.every(
      (entry, index) =>
        entry.probe_sequence === query.from_sequence + index &&
        entry.probe_record_sha256 === sourceProbeRecordSha256(candidate, entry) &&
        (index === 0 ||
          entry.previous_probe_record_sha256 === candidate.entries[index - 1].probe_record_sha256),
    ) &&
    candidate.current_head_sequence >= query.to_sequence &&
    (candidate.current_head_sequence !== query.to_sequence ||
      candidate.current_head_sha256 === candidate.entries.at(-1).probe_record_sha256);
  const query = {
    environment_id: 'prod',
    source_id: 'identity-source-01',
    monitor_service_id: 'challenge-monitor',
    query_nonce: 'A'.repeat(43),
    from_sequence: 40,
    to_sequence: 41,
    previous_record_sha256: digest,
    expected_probes: page.entries,
  };

  assert.equal(
    validateSourceProbeJournalPage(page),
    true,
    JSON.stringify(validateSourceProbeJournalPage.errors),
  );
  assert.equal(pageIsSemanticallyValid(page, query), true);
  assert.equal(pageIsSemanticallyValid({ ...page, query_nonce: 'B'.repeat(43) }, query), false);
  assert.equal(
    pageIsSemanticallyValid(
      {
        ...page,
        entries: [page.entries[0], { ...page.entries[1], outcome: 'authenticated-current-read' }],
      },
      query,
    ),
    false,
  );
  const skippedPageEntries = [page.entries[0], { ...page.entries[1], probe_sequence: 42 }];
  skippedPageEntries[1].probe_record_sha256 = sourceProbeRecordSha256(
    pageProbeScope,
    skippedPageEntries[1],
  );
  const skippedPage = {
    ...page,
    entries: skippedPageEntries,
    current_head_sha256: skippedPageEntries.at(-1).probe_record_sha256,
  };
  assert.equal(
    pageIsSemanticallyValid(skippedPage, { ...query, expected_probes: skippedPageEntries }),
    false,
  );
  assert.equal(pageIsSemanticallyValid({ ...page, current_head_sequence: 40 }, query), false);
  assert.equal(validateSourceProbeJournalPage({ ...page, unexpected: true }), false);
});

test('matches the frozen monitor probe journal page JCS and Ed25519 vector', () => {
  const scope = {
    environment_id: 'vector-env',
    source_id: 'vector-source',
    monitor_service_id: 'vector-monitor',
  };
  const probe = {
    started_at_utc: '2026-10-23T00:00:00Z',
    completed_at_utc: '2026-10-23T00:00:01Z',
    probe_sequence: 1,
    previous_probe_record_sha256: '0'.repeat(64),
    probe_record_sha256: '965f24e19db7908118470d8cb141f1853fd266ea74e8b1f4d19443ae0dee07d8',
    request_id: 'probe-vector-1',
    outcome: 'availability-failure',
    failure_class: 'timeout',
  };
  assert.equal(
    sourceProbeRecordSha256(scope, probe),
    '965f24e19db7908118470d8cb141f1853fd266ea74e8b1f4d19443ae0dee07d8',
  );
  const message = {
    schema: 'stage5-source-probe-journal-page-v1',
    ...scope,
    query_nonce: 'A'.repeat(43),
    requested_from_sequence: 1,
    requested_to_sequence: 1,
    entries: [probe],
    current_head_sequence: 1,
    current_head_sha256: probe.probe_record_sha256,
    observed_at_utc: '2026-10-23T00:00:02Z',
    signature_profile: 'ed25519-jcs-stage5-source-probe-journal-page-v1',
    signing_key_id: 'monitor-key-vector',
  };
  const canonical = canonicalize(message);
  assert.equal(
    createHash('sha256').update(canonical, 'utf8').digest('hex'),
    '140f21b5c9aa4f3c375b209a94498c42b22430183102aea4b3333bfaabe57e73',
  );
  const publicKey = createPublicKey({
    key: Buffer.concat([
      Buffer.from('302a300506032b6570032100', 'hex'),
      Buffer.from('A6EHv_POEL4dcN0Y50vAmWfk1jCbpQ1fHdyGZBJVMbg', 'base64url'),
    ]),
    format: 'der',
    type: 'spki',
  });
  const signature = Buffer.from(
    'q2snUgLHG0HFL_AJgW4Od_tPIBCe1ughRiCE7Nun4HFpXGiDUjOOOUM2IINUFw0dq4wp5CgvvurGR5qar3VCAg',
    'base64url',
  );
  assert.equal(verify(null, Buffer.from(canonical, 'utf8'), publicKey, signature), true);
  assert.equal(
    verify(
      null,
      Buffer.from(canonicalize({ ...message, query_nonce: 'B'.repeat(43) }), 'utf8'),
      publicKey,
      signature,
    ),
    false,
  );
});

test('validates bounded-snapshot decision policies and rejects incomplete risk bindings', () => {
  const policy = {
    schema: 'stage5-decision-consumption-policy-v1',
    policy_id: 'release-policy-v1',
    policy_type: 'release-authorization',
    consistency_profile: 'bounded-snapshot-v1',
    maximum_snapshot_skew_seconds: 10,
    source_ttl_seconds: {
      registry: 60,
      usage_ledger: 60,
      governance: 30,
      identity_source: 15,
      witness: 30,
    },
    challenge_triggers: ['source-head-advanced', 'signer-revoked', 'integrity-incident'],
    resolution: {
      requires_fresh_verifier_decision: true,
      requires_exact_challenge_digest: true,
      preserves_challenge_history: true,
    },
    residual_risk_statement:
      'External sources cannot be atomically committed with the decision log.',
  };
  assert.equal(
    validateDecisionConsumptionPolicy(policy),
    true,
    JSON.stringify(validateDecisionConsumptionPolicy.errors),
  );
  assert.equal(
    validateDecisionConsumptionPolicy({ ...policy, consistency_profile: 'globally-atomic-v1' }),
    false,
  );
  assert.equal(
    validateDecisionConsumptionPolicy({ ...policy, residual_risk_statement: '' }),
    false,
  );
  assert.equal(
    validateDecisionConsumptionPolicy({
      ...policy,
      resolution: { ...policy.resolution, preserves_challenge_history: false },
    }),
    false,
  );
  assert.equal(validateDecisionConsumptionPolicy({ ...policy, mutable: true }), false);
});

test('validates challenge-monitor policy v2 shapes and detection-delay arithmetic', () => {
  const policy = {
    schema: 'stage5-decision-consumption-policy-v2',
    policy_id: 'release-policy-v2',
    policy_type: 'release-authorization',
    consistency_profile: 'bounded-snapshot-v1',
    challenge_event_schema: 'stage5-decision-challenge-v2',
    trigger_evidence_digest_profile: 'sha256-jcs-signed-evidence-v1',
    maximum_snapshot_skew_seconds: 10,
    source_ttl_seconds: {
      registry: 60,
      usage_ledger: 60,
      governance: 30,
      identity_source: 15,
      witness: 30,
      challenge_monitor: 10,
    },
    challenge_triggers: ['source-head-advanced', 'source-unavailable', 'integrity-incident'],
    resolution: {
      requires_fresh_verifier_decision: true,
      requires_exact_challenge_digest: true,
      preserves_challenge_history: true,
    },
    challenge_monitoring: {
      monitoring_mode: 'notifications-with-periodic-reconciliation',
      notification_delivery_bound_seconds: 5,
      full_reconciliation_interval_seconds: 60,
      full_reconciliation_duration_bound_seconds: 20,
      target_fanout_duration_bound_seconds: 10,
      maximum_detection_delay_seconds: 80,
      source_probe_interval_seconds: 10,
      source_probe_timeout_bound_seconds: 2,
      source_unavailability_threshold_seconds: 30,
      source_head_confirmation: 'authenticated-authoritative-read',
      cursor_gap_action: 'full-rescan-and-unverified',
      coverage_unknown_action: 'block-positive-actions',
    },
    residual_risk_statement: 'A bounded source-change detection interval remains.',
  };

  assert.equal(
    validateDecisionConsumptionPolicyV2(policy),
    true,
    JSON.stringify(validateDecisionConsumptionPolicyV2.errors),
  );
  assert.equal(isDecisionConsumptionPolicyV2SemanticallyValid(policy), true);
  assert.equal(
    validateDecisionConsumptionPolicyV2({
      ...policy,
      source_ttl_seconds: Object.fromEntries(
        Object.entries(policy.source_ttl_seconds).filter(([name]) => name !== 'challenge_monitor'),
      ),
    }),
    false,
  );
  assert.equal(
    validateDecisionConsumptionPolicyV2({
      ...policy,
      challenge_event_schema: 'stage5-decision-challenge-v1',
    }),
    false,
  );
  assert.equal(
    validateDecisionConsumptionPolicyV2({
      ...policy,
      trigger_evidence_digest_profile: 'unspecified',
    }),
    false,
  );
  assert.equal(
    validateDecisionConsumptionPolicyV2({
      ...policy,
      challenge_triggers: ['source-head-advanced', 'integrity-incident'],
    }),
    false,
  );

  const tooShort = {
    ...policy,
    challenge_monitoring: { ...policy.challenge_monitoring, maximum_detection_delay_seconds: 79 },
  };
  assert.equal(validateDecisionConsumptionPolicyV2(tooShort), true);
  assert.equal(isDecisionConsumptionPolicyV2SemanticallyValid(tooShort), false);

  const outageTooShort = {
    ...policy,
    challenge_monitoring: { ...policy.challenge_monitoring, maximum_detection_delay_seconds: 63 },
  };
  assert.equal(validateDecisionConsumptionPolicyV2(outageTooShort), true);
  assert.equal(isDecisionConsumptionPolicyV2SemanticallyValid(outageTooShort), false);

  const overflowingSum = {
    ...policy,
    challenge_monitoring: {
      ...policy.challenge_monitoring,
      full_reconciliation_interval_seconds: Number.MAX_SAFE_INTEGER,
      full_reconciliation_duration_bound_seconds: Number.MAX_SAFE_INTEGER,
      maximum_detection_delay_seconds: Number.MAX_SAFE_INTEGER,
    },
  };
  assert.equal(validateDecisionConsumptionPolicyV2(overflowingSum), true);
  assert.equal(isDecisionConsumptionPolicyV2SemanticallyValid(overflowingSum), false);

  const pollingOnly = {
    ...policy,
    challenge_monitoring: {
      ...policy.challenge_monitoring,
      monitoring_mode: 'bounded-polling',
      notification_delivery_bound_seconds: 0,
    },
  };
  assert.equal(validateDecisionConsumptionPolicyV2(pollingOnly), true);
  assert.equal(isDecisionConsumptionPolicyV2SemanticallyValid(pollingOnly), true);
  assert.equal(
    validateDecisionConsumptionPolicyV2({
      ...pollingOnly,
      challenge_monitoring: {
        ...pollingOnly.challenge_monitoring,
        notification_delivery_bound_seconds: 1,
      },
    }),
    false,
  );
  assert.equal(
    validateDecisionConsumptionPolicyV2({
      ...policy,
      challenge_monitoring: {
        ...policy.challenge_monitoring,
        notification_delivery_bound_seconds: 0,
      },
    }),
    false,
  );
  assert.equal(
    validateDecisionConsumptionPolicyV2({
      ...policy,
      challenge_monitoring: {
        ...policy.challenge_monitoring,
        cursor_gap_action: 'continue-from-last-known-cursor',
      },
    }),
    false,
  );
  assert.equal(
    validateDecisionConsumptionPolicyV2({
      ...policy,
      challenge_monitoring: undefined,
    }),
    false,
  );
});

test('validates deployment operation statement lifecycle shapes', () => {
  const attestation = {
    statement_id: 'deploy-statement-01',
    operation_id: 'deploy-op-01',
    release_id: 'release-01',
    release_record_sha256: digest,
    target_environment_id: 'prod',
    artifact_sha256: digest,
    image_digest: `sha256:${digest}`,
    controller_id: 'deploy-controller-01',
    event_type: 'claimed',
    state: 'claimed',
    idempotency_key: 'deploy-claim-01',
    previous_statement_sha256: null,
    observed_at_utc: '2026-10-23T10:00:00Z',
    signature_profile: 'ed25519-jcs-deployment-operation-v1',
    signing_key_id: 'deploy-controller-key',
    signature: 'A'.repeat(86),
  };
  const record = {
    schema: 'stage5-deployment-operation-event-v1',
    attestation,
    append_receipt: {
      schema: 'stage5-decision-consumption-receipt-v1',
      decision_log_id: 'decision-log',
      record_type: 'deployment-operation',
      record_id: attestation.statement_id,
      sequence: 5,
      previous_record_sha256: digest,
      record_sha256: digest,
      recorded_at_utc: '2026-10-23T10:00:01Z',
      key_id: 'decision-log-key',
      signature_profile: 'ed25519-jcs-decision-consumption-receipt-v1',
      signature: 'A'.repeat(86),
    },
  };
  assert.equal(
    validateDeploymentOperation(record),
    true,
    JSON.stringify(validateDeploymentOperation.errors),
  );
  assert.equal(
    validateDeploymentOperation({
      ...record,
      attestation: { ...attestation, state: 'started' },
    }),
    false,
  );
  assert.equal(
    validateDeploymentOperation({
      ...record,
      attestation: {
        ...attestation,
        event_type: 'terminal',
        state: 'unknown',
        previous_statement_sha256: digest,
      },
    }),
    false,
  );
  assert.equal(
    validateDeploymentOperation({
      ...record,
      append_receipt: { ...record.append_receipt, record_type: 'release-authorization' },
    }),
    false,
  );
  const correction = {
    ...attestation,
    statement_id: 'deploy-statement-correction',
    event_type: 'correction',
    state: 'corrected',
    idempotency_key: 'deploy-correction-01',
    previous_statement_sha256: digest,
    correction_of_sha256: digest,
    corrected_state: 'started',
    correction_evidence_sha256: digest,
    reason_code: 'terminal-status-misreported',
  };
  assert.equal(
    validateDeploymentOperation({
      ...record,
      attestation: correction,
      append_receipt: {
        ...record.append_receipt,
        record_id: correction.statement_id,
        sequence: 6,
      },
    }),
    true,
    JSON.stringify(validateDeploymentOperation.errors),
  );
  assert.equal(
    validateDeploymentOperation({
      ...record,
      attestation: { ...correction, correction_evidence_sha256: undefined },
    }),
    false,
  );
  assert.equal(
    validateDeploymentOperation({ ...record, attestation: { ...attestation, unbounded: true } }),
    false,
  );
});
