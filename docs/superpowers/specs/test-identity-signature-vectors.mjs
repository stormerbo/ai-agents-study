import assert from 'node:assert/strict';
import { createHash, createPublicKey, verify } from 'node:crypto';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import canonicalize from 'canonicalize';

const vectorDocument = JSON.parse(
  await readFile(
    new URL('stage5-identity-signature-vectors-v1.json', import.meta.url),
    'utf8',
  ),
);

const publicKeyPrefix = Buffer.from('302a300506032b6570032100', 'hex');

test('identity signature vectors are explicitly test-only and cover each pinned profile', () => {
  assert.equal(vectorDocument.schema, 'stage5-identity-signature-vectors-v1');
  assert.equal(vectorDocument.test_only, true);
  assert.deepEqual(
    new Set(vectorDocument.vectors.map((vector) => vector.profile)),
    new Set([
      'ed25519-jcs-identity-role-change-approval-v1',
      'ed25519-jcs-identity-role-change-v1',
      'ed25519-jcs-identity-role-history-head-v1',
      'ed25519-jcs-identity-policy-transition-approval-v1',
      'ed25519-jcs-verifier-policy-pin-update-v1',
      'ed25519-jcs-identity-policy-transition-v1',
      'ed25519-jcs-identity-bootstrap-root-approval-v1',
      'ed25519-jcs-identity-bootstrap-root-possession-v1',
      'ed25519-jcs-identity-bootstrap-recovery-approval-v1',
      'ed25519-jcs-identity-bootstrap-root-pin-update-v1',
      'ed25519-jcs-verifier-pin-bundle-commit-v1',
      'ed25519-jcs-verifier-pin-witness-head-v1',
    ]),
  );
});

for (const vector of vectorDocument.vectors) {
  test(`canonical bytes, digest, and Ed25519 signature match ${vector.profile}`, () => {
    const canonical = canonicalize(vector.message);
    assert.equal(canonical, vector.canonical_utf8);
    assert.equal(
      createHash('sha256').update(canonical, 'utf8').digest('hex'),
      vector.sha256,
    );
    if (vector.record_content) {
      assert.equal(
        createHash('sha256')
          .update(canonicalize(vector.record_content), 'utf8')
          .digest('hex'),
        vector.record_sha256,
      );
    }
    const publicKey = createPublicKey({
      key: Buffer.concat([
        publicKeyPrefix,
        Buffer.from(vector.public_key_base64url, 'base64url'),
      ]),
      format: 'der',
      type: 'spki',
    });
    const signature = Buffer.from(vector.signature_base64url, 'base64url');
    assert.equal(verify(null, Buffer.from(canonical, 'utf8'), publicKey, signature), true);

    const tampered = { ...vector.message, [vector.tamper_field]: 'tampered' };
    assert.equal(
      verify(
        null,
        Buffer.from(canonicalize(tampered), 'utf8'),
        publicKey,
        signature,
      ),
      false,
    );
  });
}

for (const vector of vectorDocument.digest_vectors) {
  test(`canonical digest preimage matches ${vector.id}`, () => {
    const canonical = canonicalize(vector.value);
    assert.equal(canonical, vector.canonical_utf8);
    assert.equal(
      createHash('sha256').update(canonical, 'utf8').digest('hex'),
      vector.sha256,
    );
  });
}

test('signed identity history head binds the canonical query including the fresh nonce', () => {
  const historyHead = vectorDocument.vectors.find(
    (vector) => vector.profile === 'ed25519-jcs-identity-role-history-head-v1',
  );
  const query = vectorDocument.digest_vectors.find(
    (vector) => vector.id === 'identity-history-query-including-fresh-nonce',
  );
  assert.ok(historyHead && query);
  assert.equal(historyHead.message.query_sha256, query.sha256);
  assert.equal(query.value.challenge_nonce.length, 43);
});
