import { xxHash32 } from 'js-xxhash';
import {
  getDataFromAsyncStorage,
  setDataInAsyncStorage,
} from './AsyncStorageManagement';

const STORAGE_KEY = 'extended_outbound_queue_v1';
const MAX_ITEMS = 64;
const MAX_TOTAL_CHARS = 16 * 1024 * 1024;
const MAX_AGE_MS = 24 * 60 * 60 * 1000;
const MAX_FAILURES = 8;
let operationChain = Promise.resolve();

const serialize = operation => {
  const next = operationChain.then(operation, operation);
  operationChain = next.catch(() => undefined);
  return next;
};

const emptyState = scope => ({scope, items: [], dropped: 0});

const fingerprint = (content, type) =>
  `${type}:${content.length}:${String(xxHash32(content, 0))}`;

async function load(scope) {
  const raw = await getDataFromAsyncStorage(STORAGE_KEY);
  const state =
    raw && raw.scope === scope && Array.isArray(raw.items)
      ? raw
      : emptyState(scope);
  const cutoff = Date.now() - MAX_AGE_MS;
  const active = state.items.filter(
    item =>
      item &&
      typeof item.id === 'string' &&
      typeof item.content === 'string' &&
      typeof item.type === 'string' &&
      Number(item.createdAt) >= cutoff,
  );
  const expired = state.items.length - active.length;
  if (expired > 0 || state !== raw) {
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
    enqueue(content, type) {
      return serialize(async () => {
        if (typeof content !== 'string' || content.length === 0) {
          throw new Error('Outbound clipboard content is empty');
        }
        if (!['text', 'image', 'files'].includes(type)) {
          throw new Error(`Unsupported outbound clipboard type: ${type}`);
        }
        if (content.length > MAX_TOTAL_CHARS) {
          throw new Error('Outbound clipboard item is too large for the durable queue');
        }

        const state = await load(scope);
        const itemFingerprint = fingerprint(content, type);
        const last = state.items[state.items.length - 1];
        if (last && last.type === type && last.content === content) {
          return {queued: false, duplicate: true, id: last.id, count: state.items.length};
        }

        const item = {
          id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
          content,
          type,
          fingerprint: itemFingerprint,
          createdAt: Date.now(),
          failures: 0,
          lastError: '',
        };
        state.items.push(item);

        let totalChars = state.items.reduce(
          (total, queued) => total + queued.content.length,
          0,
        );
        while (state.items.length > MAX_ITEMS || totalChars > MAX_TOTAL_CHARS) {
          const removed = state.items.shift();
          if (!removed) break;
          totalChars -= removed.content.length;
          state.dropped = Number(state.dropped || 0) + 1;
        }
        await persist(state);
        return {queued: true, duplicate: false, id: item.id, count: state.items.length};
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
        if (index < 0) return {removed: null, count: state.items.length};
        const [removed] = state.items.splice(index, 1);
        await persist(state);
        return {removed, count: state.items.length};
      });
    },

    recordFailure(id, error) {
      return serialize(async () => {
        const state = await load(scope);
        const item = state.items.find(queued => queued.id === id);
        if (!item) return {dropped: false, item: null, count: state.items.length};
        item.failures = Number(item.failures || 0) + 1;
        item.lastError = String(error || 'unknown').slice(0, 300);
        let dropped = false;
        if (item.failures >= MAX_FAILURES) {
          state.items = state.items.filter(queued => queued.id !== id);
          state.dropped = Number(state.dropped || 0) + 1;
          dropped = true;
        }
        await persist(state);
        return {dropped, item, count: state.items.length};
      });
    },

    snapshot() {
      return serialize(async () => {
        const state = await load(scope);
        return {
          scopeFingerprint: String(xxHash32(scope, 0)),
          count: state.items.length,
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
