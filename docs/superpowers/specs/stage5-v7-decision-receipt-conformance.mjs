import { isDeepStrictEqual } from 'node:util';

const UTC_TIMESTAMP = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.(\d{1,6}))?Z$/;

function reject(code, message) {
  throw Object.assign(new Error(message), { code });
}

export function parseUtcTimestampMicros(value) {
  if (typeof value !== 'string') return null;
  const match = UTC_TIMESTAMP.exec(value);
  if (!match) return null;
  const [, yText, monthText, dayText, hourText, minuteText, secondText, fraction = ''] = match;
  const year = Number(yText);
  const month = Number(monthText);
  const day = Number(dayText);
  const hour = Number(hourText);
  const minute = Number(minuteText);
  const second = Number(secondText);
  const leap = year % 4 === 0 && (year % 100 !== 0 || year % 400 === 0);
  const daysInMonth = [31, leap ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
  if (
    month < 1 ||
    month > 12 ||
    day < 1 ||
    day > daysInMonth[month - 1] ||
    hour > 23 ||
    minute > 59 ||
    second > 59
  )
    return null;

  let adjustedYear = year;
  if (month <= 2) adjustedYear -= 1;
  const era = Math.floor(adjustedYear / 400);
  const yearOfEra = adjustedYear - era * 400;
  const adjustedMonth = month + (month > 2 ? -3 : 9);
  const dayOfYear = Math.floor((153 * adjustedMonth + 2) / 5) + day - 1;
  const dayOfEra =
    yearOfEra * 365 + Math.floor(yearOfEra / 4) - Math.floor(yearOfEra / 100) + dayOfYear;
  const daysSinceEpoch = era * 146097 + dayOfEra - 719468;
  const secondsSinceEpoch =
    BigInt(daysSinceEpoch) * 86400n + BigInt(hour * 3600 + minute * 60 + second);
  const micros = BigInt((fraction + '000000').slice(0, 6));
  return secondsSinceEpoch * 1_000_000n + micros;
}

/**
 * Checks bindings/freshness semantics for a detached decision receipt whose JSON
 * shape and signature are verified separately. Expiry values must be derived from
 * authenticated source observations by the caller.
 */
export function verifyV7DecisionReceiptClaims(receipt, expectedBindings, freshnessExpiries) {
  if (
    !receipt ||
    typeof receipt !== 'object' ||
    Array.isArray(receipt) ||
    !expectedBindings ||
    typeof expectedBindings !== 'object' ||
    Array.isArray(expectedBindings)
  ) {
    reject('V7_DECISION_BINDING', 'receipt and expected verifier bindings must be objects');
  }
  for (const [key, value] of Object.entries(expectedBindings)) {
    if (!Object.hasOwn(receipt, key) || !isDeepStrictEqual(receipt[key], value)) {
      reject('V7_DECISION_BINDING', `decision receipt field ${key} differs from verifier output`);
    }
  }

  const verifiedAt = parseUtcTimestampMicros(receipt.verified_at_utc);
  const validUntil = parseUtcTimestampMicros(receipt.valid_until_utc);
  if (
    verifiedAt === null ||
    validUntil === null ||
    validUntil < verifiedAt ||
    !Array.isArray(freshnessExpiries) ||
    freshnessExpiries.length === 0
  ) {
    reject(
      'V7_DECISION_EXPIRY',
      'decision receipt freshness interval or source bounds are invalid',
    );
  }
  const expiryMicros = freshnessExpiries.map(parseUtcTimestampMicros);
  if (expiryMicros.some((value) => value === null)) {
    reject('V7_DECISION_EXPIRY', 'an authenticated source freshness expiry is malformed');
  }
  const earliest = expiryMicros.reduce((minimum, value) => (value < minimum ? value : minimum));
  if (validUntil !== earliest) {
    reject(
      'V7_DECISION_EXPIRY',
      'decision receipt expiry must equal the earliest source freshness bound',
    );
  }
  return { valid: true };
}
