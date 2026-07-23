#!/usr/bin/env python3
"""Use the same locale dictionary for self-test labels instead of mixed English/Japanese UI."""
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
    panel = root / "ExtendedControlPanel.js"

    old = """    const lines = [
      `Package: ${status.packageName}`,
      `Service requested: ${status.serviceRequested}`,
      `Connection: ${status.connectionStatus || '—'}`,
      `Accessibility: ${status.accessibilityEnabled}`,
      `Accessibility state: ${status.accessibilityServiceStatus || '—'}`,
      `Capture: ${status.accessibilityCaptureStatus || '—'}`,
      `Coordinator: ${status.captureCoordinator || '—'}`,
      `JS listener: ${status.jsListenerStatus || '—'}`,
      `Native delivery ready: ${status.nativeDeliveryReady}`,
      `Pending native events: ${status.pendingEvents}`,
      `Shared payload: ${status.sharedPayloadStatus || 'idle'}`,
      `Outbound queue:\n${pretty(status.outboundQueueStatus)}`,
      `Foreground service state: ${status.foregroundServiceState || '—'}`,
      `Foreground service heartbeat: ${status.foregroundServiceHeartbeatAt || '—'}`,
      `Foreground service error: ${status.foregroundServiceError || 'none'}`,
      `P2P candidates/compatible/incompatible: ${
        status.p2pCandidatePeers || 0
      }/${status.p2pCompatiblePeers || 0}/${
        status.p2pIncompatiblePeers || 0
      }`,
      `P2P last compatibility error: ${
        status.p2pLastCompatibilityError || 'none'
      }`,
      `READ_LOGS: ${status.readLogs}`,
      `Overlay: ${status.overlay}`,
      `Shizuku:\n${pretty(status.shizuku)}`,
      `Restart receiver: ${status.restartReceiverStatus || 'not observed'}`,
    ];"""
    new = """    const lines = [
      `${text.packageLabel}: ${status.packageName}`,
      `${text.requestedLabel}: ${status.serviceRequested}`,
      `${text.connectionStatus}: ${localizeRuntimeMessage(
        status.connectionStatus,
        text,
      )}`,
      `${text.accessibilityLabel}: ${status.accessibilityEnabled}`,
      `${text.accessibilityLabel}: ${status.accessibilityServiceStatus || '—'}`,
      `${text.captureLabel}: ${status.accessibilityCaptureStatus || '—'}`,
      `${text.coordinatorLabel}: ${status.captureCoordinator || '—'}`,
      `${text.listenerLabel}: ${status.jsListenerStatus || '—'}`,
      `Native delivery ready: ${status.nativeDeliveryReady}`,
      `${text.pendingEventsLabel}: ${status.pendingEvents}`,
      `${text.sharedPayloadLabel}: ${status.sharedPayloadStatus || 'idle'}`,
      `${text.outboundQueueLabel}:\n${pretty(status.outboundQueueStatus)}`,
      `${text.foregroundStateLabel}: ${status.foregroundServiceState || '—'}`,
      `${text.foregroundHeartbeatLabel}: ${
        status.foregroundServiceHeartbeatAt || '—'
      }`,
      `${text.foregroundErrorLabel}: ${status.foregroundServiceError || '—'}`,
      `${text.p2pCompatibilityLabel}: ${status.p2pCandidatePeers || 0}/${
        status.p2pCompatiblePeers || 0
      }/${status.p2pIncompatiblePeers || 0}`,
      `${text.p2pLastErrorLabel}: ${status.p2pLastCompatibilityError || '—'}`,
      `READ_LOGS: ${status.readLogs}`,
      `Overlay: ${status.overlay}`,
      `Shizuku:\n${pretty(status.shizuku)}`,
      `${text.restartLabel}: ${status.restartReceiverStatus || '—'}`,
    ];"""
    replace_once(panel, old, new, "localized self-test fields")

    replace_once(
        panel,
        "import { getExtendedStrings } from './ExtendedI18n';",
        "import { getExtendedStrings, localizeRuntimeMessage } from './ExtendedI18n';",
        "runtime localization import",
    )


if __name__ == "__main__":
    main()
