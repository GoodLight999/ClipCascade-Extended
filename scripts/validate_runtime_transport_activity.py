#!/usr/bin/env python3
"""Require one live runtime lease around clipboard and transport side effects."""
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

    for scope in (
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
        "p2s-receipt-timeout",
        "p2s-receipt",
        "signaling-reconnect",
        "signaling-open",
        "signaling-message",
        "signaling-error",
        "signaling-close",
    ):
        require(service, f"runRuntimeDetached('{scope}'", f"runtime-scoped callback {scope}")
        forbid(service, f"runDetached('{scope}'", f"unscoped callback {scope}")

    for scope in (
        "ice-candidate",
        "datachannel-received",
        "peer-recovery",
        "datachannel-open",
        "datachannel-message",
        "datachannel-close",
        "datachannel-error",
    ):
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
        ("if (!runtimeCanAcceptEvents()) return OUTBOUND_DELIVERY.WAITING;", "explicit transport guard"),
        ("const signalingSend = async obj => {\n            if (!runtimeCanAcceptEvents()) return false;", "signaling guard"),
        ("const onDataChannelMessage = async (messageJson, remotePeerId) => {\n            if (!runtimeCanAcceptEvents()) return;", "P2P inbound guard"),
        ("throw new Error('Invalid P2P peer list')", "peer-list boundary"),
        ("if (!runtimeCanAcceptEvents()) break;\n              if (pid === myPeerId)", "peer reconciliation guard"),
        ("if (!runtimeCanAcceptEvents() || p2pShuttingDown)", "OFFER guard"),
        ("const handleAnswer = async (fromPeerId, answer) => {\n            if (!runtimeCanAcceptEvents()) return;", "ANSWER guard"),
        ("const handleIceCandidate = async (fromPeerId, candidateData) => {\n            if (!runtimeCanAcceptEvents()) return;", "ICE guard"),
        ("const setupDataChannel = async (remotePeerId, channel) => {\n            if (!runtimeCanAcceptEvents())", "DataChannel setup guard"),
        ("await cleanupPeerConnections();\n                  if (!runtimeCanAcceptEvents()) return;", "signaling-open guard"),
        ("stopServicesP2S = async () => {\n            stopAcceptingRuntimeEvents();", "P2S stop admission guard"),
        ("stopServicesP2P = async () => {\n            stopAcceptingRuntimeEvents();", "P2P stop admission guard"),
    ):
        require(service, marker, label)

    require(
        service,
        "!runtimeCanAcceptEvents() ||\n              p2pShuttingDown ||",
        "peer recovery runtime guard",
    )
    require(service, "return OUTBOUND_DELIVERY.SENT;", "explicit P2P success")
    require(service, "return OUTBOUND_DELIVERY.AWAITING_P2S_RECEIPT;", "explicit P2S pending result")
    require(service, "headers: {receipt: receiptId}", "standard STOMP receipt")
    require(service, "p2sReceiptTracker.cancel();\n                p2sEchoGuard.clear();\n                return OUTBOUND_DELIVERY.WAITING;", "publish-time stop guard")

    forbid(service, "result !== false", "ambiguous truthy transport ACK")
    forbid(service, "return result !== false", "ambiguous transport result")

    print("clipboard and explicit transport side effects are scoped to one live runtime: OK")


if __name__ == "__main__":
    main()
