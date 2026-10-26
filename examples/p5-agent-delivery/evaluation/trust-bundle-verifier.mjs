import { createHash, createPublicKey, verify } from 'node:crypto';
import Ajv2020 from 'ajv/dist/2020.js';
import { canonicalizeForProfile } from './jcs-profile.mjs';

const ED25519_SPKI_PREFIX = Buffer.from('302a300506032b6570032100', 'hex');
const ROOT_SIGNATURE_SCHEMA = 'stage5-trust-root-signature-v1';
const ROOT_SIGNATURE_PROFILE = 'ed25519-jcs-trust-bundle-v1';

function fail(message) {
  throw new Error(`Trust bundle verification failed: ${message}`);
}

function decodeBase64Url(value, expectedBytes, field) {
  if (typeof value !== 'string' || !/^[A-Za-z0-9_-]+$/.test(value)) fail(`${field} is not unpadded base64url`);
  const bytes = Buffer.from(value, 'base64url');
  if (bytes.length !== expectedBytes || bytes.toString('base64url') !== value) fail(`${field} has invalid encoding or length`);
  return bytes;
}

export function parseUtcTimestamp(value, field) {
  const match = typeof value === 'string'
    ? /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.(\d{1,6}))?Z$/.exec(value)
    : null;
  if (!match) fail(`${field} is not a UTC timestamp`);
  const [, yearText, monthText, dayText, hourText, minuteText, secondText] = match;
  const [year, month, day, hour, minute, second] = [yearText, monthText, dayText, hourText, minuteText, secondText].map(Number);
  if (year < 1970 || month < 1 || month > 12 || hour > 23 || minute > 59 || second > 59) fail(`${field} is outside the supported timestamp range`);
  const date = new Date(0);
  date.setUTCFullYear(year, month - 1, day);
  date.setUTCHours(hour, minute, second, 0);
  if (date.getUTCFullYear() !== year || date.getUTCMonth() !== month - 1 || date.getUTCDate() !== day) fail(`${field} is not a real calendar timestamp`);
  return Date.parse(value);
}

export function verifyRootSignedPayload({ payload, rootSignature, trustedRoot, expectedDigest, expectedProfile }) {
  if (expectedDigest !== undefined && !/^[a-f0-9]{64}$/.test(expectedDigest)) fail('frozen digest must be lowercase SHA-256 hex');
  let payloadBytes;
  try {
    payloadBytes = Buffer.from(canonicalizeForProfile(payload), 'utf8');
  } catch (error) {
    fail(`payload cannot be canonicalized (${error.message})`);
  }
  const digest = createHash('sha256').update(payloadBytes).digest('hex');
  if (expectedDigest !== undefined && digest !== expectedDigest) fail('payload digest does not match the frozen digest');
  if (!rootSignature || Object.keys(rootSignature).sort().join(',') !== 'profile,root_key_id,schema,signature') fail('detached root signature has an invalid shape');
  if (rootSignature.schema !== ROOT_SIGNATURE_SCHEMA || rootSignature.profile !== expectedProfile) fail('unsupported root signature profile');
  if (!trustedRoot || typeof trustedRoot.keyId !== 'string' || rootSignature.root_key_id !== trustedRoot.keyId) fail('root key id is not pinned by release configuration');

  const rootBytes = decodeBase64Url(trustedRoot.publicKey, 32, 'pinned root public key');
  if (!/^[a-f0-9]{64}$/.test(trustedRoot.fingerprintSha256 ?? '')) fail('release-pinned root fingerprint must be lowercase SHA-256 hex');
  if (createHash('sha256').update(rootBytes).digest('hex') !== trustedRoot.fingerprintSha256) fail('pinned root fingerprint does not match the configured root key');
  const rootKey = createPublicKey({ key: Buffer.concat([ED25519_SPKI_PREFIX, rootBytes]), format: 'der', type: 'spki' });
  const signatureBytes = decodeBase64Url(rootSignature.signature, 64, 'root signature');
  if (!verify(null, payloadBytes, rootKey, signatureBytes)) fail('root signature is invalid');
  return digest;
}

export function verifyTrustBundle({ bundle, rootSignature, trustedRoot, expectedDigest, expectedScope, schema }) {
  if (!schema || !bundle || !expectedScope) fail('schema, payload, and frozen expected scope are required');
  const validate = new Ajv2020({ allErrors: true, strict: true, strictRequired: false }).compile(schema);
  if (!validate(bundle)) fail(`payload schema is invalid (${validate.errors?.map(({ instancePath, keyword }) => `${instancePath || '/'} ${keyword}`).join('; ')})`);
  const digest = verifyRootSignedPayload({ payload: bundle, rootSignature, trustedRoot, expectedDigest, expectedProfile: ROOT_SIGNATURE_PROFILE });
  parseUtcTimestamp(bundle.issued_at_utc, 'issued_at_utc');

  const keyIds = new Set();
  const keys = bundle.keys.map((key) => {
    if (keyIds.has(key.key_id)) fail(`duplicate key id ${key.key_id}`);
    keyIds.add(key.key_id);
    decodeBase64Url(key.public_key, 32, `public key ${key.key_id}`);
    const notBefore = parseUtcTimestamp(key.not_before_utc, `${key.key_id}.not_before_utc`);
    const notAfter = parseUtcTimestamp(key.not_after_utc, `${key.key_id}.not_after_utc`);
    if (notBefore >= notAfter) fail(`key ${key.key_id} has an invalid validity interval`);
    if (key.retired_at_utc && parseUtcTimestamp(key.retired_at_utc, `${key.key_id}.retired_at_utc`) < notBefore) fail(`key ${key.key_id} retires before activation`);
    if (key.revoked_at_utc && parseUtcTimestamp(key.revoked_at_utc, `${key.key_id}.revoked_at_utc`) < notBefore) fail(`key ${key.key_id} is revoked before activation`);
    return Object.freeze({ ...key });
  });

  if (bundle.environment_id !== expectedScope.environmentId) fail('environment does not match the frozen run scope');
  if (bundle.log_id !== expectedScope.logId) fail('log does not match the frozen run scope');
  if (typeof expectedScope.permittedSignerKeyId !== 'string' || !keyIds.has(expectedScope.permittedSignerKeyId)) fail('permitted signer key is absent from the frozen bundle');

  return Object.freeze({ bundleId: bundle.bundle_id, environmentId: bundle.environment_id, logId: bundle.log_id, digest, keys: Object.freeze(keys) });
}

export function receiptKeyStatusAt(key, authorityRecordedAtUtc) {
  if (key.state === 'revoked') return 'revoked';
  const eventTime = parseUtcTimestamp(authorityRecordedAtUtc, 'receipt.registry_recorded_at');
  const notBefore = parseUtcTimestamp(key.not_before_utc, `${key.key_id}.not_before_utc`);
  const notAfter = parseUtcTimestamp(key.not_after_utc, `${key.key_id}.not_after_utc`);
  if (eventTime < notBefore || eventTime > notAfter) return 'invalid';
  if (key.state === 'retired' && eventTime > parseUtcTimestamp(key.retired_at_utc, `${key.key_id}.retired_at_utc`)) return 'invalid';
  return 'valid';
}
