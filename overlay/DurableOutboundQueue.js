import * as encoding from 'text-encoding';
import { xxHash32 } from 'js-xxhash';
import {
  getDataFromAsyncStorage,
  setDataInAsyncStorage,
} from './AsyncStorageManagement';

const STORAGE_KEY = 'extended_outbound_queue_v1';
const MAX_ITEMS = 64;
const MAX_TOTAL_BYTES = 16 * 1024 * 1024;
const MAX_AGE_MS = 24 * 60 * 60 * 1000;
const MAX_FAILURES = 8;
const UTF8_ENCODER = new encoding.TextEncoder();
let operationChain = Promise.resolve();

const serialize = operation => {
  const next = operationChain.then(operation, operation);
  operationChain = next.catch(() => undefined);
  return next;
};

const emptyState = scope => ({ scope, items: [], dropped: 0 });
const utf8ByteLength = content => UTF8_ENCODER.encode(content).length;
const itemByteLength = item => {
  const persisted = Number(item?.byteLength);
  return Number.isFinite(persisted) && persisted >= 0
    ? persisted
    : utf8ByteLength(item?.content || '');
};

const fingerprint = (content, type, byteLength) =>
  `${type}:${byteLength}:${String(xxHash32(content, 0))}`;

async function load(scope) {
  const raw = await getDataFromAsyncStorage(STORAGE_KEY);
  const state =
    raw && raw.scope === scope && Array.isArray(raw.items)
      ? raw
      : emptyState(scope);
  const cutoff = Date.now() - MAX_AGE_MS;
  let normalized = false;
  const active = state.items.filter(item => {
    const valid =
      item &&
      typeof item.id === 'string' &&
      typeof item.content === 'string' &&
      typeof item.type === 'string' &&
      Number(item.createdAt) >= cutoff;
    if (!valid) return false;
    if (!Number.isFinite(Number(item.byteLength)) || Number(item.byteLength) < 0) {
      item.byteLength = utf8ByteLength(item.content);
      normalized = true;
    }
    return true;
  });
  const expired = state.items.length - active.length;
  if (expired > 0 || state !== raw || normalized) {
    state.items = active;
    state.dropped = Number(state.dropped || 0) + expired;
    await setDataInAsyncStorage(STORAGE_KEY, state);
  }
  return state;
}

const persist = state => setDataInAsyncStorage(STORAGE_KEY, state);

export function createDurableOutboundQueue(scope) {
  if (typeof scope !== 'string' || scope.length === 0) {
    throw new Error('Outbound queue scope is required');
  }

  return {
    enqueue(content, type, shouldEnqueue = null) {
      return serialize(async () => {
        if (typeof content !== 'string' || content.length === 0) {
          throw new Error('Outbound clipboard content is empty');
        }
        if (!['text', 'image', 'files'].includes(type)) {
          throw new Error(`Unsupported outbound clipboard type: ${type}`);
        }
        if (shouldEnqueue != null && typeof shouldEnqueue !== 'function') {
          throw new TypeError('Outbound queue admission guard must be a function');
        }
        const byteLength = utf8ByteLength(content);
        if (byteLength > MAX_TOTAL_BYTES) {
          throw new Error('Outbound clipboard item is too large for the durable queue');
        }

        const state = await load(scope);
        // Evaluate inside the serialized operation after loading state. If a stop
        // clear is already ahead of this operation, the old runtime is rejected
        // before it can append after that clear.
        if (shouldEnqueue && shouldEnqueue() !== true) {
          return {
            queued: false,
            duplicate: false,
            cancelled: true,
            id: null,
            count: state.items.length,
          };
        }

        const itemFingerprint = fingerprint(content, type, byteLength);
        const last = state.items[state.items.length - 1];
        if (last && last.type === type && last.content === content) {
          return {
            queued: false,
            duplicate: true,
            cancelled: false,
            id: last.id,
            count: state.items.length,
          };
        }

        const item = {
          id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
          content,
          type,
          byteLength,
          fingerprint: itemFingerprint,
          createdAt: Date.now(),
          failures: 0,
          lastError: '',
        };
        state.items.push(item);

        let totalBytes = state.items.reduce(
          (total, queued) => total + itemByteLength(queued),
          0,
        );
        while (state.items.length > MAX_ITEMS || totalBytes > MAX_TOTAL_BYTES) {
          const removed = state.items.shift();
          if (!removed) break;
          totalBytes -= itemByteLength(removed);
          state.dropped = Number(state.dropped || 0) + 1;
        }
        await persist(state);
        return {
          queued: true,
          duplicate: false,
          cancelled: false,
          id: item.id,
          count: state.items.length,
        };
      });
    },

    peek() {
      return serialize(async () => {
        const state = await load(scope);
        return state.items[0] || null;
      });
    },

    acknowledge(id) {
      return serialize(async () => {
        const state = await load(scope);
        const index = state.items.findIndex(item => item.id === id);
        if (index < 0) return { removed: null, count: state.items.length };
        const [removed] = state.items.splice(index, 1);
        await persist(state);
        return { removed, count: state.items.length };
      });
    },

    recordFailure(id, error) {
      return serialize(async () => {
        const state = await load(scope);
        const item = state.items.find(queued => queued.id === id);
        if (!item) {
          return { dropped: false, item: null, count: state.items.length };
        }
        item.failures = Number(item.failures || 0) + 1;
        item.lastError = String(error || 'unknown').slice(0, 300);
        let dropped = false;
        if (item.failures >= MAX_FAILURES) {
          state.items = state.items.filter(queued => queued.id !== id);
          state.dropped = Number(state.dropped || 0) + 1;
          dropped = true;
        }
        await persist(state);
        return { dropped, item, count: state.items.length };
      });
    },

    snapshot() {
      return serialize(async () => {
        const state = await load(scope);
        return {
          scopeFingerprint: String(xxHash32(scope, 0)),
          count: state.items.length,
          totalBytes: state.items.reduce(
            (total, item) => total + itemByteLength(item),
            0,
          ),
          dropped: Number(state.dropped || 0),
          oldestCreatedAt: state.items[0]?.createdAt || null,
          headFailures: Number(state.items[0]?.failures || 0),
          headError: state.items[0]?.lastError || '',
        };
      });
    },

    clear() {
      return serialize(async () => {
        const state = emptyState(scope);
        await persist(state);
        return state;
      });
    },
  };
}
