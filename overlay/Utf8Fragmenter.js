import * as encoding from 'text-encoding';

/** Splits text by UTF-8 byte budget without cutting a multi-byte code point. */
export function fragmentUtf8String(input, maxBytes) {
  if (typeof input !== 'string') {
    throw new TypeError('input must be a string');
  }
  if (!Number.isInteger(maxBytes) || maxBytes <= 0) {
    throw new RangeError('maxBytes must be a positive integer');
  }

  const bytes = new encoding.TextEncoder().encode(input);
  if (bytes.length === 0) {
    return [''];
  }

  const decoder = new encoding.TextDecoder('utf-8', { fatal: true });
  const fragments = [];
  let start = 0;
  while (start < bytes.length) {
    let end = Math.min(start + maxBytes, bytes.length);
    if (end < bytes.length) {
      while (end > start && (bytes[end] & 0xc0) === 0x80) {
        end -= 1;
      }
      // A caller may choose a budget smaller than one code point. Preserve the
      // character intact even if that single fragment exceeds the requested budget.
      if (end === start) {
        end = Math.min(start + maxBytes, bytes.length);
        while (end < bytes.length && (bytes[end] & 0xc0) === 0x80) {
          end += 1;
        }
      }
    }
    fragments.push(decoder.decode(bytes.slice(start, end)));
    start = end;
  }
  return fragments;
}
