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

    require(queue, "SCHEMA_VERSION = 2", "queue schema version")
    require(queue, "enqueue(content, type, shouldEnqueue = null)", "queue admission parameter")
    require(queue, "typeof shouldEnqueue !== 'function'", "admission guard type check")
    require(queue, "if (shouldEnqueue && shouldEnqueue() !== true)", "serialized admission decision")
    require(queue, "cancelled: true", "cancelled enqueue result")
    require_before(
        queue,
        "const state = await load(scope);",
        "if (shouldEnqueue && shouldEnqueue() !== true)",
        "admission decision after serialized state load",
    )
    require_before(
        queue,
        "if (shouldEnqueue && shouldEnqueue() !== true)",
        "state.items.push(item);",
        "admission decision before append",
    )

    require(queue, "const scopeMatches = Boolean(", "persisted scope ownership check")
    require(queue, "const migrateByteLengths", "legacy queue migration")
    require(queue, "let removedCount = 0", "load-time removal accounting")
    require(
        queue,
        "while (active.length > MAX_ITEMS || totalBytes > MAX_TOTAL_BYTES)",
        "load-time queue bounds",
    )
    require(
        queue,
        "if (scopeMatches && (removedCount > 0 || normalized))",
        "same-scope-only normalization write",
    )
    require(queue, "raw.scope !== scope", "mismatched-scope clear guard")
    require(queue, "skipped: true", "non-destructive stale clear result")
    forbid(queue, "expired > 0 || state !== raw || normalized", "scope-mismatch read overwrite")

    require(coordinator, "shouldPreserveOutboundQueue", "stop-reason queue policy")
    require(coordinator, "MANUAL_FOREGROUND_STOP_REASON = 'manual'", "manual stop identity")
    require(
        coordinator,
        "!== MANUAL_FOREGROUND_STOP_REASON",
        "non-manual queue preservation",
    )

    require(service, "let runtimeAcceptingEvents = true", "runtime event-admission state")
    require(service, "let runtimeStopReason = 'manual'", "default manual stop reason")
    require(service, "runtimeStopReason = String(reason || 'restart')", "restart reason propagation")
    require(service, "const shouldPreserveRuntimeQueue = () =>", "runtime queue policy binding")
    require(service, "const runtimeCanAcceptEvents = () =>", "runtime admission predicate")
    require(service, "const stopAcceptingRuntimeEvents = () =>", "runtime admission close operation")
    require(
        service,
        "runtimeAcceptingEvents && runtimeLease?.isActive() === true",
        "null-safe coordinated lease admission guard",
    )
    require(service, "foregroundRuntimeCoordinator.acquire(", "coordinated runtime identity")
    require(service, "runtimeCanAcceptEvents,", "queue admission predicate wiring")
    require(service, "if (enqueueResult.cancelled)", "cancelled enqueue handling")
    require(service, "ignored-after-runtime-stop", "post-stop event evidence")
    require(service, "queued-before-runtime-stop", "stop-during-enqueue evidence")
    require(service, "if (shouldPreserveRuntimeQueue())", "recovery queue branch")
    require(service, "`preserved-for-${runtimeStopReason}`", "queue preservation evidence")
    if service.count("await outboundQueue.clear();") != 2:
        raise RuntimeError("manual-only P2S/P2P queue clear count changed")
    if service.count("if (shouldPreserveRuntimeQueue())") != 2:
        raise RuntimeError("P2S/P2P queue preservation branch count changed")

    for mode in ("P2S", "P2P"):
        marker = f"stopServices{mode} = async () => {{\n            stopAcceptingRuntimeEvents();"
        require(service, marker, f"{mode} admission closure before stop")
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
        "coordinated runtime lease closes queue admission, recovery preserves durable work, "
        "manual stop clears explicitly, and stale scopes cannot erase active data: OK"
    )


if __name__ == "__main__":
    main()
