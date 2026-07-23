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


def replace_section(
    path: Path,
    start_marker: str,
    end_marker: str,
    replacement: str,
    label: str,
) -> None:
    text = path.read_text(encoding="utf-8")
    if text.count(start_marker) != 1:
        raise RuntimeError(
            f"{label}: expected one start marker, found {text.count(start_marker)}"
        )
    start = text.index(start_marker)
    end = text.find(end_marker, start)
    if end < 0:
        raise RuntimeError(f"{label}: end marker not found")
    path.write_text(text[:start] + replacement + text[end:], encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("destination", type=Path)
    root = parser.parse_args().destination.resolve()
    panel = root / "ExtendedControlPanel.js"
    i18n = root / "ExtendedI18n.js"

    locale_additions = (
        (
            "    restartLabel: '再起動レシーバー',\n",
            """    restartLabel: '再起動レシーバー',
    accessibilityStateLabel: 'ユーザー補助サービス状態',
    nativeDeliveryLabel: 'ネイティブイベント配送準備',
    readLogsLabel: 'READ_LOGS権限',
    overlayLabel: 'オーバーレイ権限',
    shizukuLabel: 'Shizuku状態',
""",
            "Japanese diagnostic labels",
        ),
        (
            "    restartLabel: '重启接收器',\n",
            """    restartLabel: '重启接收器',
    accessibilityStateLabel: '无障碍服务状态',
    nativeDeliveryLabel: '原生事件传递就绪',
    readLogsLabel: 'READ_LOGS 权限',
    overlayLabel: '悬浮窗权限',
    shizukuLabel: 'Shizuku 状态',
""",
            "Chinese diagnostic labels",
        ),
        (
            "    restartLabel: 'Restart receiver',\n",
            """    restartLabel: 'Restart receiver',
    accessibilityStateLabel: 'Accessibility Service state',
    nativeDeliveryLabel: 'Native event delivery ready',
    readLogsLabel: 'READ_LOGS permission',
    overlayLabel: 'Overlay permission',
    shizukuLabel: 'Shizuku state',
""",
            "English diagnostic labels",
        ),
    )
    for old, new, label in locale_additions:
        replace_once(i18n, old, new, label)

    replacement = """    const lines = [
      `${text.packageLabel}: ${status.packageName}`,
      `${text.requestedLabel}: ${status.serviceRequested}`,
      `${text.connectionStatus}: ${localizeRuntimeMessage(
        status.connectionStatus,
        text,
      )}`,
      `${text.accessibilityLabel}: ${status.accessibilityEnabled}`,
      `${text.accessibilityStateLabel}: ${
        status.accessibilityServiceStatus || '—'
      }`,
      `${text.captureLabel}: ${status.accessibilityCaptureStatus || '—'}`,
      `${text.coordinatorLabel}: ${status.captureCoordinator || '—'}`,
      `${text.listenerLabel}: ${status.jsListenerStatus || '—'}`,
      `${text.nativeDeliveryLabel}: ${status.nativeDeliveryReady}`,
      `${text.pendingEventsLabel}: ${status.pendingEvents}`,
      `${text.sharedPayloadLabel}: ${status.sharedPayloadStatus || '—'}`,
      `${text.outboundQueueLabel}:\\n${pretty(status.outboundQueueStatus)}`,
      `${text.foregroundStateLabel}: ${status.foregroundServiceState || '—'}`,
      `${text.foregroundHeartbeatLabel}: ${
        status.foregroundServiceHeartbeatAt || '—'
      }`,
      `${text.foregroundErrorLabel}: ${status.foregroundServiceError || '—'}`,
      `${text.p2pCompatibilityLabel}: ${status.p2pCandidatePeers || 0}/${
        status.p2pCompatiblePeers || 0
      }/${status.p2pIncompatiblePeers || 0}`,
      `${text.p2pLastErrorLabel}: ${status.p2pLastCompatibilityError || '—'}`,
      `${text.readLogsLabel}: ${status.readLogs}`,
      `${text.overlayLabel}: ${status.overlay}`,
      `${text.shizukuLabel}:\\n${pretty(status.shizuku)}`,
      `${text.restartLabel}: ${status.restartReceiverStatus || '—'}`,
    ];
"""
    replace_section(
        panel,
        "    const lines = [\n",
        "    show(text.selfTest, lines.join('\\n'));",
        replacement,
        "localized self-test fields",
    )

    replace_once(
        panel,
        "import { getExtendedStrings } from './ExtendedI18n';",
        "import { getExtendedStrings, localizeRuntimeMessage } from './ExtendedI18n';",
        "runtime localization import",
    )


if __name__ == "__main__":
    main()
