import AsyncStorage from '@react-native-async-storage/async-storage';
import { createDurableOutboundQueue } from '../DurableOutboundQueue';

describe('DurableOutboundQueue', () => {
  beforeEach(async () => {
    await AsyncStorage.clear();
    jest.useRealTimers();
  });

  test('persists entries across queue instances with the same scope', async () => {
    const first = createDurableOutboundQueue('P2S|server|user');
    await first.enqueue('hello', 'text');

    const second = createDurableOutboundQueue('P2S|server|user');
    expect((await second.peek()).content).toBe('hello');
    expect((await second.snapshot()).count).toBe(1);
  });

  test('never sends stale entries to a different server scope', async () => {
    const first = createDurableOutboundQueue('P2S|server-a|user');
    await first.enqueue('secret for A', 'text');

    const second = createDurableOutboundQueue('P2S|server-b|user');
    expect(await second.peek()).toBeNull();
    expect((await second.snapshot()).count).toBe(0);
  });

  test('coalesces consecutive duplicate copies', async () => {
    const queue = createDurableOutboundQueue('scope');
    const first = await queue.enqueue('same', 'text');
    const second = await queue.enqueue('same', 'text');
    expect(first.queued).toBe(true);
    expect(second.duplicate).toBe(true);
    expect((await queue.snapshot()).count).toBe(1);
  });

  test('acknowledges only the matching entry', async () => {
    const queue = createDurableOutboundQueue('scope');
    const first = await queue.enqueue('A', 'text');
    await queue.enqueue('B', 'text');
    await queue.acknowledge(first.id);
    expect((await queue.peek()).content).toBe('B');
  });

  test('drops a permanently failing head after finite retries', async () => {
    const queue = createDurableOutboundQueue('scope');
    const queued = await queue.enqueue('broken-uri', 'files');
    expect((await queue.recordFailure(queued.id, 'one')).dropped).toBe(false);
    expect((await queue.recordFailure(queued.id, 'two')).dropped).toBe(false);
    expect((await queue.recordFailure(queued.id, 'three')).dropped).toBe(true);
    expect(await queue.peek()).toBeNull();
  });

  test('expires stale clipboard data instead of sending it a day later', async () => {
    jest.useFakeTimers().setSystemTime(new Date('2026-07-20T00:00:00Z'));
    const queue = createDurableOutboundQueue('scope');
    await queue.enqueue('old', 'text');
    jest.setSystemTime(new Date('2026-07-22T00:00:01Z'));
    expect(await queue.peek()).toBeNull();
    expect((await queue.snapshot()).dropped).toBe(1);
  });
});
