#!/usr/bin/env python3
"""Require one runtime lease around clipboard and transport side effects."""
from __future__ import annotations

import argparse
from pathlib import Path


def require(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise RuntimeError(f"missing {label}: {needle!r}")


def forbid(text: str, needle: str, label: str) -> None:
    if needle in text:
        raise RuntimeError(f"forbidden {label}: {needle!r}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    root = parser.parse_args().root.resolve()
    service = (root / "StartForegroundService.js").read_text(encoding="utf-8")

    require(service, "const runRuntimeDetached = (scope, task) =>", "runtime callback wrapper")
    require(
        service,
        "if (!runtimeCanAcceptEvents()) return;\n                await task();",
        "runtime callback admission check",
    )

    literal_scopes = (
        "shared-text",
        "shared-image",
        "shared-files",
        "native-clipboard-change",
        "outbound-retry",
        "p2s-connect",
        "p2s-disconnect",
        "p2s-stomp-error",
        "p2s-websocket-error",
        "p2s-websocket-close",
        "p2s-subscription-message",
        "p2s-ack-timeout",
        "signaling-reconnect",
        "signaling-open",
        "signaling-message",
        "signaling-error",
        "signaling-close",
    )
    for scope in literal_scopes:
        require(
            service,
            f"runRuntimeDetached('{scope}'",
            f"runtime-scoped callback {scope}",
        )
        forbid(
            service,
            f"runDetached('{scope}'",
            f"unscoped callback {scope}",
        )

    template_scopes = (
        "ice-candidate",
        "datachannel-received",
        "peer-recovery",
        "datachannel-open",
        "datachannel-message",
        "datachannel-close",
        "datachannel-error",
    )
    for scope in template_scopes:
        require(
            service,
            f"runRuntimeDetached(`{scope}:${{remotePeerId}}`",
            f"runtime-scoped callback {scope}",
        )
        forbid(
            service,
            f"runDetached(`{scope}:${{remotePeerId}}`",
            f"unscoped callback {scope}",
        )

    for marker, label in (
        ("if (!runtimeCanAcceptEvents()) {\n            cancelOutboundRetry();", "flush entry guard"),
        ("while (runtimeCanAcceptEvents())", "flush loop guard"),
        ("if (!runtimeCanAcceptEvents()) break;", "transport dispatch guard"),
        ("if (!runtimeCanAcceptEvents()) return false;\n          if (server_mode", "transport dispatcher guard"),
        ("if (!runtimeCanAcceptEvents()) return false;\n                      // send", "P2S publish guard"),
        ("if (!runtimeCanAcceptEvents()) return false;\n              await clearFiles();", "P2P send guard"),
        ("if (!runtimeCanAcceptEvents()) return false;\n                      if (sendingFragmentId", "P2P fragment guard"),
        ("const signalingSend = async obj => {\n            if (!runtimeCanAcceptEvents()) return false;", "signaling send guard"),
        ("const onDataChannelMessage = async (messageJson, remotePeerId) => {\n            if (!runtimeCanAcceptEvents()) return;", "P2P inbound guard"),
        ("if (!runtimeCanAcceptEvents()) return;\n                            // set clipboard content", "P2S inbound apply guard"),
        ("if (!runtimeCanAcceptEvents()) return;\n                  // set clipboard content", "P2P inbound apply guard"),
        ("throw new Error('Invalid P2P peer list')", "peer-list type boundary"),
        ("if (!runtimeCanAcceptEvents()) break;\n              if (pid === myPeerId)", "peer reconciliation guard"),
        ("if (!runtimeCanAcceptEvents() || p2pShuttingDown)", "OFFER runtime guard"),
        ("const handleAnswer = async (fromPeerId, answer) => {\n            if (!runtimeCanAcceptEvents()) return;", "ANSWER runtime guard"),
        ("const handleIceCandidate = async (fromPeerId, candidateData) => {\n            if (!runtimeCanAcceptEvents()) return;", "ICE runtime guard"),
        ("const setupDataChannel = async (remotePeerId, channel) => {\n            if (!runtimeCanAcceptEvents())", "DataChannel setup guard"),
        ("await cleanupPeerConnections();\n                  if (!runtimeCanAcceptEvents()) return;", "signaling-open post-cleanup guard"),
        ("toggle = false;\n                if (!runtimeCanAcceptEvents()) return;\n                // Subscribe", "P2S subscription guard"),
    ):
        require(service, marker, label)

    require(
        service,
        "!runtimeCanAcceptEvents() ||\n              p2pShuttingDown ||",
        "peer recovery runtime guard",
    )
    require(service, "return true;\n              }\n              return false;", "truthful signaling result")

    print("clipboard and transport side effects are scoped to one live runtime: OK")


if __name__ == "__main__":
    main()
