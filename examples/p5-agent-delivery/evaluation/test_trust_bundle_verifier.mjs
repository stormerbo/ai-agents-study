import assert from 'node:assert/strict';
import { createHash, createPrivateKey, createPublicKey, sign } from 'node:crypto';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import { canonicalizeForProfile } from './jcs-profile.mjs';
import { verifyTrustBundle, receiptKeyStatusAt } from './trust-bundle-verifier.mjs';

const schema = JSON.parse(await readFile(new URL('./trust-bundle.schema.json', import.meta.url), 'utf8'));
const seed = Buffer.from('9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60', 'hex');
const privateKey = createPrivateKey({ key: Buffer.concat([Buffer.from('302e020100300506032b657004220420', 'hex'), seed]), format: 'der', type: 'pkcs8' });
const publicKey = createPublicKey(privateKey);
const rootPublicKeyBytes = publicKey.export({ format: 'der', type: 'spki' }).subarray(-32);
const rootPublicKey = rootPublicKeyBytes.toString('base64url');
const rootFingerprint = createHash('sha256').update(rootPublicKeyBytes).digest('hex');

const payload = {
  schema: 'stage5-receipt-trust-bundle-v1',
  bundle_id: 'stage5-trust-2026-10-23-01',
  hash_profile: 'jcs-rfc8785-v1',
  signature_profile: 'ed25519-jcs-receipt-v1',
  environment_id: 'prod-eval',
  log_id: 'official-holdout-v1',
  issued_at_utc: '2026-10-23T09:00:00Z',
  keys: [{
    key_id: 'audit-key-2026-02', algorithm: 'Ed25519', public_key: 'A'.repeat(43), state: 'active',
    not_before_utc: '2026-10-23T09:00:00Z', not_after_utc: '2027-01-23T00:00:00Z',
  }],
};

function signedArtifact(bundle = payload, overrides = {}) {
  const bytes = Buffer.from(canonicalizeForProfile(bundle), 'utf8');
  return {
    bundle,
    expectedDigest: createHash('sha256').update(bytes).digest('hex'),
    rootSignature: {
      schema: 'stage5-trust-root-signature-v1',
      root_key_id: 'offline-root-1',
      profile: 'ed25519-jcs-trust-bundle-v1',
      signature: sign(null, bytes, privateKey).toString('base64url'),
      ...overrides,
    },
    trustedRoot: { keyId: 'offline-root-1', publicKey: rootPublicKey, fingerprintSha256: rootFingerprint },
    expectedScope: {
      environmentId: bundle.environment_id,
      logId: bundle.log_id,
      permittedSignerKeyId: bundle.keys[0].key_id,
    },
  };
}

test('accepts a root-signed bundle pinned by digest and root key id', () => {
  const result = verifyTrustBundle({ ...signedArtifact(), schema });
  assert.equal(result.bundleId, payload.bundle_id);
  assert.equal(result.keys.length, 1);
});

test('matches RFC 8032 Ed25519 test vector 1', () => {
  assert.equal(rootPublicKeyBytes.toString('hex'), 'd75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a');
  assert.equal(sign(null, Buffer.alloc(0), privateKey).toString('hex'), 'e5564300c360ac729086e2cc806e828a84877f1eb8e5d974d873e06522490155' + '5fb8821590a33bacc61e39701cf9b46bd25bf5f0595bbe24655141438e7a100b');
});

test('rejects changed payload, wrong frozen digest, and unpinned root identity', () => {
  const artifact = signedArtifact();
  assert.throws(() => verifyTrustBundle({ ...artifact, schema, bundle: { ...payload, log_id: 'other-log' } }), /digest|signature/i);
  assert.throws(() => verifyTrustBundle({ ...artifact, schema, expectedDigest: '0'.repeat(64) }), /digest/i);
  assert.throws(() => verifyTrustBundle({ ...artifact, schema, trustedRoot: { ...artifact.trustedRoot, keyId: 'attacker-root' } }), /root key/i);
  assert.throws(() => verifyTrustBundle({ ...artifact, schema, trustedRoot: { ...artifact.trustedRoot, fingerprintSha256: '0'.repeat(64) } }), /fingerprint/i);
});

test('binds the verified bundle to the frozen environment, log, and permitted signer key', () => {
  const artifact = signedArtifact();
  assert.throws(() => verifyTrustBundle({ ...artifact, schema, expectedScope: { ...artifact.expectedScope, environmentId: 'staging' } }), /environment/i);
  assert.throws(() => verifyTrustBundle({ ...artifact, schema, expectedScope: { ...artifact.expectedScope, logId: 'other-log' } }), /log/i);
  assert.throws(() => verifyTrustBundle({ ...artifact, schema, expectedScope: { ...artifact.expectedScope, permittedSignerKeyId: 'other-key' } }), /permitted signer/i);
});

test('rejects malformed or invalid root signatures and structurally invalid bundles', () => {
  const artifact = signedArtifact(payload, { signature: 'A'.repeat(86) });
  assert.throws(() => verifyTrustBundle({ ...artifact, schema }), /signature/i);
  assert.throws(() => verifyTrustBundle({ ...signedArtifact({ ...payload, extra: true }), schema }), /schema/i);
});

test('rejects duplicate key ids and impossible UTC validity intervals', () => {
  const duplicate = { ...payload, keys: [payload.keys[0], { ...payload.keys[0], public_key: 'B'.repeat(43) }] };
  assert.throws(() => verifyTrustBundle({ ...signedArtifact(duplicate), schema }), /duplicate key/i);
  const inverted = { ...payload, keys: [{ ...payload.keys[0], not_before_utc: '2027-01-24T00:00:00Z' }] };
  assert.throws(() => verifyTrustBundle({ ...signedArtifact(inverted), schema }), /validity interval/i);
  const impossible = { ...payload, issued_at_utc: '2026-02-31T00:00:00Z' };
  assert.throws(() => verifyTrustBundle({ ...signedArtifact(impossible), schema }), /timestamp/i);
});

test('retired keys verify only receipts inside their recorded validity window; revoked keys fail closed', () => {
  const retired = {
    ...payload.keys[0], state: 'retired', retired_at_utc: '2026-12-01T00:00:00Z',
  };
  assert.equal(receiptKeyStatusAt(retired, '2026-11-01T00:00:00Z'), 'valid');
  assert.equal(receiptKeyStatusAt(retired, '2026-12-02T00:00:00Z'), 'invalid');
  const revoked = {
    ...payload.keys[0], state: 'revoked', revoked_at_utc: '2026-12-01T00:00:00Z', revocation_id: 'incident-17',
  };
  assert.equal(receiptKeyStatusAt(revoked, '2026-11-01T00:00:00Z'), 'revoked');
});
