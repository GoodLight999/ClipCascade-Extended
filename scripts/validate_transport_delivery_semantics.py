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


def require_before(text: str, first: str, second: str, label: str) -> None:
    first_index = text.find(first)
    second_index = text.find(second)
    if first_index < 0 or second_index < 0 or first_index >= second_index:
        raise RuntimeError(f"invalid ordering for {label}")


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
        ("createOneShotContentGuard", "typed guard factory"),
        ("clearOnMismatch", "mismatch policy"),
        ("metadata", "out-of-payload identity metadata"),
        ("clock-rollback", "clock rollback invalidation"),
    ):
        require(one_shot, marker, label)
    for marker, label in (
        ("AWAITING_P2S_RECEIPT", "P2S in-flight outcome"),
        ("FEEDBACK_SUPPRESSED", "feedback outcome"),
        ("POLICY_DISCARDED", "policy outcome"),
        ("Invalid outbound delivery result", "unknown result rejection"),
        ("resolveAwaitingReceiptHead", "fast-receipt resolver"),
    ):
        require(policy, marker, label)
    for marker, label in (
        ("applyOutboundDeliveryResult", "queue result executor"),
        ("currentHead?.id || null", "post-receipt head recheck"),
        ("await acknowledge(deliveryId)", "explicit terminal ACK"),
    ):
        require(executor, marker, label)
    for marker, label in (
        ("createP2SReceiptTracker", "receipt tracker"),
        ("onCallbackError", "receipt callback supervision"),
        ("shouldAcknowledgeP2SDelivery", "late callback guard"),
        ("String(queuedHeadId || '') === id", "queue-head identity check"),
    ):
        require(receipt, marker, label)

    for marker, label in (
        ("headers: {receipt: receiptId}", "standard STOMP receipt"),
        ("stompClient.watchForReceipt(receiptId", "receipt callback"),
        ("p2sEchoGuard.mark(type_, hcb", "self-echo identity"),
        ("p2sEchoGuard.consume(type_, hcb", "self-echo consumption"),
        ("shouldAcknowledgeP2SDelivery", "late receipt/echo guard"),
        ("runRuntimeDetached('p2s-receipt'", "supervised receipt"),
        ("runRuntimeDetached('p2s-receipt-timeout'", "supervised timeout"),
        ("p2s-receipt-timeout", "transient timeout evidence"),
        ("applyOutboundDeliveryResult({", "explicit delivery executor"),
        ("return OUTBOUND_DELIVERY.AWAITING_P2S_RECEIPT", "P2S pending outcome"),
        ("return OUTBOUND_DELIVERY.SENT", "P2P success outcome"),
        ("return OUTBOUND_DELIVERY.WAITING", "transport wait outcome"),
        ("return OUTBOUND_DELIVERY.FEEDBACK_SUPPRESSED", "typed feedback outcome"),
        ("return OUTBOUND_DELIVERY.POLICY_DISCARDED", "policy outcome"),
        ("const clipboardFeedbackGuard", "clipboard feedback guard"),
        ("const p2sEchoGuard", "self-echo guard"),
        ("await applyInboundClipboard(cb, type_, hcb)", "central inbound apply"),
        ("Base64 conversion, encryption and storage writes above may yield", "publish race rationale"),
        ("p2sReceiptTracker.cancel();\n                p2sEchoGuard.clear();\n                return OUTBOUND_DELIVERY.WAITING;", "publish-time stop cancellation"),
    ):
        require(service, marker, label)

    require_before(
        service,
        "// Re-check ownership immediately before the irreversible publish.",
        "stompClient.publish({",
        "runtime ownership check before STOMP publish",
    )
    require(
        service,
        "body: JSON.stringify({\n                    payload: String(outboundContent),\n                    type: type_,\n                  })",
        "upstream-compatible P2S payload",
    )

    for marker, label in (
        ("previous_clipboard_content_hash", "global hash suppression"),
        ("block_image_once", "untyped image flag"),
        ("extendedDeliveryId", "proprietary payload metadata"),
        ("awaiting-p2s-ack", "obsolete echo ACK state"),
        ("p2s-ack-timeout-dropped", "receipt timeout permanent drop"),
        ("result !== false", "ambiguous truthy success"),
        ("return result !== false", "ambiguous adapter"),
    ):
        forbid(service, marker, label)

    print(
        "standard receipt/self-echo ACK, typed feedback, explicit P2P outcomes, "
        "publish-time ownership and upstream-compatible payloads: OK"
    )


if __name__ == "__main__":
    main()
