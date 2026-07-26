const MAX_SIGNALING_MESSAGE_CHARS = 1024 * 1024;
const MAX_PEERS = 4096;
const MAX_PEER_ID_LENGTH = 256;
const CONTROL_CHARACTERS = /[\u0000-\u001f\u007f]/;

function requireObject(value, field) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    throw new Error(`Invalid P2P signaling ${field}`);
  }
  return value;
}

export function normalizeP2PPeerId(value, field = 'peerId') {
  if (
    typeof value !== 'string' ||
    value.length === 0 ||
    value.length > MAX_PEER_ID_LENGTH ||
    value.trim() !== value ||
    CONTROL_CHARACTERS.test(value)
  ) {
    throw new Error(`Invalid P2P signaling ${field}`);
  }
  return value;
}

export function normalizeP2PPeerList(value) {
  if (!Array.isArray(value)) {
    throw new Error('Invalid P2P peer list');
  }
  if (value.length > MAX_PEERS) {
    throw new Error('P2P peer list exceeds the client safety limit');
  }
  const unique = new Set();
  for (const peerId of value) {
    unique.add(normalizeP2PPeerId(peerId, 'peer list entry'));
  }
  return Array.from(unique);
}

export function parseP2PSignalingMessage(raw) {
  if (typeof raw !== 'string') {
    throw new Error('P2P signaling message must be text');
  }
  if (raw.length === 0 || raw.length > MAX_SIGNALING_MESSAGE_CHARS) {
    throw new Error('P2P signaling message size is invalid');
  }

  const data = requireObject(JSON.parse(raw), 'envelope');
  const type = typeof data.type === 'string' ? data.type : '';

  if (type === 'ASSIGNED_ID') {
    return {
      type,
      peerId: normalizeP2PPeerId(data.peerId, 'assigned peerId'),
    };
  }
  if (type === 'PEER_LIST') {
    return { type, peers: normalizeP2PPeerList(data.peers) };
  }
  if (type === 'OFFER' || type === 'ANSWER' || type === 'ICE_CANDIDATE') {
    const fromPeerId = normalizeP2PPeerId(data.fromPeerId, 'fromPeerId');
    const toPeerId = normalizeP2PPeerId(data.toPeerId, 'toPeerId');
    const payloadField =
      type === 'OFFER'
        ? 'offer'
        : type === 'ANSWER'
          ? 'answer'
          : 'candidate';
    const payload = requireObject(data[payloadField], payloadField);
    if (
      data.compatibility != null &&
      (typeof data.compatibility !== 'object' ||
        Array.isArray(data.compatibility))
    ) {
      throw new Error('Invalid P2P signaling compatibility metadata');
    }
    return {
      type,
      fromPeerId,
      toPeerId,
      [payloadField]: payload,
      compatibility: data.compatibility || null,
    };
  }

  return { type: 'IGNORED' };
}
