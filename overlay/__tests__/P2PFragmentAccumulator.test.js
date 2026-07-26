import { createP2PFragmentAccumulator } from '../P2PFragmentAccumulator';

const meta = (id, index, totalFragments = 3, size = 30) => ({
  id,
  index,
  totalFragments,
  combinedRawPayloadSizeInBytes: size,
  isFragmented: true,
});

describe('P2PFragmentAccumulator', () => {
  test('reassembles out-of-order fragments', () => {
    const accumulator = createP2PFragmentAccumulator();
    expect(accumulator.add('peer', meta('a', 2), 'C').status).toBe('pending');
    expect(accumulator.add('peer', meta('a', 0), 'A').status).toBe('pending');
    const result = accumulator.add('peer', meta('a', 1), 'B');
    expect(result.status).toBe('complete');
    expect(result.payload).toBe('ABC');
  });

  test('keeps simultaneous peer/message streams independent', () => {
    const accumulator = createP2PFragmentAccumulator();
    accumulator.add('peer-1', meta('same-id', 0, 2), 'A');
    accumulator.add('peer-2', meta('same-id', 0, 2), 'X');
    accumulator.add('peer-1', meta('other', 0, 2), '1');
    expect(accumulator.add('peer-2', meta('same-id', 1, 2), 'Y').payload).toBe('XY');
    expect(accumulator.add('peer-1', meta('same-id', 1, 2), 'B').payload).toBe('AB');
    expect(accumulator.add('peer-1', meta('other', 1, 2), '2').payload).toBe('12');
  });

  test('accepts identical duplicates but rejects conflicting duplicates', () => {
    const accumulator = createP2PFragmentAccumulator();
    accumulator.add('peer', meta('a', 0, 2), 'A');
    expect(accumulator.add('peer', meta('a', 0, 2), 'A').duplicate).toBe(true);
    expect(() => accumulator.add('peer', meta('a', 0, 2), 'Z')).toThrow(
      'Conflicting duplicate fragment',
    );
  });

  test('ignores a repeated completed message ID', () => {
    const accumulator = createP2PFragmentAccumulator();
    accumulator.add('peer', meta('a', 0, 2), 'A');
    expect(accumulator.add('peer', meta('a', 1, 2), 'B').status).toBe('complete');
    expect(accumulator.add('peer', meta('a', 0, 2), 'A').status).toBe(
      'duplicate-complete',
    );
  });

  test('expires abandoned streams', () => {
    const accumulator = createP2PFragmentAccumulator({maxAgeMs: 100});
    accumulator.add('peer', meta('old', 0, 2), 'A', 0);
    expect(accumulator.snapshot(101).active).toBe(0);
  });

  test('enforces metadata and concurrency limits', () => {
    const accumulator = createP2PFragmentAccumulator({
      maxActive: 1,
      maxFragments: 4,
      maxPayloadBytes: 100,
    });
    expect(() => accumulator.add('peer', meta('bad', 5, 3), 'x')).toThrow();
    expect(() => accumulator.add('peer', meta('bad', 0, 5), 'x')).toThrow();
    expect(() => accumulator.add('peer', meta('bad', 0, 2, 101), 'x')).toThrow();
    accumulator.add('peer', meta('one', 0, 2), 'A');
    expect(() => accumulator.add('peer', meta('two', 0, 2), 'B')).toThrow(
      'Too many concurrent',
    );
  });

  test('drops only one peer when requested', () => {
    const accumulator = createP2PFragmentAccumulator();
    accumulator.add('peer-1', meta('a', 0, 2), 'A');
    accumulator.add('peer-2', meta('b', 0, 2), 'B');
    accumulator.clearPeer('peer-1');
    expect(accumulator.snapshot().messages.map(message => message.peerId)).toEqual([
      'peer-2',
    ]);
  });
});
