import assert from 'node:assert/strict';
import { createHash, createPublicKey, verify } from 'node:crypto';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import canonicalize from 'canonicalize';
import { canonicalizeForProfile } from './jcs-profile.mjs';

const vectors = JSON.parse(await readFile(new URL('./jcs-vectors.json', import.meta.url), 'utf8'));

for (const vector of vectors) {
  test(`RFC 8785 implementation matches ${vector.id}`, () => {
    const canonical = canonicalize(vector.value);
    assert.equal(canonical, vector.canonical_utf8);
    assert.equal(createHash('sha256').update(canonical, 'utf8').digest('hex'), vector.sha256);
  });
}

test('project profile rejects integers outside the interoperable range', () => {
  assert.equal(canonicalizeForProfile({ count: 9007199254740991 }), '{"count":9007199254740991}');
  for (const value of [
    { count: 9007199254740992 },
    { metrics: { count: 9007199254740992 } },
    { counts: [9007199254740992] },
  ]) {
    assert.throws(() => canonicalizeForProfile(value), /safe integer range/);
  }
});

test('project profile rejects non-finite numbers before canonicalization', () => {
  for (const value of [NaN, Infinity, -Infinity]) {
    assert.throws(() => canonicalizeForProfile({ value }), /must be finite/);
  }
});

test('source probe journal page verifies the shared cross-language Ed25519 vector', () => {
  const vector = vectors.find((item) => item.id === 'stage5-source-probe-journal-page');
  assert.ok(vector, 'missing source probe journal page vector');
  const publicKey = createPublicKey({
    key: Buffer.concat([
      Buffer.from('302a300506032b6570032100', 'hex'),
      Buffer.from(vector.ed25519_public_key_base64url, 'base64url'),
    ]),
    format: 'der',
    type: 'spki',
  });
  const signature = Buffer.from(vector.ed25519_signature_base64url, 'base64url');
  assert.equal(
    verify(null, Buffer.from(vector.canonical_utf8, 'utf8'), publicKey, signature),
    true,
  );
  assert.equal(
    verify(
      null,
      Buffer.from(canonicalize({ ...vector.value, query_nonce: 'B'.repeat(43) }), 'utf8'),
      publicKey,
      signature,
    ),
    false,
  );
});
