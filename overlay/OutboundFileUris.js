export function parseOutboundFileUris(serialized) {
  if (typeof serialized !== 'string') {
    throw new Error('Outbound file URI payload must be a string');
  }
  const value = serialized.trim();
  if (value.length === 0) return [];

  if (value.startsWith('[')) {
    const parsed = JSON.parse(value);
    if (!Array.isArray(parsed)) {
      throw new Error('Outbound file URI payload must decode to an array');
    }
    const uris = parsed.map(item => String(item).trim()).filter(Boolean);
    if (uris.length !== parsed.length) {
      throw new Error('Outbound file URI payload contains an empty item');
    }
    return uris;
  }
  if (value.startsWith('{')) {
    throw new Error('Outbound file URI JSON payload must be an array');
  }

  // Backward compatibility for queued events created by older Extended builds.
  return value
    .split(',')
    .map(item => item.trim())
    .filter(Boolean);
}
