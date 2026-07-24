#!/usr/bin/env python3
"""Repair verified correctness defects in the pinned upstream JavaScript.

These guarded edits are limited to the pinned upstream source and are removable
when upstream incorporates equivalent fixes. Besides correctness, the phase
keeps inherited warnings from hiding Extended regressions in ESLint output.
"""
from __future__ import annotations

import argparse
from pathlib import Path


def replace_exact(
    text: str,
    old: str,
    new: str,
    expected: int,
    label: str,
) -> str:
    actual = text.count(old)
    if actual != expected:
        raise RuntimeError(f"{label}: expected {expected} marker(s), found {actual}")
    return text.replace(old, new)


def patch_app(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = replace_exact(
        text,
        """  const fetchTimeout = async (input, init, timeout_ms = FETCH_TIMEOUT) => {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), timeout_ms);
      return await fetch(input, { ...init, signal: controller.signal });
    } catch (e) {
      throw e;
    }
  };""",
        """  const fetchTimeout = async (input, init, timeout_ms = FETCH_TIMEOUT) => {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout_ms);
    try {
      return await fetch(input, { ...init, signal: controller.signal });
    } finally {
      clearTimeout(timeoutId);
    }
  };""",
        1,
        "fetch timeout cleanup",
    )
    text = replace_exact(
        text,
        "          validResult = await validateSession(data_s);",
        "          const validResult = await validateSession(data_s);",
        1,
        "session validation declaration",
    )
    text = replace_exact(
        text,
        "          hashResult = await hash(data_s, password);",
        "          const hashResult = await hash(data_s, password_s);",
        1,
        "encryption hash declaration and password source",
    )
    text = replace_exact(
        text,
        "        wsIsRunning_s = wsIsRunning === 'true' ? 'false' : 'true'; // toggle",
        "        const wsIsRunning_s =\n          wsIsRunning === 'true' ? 'false' : 'true'; // toggle",
        1,
        "foreground service state declaration",
    )
    text = replace_exact(
        text,
        "      if (response.status == 204) {",
        "      if (response.status === 204) {",
        1,
        "logout status comparison",
    )
    hook_end = """    };
  }, []);

  // Function to convert a server URL to a WebSocket URL"""
    hook_end_fixed = """    };
    // This initialization intentionally runs once. Runtime state is exchanged
    // through AsyncStorage and the native foreground service rather than by
    // restarting the complete login/bootstrap sequence after every render.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Function to convert a server URL to a WebSocket URL"""
    text = replace_exact(
        text,
        hook_end,
        hook_end_fixed,
        1,
        "intentional one-shot initialization",
    )
    path.write_text(text, encoding="utf-8")


def patch_headless(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = replace_exact(
        text,
        """import {
  setDataInAsyncStorage,
  getDataFromAsyncStorage,
  clearAsyncStorage,
} from './AsyncStorageManagement'; // persistent storage""",
        """import {
  setDataInAsyncStorage,
  getDataFromAsyncStorage,
} from './AsyncStorageManagement'; // persistent storage""",
        1,
        "unused HeadlessTask storage import",
    )
    path.write_text(text, encoding="utf-8")


def patch_foreground_service(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = replace_exact(
        text,
        "import * as encoding from 'text-encoding'; //do not remove this (polyfills for TextEncoder/TextDecoder stompjs)",
        "import { fragmentUtf8String } from './Utf8Fragmenter';",
        1,
        "UTF-8 fragmenter import",
    )
    text = replace_exact(
        text,
        """import {
  setDataInAsyncStorage,
  getDataFromAsyncStorage,
  getMultipleDataFromAsyncStorage,
  clearAsyncStorage,
} from './AsyncStorageManagement';""",
        """import {
  setDataInAsyncStorage,
  getDataFromAsyncStorage,
  getMultipleDataFromAsyncStorage,
} from './AsyncStorageManagement';""",
        1,
        "unused foreground storage import",
    )
    text = replace_exact(
        text,
        """        const textEncoder = new TextEncoder();
        const textDecoder = new TextDecoder();

""",
        "",
        1,
        "remove unsafe per-fragment codec instances",
    )
    text = replace_exact(
        text,
        """        const fragmentString = async (str, fragmentSize) => {
          const bytes = textEncoder.encode(str); // convert to UTF-8 bytes
          const fragments = [];
          for (let i = 0; i < bytes.length; i += fragmentSize) {
            const chunk = bytes.slice(i, i + fragmentSize);
            fragments.push(textDecoder.decode(chunk));
          }
          return fragments;
        };""",
        """        const fragmentString = async (str, fragmentSize) =>
          fragmentUtf8String(str, fragmentSize);""",
        1,
        "UTF-8 safe P2P fragmentation",
    )
    text = replace_exact(
        text,
        """                    const rawPayloadSizeInBytes =
                      textEncoder.encode(clipContent).length;""",
        """                    const rawPayloadSizeInBytes = Buffer.byteLength(
                      clipContent,
                      'utf8',
                    );""",
        1,
        "P2P raw UTF-8 byte length",
    )
    text = replace_exact(
        text,
        "encryptedData['ciphertext']",
        "encryptedData.ciphertext",
        1,
        "encrypted payload dot notation",
    )
    text = replace_exact(
        text,
        "encryptedData['nonce']",
        "encryptedData.nonce",
        1,
        "encrypted nonce dot notation",
    )
    text = replace_exact(
        text,
        "encryptedData['tag']",
        "encryptedData.tag",
        1,
        "encrypted tag dot notation",
    )
    text = replace_exact(
        text,
        "const padding = (base64Str.match(/=/g) || []).length;",
        "const padding = (base64Str.match(/[=]/g) || []).length;",
        1,
        "unambiguous base64 padding regex",
    )
    text = replace_exact(
        text,
        """            const r = (Math.random() * 16) | 0;
            const v = c === 'x' ? r : (r & 0x3) | 0x8;""",
        """            const r = Math.floor(Math.random() * 16);
            const v = c === 'x' ? r : (r % 4) + 8;""",
        1,
        "UUID nibble calculation without implicit signed bitwise coercion",
    )
    text = replace_exact(text, "temp = {};", "const temp = {};", 2, "file payload declarations")
    text = replace_exact(
        text,
        "              await clearFiles((expensiveCall = true));",
        "              await clearFiles(true);",
        1,
        "clearFiles argument assignment",
    )
    text = replace_exact(
        text,
        "websocket_status_notification_toggle == true",
        "websocket_status_notification_toggle === true",
        2,
        "strict notification-enabled comparisons",
    )
    text = replace_exact(
        text,
        "websocket_status_notification_toggle == false",
        "websocket_status_notification_toggle === false",
        2,
        "strict notification-disabled comparisons",
    )
    text = replace_exact(
        text,
        "sendingFragmentId != metadata.id",
        "sendingFragmentId !== metadata.id",
        1,
        "strict P2P fragment cancellation comparison",
    )
    text = replace_exact(
        text,
        "metadata['combinedRawPayloadSizeInBytes']",
        "metadata.combinedRawPayloadSizeInBytes",
        1,
        "P2P metadata dot notation",
    )
    text = replace_exact(
        text,
        """              {
                if (
                  (type_ === 'image' && enable_image_sharing === 'false') ||""",
        """              if (
                  (type_ === 'image' && enable_image_sharing === 'false') ||""",
        1,
        "remove redundant P2S send block opening",
    )
    text = replace_exact(
        text,
        """                }
              }
            } catch (e) {""",
        """                }
            } catch (e) {""",
        1,
        "remove redundant P2S send block closing",
    )
    text = replace_exact(
        text,
        """        const maxsize = Number(maxsizeStr);
        let max_clipboard_size_local_limit_bytes = Number(maxClipboardLimitStr);""",
        """        const maxsize = Number(maxsizeStr);
        await setDataInAsyncStorage('wsStatusMessage', '⏳ Connecting...');
        await setDataInAsyncStorage('p2pStatusMessage', '');
        let max_clipboard_size_local_limit_bytes = Number(maxClipboardLimitStr);""",
        1,
        "clear stale connection status at service start",
    )
    text = replace_exact(
        text,
        """                    let loopBroken = false;
                    sendingFragmentId = metadata.id;""",
        """                    const openChannels = Object.values(dataChannels).filter(
                      channel => channel && channel.readyState === 'open',
                    );
                    if (openChannels.length === 0) {
                      throw new Error('No open P2P peer data channel');
                    }

                    let loopBroken = false;
                    sendingFragmentId = metadata.id;""",
        1,
        "P2P open-channel precondition",
    )
    text = replace_exact(
        text,
        """                      // send to all open DataChannels
                      Object.entries(dataChannels).forEach(
                        async ([peerId, channel]) => {
                          if (channel.readyState === 'open') {
                            await channel.send(messageJson);
                          }
                        },
                      );""",
        """                      // DataChannel.send is synchronous. A for...of loop keeps
                      // failures inside this send attempt instead of losing them in
                      // an unobserved async forEach callback.
                      for (const channel of openChannels) {
                        channel.send(messageJson);
                      }""",
        1,
        "P2P channel send error propagation",
    )
    text = replace_exact(
        text,
        """              wsSignalingClient.onopen = async () => {
                await cleanupPeerConnections();

                await setDataInAsyncStorage('wsStatusMessage', '✅ Connected');""",
        """              wsSignalingClient.onopen = async () => {
                await cleanupPeerConnections();

                await setDataInAsyncStorage(
                  'wsStatusMessage',
                  '✅ Signaling connected; waiting for peer',
                );""",
        1,
        "P2P signaling status",
    )
    text = replace_exact(
        text,
        """                wsSignalingClient.send(JSON.stringify(obj));
                await setDataInAsyncStorage('wsStatusMessage', '✅ Connected');""",
        """                wsSignalingClient.send(JSON.stringify(obj));
                await setDataInAsyncStorage(
                  'wsStatusMessage',
                  liveConnectionsCount > 0
                    ? '✅ P2P peer connected'
                    : '✅ Signaling connected; waiting for peer',
                );""",
        1,
        "P2P signaling send must not fabricate peer connection",
    )
    text = replace_exact(
        text,
        """            channel.onopen = async () => {
              startDataChannelHeartbeat(remotePeerId, channel);
              await syncLiveConnectionsCount();
            };""",
        """            channel.onopen = async () => {
              startDataChannelHeartbeat(remotePeerId, channel);
              await syncLiveConnectionsCount();
              await setDataInAsyncStorage(
                'wsStatusMessage',
                '✅ P2P peer connected',
              );
            };""",
        1,
        "P2P data channel open status",
    )
    text = replace_exact(
        text,
        """              await syncLiveConnectionsCount();
              await recoverPeerTransport(remotePeerId, null);""",
        """              await syncLiveConnectionsCount();
              if (liveConnectionsCount === 0) {
                await setDataInAsyncStorage(
                  'wsStatusMessage',
                  '✅ Signaling connected; waiting for peer',
                );
              }
              await recoverPeerTransport(remotePeerId, null);""",
        1,
        "P2P data channel close status",
    )
    text = replace_exact(
        text,
        """            if (channel.readyState === 'open') {
              startDataChannelHeartbeat(remotePeerId, channel);
              await syncLiveConnectionsCount();
            }""",
        """            if (channel.readyState === 'open') {
              startDataChannelHeartbeat(remotePeerId, channel);
              await syncLiveConnectionsCount();
              await setDataInAsyncStorage(
                'wsStatusMessage',
                '✅ P2P peer connected',
              );
            }""",
        1,
        "already-open P2P data channel status",
    )
    path.write_text(text, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("destination", type=Path)
    destination = parser.parse_args().destination.resolve()
    patch_app(destination / "App.js")
    patch_headless(destination / "HeadlessTask.js")
    patch_foreground_service(destination / "StartForegroundService.js")


if __name__ == "__main__":
    main()
