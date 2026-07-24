"""Wire bounded, unit-tested signaling validation into the generated service."""
from __future__ import annotations

from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one marker, found {count}")
    return text.replace(old, new, 1)


def apply(root: Path) -> None:
    path = root / "StartForegroundService.js"
    text = path.read_text(encoding="utf-8")

    text = replace_once(
        text,
        """import {
  evaluateP2PCompatibility,
  isEncryptedEnvelope,
} from './P2PCompatibility';""",
        """import {
  evaluateP2PCompatibility,
  isEncryptedEnvelope,
} from './P2PCompatibility';
import { parseP2PSignalingMessage } from './P2PSignalingValidation';""",
        "P2P signaling validator import",
    )

    text = replace_once(
        text,
        """                    const data = JSON.parse(event.data);
                    switch (data.type) {""",
        """                    const data = parseP2PSignalingMessage(event.data);
                    if (data.type === 'IGNORED') return;
                    const routedMessage =
                      data.type === 'OFFER' ||
                      data.type === 'ANSWER' ||
                      data.type === 'ICE_CANDIDATE';
                    if (
                      routedMessage &&
                      (!myPeerId ||
                        data.toPeerId !== myPeerId ||
                        data.fromPeerId === myPeerId)
                    ) {
                      return;
                    }
                    switch (data.type) {""",
        "validated signaling message dispatch",
    )

    text = replace_once(
        text,
        """                    await setDataInAsyncStorage(
                      'wsStatusMessage',
                      liveConnectionsCount > 0
                        ? '✅ P2P peer connected'
                        : '✅ Signaling connected; waiting for peer',
                    );
                  } catch (e) {
                    await setDataInAsyncStorage(
                      'wsStatusMessage',
                      '❌ Inbound Error: ' + e,
                    );
                  }""",
        """                    await setDataInAsyncStorage(
                      'p2p_last_signaling_error',
                      '',
                    );
                    await setDataInAsyncStorage(
                      'wsStatusMessage',
                      liveConnectionsCount > 0
                        ? '✅ P2P peer connected'
                        : '✅ Signaling connected; waiting for peer',
                    );
                  } catch (e) {
                    await recordSignalingFailure('message', e);
                  }""",
        "observable signaling validation failure and recovery",
    )

    path.write_text(text, encoding="utf-8")
