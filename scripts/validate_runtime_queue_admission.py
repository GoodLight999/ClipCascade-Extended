#!/usr/bin/env python3
"""Require stop-safe, scope-isolated durable-queue admission."""
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
    require(
        queue,
        "raw.scope !== scope",
        "mismatched-scope clear guard",
    )
    require(queue, "skipped: true", "non-destructive stale clear result")
    forbid(
        queue,
        "expired > 0 || state !== raw || normalized",
        "scope-mismatch read overwrite",
    )

    require(service, "let runtimeAcceptingEvents = true", "runtime event-admission state")
    require(service, "const runtimeCanAcceptEvents = () =>", "runtime admission predicate")
    require(service, "const stopAcceptingRuntimeEvents = () =>", "runtime admission close operation")
    require(service, "activeForegroundRuntimeId === runtimeId", "runtime identity admission guard")
    require(service, "runtimeCanAcceptEvents,", "queue admission predicate wiring")
    require(service, "if (enqueueResult.cancelled)", "cancelled enqueue handling")
    require(service, "ignored-after-runtime-stop", "post-stop event evidence")
    require(service, "queued-before-runtime-stop", "stop-during-enqueue evidence")
    require(
        service,
        "stopServicesP2S = async () => {\n            stopAcceptingRuntimeEvents();",
        "P2S admission closure before stop",
    )
    require(
        service,
        "stopServicesP2P = async () => {\n            stopAcceptingRuntimeEvents();",
        "P2P admission closure before stop",
    )
    require_before(
        service,
        "stopServicesP2S = async () => {\n            stopAcceptingRuntimeEvents();",
        "await outboundQueue.clear();",
        "P2S admission closure before queue clear",
    )
    p2p_stop = service.find(
        "stopServicesP2P = async () => {\n            stopAcceptingRuntimeEvents();"
    )
    p2p_clear = service.find("await outboundQueue.clear();", p2p_stop)
    if p2p_stop < 0 or p2p_clear < 0 or p2p_stop >= p2p_clear:
        raise RuntimeError("invalid ordering for P2P admission closure before queue clear")

    forbid(
        service,
        "await outboundQueue.enqueue(String(clipContent), type_);",
        "unguarded runtime enqueue",
    )

    print(
        "runtime lease closes queue admission, persisted bounds are migrated, "
        "and stale scopes cannot erase active data: OK"
    )


if __name__ == "__main__":
    main()
