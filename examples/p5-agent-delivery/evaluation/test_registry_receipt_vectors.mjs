import assert from 'node:assert/strict';
import { createHash, createPrivateKey, createPublicKey, sign, verify } from 'node:crypto';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import { canonicalizeForProfile } from './jcs-profile.mjs';

const vectors = JSON.parse(await readFile(new URL('./jcs-vectors.json', import.meta.url), 'utf8'));
const byId = new Map(vectors.map((vector) => [vector.id, vector]));
const payload = byId.get('stage5-registry-event-payload');
const event = byId.get('stage5-registry-event-envelope');
const receipt = byId.get('stage5-append-receipt');
const sha256 = (text) => createHash('sha256').update(text, 'utf8').digest('hex');

test('cross-checks event payload digest, event hash, receipt canonical bytes and SHA-256', () => {
  assert.ok(payload && event && receipt, 'required vectors are present');
  assert.equal(sha256(payload.canonical_utf8), event.value.payload_sha256);
  assert.equal(event.value.previous_event_hash, '0'.repeat(64));
  assert.equal(sha256(event.canonical_utf8), event.sha256);
  assert.equal(event.value.event_hash, undefined, 'event hash is outside its own preimage');
  assert.equal(receipt.value.event_hash, event.sha256);
  assert.equal(sha256(receipt.canonical_utf8), receipt.sha256);
});

test('RFC 8032 signer produces the fixed unpadded base64url receipt signature', () => {
  const seed = Buffer.from('9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60', 'hex');
  const privateKey = createPrivateKey({ key: Buffer.concat([Buffer.from('302e020100300506032b657004220420', 'hex'), seed]), format: 'der', type: 'pkcs8' });
  const signature = sign(null, Buffer.from(receipt.canonical_utf8, 'utf8'), privateKey);
  assert.equal(signature.toString('base64url'), receipt.ed25519_signature_base64url);
  const publicDer = createPublicKey(privateKey).export({ format: 'der', type: 'spki' });
  const rawPublic = publicDer.subarray(-32);
  const publicKey = createPublicKey({ key: Buffer.concat([Buffer.from('302a300506032b6570032100', 'hex'), rawPublic]), format: 'der', type: 'spki' });
  assert.equal(verify(null, Buffer.from(receipt.canonical_utf8, 'utf8'), publicKey, signature), true);
});

test('rejects a receipt signature if any signed field changes', () => {
  const seed = Buffer.from('9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60', 'hex');
  const privateKey = createPrivateKey({ key: Buffer.concat([Buffer.from('302e020100300506032b657004220420', 'hex'), seed]), format: 'der', type: 'pkcs8' });
  const publicDer = createPublicKey(privateKey).export({ format: 'der', type: 'spki' });
  const publicKey = createPublicKey({ key: Buffer.concat([Buffer.from('302a300506032b6570032100', 'hex'), publicDer.subarray(-32)]), format: 'der', type: 'spki' });
  const changed = { ...receipt.value, event_hash: 'f'.repeat(64) };
  assert.equal(verify(null, Buffer.from(canonicalizeForProfile(changed), 'utf8'), publicKey, Buffer.from(receipt.ed25519_signature_base64url, 'base64url')), false);
});
