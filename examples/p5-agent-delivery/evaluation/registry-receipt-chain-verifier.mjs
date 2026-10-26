import { createHash, createPublicKey, verify } from 'node:crypto';
import Ajv2020 from 'ajv/dist/2020.js';
import { canonicalizeForProfile } from './jcs-profile.mjs';
import { verifyTrustBundle, parseUtcTimestamp, receiptKeyStatusAt } from './trust-bundle-verifier.mjs';
import { verifyKeyStatusStatement } from './key-status-verifier.mjs';

const EVENT_SCHEMA = 'stage5-registry-event-envelope-v1';
const RECEIPT_SCHEMA = 'stage5-append-receipt-v1';
const HASH_PROFILE = 'jcs-rfc8785-v1';
const RECEIPT_PROFILE = 'ed25519-jcs-receipt-v1';
const GENESIS_HASH = '0'.repeat(64);
const SPKI_PREFIX = Buffer.from('302a300506032b6570032100', 'hex');
const EVENT_FIELDS = [
  'actor_asserted_at', 'actor_role', 'actor_subject_id', 'event_hash', 'event_id', 'event_type',
  'hash_profile', 'payload', 'payload_sha256', 'previous_event_hash', 'registry_recorded_at',
  'run_id', 'schema', 'sequence',
];
const PREIMAGE_FIELDS = [
  'schema', 'hash_profile', 'run_id', 'sequence', 'event_id', 'previous_event_hash', 'event_type',
  'actor_subject_id', 'actor_role', 'registry_recorded_at', 'actor_asserted_at', 'payload_sha256',
];
const RECEIPT_FIELDS = [
  'environment_id', 'event_hash', 'event_id', 'hash_profile', 'key_id', 'log_id',
  'previous_event_hash', 'registry_recorded_at', 'run_id', 'schema', 'sequence',
  'signature', 'signature_algorithm', 'signature_profile',
];

function fail(message) {
  throw new Error(`Registry receipt-chain verification failed: ${message}`);
}

function sha256Canonical(value, description) {
  let bytes;
  try {
    bytes = Buffer.from(canonicalizeForProfile(value), 'utf8');
  } catch (error) {
    fail(`${description} cannot be canonicalized (${error.message})`);
  }
  return createHash('sha256').update(bytes).digest('hex');
}

function verifyReceiptSignature(receipt, publicKeyBase64Url) {
  const { signature, ...signedReceipt } = receipt;
  if (typeof signature !== 'string' || !/^[A-Za-z0-9_-]{86}$/.test(signature)) fail('receipt signature is not unpadded base64url');
  const signatureBytes = Buffer.from(signature, 'base64url');
  if (signatureBytes.length !== 64 || signatureBytes.toString('base64url') !== signature) fail('receipt signature has invalid encoding or length');
  if (!/^[A-Za-z0-9_-]{43}$/.test(publicKeyBase64Url)) fail('trusted event key is not raw Ed25519 base64url');
  const publicBytes = Buffer.from(publicKeyBase64Url, 'base64url');
  if (publicBytes.length !== 32 || publicBytes.toString('base64url') !== publicKeyBase64Url) fail('trusted event key has invalid encoding or length');
  const publicKey = createPublicKey({ key: Buffer.concat([SPKI_PREFIX, publicBytes]), format: 'der', type: 'spki' });
  const bytes = Buffer.from(canonicalizeForProfile(signedReceipt), 'utf8');
  if (!verify(null, bytes, publicKey, signatureBytes)) fail('receipt signature is invalid');
}

function verifyPreCompromiseAnchor({ anchor, entry, trustedAnchor, schema, boundaryUtc, expectedScope, currentTimeUtc, clockSkewSeconds }) {
  if (!anchor || !entry || !trustedAnchor || !schema) fail('revoked-key historical verification requires an anchor and externally trusted anchor configuration');
  const validate = new Ajv2020({ allErrors: true, strict: true, strictRequired: false }).compile(schema);
  if (!validate(anchor)) fail(`pre-compromise anchor schema is invalid (${validate.errors?.map(({ instancePath, keyword }) => `${instancePath || '/'} ${keyword}`).join('; ')})`);
  if (trustedAnchor.authorityId !== anchor.anchor_authority_id || trustedAnchor.keyId !== anchor.anchor_key_id) fail('anchor authority or key id is not pinned by verifier configuration');
  if (anchor.environment_id !== expectedScope.environmentId || anchor.log_id !== expectedScope.logId || anchor.run_id !== expectedScope.runId) {
    fail('anchor scope does not match the frozen event chain');
  }
  if (anchor.sequence !== entry.event.sequence || anchor.event_id !== entry.event.event_id || anchor.event_hash !== entry.event.event_hash || anchor.key_id !== entry.receipt.key_id) {
    fail('anchor does not bind the revoked-key event identity');
  }
  if (anchor.receipt_sha256 !== sha256Canonical({ event: entry.event, receipt: entry.receipt }, 'anchored event and receipt')) {
    fail('anchor does not bind the exact committed event and receipt bytes');
  }

  const publicBytes = Buffer.from(trustedAnchor.publicKey ?? '', 'base64url');
  if (publicBytes.length !== 32 || publicBytes.toString('base64url') !== trustedAnchor.publicKey) fail('trusted anchor key has invalid raw Ed25519 encoding');
  if (!/^[a-f0-9]{64}$/.test(trustedAnchor.fingerprintSha256 ?? '') || createHash('sha256').update(publicBytes).digest('hex') !== trustedAnchor.fingerprintSha256) {
    fail('trusted anchor key fingerprint does not match release-pinned configuration');
  }
  const signatureBytes = Buffer.from(anchor.signature, 'base64url');
  if (signatureBytes.length !== 64 || signatureBytes.toString('base64url') !== anchor.signature) fail('anchor signature has invalid encoding');
  const publicKey = createPublicKey({ key: Buffer.concat([Buffer.from('302a300506032b6570032100', 'hex'), publicBytes]), format: 'der', type: 'spki' });
  const signedAnchor = { ...anchor };
  delete signedAnchor.signature;
  const signedBytes = Buffer.from(canonicalizeForProfile(signedAnchor), 'utf8');
  if (!verify(null, signedBytes, publicKey, signatureBytes)) fail('anchor signature is invalid');

  const anchorTime = parseUtcTimestamp(anchor.anchor_recorded_at_utc, 'anchor.anchor_recorded_at_utc');
  const eventTime = parseUtcTimestamp(entry.event.registry_recorded_at, 'event.registry_recorded_at');
  const compromiseBoundary = parseUtcTimestamp(boundaryUtc, 'key_status.compromise_not_before_utc');
  const verifierTime = parseUtcTimestamp(currentTimeUtc, 'verifier.current_time_utc');
  if (anchorTime < eventTime) fail('anchor predates the committed event recorded time');
  if (anchorTime >= compromiseBoundary) fail('anchor is not strictly before the compromise boundary');
  if (anchorTime > verifierTime + clockSkewSeconds * 1000) fail('anchor timestamp is future dated');
  return anchor.anchor_id;
}

export function verifyOfficialReceiptChain({
  entries,
  runId,
  environmentId,
  logId,
  trustBundle,
  trustBundleRootSignature,
  trustBundleDigest,
  trustedRoot,
  permittedSignerKeyId,
  trustBundleSchema,
  keyStatusStatement,
  keyStatusRootSignature,
  keyStatusSchema,
  statusPolicy,
  preCompromiseAnchors = [],
  preCompromiseAnchorSchema,
  trustedAnchor,
}) {
  if (!Array.isArray(entries) || entries.length === 0) fail('a non-empty committed event chain is required');
  if (typeof runId !== 'string' || !runId || typeof environmentId !== 'string' || !environmentId || typeof logId !== 'string' || !logId) {
    fail('frozen run, environment, and log identities are required');
  }
  if (!Array.isArray(preCompromiseAnchors)) fail('pre-compromise anchors must be an array');

  const trust = verifyTrustBundle({
    bundle: trustBundle,
    rootSignature: trustBundleRootSignature,
    trustedRoot,
    expectedDigest: trustBundleDigest,
    expectedScope: { environmentId, logId, permittedSignerKeyId },
    schema: trustBundleSchema,
  });
  const keyStatus = verifyKeyStatusStatement({
    statement: keyStatusStatement,
    rootSignature: keyStatusRootSignature,
    trustedRoot,
    frozenBundle: { digest: trust.digest, environmentId: trust.environmentId, logId: trust.logId, keys: trust.keys },
    schema: keyStatusSchema,
    ...statusPolicy,
  });

  const anchorsByEventId = new Map();
  const seenAnchorIds = new Set();
  for (const anchor of preCompromiseAnchors) {
    if (!anchor || typeof anchor.event_id !== 'string' || !anchor.event_id) fail('anchor event id is required');
    if (anchorsByEventId.has(anchor.event_id)) fail('duplicate pre-compromise anchor for event');
    if (typeof anchor.anchor_id !== 'string' || !anchor.anchor_id || seenAnchorIds.has(anchor.anchor_id)) fail('anchor id is missing or duplicated');
    anchorsByEventId.set(anchor.event_id, anchor);
    seenAnchorIds.add(anchor.anchor_id);
  }

  const trustKeys = new Map(trust.keys.map((key) => [key.key_id, key]));
  const revocations = new Map(keyStatus.revokedKeys.map((entry) => [entry.key_id, entry]));
  const boundaries = new Map(keyStatus.compromiseBoundaries.map((entry) => [entry.keyId, entry]));
  const seenEventIds = new Set();
  let previousHash = GENESIS_HASH;
  let previousRecordedAt = -Infinity;
  const verifiedEventIds = [];
  const historicallyAnchoredEventIds = [];
  const consumedAnchorEventIds = new Set();

  for (let index = 0; index < entries.length; index += 1) {
    const entry = entries[index];
    const event = entry?.event;
    const receipt = entry?.receipt;
    if (!event || !receipt) fail(`entry ${index} is missing its committed event or receipt`);
    if (Object.keys(event).sort().join(',') !== [...EVENT_FIELDS].sort().join(',')) fail(`event ${index} has missing or unknown fields`);
    if (Object.keys(receipt).sort().join(',') !== [...RECEIPT_FIELDS].sort().join(',')) fail(`receipt ${index} has missing or unknown fields`);
    if (event.schema !== EVENT_SCHEMA || event.hash_profile !== HASH_PROFILE) fail(`event ${index} has an unsupported schema or hash profile`);
    for (const [field, value] of Object.entries({ event_id: event.event_id, event_type: event.event_type, actor_subject_id: event.actor_subject_id, actor_role: event.actor_role })) {
      if (typeof value !== 'string' || value.length === 0 || value.length > 256) fail(`event ${index} has an invalid ${field}`);
    }
    if (!/^[a-f0-9]{64}$/.test(event.payload_sha256)) fail(`event ${index} payload digest is not lowercase SHA-256 hex`);
    if (!Number.isSafeInteger(event.sequence) || event.sequence !== index + 1) fail(`event ${index} has a non-contiguous sequence`);
    if (event.run_id !== runId || receipt.run_id !== runId) fail(`event ${index} run id does not match the frozen run`);
    if (receipt.schema !== RECEIPT_SCHEMA || receipt.hash_profile !== HASH_PROFILE) fail(`receipt ${index} has an unsupported schema or hash profile`);
    if (receipt.environment_id !== environmentId) fail(`receipt ${index} environment does not match the frozen scope`);
    if (receipt.log_id !== logId) fail(`receipt ${index} log does not match the frozen scope`);
    if (event.event_id !== receipt.event_id || seenEventIds.has(event.event_id)) fail(`event ${index} id is mismatched or duplicated`);
    if (event.sequence !== receipt.sequence || event.previous_event_hash !== receipt.previous_event_hash || event.event_hash !== receipt.event_hash) {
      fail(`receipt ${index} does not bind the committed event fields`);
    }
    if (event.registry_recorded_at !== receipt.registry_recorded_at) fail(`receipt ${index} recorded time does not match the event`);
    if (event.previous_event_hash !== previousHash) fail(`event ${index} predecessor does not match the verified chain head`);
    if (event.actor_asserted_at !== null) parseUtcTimestamp(event.actor_asserted_at, `event[${index}].actor_asserted_at`);
    const recordedAt = parseUtcTimestamp(event.registry_recorded_at, `event[${index}].registry_recorded_at`);
    if (recordedAt < previousRecordedAt) fail(`event ${index} recorded time moves backwards`);
    if (!event.payload || typeof event.payload !== 'object' || Array.isArray(event.payload)) fail(`event ${index} payload must be a JSON object`);
    const payloadDigest = sha256Canonical(event.payload, `event ${index} payload`);
    if (payloadDigest !== event.payload_sha256) fail(`event ${index} payload hash is invalid`);
    const eventPreimage = Object.fromEntries(PREIMAGE_FIELDS.map((field) => [field, event[field]]));
    const computedEventHash = sha256Canonical(eventPreimage, `event ${index} hash preimage`);
    if (computedEventHash !== event.event_hash) fail(`event ${index} event hash is invalid`);

    if (receipt.signature_profile !== RECEIPT_PROFILE || receipt.signature_algorithm !== 'Ed25519') fail(`receipt ${index} uses an unsupported signature profile`);
    if (receipt.key_id !== permittedSignerKeyId) fail(`receipt ${index} does not use the frozen permitted signer key`);
    const key = trustKeys.get(receipt.key_id);
    if (!key) fail(`receipt ${index} uses an unknown signing key`);
    const revoked = keyStatus.revokedKeyIds.includes(key.key_id);
    const keyStatusAtEvent = receiptKeyStatusAt(key, receipt.registry_recorded_at);
    if (revoked) {
      const revocation = revocations.get(key.key_id);
      const boundary = boundaries.get(key.key_id);
      const anchor = anchorsByEventId.get(event.event_id);
      if (!revocation || !boundary || !anchor) fail(`receipt ${index} signing key is revoked and lacks an eligible compromise anchor`);
      const eventTime = parseUtcTimestamp(receipt.registry_recorded_at, `receipt[${index}].registry_recorded_at`);
      const keyStart = parseUtcTimestamp(key.not_before_utc, `${key.key_id}.not_before_utc`);
      const keyEnd = parseUtcTimestamp(key.not_after_utc, `${key.key_id}.not_after_utc`);
      const revokedAt = parseUtcTimestamp(revocation.revoked_at_utc, `${key.key_id}.revoked_at_utc`);
      if (eventTime < keyStart || eventTime > keyEnd || eventTime > revokedAt) fail(`receipt ${index} was recorded outside the signing key's active interval`);
      const anchorId = verifyPreCompromiseAnchor({
        anchor,
        entry,
        trustedAnchor,
        schema: preCompromiseAnchorSchema,
        boundaryUtc: boundary.notBeforeUtc,
        expectedScope: { environmentId, logId, runId },
        currentTimeUtc: statusPolicy.currentTimeUtc,
        clockSkewSeconds: statusPolicy.clockSkewSeconds ?? 0,
      });
      consumedAnchorEventIds.add(event.event_id);
      historicallyAnchoredEventIds.push(event.event_id);
      seenAnchorIds.add(anchorId);
    } else {
      if (keyStatusAtEvent !== 'valid') fail(`receipt ${index} signing key is outside its validity window`);
      verifyReceiptSignature(receipt, key.public_key);
    }

    if (revoked) verifyReceiptSignature(receipt, key.public_key);

    seenEventIds.add(event.event_id);
    verifiedEventIds.push(event.event_id);
    previousHash = event.event_hash;
    previousRecordedAt = recordedAt;
  }

  if (consumedAnchorEventIds.size !== anchorsByEventId.size) fail('unused pre-compromise anchor supplied');
  return Object.freeze({
    verified: true,
    eventCount: entries.length,
    headHash: previousHash,
    eventIds: Object.freeze(verifiedEventIds),
    historicallyAnchoredEventIds: Object.freeze(historicallyAnchoredEventIds),
    trustBundleDigest: trust.digest,
    keyStatusSequence: keyStatus.sequence,
  });
}

/**
 * Verify the independent witness's own append chain against a previously verified
 * authority event chain. This verifies cryptographic binding and continuity only;
 * transport authentication, independent operation, and the witness's actual log
 * read are deployment properties that require external evidence.
 */
export function verifyDualWitnessReceiptChain({
  authorityEntries,
  witnessReceipts,
  runId,
  environmentId,
  logId,
  appendAuthorityDomainId,
  signingKeyCustodianDomainId,
  trustedWitness,
  witnessReceiptSchema,
  currentTimeUtc,
  clockSkewSeconds = 0,
}) {
  if (!Array.isArray(authorityEntries) || authorityEntries.length === 0) fail('dual-witness verification requires a non-empty authority chain');
  if (!Array.isArray(witnessReceipts) || witnessReceipts.length !== authorityEntries.length) fail('witness receipts must cover every authority event exactly once');
  if (![runId, environmentId, logId, appendAuthorityDomainId, signingKeyCustodianDomainId].every((value) => typeof value === 'string' && value.length > 0)) {
    fail('dual-witness frozen identities and trust domains are required');
  }
  if (!trustedWitness || trustedWitness.authorityId === appendAuthorityDomainId
      || trustedWitness.authorityId === signingKeyCustodianDomainId
      || typeof trustedWitness.witnessId !== 'string' || !trustedWitness.witnessId
      || typeof trustedWitness.keyId !== 'string' || !trustedWitness.keyId) {
    fail('witness identity and an independent trust domain are required');
  }
  if (!/^[a-f0-9]{64}$/.test(trustedWitness.fingerprintSha256 ?? '')) fail('witness key fingerprint is invalid');
  const publicBytes = Buffer.from(trustedWitness.publicKey ?? '', 'base64url');
  if (publicBytes.length !== 32 || publicBytes.toString('base64url') !== trustedWitness.publicKey
      || createHash('sha256').update(publicBytes).digest('hex') !== trustedWitness.fingerprintSha256) {
    fail('witness key does not match the pinned fingerprint');
  }
  if (!Number.isSafeInteger(clockSkewSeconds) || clockSkewSeconds < 0 || clockSkewSeconds > 300) fail('witness clock skew policy is invalid');
  const verifierTime = parseUtcTimestamp(currentTimeUtc, 'witness verifier current_time_utc');
  if (!witnessReceiptSchema || typeof witnessReceiptSchema !== 'object') fail('the pinned witness receipt schema is required');
  const validateWitnessReceipt = new Ajv2020({ allErrors: true, strict: true }).compile(witnessReceiptSchema);
  const witnessPublicKey = createPublicKey({ key: Buffer.concat([SPKI_PREFIX, publicBytes]), format: 'der', type: 'spki' });
  const fields = [
    'authority_event_hash', 'authority_event_id', 'authority_entry_sha256', 'authority_sequence',
    'authority_id', 'environment_id', 'hash_profile', 'key_id', 'log_id', 'observed_at_utc',
    'previous_witness_receipt_sha256', 'run_id', 'schema', 'signature', 'signature_algorithm',
    'signature_profile', 'witness_id', 'witness_sequence',
  ];
  let previousWitnessDigest = '0'.repeat(64);
  let previousObservedAt = -Infinity;
  for (let index = 0; index < authorityEntries.length; index += 1) {
    const entry = authorityEntries[index];
    const receipt = witnessReceipts[index];
    const event = entry?.event;
    const authorityReceipt = entry?.receipt;
    if (!event || !authorityReceipt || !receipt || typeof receipt !== 'object' || Array.isArray(receipt)) fail(`witness entry ${index} is malformed`);
    if (!validateWitnessReceipt(receipt)) fail(`witness receipt ${index} does not match the pinned schema (${validateWitnessReceipt.errors?.map(({ instancePath, keyword }) => `${instancePath || '/'} ${keyword}`).join('; ')})`);
    if (Object.keys(receipt).sort().join(',') !== fields.sort().join(',')) fail(`witness receipt ${index} has missing or unknown fields`);
    if (receipt.schema !== 'stage5-independent-witness-receipt-v1'
        || receipt.hash_profile !== HASH_PROFILE
        || receipt.signature_profile !== 'ed25519-jcs-witness-receipt-v1'
        || receipt.signature_algorithm !== 'Ed25519') fail(`witness receipt ${index} uses an unsupported profile`);
    if (receipt.witness_id !== trustedWitness.witnessId || receipt.authority_id !== trustedWitness.authorityId
        || receipt.key_id !== trustedWitness.keyId) fail(`witness receipt ${index} identity does not match pinned witness`);
    if (receipt.environment_id !== environmentId || receipt.log_id !== logId || receipt.run_id !== runId
        || event.run_id !== runId || authorityReceipt.environment_id !== environmentId
        || authorityReceipt.log_id !== logId || authorityReceipt.run_id !== runId) fail(`witness receipt ${index} scope does not match frozen run`);
    if (receipt.witness_sequence !== index + 1 || receipt.authority_sequence !== event.sequence
        || receipt.authority_event_id !== event.event_id || receipt.authority_event_hash !== event.event_hash) {
      fail(`witness receipt ${index} does not bind the authority event or has a sequence gap`);
    }
    if (receipt.authority_entry_sha256 !== sha256Canonical(entry, `authority entry ${index}`)) fail(`witness receipt ${index} does not bind the exact authority receipt`);
    if (receipt.previous_witness_receipt_sha256 !== previousWitnessDigest) fail(`witness receipt ${index} predecessor breaks the witness chain`);
    const observedAt = parseUtcTimestamp(receipt.observed_at_utc, `witness receipt[${index}].observed_at_utc`);
    const eventAt = parseUtcTimestamp(event.registry_recorded_at, `authority event[${index}].registry_recorded_at`);
    if (observedAt < eventAt || observedAt < previousObservedAt || observedAt > verifierTime + clockSkewSeconds * 1000) {
      fail(`witness receipt ${index} observation time is invalid or out of order`);
    }
    const signatureBytes = Buffer.from(receipt.signature ?? '', 'base64url');
    if (signatureBytes.length !== 64 || signatureBytes.toString('base64url') !== receipt.signature) fail(`witness receipt ${index} signature encoding is invalid`);
    const signedBody = { ...receipt };
    delete signedBody.signature;
    if (!verify(null, Buffer.from(canonicalizeForProfile(signedBody), 'utf8'), witnessPublicKey, signatureBytes)) fail(`witness receipt ${index} signature is invalid`);
    previousWitnessDigest = sha256Canonical(receipt, `witness receipt ${index}`);
    previousObservedAt = observedAt;
  }
  const terminalWitnessReceipt = witnessReceipts.at(-1);
  return Object.freeze({
    verified: true,
    witnessId: trustedWitness.witnessId,
    terminalEventId: terminalWitnessReceipt.authority_event_id,
    terminalWitnessSequence: terminalWitnessReceipt.witness_sequence,
    terminalWitnessReceiptSha256: previousWitnessDigest,
  });
}
