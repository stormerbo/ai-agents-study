import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import Ajv2020 from 'ajv/dist/2020.js';

const schema = JSON.parse(await readFile(new URL('./trust-bundle.schema.json', import.meta.url), 'utf8'));
const ajv = new Ajv2020({ allErrors: true, strict: true, strictRequired: false });
const validate = ajv.compile(schema);

const good = {
  schema: 'stage5-receipt-trust-bundle-v1',
  bundle_id: 'stage5-trust-2026-10-23-01',
  hash_profile: 'jcs-rfc8785-v1',
  signature_profile: 'ed25519-jcs-receipt-v1',
  environment_id: 'prod-eval',
  log_id: 'official-holdout-v1',
  issued_at_utc: '2026-10-23T09:00:00Z',
  keys: [{
    key_id: 'audit-key-2026-02',
    algorithm: 'Ed25519',
    public_key: 'A'.repeat(43),
    state: 'active',
    not_before_utc: '2026-10-23T09:00:00Z',
    not_after_utc: '2027-01-23T00:00:00Z',
  }],
};

function valid(bundle) {
  return validate(bundle);
}

test('accepts the documented active-key trust bundle', () => {
  assert.equal(valid(good), true, JSON.stringify(validate.errors));
});

test('rejects unknown fields and wildcard-like scope', () => {
  assert.equal(valid({ ...good, owner_note: 'ignored?' }), false);
  assert.equal(valid({ ...good, environment_id: '*' }), false);
  assert.equal(valid({ ...good, log_id: '*' }), false);
});

test('requires retirement and revocation metadata for those key states', () => {
  const key = good.keys[0];
  assert.equal(valid({ ...good, keys: [{ ...key, state: 'retired' }] }), false);
  assert.equal(valid({ ...good, keys: [{ ...key, state: 'retired', retired_at_utc: '2026-10-24T00:00:00Z' }] }), true);
  assert.equal(valid({ ...good, keys: [{ ...key, state: 'revoked' }] }), false);
  assert.equal(valid({ ...good, keys: [{ ...key, state: 'revoked', revoked_at_utc: '2026-10-24T00:00:00Z', revocation_id: 'incident-17' }] }), true);
});

test('rejects malformed UTC timestamps and non-canonical public-key encoding length', () => {
  assert.equal(valid({ ...good, issued_at_utc: '2026-10-23' }), false);
  assert.equal(valid({ ...good, keys: [{ ...good.keys[0], public_key: 'short' }] }), false);
});

test('documents semantic checks JSON Schema alone cannot enforce', () => {
  assert.match(schema.$comment, /unique key_id/i);
  assert.match(schema.$comment, /signature verification/i);
});
