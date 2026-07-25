export const LOCAL_FEEDBACK_WINDOW_MS = 5_000;
export const P2S_ECHO_WINDOW_MS = 30_000;

/**
 * One typed content fingerprint may be suppressed exactly once. Local clipboard
 * feedback clears on mismatch so an unrelated user action cannot be swallowed;
 * P2S loopback matching may keep the token across unrelated inbound traffic.
 * Optional metadata ties a loopback to its durable delivery without changing
 * the upstream-compatible payload schema.
 */
export function createOneShotContentGuard({windowMs, clearOnMismatch}) {
  if (!Number.isFinite(Number(windowMs)) || Number(windowMs) <= 0) {
    throw new Error('One-shot content guard window must be positive');
  }
  let token = null;

  const inspect = now => {
    if (!token) return {active: false, reason: 'empty', metadata: null};
    const elapsed = Number(now) - Number(token.createdAt);
    if (!Number.isFinite(elapsed) || elapsed < 0 || elapsed > Number(windowMs)) {
      token = null;
      return {
        active: false,
        reason: elapsed < 0 ? 'clock-rollback' : 'expired',
        metadata: null,
      };
    }
    return {active: true, reason: 'active', metadata: token.metadata};
  };

  return {
    mark(type, hash, now, metadata = null) {
      if (typeof type !== 'string' || type.length === 0) {
        throw new Error('One-shot content guard type is required');
      }
      if (typeof hash !== 'string' || hash.length === 0) {
        throw new Error('One-shot content guard hash is required');
      }
      if (!Number.isFinite(Number(now))) {
        throw new Error('One-shot content guard timestamp is invalid');
      }
      token = {
        type,
        hash,
        createdAt: Number(now),
        metadata,
      };
    },

    consume(type, hash, now) {
      const state = inspect(now);
      if (!state.active) {
        return {suppress: false, reason: state.reason, metadata: null};
      }
      const matches = token.type === type && token.hash === hash;
      if (matches) {
        const metadata = token.metadata;
        token = null;
        return {suppress: true, reason: 'matched', metadata};
      }
      if (clearOnMismatch) token = null;
      return {
        suppress: false,
        reason: clearOnMismatch ? 'mismatch-cleared' : 'mismatch-kept',
        metadata: null,
      };
    },

    clear() {
      token = null;
    },

    snapshot(now) {
      const state = inspect(now);
      return {
        ...state,
        type: state.active ? token.type : null,
        createdAt: state.active ? token.createdAt : null,
      };
    },
  };
}
