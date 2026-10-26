import Ajv2020 from 'ajv/dist/2020.js';
import assert from 'node:assert/strict';
import { createHash, createPrivateKey, createPublicKey, sign } from 'node:crypto';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import { canonicalizeForProfile } from './jcs-profile.mjs';
import { verifyDualWitnessReceiptChain, verifyOfficialReceiptChain } from './registry-receipt-chain-verifier.mjs';

const readJson = async (name) => JSON.parse(await readFile(new URL(name, import.meta.url), 'utf8'));
const [vectors, trustBundleSchema, keyStatusSchema, keyStatusV2Schema, anchorSchema, witnessReceiptSchema] = await Promise.all([
  readJson('./jcs-vectors.json'),
  readJson('./trust-bundle.schema.json'),
  readJson('./key-status.schema.json'),
  readJson('./key-status-v2.schema.json'),
  readJson('./pre-compromise-anchor.schema.json'),
  readJson('./independent-witness-receipt.schema.json'),
]);
const validateWitnessReceipt = new Ajv2020({ allErrors: true, strict: true }).compile(witnessReceiptSchema);
const vector = (id) => vectors.find((item) => item.id === id);
const eventVector = vector('stage5-registry-event-envelope');
const payloadVector = vector('stage5-registry-event-payload');
const receiptVector = vector('stage5-append-receipt');
const sha256 = (text) => createHash('sha256').update(text, 'utf8').digest('hex');

const rootSeed = Buffer.from('4c3a1d8f62b0e597a1f4c891d7732a5e9f6b0c4281d3e7a9556c0bf21e84a369', 'hex');
const rootPrivateKey = createPrivateKey({ key: Buffer.concat([Buffer.from('302e020100300506032b657004220420', 'hex'), rootSeed]), format: 'der', type: 'pkcs8' });
const rootPublicBytes = createPublicKey(rootPrivateKey).export({ format: 'der', type: 'spki' }).subarray(-32);
const trustedRoot = {
  keyId: 'offline-root-vector-1',
  publicKey: rootPublicBytes.toString('base64url'),
  fingerprintSha256: createHash('sha256').update(rootPublicBytes).digest('hex'),
};

function rootSign(payload, profile) {
  const bytes = Buffer.from(canonicalizeForProfile(payload), 'utf8');
  return {
    schema: 'stage5-trust-root-signature-v1',
    root_key_id: trustedRoot.keyId,
    profile,
    signature: sign(null, bytes, rootPrivateKey).toString('base64url'),
  };
}


const anchorSeed = Buffer.from('7f4a9c12d3e5b6078a9b0c1d2e3f40517f4a9c12d3e5b6078a9b0c1d2e3f4051', 'hex');
const anchorPrivateKey = createPrivateKey({ key: Buffer.concat([Buffer.from('302e020100300506032b657004220420', 'hex'), anchorSeed]), format: 'der', type: 'pkcs8' });
const anchorPublicBytes = createPublicKey(anchorPrivateKey).export({ format: 'der', type: 'spki' }).subarray(-32);
const trustedAnchor = {
  authorityId: 'independent-time-anchor-1',
  keyId: 'anchor-key-1',
  publicKey: anchorPublicBytes.toString('base64url'),
  fingerprintSha256: createHash('sha256').update(anchorPublicBytes).digest('hex'),
};

function signAnchor(entry, anchorRecordedAtUtc = '2026-10-23T12:00:30Z') {
  const anchor = {
    schema: 'stage5-pre-compromise-anchor-v1',
    anchor_id: 'anchor-evt-001',
    environment_id: entry.receipt.environment_id,
    log_id: entry.receipt.log_id,
    run_id: entry.receipt.run_id,
    sequence: entry.receipt.sequence,
    event_id: entry.event.event_id,
    event_hash: entry.event.event_hash,
    key_id: entry.receipt.key_id,
    receipt_sha256: sha256(canonicalizeForProfile({ event: entry.event, receipt: entry.receipt })),
    anchor_recorded_at_utc: anchorRecordedAtUtc,
    anchor_authority_id: trustedAnchor.authorityId,
    anchor_key_id: trustedAnchor.keyId,
    signature_algorithm: 'Ed25519',
    signature_profile: 'ed25519-jcs-precompromise-anchor-v1',
  };
  return { ...anchor, signature: sign(null, Buffer.from(canonicalizeForProfile(anchor), 'utf8'), anchorPrivateKey).toString('base64url') };
}

const eventSeed = Buffer.from('9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60', 'hex');
const eventPrivateKey = createPrivateKey({ key: Buffer.concat([Buffer.from('302e020100300506032b657004220420', 'hex'), eventSeed]), format: 'der', type: 'pkcs8' });
const eventPublicKey = createPublicKey(eventPrivateKey).export({ format: 'der', type: 'spki' }).subarray(-32).toString('base64url');

const bundle = {
  schema: 'stage5-receipt-trust-bundle-v1',
  bundle_id: 'trust-vector-1',
  hash_profile: 'jcs-rfc8785-v1',
  signature_profile: 'ed25519-jcs-receipt-v1',
  environment_id: 'prod-eval',
  log_id: 'official-holdout-v1',
  issued_at_utc: '2026-10-23T11:00:00Z',
  keys: [{
    key_id: 'audit-key-vector-1', algorithm: 'Ed25519', public_key: eventPublicKey, state: 'active',
    not_before_utc: '2026-10-23T11:00:00Z', not_after_utc: '2027-10-23T11:00:00Z',
  }],
};
const bundleDigest = sha256(canonicalizeForProfile(bundle));
const bundleRootSignature = rootSign(bundle, 'ed25519-jcs-trust-bundle-v1');
const statusStatement = {
  schema: 'stage5-key-status-statement-v1', statement_id: 'status-vector-1', sequence: 1,
  bundle_sha256: bundleDigest, environment_id: 'prod-eval', log_id: 'official-holdout-v1',
  issued_at_utc: '2026-10-23T12:00:00Z', expires_at_utc: '2026-10-23T12:05:00Z', revoked_keys: [],
};
const statusRootSignature = rootSign(statusStatement, 'ed25519-jcs-key-status-v1');

function baseEventEntry() {
  return {
    event: {
      ...eventVector.value,
      payload: payloadVector.value,
      event_hash: eventVector.sha256,
    },
    receipt: {
      ...receiptVector.value,
      signature: receiptVector.ed25519_signature_base64url,
    },
  };
}

function nextEntry(previous, sequence) {
  const payload = { operation: 'reserve', run_id: 'run-vector-1' };
  const payloadSha = sha256(canonicalizeForProfile(payload));
  const preimage = {
    schema: 'stage5-registry-event-envelope-v1', hash_profile: 'jcs-rfc8785-v1', run_id: 'run-vector-1',
    sequence, event_id: `evt-00${sequence}`, previous_event_hash: previous.event.event_hash,
    event_type: 'reserved', actor_subject_id: 'executor-1', actor_role: 'executor',
    registry_recorded_at: `2026-10-23T12:00:0${sequence}Z`, actor_asserted_at: null, payload_sha256: payloadSha,
  };
  const eventHash = sha256(canonicalizeForProfile(preimage));
  const receiptBody = {
    schema: 'stage5-append-receipt-v1', hash_profile: 'jcs-rfc8785-v1', environment_id: 'prod-eval',
    log_id: 'official-holdout-v1', run_id: 'run-vector-1', sequence, event_id: preimage.event_id,
    previous_event_hash: preimage.previous_event_hash, event_hash: eventHash,
    registry_recorded_at: preimage.registry_recorded_at, signature_profile: 'ed25519-jcs-receipt-v1',
    signature_algorithm: 'Ed25519', key_id: 'audit-key-vector-1',
  };
  return {
    event: { ...preimage, payload, event_hash: eventHash },
    receipt: { ...receiptBody, signature: sign(null, Buffer.from(canonicalizeForProfile(receiptBody)), eventPrivateKey).toString('base64url') },
  };
}

function verify(entries = [baseEventEntry()], overrides = {}) {
  return verifyOfficialReceiptChain({
    entries,
    runId: 'run-vector-1',
    environmentId: 'prod-eval',
    logId: 'official-holdout-v1',
    trustBundle: bundle,
    trustBundleRootSignature: bundleRootSignature,
    trustBundleDigest: bundleDigest,
    trustedRoot,
    permittedSignerKeyId: 'audit-key-vector-1',
    trustBundleSchema,
    keyStatusStatement: statusStatement,
    keyStatusRootSignature: statusRootSignature,
    keyStatusSchema,
    statusPolicy: { currentTimeUtc: '2026-10-23T12:01:00Z', maxFreshnessSeconds: 600, minimumSequence: 1 },
    ...overrides,
  });
}

test('verifies the full trust bundle, fresh key status, event chain and signed receipt', () => {
  const result = verify();
  assert.equal(result.verified, true);
  assert.equal(result.eventCount, 1);
  assert.equal(result.headHash, eventVector.sha256);
  assert.deepEqual(result.eventIds, ['evt-001']);
});

test('verifies a multi-event chain using the previous committed event hash as the next predecessor', () => {
  const first = baseEventEntry();
  const second = nextEntry(first, 2);
  const result = verify([first, second]);
  assert.equal(result.eventCount, 2);
  assert.equal(result.headHash, second.event.event_hash);
  assert.deepEqual(result.eventIds, ['evt-001', 'evt-002']);
});

test('rejects payload, event-hash, receipt-signature, sequence and predecessor tampering', () => {
  const original = baseEventEntry();
  assert.throws(() => verify([{ ...original, event: { ...original.event, payload: { reservation_id: 'changed' } } }]), /payload hash/i);
  assert.throws(() => verify([{ ...original, event: { ...original.event, actor_role: 7 } }]), /actor_role/i);
  assert.throws(() => verify([{ ...original, event: { ...original.event, event_hash: 'f'.repeat(64) } }]), /event hash|committed event fields/i);
  assert.throws(() => verify([{ ...original, receipt: { ...original.receipt, signature: 'A'.repeat(86) } }]), /signature/i);
  assert.throws(() => verify([{ ...original, event: { ...original.event, sequence: 2 }, receipt: { ...original.receipt, sequence: 2 } }]), /sequence/i);
  assert.throws(() => verify([{ ...original, event: { ...original.event, previous_event_hash: '1'.repeat(64) }, receipt: { ...original.receipt, previous_event_hash: '1'.repeat(64) } }]), /predecessor/i);
});

test('rejects receipt scope, event identity, order and duplicate-id mismatches', () => {
  const original = baseEventEntry();
  assert.throws(() => verify([{ ...original, receipt: { ...original.receipt, environment_id: 'staging' } }]), /environment/i);
  assert.throws(() => verify([{ ...original, event: { ...original.event, run_id: 'other-run' } }]), /run id/i);
  const second = { ...original, event: { ...original.event, sequence: 2, event_id: 'evt-002' }, receipt: { ...original.receipt, sequence: 2, event_id: 'evt-002' } };
  assert.throws(() => verify([original, second]), /predecessor|event hash/i);
  assert.throws(() => verify([original, original]), /sequence|duplicate/i);
  const duplicateId = nextEntry(original, 2);
  duplicateId.event.event_id = 'evt-001';
  duplicateId.receipt.event_id = 'evt-001';
  assert.throws(() => verify([original, duplicateId]), /duplicated/i);
});

test('rejects revoked or time-invalid signing keys and a revoked status snapshot', () => {
  const revokedKeyBundle = {
    ...bundle,
    keys: [{ ...bundle.keys[0], state: 'revoked', revoked_at_utc: '2026-10-23T11:30:00Z', revocation_id: 'incident-1' }],
  };
  const revokedDigest = sha256(canonicalizeForProfile(revokedKeyBundle));
  const revokedBundleSig = rootSign(revokedKeyBundle, 'ed25519-jcs-trust-bundle-v1');
  const revokedStatus = { ...statusStatement, bundle_sha256: revokedDigest, revoked_keys: [{ key_id: 'audit-key-vector-1', revoked_at_utc: '2026-10-23T11:30:00Z', revocation_id: 'incident-1' }] };
  const revokedStatusSig = rootSign(revokedStatus, 'ed25519-jcs-key-status-v1');
  assert.throws(() => verify([baseEventEntry()], {
    trustBundle: revokedKeyBundle, trustBundleRootSignature: revokedBundleSig, trustBundleDigest: revokedDigest,
    keyStatusStatement: revokedStatus, keyStatusRootSignature: revokedStatusSig,
  }), /revoked/i);
  const outOfWindowBundle = { ...bundle, keys: [{ ...bundle.keys[0], not_after_utc: '2026-10-23T11:59:59Z' }] };
  const outDigest = sha256(canonicalizeForProfile(outOfWindowBundle));
  assert.throws(() => verify([baseEventEntry()], {
    trustBundle: outOfWindowBundle, trustBundleRootSignature: rootSign(outOfWindowBundle, 'ed25519-jcs-trust-bundle-v1'), trustBundleDigest: outDigest,
    keyStatusStatement: { ...statusStatement, bundle_sha256: outDigest },
    keyStatusRootSignature: rootSign({ ...statusStatement, bundle_sha256: outDigest }, 'ed25519-jcs-key-status-v1'),
  }), /valid|window|expired/i);
});


test('accepts a revoked-key receipt only with an independent exact-byte anchor before compromise', () => {
  const entry = baseEventEntry();
  const revokedKeyBundle = {
    ...bundle,
    keys: [{ ...bundle.keys[0], state: 'revoked', revoked_at_utc: '2026-10-23T12:02:00Z', revocation_id: 'incident-10' }],
  };
  const revokedDigest = sha256(canonicalizeForProfile(revokedKeyBundle));
  const revokedStatus = {
    ...statusStatement,
    schema: 'stage5-key-status-statement-v2',
    bundle_sha256: revokedDigest,
    revoked_keys: [{
      key_id: 'audit-key-vector-1', revoked_at_utc: '2026-10-23T12:02:00Z', revocation_id: 'incident-10',
      reason: 'compromise_confirmed', compromise_not_before_utc: '2026-10-23T12:01:00Z',
      incident_review: { review_id: 'review-incident-10', record_sha256: 'c'.repeat(64) },
    }],
  };
  const anchor = signAnchor(entry);
  const result = verify([entry], {
    trustBundle: revokedKeyBundle,
    trustBundleRootSignature: rootSign(revokedKeyBundle, 'ed25519-jcs-trust-bundle-v1'),
    trustBundleDigest: revokedDigest,
    keyStatusStatement: revokedStatus,
    keyStatusRootSignature: rootSign(revokedStatus, 'ed25519-jcs-key-status-v1'),
    keyStatusSchema: keyStatusV2Schema,
    preCompromiseAnchors: [anchor],
    preCompromiseAnchorSchema: anchorSchema,
    trustedAnchor,
  });
  assert.deepEqual(result.historicallyAnchoredEventIds, [entry.event.event_id]);
});

test('does not allow an anchor at or after compromise or for different receipt bytes', () => {
  const entry = baseEventEntry();
  const revokedKeyBundle = {
    ...bundle,
    keys: [{ ...bundle.keys[0], state: 'revoked', revoked_at_utc: '2026-10-23T12:02:00Z', revocation_id: 'incident-10' }],
  };
  const revokedDigest = sha256(canonicalizeForProfile(revokedKeyBundle));
  const revokedStatus = {
    ...statusStatement,
    schema: 'stage5-key-status-statement-v2',
    bundle_sha256: revokedDigest,
    revoked_keys: [{
      key_id: 'audit-key-vector-1', revoked_at_utc: '2026-10-23T12:02:00Z', revocation_id: 'incident-10',
      reason: 'compromise_suspected', compromise_not_before_utc: '2026-10-23T12:01:00Z',
      incident_review: { review_id: 'review-incident-10', record_sha256: 'c'.repeat(64) },
    }],
  };
  const verificationInputs = {
    trustBundle: revokedKeyBundle,
    trustBundleRootSignature: rootSign(revokedKeyBundle, 'ed25519-jcs-trust-bundle-v1'),
    trustBundleDigest: revokedDigest,
    keyStatusStatement: revokedStatus,
    keyStatusRootSignature: rootSign(revokedStatus, 'ed25519-jcs-key-status-v1'),
    keyStatusSchema: keyStatusV2Schema,
    preCompromiseAnchorSchema: anchorSchema,
    trustedAnchor,
  };
  assert.throws(() => verify([entry], { ...verificationInputs, preCompromiseAnchors: [signAnchor(entry, '2026-10-23T12:01:00Z')] }), /before.*compromise|anchor/i);
  const validAnchor = signAnchor(entry);
  assert.throws(() => verify([entry], { ...verificationInputs, preCompromiseAnchors: [validAnchor], trustedAnchor: undefined }), /external.*configuration|anchor/i);
  assert.throws(() => verify([entry], { ...verificationInputs, preCompromiseAnchors: [{ ...validAnchor, signature: 'A'.repeat(86) }] }), /signature/i);
  const altered = { ...entry, receipt: { ...entry.receipt, event_hash: 'f'.repeat(64) } };
  assert.throws(() => verify([entry], { ...verificationInputs, preCompromiseAnchors: [signAnchor(altered)] }), /receipt|anchor|event/i);
});

test('verifies an independent witness chain for every authority event and binds the terminal receipt', () => {
  const witnessSeed = Buffer.from('1f9cbd8a376ee0214d5a7b9c0e2f31461f9cbd8a376ee0214d5a7b9c0e2f3146', 'hex');
  const witnessPrivateKey = createPrivateKey({ key: Buffer.concat([Buffer.from('302e020100300506032b657004220420', 'hex'), witnessSeed]), format: 'der', type: 'pkcs8' });
  const witnessPublicBytes = createPublicKey(witnessPrivateKey).export({ format: 'der', type: 'spki' }).subarray(-32);
  const trustedWitness = {
    witnessId: 'independent-witness-1',
    authorityId: 'witness-domain-1',
    keyId: 'witness-key-1',
    publicKey: witnessPublicBytes.toString('base64url'),
    fingerprintSha256: createHash('sha256').update(witnessPublicBytes).digest('hex'),
  };
  const entries = [baseEventEntry()];
  entries.push(nextEntry(entries[0], 2));
  let previousWitnessDigest = '0'.repeat(64);
  const witnessReceipts = entries.map((entry, index) => {
    const body = {
      schema: 'stage5-independent-witness-receipt-v1',
      hash_profile: 'jcs-rfc8785-v1',
      witness_id: trustedWitness.witnessId,
      authority_id: trustedWitness.authorityId,
      environment_id: entry.receipt.environment_id,
      log_id: entry.receipt.log_id,
      run_id: entry.receipt.run_id,
      authority_sequence: entry.event.sequence,
      authority_event_id: entry.event.event_id,
      authority_event_hash: entry.event.event_hash,
      authority_entry_sha256: sha256(canonicalizeForProfile(entry)),
      witness_sequence: index + 1,
      previous_witness_receipt_sha256: previousWitnessDigest,
      observed_at_utc: `2026-10-23T12:00:0${index + 2}Z`,
      key_id: trustedWitness.keyId,
      signature_algorithm: 'Ed25519',
      signature_profile: 'ed25519-jcs-witness-receipt-v1',
    };
    const receipt = { ...body, signature: sign(null, Buffer.from(canonicalizeForProfile(body)), witnessPrivateKey).toString('base64url') };
    previousWitnessDigest = sha256(canonicalizeForProfile(receipt));
    return receipt;
  });

  assert.ok(witnessReceipts.every((receipt) => validateWitnessReceipt(receipt)));
  assert.equal(validateWitnessReceipt({ ...witnessReceipts[0], unexpected: true }), false);
  const result = verifyDualWitnessReceiptChain({
    authorityEntries: entries,
    witnessReceipts,
    runId: 'run-vector-1',
    environmentId: 'prod-eval',
    logId: 'official-holdout-v1',
    appendAuthorityDomainId: 'registry-domain-1',
    signingKeyCustodianDomainId: 'registry-keys-1',
    trustedWitness,
    witnessReceiptSchema,
    currentTimeUtc: '2026-10-23T12:01:00Z',
    clockSkewSeconds: 0,
  });
  assert.equal(result.verified, true);
  assert.equal(result.terminalWitnessSequence, 2);
  assert.equal(result.terminalEventId, entries[1].event.event_id);
  assert.equal(result.terminalWitnessReceiptSha256, previousWitnessDigest);
  assert.throws(() => verifyDualWitnessReceiptChain({
    authorityEntries: entries, witnessReceipts, runId: 'run-vector-1', environmentId: 'prod-eval',
    logId: 'official-holdout-v1', appendAuthorityDomainId: 'witness-domain-1',
    signingKeyCustodianDomainId: 'registry-keys-1', trustedWitness,
    witnessReceiptSchema,
    currentTimeUtc: '2026-10-23T12:01:00Z', clockSkewSeconds: 0,
  }), /independent trust domain/i);
  const alteredWitness = witnessReceipts.map((receipt) => ({ ...receipt }));
  alteredWitness[1].authority_entry_sha256 = 'f'.repeat(64);
  assert.throws(() => verifyDualWitnessReceiptChain({
    authorityEntries: entries, witnessReceipts: alteredWitness, runId: 'run-vector-1', environmentId: 'prod-eval',
    logId: 'official-holdout-v1', appendAuthorityDomainId: 'registry-domain-1',
    signingKeyCustodianDomainId: 'registry-keys-1', trustedWitness,
    witnessReceiptSchema,
    currentTimeUtc: '2026-10-23T12:01:00Z', clockSkewSeconds: 0,
  }), /exact authority receipt/i);
});

test('rejects a re-signed witness fork that breaks its prior observed head', () => {
  const witnessSeed = Buffer.from('1f9cbd8a376ee0214d5a7b9c0e2f31461f9cbd8a376ee0214d5a7b9c0e2f3146', 'hex');
  const witnessPrivateKey = createPrivateKey({ key: Buffer.concat([Buffer.from('302e020100300506032b657004220420', 'hex'), witnessSeed]), format: 'der', type: 'pkcs8' });
  const witnessPublicBytes = createPublicKey(witnessPrivateKey).export({ format: 'der', type: 'spki' }).subarray(-32);
  const trustedWitness = {
    witnessId: 'independent-witness-1', authorityId: 'witness-domain-1', keyId: 'witness-key-1',
    publicKey: witnessPublicBytes.toString('base64url'),
    fingerprintSha256: createHash('sha256').update(witnessPublicBytes).digest('hex'),
  };
  const entries = [baseEventEntry()];
  entries.push(nextEntry(entries[0], 2));
  const makeReceipt = (entry, sequence, previousDigest) => {
    const body = {
      schema: 'stage5-independent-witness-receipt-v1', hash_profile: 'jcs-rfc8785-v1',
      witness_id: trustedWitness.witnessId, authority_id: trustedWitness.authorityId,
      environment_id: entry.receipt.environment_id, log_id: entry.receipt.log_id, run_id: entry.receipt.run_id,
      authority_sequence: entry.event.sequence, authority_event_id: entry.event.event_id,
      authority_event_hash: entry.event.event_hash, authority_entry_sha256: sha256(canonicalizeForProfile(entry)),
      witness_sequence: sequence, previous_witness_receipt_sha256: previousDigest,
      observed_at_utc: `2026-10-23T12:00:0${sequence + 1}Z`, key_id: trustedWitness.keyId,
      signature_algorithm: 'Ed25519', signature_profile: 'ed25519-jcs-witness-receipt-v1',
    };
    return { ...body, signature: sign(null, Buffer.from(canonicalizeForProfile(body)), witnessPrivateKey).toString('base64url') };
  };
  const first = makeReceipt(entries[0], 1, '0'.repeat(64));
  const fork = makeReceipt(entries[1], 2, 'f'.repeat(64));
  assert.throws(() => verifyDualWitnessReceiptChain({
    authorityEntries: entries,
    witnessReceipts: [first, fork],
    runId: 'run-vector-1',
    environmentId: 'prod-eval',
    logId: 'official-holdout-v1',
    appendAuthorityDomainId: 'registry-domain-1',
    signingKeyCustodianDomainId: 'registry-keys-1',
    trustedWitness,
    witnessReceiptSchema,
    currentTimeUtc: '2026-10-23T12:01:00Z',
    clockSkewSeconds: 0,
  }), /predecessor|witness chain/i);
});

test('does not accept a different trusted key when the frozen run permits only one signer', () => {
  const alternateBundle = {
    ...bundle,
    keys: [...bundle.keys, {
      key_id: 'audit-key-alternate', algorithm: 'Ed25519', public_key: Buffer.alloc(32, 7).toString('base64url'),
      state: 'active', not_before_utc: '2026-10-23T11:00:00Z', not_after_utc: '2027-10-23T11:00:00Z',
    }],
  };
  const alternateDigest = sha256(canonicalizeForProfile(alternateBundle));
  const alternateStatus = { ...statusStatement, bundle_sha256: alternateDigest };
  assert.throws(() => verify([{
    ...baseEventEntry(),
    receipt: { ...baseEventEntry().receipt, key_id: 'audit-key-alternate' },
  }], {
    trustBundle: alternateBundle,
    trustBundleRootSignature: rootSign(alternateBundle, 'ed25519-jcs-trust-bundle-v1'),
    trustBundleDigest: alternateDigest,
    keyStatusStatement: alternateStatus,
    keyStatusRootSignature: rootSign(alternateStatus, 'ed25519-jcs-key-status-v1'),
  }), /permitted signer/i);
});
