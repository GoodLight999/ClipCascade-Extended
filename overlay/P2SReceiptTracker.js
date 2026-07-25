export const P2S_RECEIPT_TIMEOUT_MS = 10_000;

export function createP2SReceiptTracker({
  timeoutMs = P2S_RECEIPT_TIMEOUT_MS,
  setTimer = (callback, delay) => setTimeout(callback, delay),
  clearTimer = handle => clearTimeout(handle),
  onCallbackError = () => {},
} = {}) {
  if (typeof onCallbackError !== 'function') {
    throw new TypeError('P2S receipt callback error handler is required');
  }
  let active = null;

  const clearActive = () => {
    if (!active) return null;
    const previous = active;
    active = null;
    clearTimer(previous.timer);
    return previous;
  };

  return {
    begin(deliveryId, onTimeout) {
      const id = String(deliveryId || '');
      if (!id) throw new Error('P2S receipt delivery ID is required');
      if (typeof onTimeout !== 'function') {
        throw new TypeError('P2S receipt timeout callback is required');
      }
      clearActive();
      const timer = setTimer(() => {
        if (!active || active.id !== id) return;
        active = null;
        try {
          Promise.resolve(onTimeout(id)).catch(onCallbackError);
        } catch (error) {
          onCallbackError(error);
        }
      }, Number(timeoutMs));
      active = {id, timer};
      return id;
    },

    acknowledge(deliveryId) {
      const id = String(deliveryId || '');
      if (!active || active.id !== id) return false;
      clearActive();
      return true;
    },

    cancel() {
      return clearActive()?.id || null;
    },

    isAwaiting(deliveryId) {
      return active?.id === String(deliveryId || '');
    },

    active() {
      return active ? {id: active.id} : null;
    },
  };
}

/**
 * A receipt or loopback may arrive after the timeout callback cleared the active
 * timer. It is still safe to acknowledge only while the same durable item is
 * the queue head; an unrelated stale callback must never remove a later item.
 */
export function shouldAcknowledgeP2SDelivery({
  activeReceiptMatched,
  queuedHeadId,
  deliveryId,
}) {
  const id = String(deliveryId || '');
  if (!id) return false;
  return activeReceiptMatched === true || String(queuedHeadId || '') === id;
}
