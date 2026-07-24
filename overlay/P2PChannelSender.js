const defaultSleep = ms => new Promise(resolve => setTimeout(resolve, ms));

/** Waits for every peer to have capacity, then sends one identical fragment. */
export async function sendP2PFragment(
  channels,
  message,
  options = {},
) {
  if (!Array.isArray(channels) || channels.length === 0) {
    throw new Error('No P2P channels supplied');
  }
  const highWaterMark = options.highWaterMark ?? 1024 * 1024;
  const timeoutMs = options.timeoutMs ?? 15000;
  const pollMs = options.pollMs ?? 25;
  const sleep = options.sleep ?? defaultSleep;
  const now = options.now ?? Date.now;
  const deadline = now() + timeoutMs;

  while (true) {
    for (const channel of channels) {
      if (!channel || channel.readyState !== 'open') {
        throw new Error('P2P data channel closed during send');
      }
    }
    const blocked = channels.some(
      channel => Number(channel.bufferedAmount || 0) > highWaterMark,
    );
    if (!blocked) break;
    if (now() >= deadline) {
      throw new Error('P2P data channel backpressure timeout');
    }
    await sleep(pollMs);
  }

  // Capacity is checked for all peers before any peer receives this fragment.
  for (const channel of channels) {
    channel.send(message);
  }
}
