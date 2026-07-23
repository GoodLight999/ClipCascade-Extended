#!/usr/bin/env python3
"""Localize all user-visible Foreground Service notifications and dialogs."""
from __future__ import annotations

import argparse
from pathlib import Path


def replace_once(path: Path, old: str, new: str, label: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one marker, found {count}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def replace_exact(path: Path, old: str, new: str, expected: int, label: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != expected:
        raise RuntimeError(f"{label}: expected {expected} markers, found {count}")
    path.write_text(text.replace(old, new), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("destination", type=Path)
    root = parser.parse_args().destination.resolve()
    service = root / "StartForegroundService.js"
    i18n = root / "ExtendedI18n.js"

    for old, new, label in (
        (
            "    diagnosticRecovery: '表示中コピー取得からのService復旧',\n",
            """    diagnosticRecovery: '表示中コピー取得からのService復旧',
    notificationMonitorChannel: 'クリップボード同期',
    notificationDownloadProgressChannel: 'ファイル保存の進行状況',
    notificationConnectionChannel: '接続状態',
    notificationConnectionRestored: '接続を復旧しました 🔗',
    notificationConnectionLost: '接続が切れました ⛓️‍💥',
    notificationDownloadFiles: '📥 受信ファイルがあります',
    notificationDownloadingFiles: 'ファイルを保存中…',
    downloadFilesFailed: 'ファイルの保存に失敗しました',
""",
            "Japanese notification labels",
        ),
        (
            "    diagnosticRecovery: '从可见复制捕获恢复 Service',\n",
            """    diagnosticRecovery: '从可见复制捕获恢复 Service',
    notificationMonitorChannel: '剪贴板同步',
    notificationDownloadProgressChannel: '文件保存进度',
    notificationConnectionChannel: '连接状态',
    notificationConnectionRestored: '连接已恢复 🔗',
    notificationConnectionLost: '连接已断开 ⛓️‍💥',
    notificationDownloadFiles: '📥 有接收文件',
    notificationDownloadingFiles: '正在保存文件…',
    downloadFilesFailed: '保存文件失败',
""",
            "Chinese notification labels",
        ),
        (
            "    diagnosticRecovery: 'Visible-copy runtime recovery',\n",
            """    diagnosticRecovery: 'Visible-copy runtime recovery',
    notificationMonitorChannel: 'Clipboard synchronization',
    notificationDownloadProgressChannel: 'File save progress',
    notificationConnectionChannel: 'Connection status',
    notificationConnectionRestored: 'Connection restored 🔗',
    notificationConnectionLost: 'Connection lost ⛓️‍💥',
    notificationDownloadFiles: '📥 Received files available',
    notificationDownloadingFiles: 'Saving files…',
    downloadFilesFailed: 'Failed to save files',
""",
            "English notification labels",
        ),
    ):
        replace_once(i18n, old, new, label)

    replace_once(
        service,
        "} from './AsyncStorageManagement';",
        """} from './AsyncStorageManagement';
import { getExtendedStrings } from './ExtendedI18n';

const RUNTIME_TEXT = getExtendedStrings();""",
        "foreground notification locale import",
    )

    replace_exact(
        service,
        "'WebSocket Connection Restored 🔗'",
        "RUNTIME_TEXT.notificationConnectionRestored",
        2,
        "localized restored notifications",
    )
    replace_exact(
        service,
        "'WebSocket Connection Lost ⛓️‍💥'",
        "RUNTIME_TEXT.notificationConnectionLost",
        2,
        "localized lost notifications",
    )
    replace_exact(
        service,
        "'📥 Download File(s)'",
        "RUNTIME_TEXT.notificationDownloadFiles",
        2,
        "localized P2S/P2P received-file notifications",
    )
    replace_once(
        service,
        "title: 'Downloading File(s)...',",
        "title: RUNTIME_TEXT.notificationDownloadingFiles,",
        "localized file-save progress notification",
    )
    replace_once(
        service,
        "Alert.alert('Error', 'Failed to download files: ' + e);",
        """Alert.alert(
                  RUNTIME_TEXT.errorTitle,
                  `${RUNTIME_TEXT.downloadFilesFailed}: ${String(e)}`,
                );""",
        "localized file-save failure dialog",
    )
    replace_once(
        service,
        "name: 'ClipCascade Monitor',",
        "name: RUNTIME_TEXT.notificationMonitorChannel,",
        "localized foreground channel",
    )
    replace_once(
        service,
        "name: 'ClipCascade Download Progress',",
        "name: RUNTIME_TEXT.notificationDownloadProgressChannel,",
        "localized progress channel",
    )
    replace_once(
        service,
        "name: 'ClipCascade Connection Status',",
        "name: RUNTIME_TEXT.notificationConnectionChannel,",
        "localized connection channel",
    )

    text = service.read_text(encoding="utf-8")
    for inherited in (
        "WebSocket Connection Restored",
        "WebSocket Connection Lost",
        "📥 Download File(s)",
        "Downloading File(s)...",
        "ClipCascade Monitor",
        "ClipCascade Download Progress",
        "ClipCascade Connection Status",
        "Failed to download files",
    ):
        if inherited in text:
            raise RuntimeError(f"inherited notification text remained: {inherited}")


if __name__ == "__main__":
    main()
