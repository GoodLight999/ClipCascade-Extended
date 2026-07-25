function errorText(error) {
  if (error == null) return 'Unknown inbound error';
  if (typeof error === 'string') return error;
  return String(error?.message || error);
}

export function classifyInboundError(error) {
  const detail = errorText(error);
  const normalized = detail.toLowerCase();
  if (
    normalized.includes('aeadbadtagexception') ||
    normalized.includes('bad auth tag') ||
    normalized.includes('failed to decrypt') ||
    normalized.includes('unable to decrypt p2s payload') ||
    normalized.includes('encryption-key')
  ) {
    return {
      code: 'encryption-mismatch',
      fingerprint: 'encryption-mismatch',
      message:
        'Unable to decrypt P2S payload. Check that every device uses the same encryption setting, password, hash rounds, and salt.',
      detail,
    };
  }
  if (
    normalized.includes('json') &&
    (normalized.includes('parse') || normalized.includes('unexpected'))
  ) {
    return {
      code: 'malformed-payload',
      fingerprint: 'malformed-payload',
      message: 'The server delivered a malformed clipboard payload.',
      detail,
    };
  }
  return {
    code: 'inbound-error',
    fingerprint: `inbound-error:${detail.slice(0, 240)}`,
    message: detail,
    detail,
  };
}

/**
 * Collapses repeated transport errors into one visible report while preserving
 * an exact occurrence counter for diagnostics. A successful inbound message
 * resets the incident immediately.
 */
export function createInboundErrorCoalescer({
  windowMs = 30_000,
  now = () => Date.now(),
} = {}) {
  let active = null;

  return {
    record(error) {
      const classified = classifyInboundError(error);
      const at = Number(now());
      const sameIncident =
        active &&
        active.fingerprint === classified.fingerprint &&
        at >= active.lastAt &&
        at - active.lastAt <= windowMs;
      if (sameIncident) {
        active = {
          ...active,
          lastAt: at,
          count: active.count + 1,
          detail: classified.detail,
        };
        return { ...classified, ...active, shouldReport: false };
      }
      active = {
        fingerprint: classified.fingerprint,
        firstAt: at,
        lastAt: at,
        count: 1,
        detail: classified.detail,
      };
      return { ...classified, ...active, shouldReport: true };
    },

    reset() {
      const previous = active;
      active = null;
      return previous;
    },

    snapshot() {
      return active ? { ...active } : null;
    },
  };
}
