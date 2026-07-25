#!/usr/bin/env python3
"""Require explicit, upstream-compatible and identity-safe transport delivery."""
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
    one_shot = (root / "OneShotContentGuard.js").read_text(encoding="utf-8")
    policy = (root / "OutboundDeliveryPolicy.js").read_text(encoding="utf-8")
    executor = (root / "OutboundDeliveryExecutor.js").read_text(encoding="utf-8")
    receipt = (root / "P2SReceiptTracker.js").read_text(encoding="utf-8")

    for marker, label in (
        ("createOneShotContentGuard", "typed one-shot guard factory"),
        ("clearOnMismatch", "mode-specific mismatch policy"),
        ("metadata", "delivery identity metadata outside payload"),
        ("clock-rollback", "clock rollback invalidation"),
    ):
        require(one_shot, marker, label)

    for marker, label in (
        ("AWAITING_P2S_RECEIPT", "P2S in-flight outcome"),
        ("FEEDBACK_SUPPRESSED", "feedback terminal outcome"),
        ("POLICY_DISCARDED", "policy terminal outcome"),
        ("Invalid outbound delivery result", "unknown truthy result rejection"),
        ("resolveAwaitingReceiptHead", "fast receipt race resolver"),
    ):
        require(policy, marker, label)

    for marker, label in (
        ("applyOutboundDeliveryResult", "queue result executor"),
        ("currentHead?.id || null", "post-receipt head recheck"),
        ("await acknowledge(deliveryId)", "explicit terminal acknowledgement"),
    ):
        require(executor, marker, label)

    for marker, label in (
        ("createP2SReceiptTracker", "P2S receipt tracker"),
        ("onCallbackError", "receipt callback supervision"),
        ("shouldAcknowledgeP2SDelivery", "exact late callback guard"),
        ("String(queuedHeadId || '') === id", "queue-head identity check"),
    ):
        require(receipt, marker, label)

    for marker, label in (
        ("headers: {receipt: receiptId}", "standard STOMP receipt header"),
        ("stompClient.watchForReceipt(receiptId", "STOMP receipt callback"),
        ("p2sEchoGuard.mark(type_, hcb", "self-echo fallback identity"),
        ("p2sEchoGuard.consume(type_, hcb", "self-echo fallback consumption"),
        ("shouldAcknowledgeP2SDelivery", "late receipt/echo head guard"),
        ("runRuntimeDetached('p2s-receipt'", "supervised receipt callback"),
        ("runRuntimeDetached('p2s-receipt-timeout'", "supervised receipt timeout"),
        ("p2s-receipt-timeout", "transient receipt timeout evidence"),
        ("applyOutboundDeliveryResult({", "explicit queue delivery executor"),
        ("return OUTBOUND_DELIVERY.AWAITING_P2S_RECEIPT", "P2S waiting outcome"),
        ("return OUTBOUND_DELIVERY.SENT", "explicit P2P success outcome"),
        ("return OUTBOUND_DELIVERY.WAITING", "explicit transport wait outcome"),
        ("return OUTBOUND_DELIVERY.FEEDBACK_SUPPRESSED", "typed feedback outcome"),
        ("return OUTBOUND_DELIVERY.POLICY_DISCARDED", "disabled policy outcome"),
        ("const clipboardFeedbackGuard", "local clipboard feedback guard"),
        ("const p2sEchoGuard", "P2S self-echo guard"),
        ("await applyInboundClipboard(cb, type_, hcb)", "central typed inbound apply"),
    ):
        require(service, marker, label)

    # The application payload remains compatible with the upstream server.
    require(
        service,
        "body: JSON.stringify({\n                    payload: String(outboundContent),\n                    type: type_,\n                  })",
        "upstream-compatible P2S payload body",
    )

    for marker, label in (
        ("previous_clipboard_content_hash", "global content hash suppression"),
        ("block_image_once", "untyped one-shot image flag"),
        ("extendedDeliveryId", "proprietary payload delivery metadata"),
        ("awaiting-p2s-ack", "obsolete payload echo ACK state"),
        ("p2s-ack-timeout-dropped", "receipt timeout permanent drop"),
        ("result !== false", "ambiguous truthy transport success"),
        ("return result !== false", "ambiguous transport adapter"),
    ):
        forbid(service, marker, label)

    print(
        "standard STOMP receipt/self-echo ACK, typed one-shot feedback, explicit P2P results, "
        "fast-receipt queue handling and upstream-compatible payloads: OK"
    )


if __name__ == "__main__":
    main()
