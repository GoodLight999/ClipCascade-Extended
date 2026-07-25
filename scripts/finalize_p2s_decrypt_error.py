#!/usr/bin/env python3
"""Classify and coalesce P2S inbound failures instead of flooding the UI."""
from __future__ import annotations

import argparse
from pathlib import Path


def replace_once(path: Path, old: str, new: str, label: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one marker, found {count}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("destination", type=Path)
    root = parser.parse_args().destination.resolve()
    path = root / "StartForegroundService.js"

    replace_once(
        path,
        "import { createDurableOutboundQueue } from './DurableOutboundQueue';",
        """import { createDurableOutboundQueue } from './DurableOutboundQueue';
import { createInboundErrorCoalescer } from './InboundErrorPolicy';""",
        "P2S inbound error policy import",
    )
    replace_once(
        path,
        """        const outboundQueue = createDurableOutboundQueue(outboundQueueScope);
        let sendClipBoardTransport = null;""",
        """        const outboundQueue = createDurableOutboundQueue(outboundQueueScope);
        const p2sInboundErrorPolicy = createInboundErrorCoalescer({
          windowMs: 30000,
        });
        let sendClipBoardTransport = null;""",
        "P2S inbound error policy instance",
    )

    replace_once(
        path,
        """                  await clearFiles();
                  toggle = false;
                  await setDataInAsyncStorage(
                    'wsStatusMessage',
                    '✅ Connected - Subscribed',
                  );

                  if (message && message.body) {""",
        """                  await clearFiles();

                  if (message && message.body) {""",
        "do not unlock P2S receipt flight or hide inbound failures before validation",
    )

    replace_once(
        path,
        """                        throw new Error(
                          `Encryption must be enabled on all devices if enabled. JSON parsing failed: ${error.message}`,
                        );""",
        """                        throw new Error(
                          `Unable to decrypt P2S payload. Check the encryption setting and shared key: ${error.message}`,
                        );""",
        "P2S decrypt wording",
    )

    replace_once(
        path,
        """                  }
                } catch (e) {
                  await setDataInAsyncStorage(
                    'wsStatusMessage',
                    '❌ Inbound Error: ' + e,
                  );
                }""",
        """                  }
                  p2sInboundErrorPolicy.reset();
                  await setDataInAsyncStorage('p2s_last_inbound_error_code', '');
                  await setDataInAsyncStorage('p2s_last_inbound_error_count', '0');
                  await setDataInAsyncStorage('p2s_last_inbound_error_at', '');
                  await setDataInAsyncStorage('p2s_last_inbound_error_detail', '');
                  await setDataInAsyncStorage(
                    'wsStatusMessage',
                    '✅ Connected - Subscribed',
                  );
                } catch (e) {
                  const inbound = p2sInboundErrorPolicy.record(e);
                  await setDataInAsyncStorage(
                    'p2s_last_inbound_error_code',
                    inbound.code,
                  );
                  await setDataInAsyncStorage(
                    'p2s_last_inbound_error_count',
                    String(inbound.count),
                  );
                  await setDataInAsyncStorage(
                    'p2s_last_inbound_error_at',
                    String(inbound.lastAt),
                  );
                  await setDataInAsyncStorage(
                    'p2s_last_inbound_error_detail',
                    String(inbound.detail || '').slice(0, 1000),
                  );
                  if (inbound.shouldReport) {
                    await setDataInAsyncStorage(
                      'wsStatusMessage',
                      '❌ Inbound Error: ' + inbound.code,
                    );
                  }
                }""",
        "P2S inbound error coalescing and success reset",
    )


if __name__ == "__main__":
    main()
