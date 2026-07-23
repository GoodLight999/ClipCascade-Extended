import { parseOutboundFileUris } from '../OutboundFileUris';

describe('parseOutboundFileUris', () => {
  test('preserves commas inside JSON-encoded URIs', () => {
    expect(
      parseOutboundFileUris(
        JSON.stringify([
          'content://com.clipcascade.extended.fileprovider/shared/a,b.pdf',
          'content://com.clipcascade.extended.fileprovider/shared/c.pdf',
        ]),
      ),
    ).toEqual([
      'content://com.clipcascade.extended.fileprovider/shared/a,b.pdf',
      'content://com.clipcascade.extended.fileprovider/shared/c.pdf',
    ]);
  });

  test('accepts legacy comma-separated queue entries', () => {
    expect(parseOutboundFileUris('content://one, content://two')).toEqual([
      'content://one',
      'content://two',
    ]);
  });

  test('rejects malformed or empty JSON array items', () => {
    expect(() => parseOutboundFileUris('{"uri":"x"}')).toThrow();
    expect(() => parseOutboundFileUris('["content://one",""]')).toThrow(
      'empty item',
    );
  });
});
