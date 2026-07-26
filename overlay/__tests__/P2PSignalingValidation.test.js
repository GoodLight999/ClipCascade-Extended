import {
  normalizeP2PPeerId,
  normalizeP2PPeerList,
  parseP2PSignalingMessage,
} from '../P2PSignalingValidation';

describe('P2P signaling validation', () => {
  test('accepts the upstream UUID peer ID format', () => {
    expect(
      normalizeP2PPeerId('550e8400-e29b-41d4-a716-446655440000'),
    ).toBe('550e8400-e29b-41d4-a716-446655440000');
  });

  test('keeps compatible non-UUID server peer IDs', () => {
    expect(normalizeP2PPeerId('peer_custom-42')).toBe('peer_custom-42');
  });

  test.each(['', ' peer', 'peer ', 'peer\nname', 42, null])(
    'rejects malformed peer ID %p',
    value => {
      expect(() => normalizeP2PPeerId(value)).toThrow('Invalid P2P signaling');
    },
  );

  test('deduplicates a valid peer list without converting values', () => {
    expect(normalizeP2PPeerList(['peer-a', 'peer-b', 'peer-a'])).toEqual([
      'peer-a',
      'peer-b',
    ]);
  });

  test('rejects a string peer list instead of treating characters as peers', () => {
    expect(() => normalizeP2PPeerList('peer-a')).toThrow(
      'Invalid P2P peer list',
    );
  });

  test('parses assigned ID and peer-list messages', () => {
    expect(
      parseP2PSignalingMessage(
        JSON.stringify({ type: 'ASSIGNED_ID', peerId: 'peer-a' }),
      ),
    ).toEqual({ type: 'ASSIGNED_ID', peerId: 'peer-a' });
    expect(
      parseP2PSignalingMessage(
        JSON.stringify({ type: 'PEER_LIST', peers: ['peer-a', 'peer-a'] }),
      ),
    ).toEqual({ type: 'PEER_LIST', peers: ['peer-a'] });
  });

  test('parses an upstream-compatible offer with optional compatibility metadata', () => {
    expect(
      parseP2PSignalingMessage(
        JSON.stringify({
          type: 'OFFER',
          fromPeerId: 'peer-a',
          toPeerId: 'peer-b',
          offer: { type: 'offer', sdp: 'v=0' },
          compatibility: { protocol: 1, cipherEnabled: true },
        }),
      ),
    ).toEqual({
      type: 'OFFER',
      fromPeerId: 'peer-a',
      toPeerId: 'peer-b',
      offer: { type: 'offer', sdp: 'v=0' },
      compatibility: { protocol: 1, cipherEnabled: true },
    });
  });

  test.each([
    { type: 'OFFER', fromPeerId: 'peer-a', toPeerId: 'peer-b' },
    {
      type: 'ANSWER',
      fromPeerId: 'peer-a',
      toPeerId: 'peer-b',
      answer: 'not-an-object',
    },
    {
      type: 'ICE_CANDIDATE',
      fromPeerId: '',
      toPeerId: 'peer-b',
      candidate: {},
    },
  ])('rejects malformed routed message %p', message => {
    expect(() => parseP2PSignalingMessage(JSON.stringify(message))).toThrow();
  });

  test('ignores unknown signaling types without interpreting their payload', () => {
    expect(
      parseP2PSignalingMessage(
        JSON.stringify({ type: 'FUTURE_SERVER_MESSAGE', payload: 'ignored' }),
      ),
    ).toEqual({ type: 'IGNORED' });
  });

  test('rejects non-text and over-sized signaling messages', () => {
    expect(() => parseP2PSignalingMessage({})).toThrow(
      'must be text',
    );
    expect(() => parseP2PSignalingMessage('x'.repeat(1024 * 1024 + 1))).toThrow(
      'size is invalid',
    );
  });
});
