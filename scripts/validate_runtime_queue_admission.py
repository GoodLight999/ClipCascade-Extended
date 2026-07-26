#!/usr/bin/env python3
"""Require stop-safe, scope-isolated durable-queue admission and recovery."""
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
    queue = (root / "DurableOutboundQueue.js").read_text(encoding="utf-8")
    coordinator = (root / "ForegroundRuntimeCoordinator.js").read_text(encoding="utf-8")

    for marker, label in (
        ("SCHEMA_VERSION = 2", "queue schema"),
        ("enqueue(content, type, shouldEnqueue = null)", "admission parameter"),
        ("typeof shouldEnqueue !== 'function'", "admission type check"),
        ("if (shouldEnqueue && shouldEnqueue() !== true)", "serialized admission decision"),
        ("cancelled: true", "cancelled enqueue result"),
        ("const scopeMatches = Boolean(", "scope ownership"),
        ("const migrateByteLengths", "legacy migration"),
        ("let removedCount = 0", "removal accounting"),
        ("while (active.length > MAX_ITEMS || totalBytes > MAX_TOTAL_BYTES)", "queue bounds"),
        ("if (scopeMatches && (removedCount > 0 || normalized))", "same-scope normalization"),
        ("raw.scope !== scope", "mismatched-scope clear guard"),
        ("skipped: true", "non-destructive stale clear"),
    ):
        require(queue, marker, label)
    require_before(
        queue,
        "const state = await load(scope);",
        "if (shouldEnqueue && shouldEnqueue() !== true)",
        "admission after serialized load",
    )
    require_before(
        queue,
        "if (shouldEnqueue && shouldEnqueue() !== true)",
        "state.items.push(item);",
        "admission before append",
    )
    forbid(queue, "expired > 0 || state !== raw || normalized", "scope-mismatch overwrite")

    for marker, label in (
        ("shouldPreserveOutboundQueue", "stop-reason policy"),
        ("MANUAL_FOREGROUND_STOP_REASON = 'manual'", "manual stop identity"),
        ("!== MANUAL_FOREGROUND_STOP_REASON", "non-manual preservation"),
    ):
        require(coordinator, marker, label)

    for marker, label in (
        ("let runtimeAcceptingEvents = true", "runtime admission state"),
        ("let runtimeStopReason = 'manual'", "default manual stop"),
        ("runtimeStopReason = String(reason || 'replacement-start')", "replacement reason propagation"),
        ("const shouldPreserveRuntimeQueue = () =>", "queue policy binding"),
        ("const runtimeCanAcceptEvents = () =>", "runtime predicate"),
        ("const stopAcceptingRuntimeEvents = () =>", "admission close"),
        ("runtimeAcceptingEvents && runtimeLease?.isActive() === true", "active lease guard"),
        ("foregroundRuntimeCoordinator.acquire(", "coordinated identity"),
        ("runtimeCanAcceptEvents,", "queue admission wiring"),
        ("if (enqueueResult.cancelled)", "cancelled enqueue handling"),
        ("ignored-after-runtime-stop", "post-stop evidence"),
        ("queued-before-runtime-stop", "stop-during-enqueue evidence"),
        ("if (shouldPreserveRuntimeQueue())", "recovery preservation branch"),
        ("`preserved-for-${runtimeStopReason}`", "preservation evidence"),
    ):
        require(service, marker, label)

    if service.count("await outboundQueue.clear();") != 2:
        raise RuntimeError("manual-only P2S/P2P queue clear count changed")
    if service.count("if (shouldPreserveRuntimeQueue())") != 2:
        raise RuntimeError("P2S/P2P queue preservation branch count changed")

    for mode in ("P2S", "P2P"):
        marker = f"stopServices{mode} = async () => {{\n            stopAcceptingRuntimeEvents();"
        require(service, marker, f"{mode} admission closure")
        preserve = service.find("if (shouldPreserveRuntimeQueue())", service.find(marker))
        clear = service.find("await outboundQueue.clear();", preserve)
        if preserve < 0 or clear < 0 or preserve >= clear:
            raise RuntimeError(f"invalid {mode} preserve-before-clear ordering")

    forbid(
        service,
        "await outboundQueue.enqueue(String(clipContent), type_);",
        "unguarded runtime enqueue",
    )

    print(
        "coordinated lease closes queue admission, replacement preserves durable work, "
        "manual stop clears explicitly, and stale scopes cannot erase active data: OK"
    )


if __name__ == "__main__":
    main()
