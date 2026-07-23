export function createP2SAckTracker(options = {}) {
  const timeoutMs = options.timeoutMs ?? 10000;
  const setTimer = options.setTimer ?? setTimeout;
  const clearTimer = options.clearTimer ?? clearTimeout;
  let active = null;

  const cancel = () => {
    if (active?.timer != null) clearTimer(active.timer);
    const previous = active?.id ?? null;
    active = null;
    return previous;
  };

  return {
    begin(id, onTimeout) {
      if (typeof id !== 'string' || id.length === 0) {
        throw new Error('P2S acknowledgement ID is required');
      }
      cancel();
      const timer = setTimer(() => {
        if (active?.id !== id) return;
        active = null;
        onTimeout(id);
      }, timeoutMs);
      active = {id, timer};
      return id;
    },

    acknowledge(id) {
      if (typeof id !== 'string' || active?.id !== id) return false;
      cancel();
      return true;
    },

    cancel,

    current() {
      return active?.id ?? null;
    },
  };
}
