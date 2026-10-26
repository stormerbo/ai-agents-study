import Ajv2020 from 'ajv/dist/2020.js';
import { parseUtcTimestamp, verifyRootSignedPayload } from './trust-bundle-verifier.mjs';

const PROFILE = 'ed25519-jcs-key-status-v1';

function fail(message) {
  throw new Error(`Key status verification failed: ${message}`);
}

export function verifyKeyStatusStatement({
  statement,
  rootSignature,
  trustedRoot,
  frozenBundle,
  currentTimeUtc,
  maxFreshnessSeconds,
  minimumSequence,
  clockSkewSeconds = 0,
  schema,
}) {
  if (!statement || !rootSignature) fail('status statement is unavailable');
  if (!frozenBundle || !Array.isArray(frozenBundle.keys) || !schema) fail('frozen bundle keys and statement schema are required');
  if (!Number.isSafeInteger(maxFreshnessSeconds) || maxFreshnessSeconds < 1) fail('freshness policy must be a positive safe integer');
  if (!Number.isSafeInteger(minimumSequence) || minimumSequence < 1) fail('minimum sequence must be a positive safe integer');
  if (!Number.isSafeInteger(clockSkewSeconds) || clockSkewSeconds < 0 || clockSkewSeconds > 300) fail('clock skew allowance must be between 0 and 300 seconds');

  const supportedSchemas = new Set(['stage5-key-status-statement-v1', 'stage5-key-status-statement-v2']);
  if (!supportedSchemas.has(statement.schema) || schema.properties?.schema?.const !== statement.schema) {
    fail('unsupported key status schema');
  }
  const isV2 = statement.schema === 'stage5-key-status-statement-v2';
  const validate = new Ajv2020({ allErrors: true, strict: true, strictRequired: false }).compile(schema);
  if (!validate(statement)) fail(`statement schema is invalid (${validate.errors?.map(({ instancePath, keyword }) => `${instancePath || '/'} ${keyword}`).join('; ')})`);

  const digest = verifyRootSignedPayload({
    payload: statement,
    rootSignature,
    trustedRoot,
    expectedProfile: PROFILE,
  });
  if (statement.bundle_sha256 !== frozenBundle.digest) fail('bundle digest does not match the frozen run');
  if (statement.environment_id !== frozenBundle.environmentId) fail('environment does not match the frozen bundle');
  if (statement.log_id !== frozenBundle.logId) fail('log does not match the frozen bundle');
  if (statement.sequence < minimumSequence) fail('status sequence rollback detected');

  const now = parseUtcTimestamp(currentTimeUtc, 'verifier.current_time_utc');
  const issuedAt = parseUtcTimestamp(statement.issued_at_utc, 'statement.issued_at_utc');
  const expiresAt = parseUtcTimestamp(statement.expires_at_utc, 'statement.expires_at_utc');
  const freshnessMs = maxFreshnessSeconds * 1000;
  if (issuedAt > now + clockSkewSeconds * 1000) fail('statement is future dated');
  if (now - issuedAt > freshnessMs) fail('statement is stale under the declared freshness policy');
  if (expiresAt <= now) fail('statement has expired');
  if (expiresAt <= issuedAt || expiresAt - issuedAt > freshnessMs) fail('statement validity exceeds the declared freshness policy');

  const bundleKeys = new Map(frozenBundle.keys.map((key) => [key.key_id, key]));
  if (bundleKeys.size !== frozenBundle.keys.length) fail('frozen bundle contains duplicate key ids');
  const revoked = new Map();
  const compromiseBoundaries = [];
  for (const entry of statement.revoked_keys) {
    if (revoked.has(entry.key_id)) fail(`duplicate revoked key id ${entry.key_id}`);
    const bundleKey = bundleKeys.get(entry.key_id);
    if (!bundleKey) fail(`unknown key in revocation statement: ${entry.key_id}`);
    const revokedAt = parseUtcTimestamp(entry.revoked_at_utc, `${entry.key_id}.revoked_at_utc`);
    const notBefore = parseUtcTimestamp(bundleKey.not_before_utc, `${entry.key_id}.not_before_utc`);
    if (revokedAt < notBefore) fail(`revocation predates key activation for ${entry.key_id}`);
    if (bundleKey.state === 'revoked' && (bundleKey.revoked_at_utc !== entry.revoked_at_utc || bundleKey.revocation_id !== entry.revocation_id)) {
      fail(`revocation snapshot conflicts with frozen bundle for ${entry.key_id}`);
    }
    if (isV2 && entry.reason !== 'routine' && entry.compromise_not_before_utc !== null) {
      const compromiseNotBefore = parseUtcTimestamp(entry.compromise_not_before_utc, `${entry.key_id}.compromise_not_before_utc`);
      if (compromiseNotBefore < notBefore || compromiseNotBefore > revokedAt) {
        fail(`compromise boundary is outside key activation and revocation for ${entry.key_id}`);
      }
      compromiseBoundaries.push(Object.freeze({
        keyId: entry.key_id,
        notBeforeUtc: entry.compromise_not_before_utc,
        incidentReviewId: entry.incident_review.review_id,
        incidentReviewSha256: entry.incident_review.record_sha256,
      }));
    }
    revoked.set(entry.key_id, Object.freeze({ ...entry }));
  }
  for (const key of frozenBundle.keys) {
    if (key.state === 'revoked' && !revoked.has(key.key_id)) fail(`revoked frozen key is absent from status snapshot: ${key.key_id}`);
  }

  return Object.freeze({
    statementId: statement.statement_id,
    sequence: statement.sequence,
    digest,
    checkedAtUtc: currentTimeUtc,
    validUntilUtc: statement.expires_at_utc,
    revokedKeys: Object.freeze([...revoked.values()]),
    revokedKeyIds: Object.freeze([...revoked.keys()]),
    compromiseBoundaries: Object.freeze(compromiseBoundaries),
  });
}
