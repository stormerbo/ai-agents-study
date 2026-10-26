import canonicalize from 'canonicalize';

/**
 * Apply the Stage 5 numeric profile before RFC 8785 canonicalization.
 * Callers must use a strict JSON parser that rejects duplicate object keys.
 */
export function canonicalizeForProfile(value) {
  validateJsonValue(value, '$');
  return canonicalize(value);
}

function validateJsonValue(value, path) {
  if (value === null || typeof value === 'string' || typeof value === 'boolean') return;

  if (typeof value === 'number') {
    if (!Number.isFinite(value)) throw new TypeError(`${path} must be finite`);
    if (Number.isInteger(value) && !Number.isSafeInteger(value)) {
      throw new TypeError(`${path} is outside the Stage 5 safe integer range`);
    }
    return;
  }

  if (Array.isArray(value)) {
    value.forEach((item, index) => validateJsonValue(item, `${path}[${index}]`));
    return;
  }

  if (typeof value === 'object' && Object.getPrototypeOf(value) === Object.prototype) {
    for (const [key, item] of Object.entries(value)) {
      validateJsonValue(item, `${path}.${key}`);
    }
    return;
  }

  throw new TypeError(`${path} is not a JSON value`);
}
