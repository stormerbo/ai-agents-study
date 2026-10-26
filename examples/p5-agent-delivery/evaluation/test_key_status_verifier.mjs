import assert from 'node:assert/strict';
import { createHash, createPrivateKey, createPublicKey, sign } from 'node:crypto';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import { canonicalizeForProfile } from './jcs-profile.mjs';
import { verifyKeyStatusStatement } from './key-status-verifier.mjs';

const schema = JSON.parse(await readFile(new URL('./key-status.schema.json', import.meta.url), 'utf8'));
const schemaV2 = JSON.parse(await readFile(new URL('./key-status-v2.schema.json', import.meta.url), 'utf8'));
const seed = Buffer.from('9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60', 'hex');
const privateKey = createPrivateKey({ key: Buffer.concat([Buffer.from('302e020100300506032b657004220420', 'hex'), seed]), format: 'der', type: 'pkcs8' });
const publicDer = createPublicKey(privateKey).export({ format: 'der', type: 'spki' });
const rootBytes = publicDer.subarray(-32);
const trustedRoot = {
  keyId: 'offline-root-1',
  publicKey: rootBytes.toString('base64url'),
  fingerprintSha256: createHash('sha256').update(rootBytes).digest('hex'),
};
const frozenBundle = {
  digest: 'b'.repeat(64),
  environmentId: 'prod-eval',
  logId: 'official-holdout-v1',
  keys: [{ key_id: 'audit-key-2026-02', not_before_utc: '2026-10-23T00:00:00Z' }],
};
const statement = {
  schema: 'stage5-key-status-statement-v1',
  statement_id: 'status-2026-10-23-04',
  sequence: 4,
  bundle_sha256: frozenBundle.digest,
  environment_id: frozenBundle.environmentId,
  log_id: frozenBundle.logId,
  issued_at_utc: '2026-10-23T11:59:00Z',
  expires_at_utc: '2026-10-23T12:04:00Z',
  revoked_keys: [],
};

function signedStatement(value = statement, signatureOverride) {
  const bytes = Buffer.from(canonicalizeForProfile(value), 'utf8');
  return {
    statement: value,
    rootSignature: {
      schema: 'stage5-trust-root-signature-v1',
      root_key_id: trustedRoot.keyId,
      profile: 'ed25519-jcs-key-status-v1',
      signature: signatureOverride ?? sign(null, bytes, privateKey).toString('base64url'),
    },
  };
}

const options = (overrides = {}) => ({
  ...signedStatement(),
  trustedRoot,
  frozenBundle,
  currentTimeUtc: '2026-10-23T12:00:00Z',
  maxFreshnessSeconds: 600,
  minimumSequence: 4,
  schema,
  ...overrides,
});

test('accepts a valid fresh root-signed status snapshot for the frozen bundle and scope', () => {
  const result = verifyKeyStatusStatement(options());
  assert.equal(result.sequence, 4);
  assert.deepEqual(result.revokedKeyIds, []);
  assert.equal(result.validUntilUtc, statement.expires_at_utc);
});

test('rejects unavailable, stale, future-dated, or overlong status statements', () => {
  assert.throws(() => verifyKeyStatusStatement(options({ statement: null, rootSignature: null })), /unavailable/i);
  const expired = { ...statement, expires_at_utc: '2026-10-23T11:59:59Z' };
  assert.throws(() => verifyKeyStatusStatement(options(signedStatement(expired))), /expired|freshness/i);
  const old = { ...statement, issued_at_utc: '2026-10-23T11:40:00Z', expires_at_utc: '2026-10-23T12:10:00Z' };
  assert.throws(() => verifyKeyStatusStatement(options(signedStatement(old))), /stale|freshness/i);
  const long = { ...statement, expires_at_utc: '2026-10-23T12:20:00Z' };
  assert.throws(() => verifyKeyStatusStatement(options(signedStatement(long))), /freshness/i);
  const future = { ...statement, issued_at_utc: '2026-10-23T12:01:00Z', expires_at_utc: '2026-10-23T12:05:00Z' };
  assert.throws(() => verifyKeyStatusStatement(options({ ...signedStatement(future), clockSkewSeconds: 0 })), /future/i);
});

test('rejects signature, frozen bundle, environment, log, and sequence mismatches', () => {
  const tampered = signedStatement(statement, 'A'.repeat(86));
  assert.throws(() => verifyKeyStatusStatement(options(tampered)), /signature/i);
  assert.throws(() => verifyKeyStatusStatement(options({ frozenBundle: { ...frozenBundle, digest: 'c'.repeat(64) } })), /bundle digest/i);
  assert.throws(() => verifyKeyStatusStatement(options({ frozenBundle: { ...frozenBundle, environmentId: 'staging' } })), /environment/i);
  assert.throws(() => verifyKeyStatusStatement(options({ frozenBundle: { ...frozenBundle, logId: 'other-log' } })), /log/i);
  assert.throws(() => verifyKeyStatusStatement(options({ minimumSequence: 5 })), /rollback/i);
});

test('rejects duplicate or unknown revoked key ids and invalid revocation timestamps', () => {
  const revoked = { key_id: 'audit-key-2026-02', revoked_at_utc: '2026-10-23T11:00:00Z', revocation_id: 'incident-9' };
  const duplicate = { ...statement, revoked_keys: [revoked, revoked] };
  assert.throws(() => verifyKeyStatusStatement(options(signedStatement(duplicate))), /duplicate .*key/i);
  const unknown = { ...statement, revoked_keys: [{ ...revoked, key_id: 'unknown-key' }] };
  assert.throws(() => verifyKeyStatusStatement(options(signedStatement(unknown))), /unknown key/i);
  const invalidDate = { ...statement, revoked_keys: [{ ...revoked, revoked_at_utc: '2026-02-31T11:00:00Z' }] };
  assert.throws(() => verifyKeyStatusStatement(options(signedStatement(invalidDate))), /timestamp/i);
});

test('v2 exposes a compromise boundary only from a reviewed signed status entry', () => {
  const compromised = {
    key_id: 'audit-key-2026-02',
    revoked_at_utc: '2026-10-23T11:30:00Z',
    revocation_id: 'incident-10',
    reason: 'compromise_confirmed',
    compromise_not_before_utc: '2026-10-23T10:45:00Z',
    incident_review: { review_id: 'review-10', record_sha256: 'c'.repeat(64) },
  };
  const value = { ...statement, schema: 'stage5-key-status-statement-v2', revoked_keys: [compromised] };
  const result = verifyKeyStatusStatement(options({ ...signedStatement(value), schema: schemaV2 }));
  assert.deepEqual(result.compromiseBoundaries, [{ keyId: compromised.key_id, notBeforeUtc: compromised.compromise_not_before_utc, incidentReviewId: 'review-10', incidentReviewSha256: 'c'.repeat(64) }]);
});

test('v2 refuses compromise exception without a reviewed boundary or with a future boundary', () => {
  const compromised = {
    key_id: 'audit-key-2026-02', revoked_at_utc: '2026-10-23T11:30:00Z', revocation_id: 'incident-10',
    reason: 'compromise_suspected', compromise_not_before_utc: '2026-10-23T10:45:00Z',
    incident_review: { review_id: 'review-10', record_sha256: 'c'.repeat(64) },
  };
  const missingReview = { ...statement, schema: 'stage5-key-status-statement-v2', revoked_keys: [{ ...compromised, incident_review: null }] };
  assert.throws(() => verifyKeyStatusStatement(options({ ...signedStatement(missingReview), schema: schemaV2 })), /schema/i);
  const futureBoundary = { ...compromised, compromise_not_before_utc: '2026-10-23T11:45:00Z' };
  const future = { ...statement, schema: 'stage5-key-status-statement-v2', revoked_keys: [futureBoundary] };
  assert.throws(() => verifyKeyStatusStatement(options({ ...signedStatement(future), schema: schemaV2 })), /compromise boundary/i);
});

test('v2 keeps compromised keys without a known boundary ineligible for historical exceptions', () => {
  const entry = {
    key_id: 'audit-key-2026-02', revoked_at_utc: '2026-10-23T11:30:00Z', revocation_id: 'incident-11',
    reason: 'compromise_suspected', compromise_not_before_utc: null,
    incident_review: { review_id: 'review-11', record_sha256: 'd'.repeat(64) },
  };
  const value = { ...statement, schema: 'stage5-key-status-statement-v2', revoked_keys: [entry] };
  const result = verifyKeyStatusStatement(options({ ...signedStatement(value), schema: schemaV2 }));
  assert.deepEqual(result.compromiseBoundaries, []);
  assert.ok(result.revokedKeyIds.includes(entry.key_id));
});
