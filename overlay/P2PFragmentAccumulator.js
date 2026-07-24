import { Buffer } from 'buffer';

const DEFAULT_MAX_ACTIVE = 8;
const DEFAULT_MAX_FRAGMENTS = 8192;
const DEFAULT_MAX_AGE_MS = 2 * 60 * 1000;
const DEFAULT_MAX_PAYLOAD_BYTES = 128 * 1024 * 1024;
const COMPLETED_CACHE_LIMIT = 64;

const finiteInteger = value => Number.isInteger(value) && Number.isFinite(value);

export function createP2PFragmentAccumulator(options = {}) {
  const maxActive = options.maxActive ?? DEFAULT_MAX_ACTIVE;
  const maxFragments = options.maxFragments ?? DEFAULT_MAX_FRAGMENTS;
  const maxAgeMs = options.maxAgeMs ?? DEFAULT_MAX_AGE_MS;
  const maxPayloadBytes = options.maxPayloadBytes ?? DEFAULT_MAX_PAYLOAD_BYTES;
  const active = new Map();
  const completed = new Map();

  const cleanup = now => {
    for (const [key, entry] of active.entries()) {
      if (now - entry.updatedAt > maxAgeMs) active.delete(key);
    }
    for (const [key, completedAt] of completed.entries()) {
      if (now - completedAt > maxAgeMs) completed.delete(key);
    }
  };

  const completedRemember = (key, now) => {
    completed.set(key, now);
    while (completed.size > COMPLETED_CACHE_LIMIT) {
      completed.delete(completed.keys().next().value);
    }
  };

  const keyFor = (peerId, id) => `${peerId}\u0000${id}`;

  return {
    add(peerId, metadata, payload, now = Date.now()) {
      cleanup(now);
      if (typeof peerId !== 'string' || peerId.length === 0 || peerId.length > 256) {
        throw new Error('Invalid P2P peer ID');
      }
      if (!metadata || metadata.isFragmented !== true) {
        throw new Error('Fragment metadata is required');
      }
      const {id, index, totalFragments, combinedRawPayloadSizeInBytes} = metadata;
      if (typeof id !== 'string' || id.length === 0 || id.length > 128) {
        throw new Error('Invalid fragment ID');
      }
      if (!finiteInteger(index) || !finiteInteger(totalFragments)) {
        throw new Error('Fragment index/count must be integers');
      }
      if (totalFragments <= 0 || totalFragments > maxFragments) {
        throw new Error('Fragment count exceeds the configured limit');
      }
      if (index < 0 || index >= totalFragments) {
        throw new Error('Fragment index is out of range');
      }
      if (
        !finiteInteger(combinedRawPayloadSizeInBytes) ||
        combinedRawPayloadSizeInBytes < 0 ||
        combinedRawPayloadSizeInBytes > maxPayloadBytes
      ) {
        throw new Error('Declared P2P payload size exceeds the configured limit');
      }
      if (typeof payload !== 'string') {
        throw new Error('Fragment payload must be a string');
      }

      const key = keyFor(peerId, id);
      if (completed.has(key)) {
        return {status: 'duplicate-complete', id, peerId};
      }

      let entry = active.get(key);
      if (!entry) {
        if (active.size >= maxActive) {
          throw new Error('Too many concurrent fragmented P2P messages');
        }
        entry = {
          id,
          peerId,
          totalFragments,
          declaredRawBytes: combinedRawPayloadSizeInBytes,
          fragments: new Array(totalFragments),
          received: 0,
          receivedBytes: 0,
          createdAt: now,
          updatedAt: now,
        };
        active.set(key, entry);
      } else if (
        entry.totalFragments !== totalFragments ||
        entry.declaredRawBytes !== combinedRawPayloadSizeInBytes
      ) {
        active.delete(key);
        throw new Error('Conflicting fragment metadata');
      }

      const existing = entry.fragments[index];
      if (existing !== undefined) {
        if (existing !== payload) {
          active.delete(key);
          throw new Error('Conflicting duplicate fragment');
        }
        entry.updatedAt = now;
        return {
          status: 'pending',
          duplicate: true,
          id,
          peerId,
          progress: `${entry.received}/${entry.totalFragments}`,
        };
      }

      const fragmentBytes = Buffer.byteLength(payload, 'utf8');
      entry.receivedBytes += fragmentBytes;
      if (entry.receivedBytes > maxPayloadBytes * 2 + 64 * 1024) {
        active.delete(key);
        throw new Error('Encoded fragmented payload exceeds the memory limit');
      }
      entry.fragments[index] = payload;
      entry.received += 1;
      entry.updatedAt = now;

      if (entry.received !== entry.totalFragments) {
        return {
          status: 'pending',
          id,
          peerId,
          progress: `${entry.received}/${entry.totalFragments}`,
        };
      }

      const combined = entry.fragments.join('');
      active.delete(key);
      completedRemember(key, now);
      return {
        status: 'complete',
        id,
        peerId,
        payload: combined,
        progress: `${entry.totalFragments}/${entry.totalFragments}`,
      };
    },

    drop(peerId, id) {
      active.delete(keyFor(peerId, id));
    },

    clearPeer(peerId) {
      for (const key of active.keys()) {
        if (key.startsWith(`${peerId}\u0000`)) active.delete(key);
      }
      for (const key of completed.keys()) {
        if (key.startsWith(`${peerId}\u0000`)) completed.delete(key);
      }
    },

    clear() {
      active.clear();
      completed.clear();
    },

    snapshot(now = Date.now()) {
      cleanup(now);
      return {
        active: active.size,
        completedRemembered: completed.size,
        messages: [...active.values()].map(entry => ({
          peerId: entry.peerId,
          id: entry.id,
          progress: `${entry.received}/${entry.totalFragments}`,
          receivedBytes: entry.receivedBytes,
          ageMs: now - entry.createdAt,
        })),
      };
    },
  };
}
