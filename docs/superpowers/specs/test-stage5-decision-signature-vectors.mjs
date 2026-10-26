import assert from 'node:assert/strict';
import { createHash, createPublicKey, verify } from 'node:crypto';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import canonicalize from 'canonicalize';

const document = JSON.parse(
  await readFile(new URL('stage5-decision-signature-vectors-v1.json', import.meta.url), 'utf8'),
);
const publicKeyPrefix = Buffer.from('302a300506032b6570032100', 'hex');

test('decision receipt signature vector is test-only and uses the pinned profile', () => {
  assert.equal(document.schema, 'stage5-decision-signature-vectors-v1');
  assert.equal(document.test_only, true);
  assert.equal(document.vector.profile, 'ed25519-jcs-stage5-decision-v1');
});

test('decision receipt canonical bytes, digest, and Ed25519 signature interoperate', () => {
  const { vector } = document;
  const canonical = canonicalize(vector.message);
  assert.equal(canonical, vector.canonical_utf8);
  assert.equal(createHash('sha256').update(canonical, 'utf8').digest('hex'), vector.sha256);

  const publicKey = createPublicKey({
    key: Buffer.concat([publicKeyPrefix, Buffer.from(vector.public_key_base64url, 'base64url')]),
    format: 'der',
    type: 'spki',
  });
  const signature = Buffer.from(vector.signature_base64url, 'base64url');
  assert.equal(verify(null, Buffer.from(canonical, 'utf8'), publicKey, signature), true);
  assert.equal(
    verify(
      null,
      Buffer.from(canonicalize({ ...vector.message, holdout_outcome: 'failed' }), 'utf8'),
      publicKey,
      signature,
    ),
    false,
  );
});
