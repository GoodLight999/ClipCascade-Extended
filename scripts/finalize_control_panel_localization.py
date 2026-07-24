#!/usr/bin/env python3
"""Add diagnostic-label keys to the generated locale dictionary.

The canonical control-panel implementation is complete in overlay/ and must not
be repaired during materialization. This compatibility phase only augments the
locale dictionary until those keys are folded into the canonical dictionary.
"""
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
    diagnosticsOverall: '総合判定',
    diagnosticsGenerated: '生成日時',
    diagnosticsRawStatus: '生の状態情報',
    diagnosticsNativeProbe: 'ネイティブ実経路検査',
    diagnosticNativeReact: 'ネイティブ→Reactイベント経路',
    diagnosticAccessibility: 'ユーザー補助コピー検知',
    diagnosticOverlay: 'オーバーレイ権限',
    diagnosticCapture: 'クリップボード取得コーディネーター',
    diagnosticNativeEvents: '保留中のネイティブイベント',
    diagnosticOutboundQueue: '耐久送信キュー',
    diagnosticForeground: 'Foreground Service heartbeat',
    diagnosticSingleton: 'Foreground Service単一ランタイム',
    diagnosticSharedPayload: 'Android共有／退避済みペイロード',
    diagnosticP2P: 'P2P互換性',
    diagnosticClipboardProbe: '前景クリップボード実読取',
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
    diagnosticsOverall: '总体结果',
    diagnosticsGenerated: '生成时间',
    diagnosticsRawStatus: '原始状态',
    diagnosticsNativeProbe: '原生实际路径检查',
    diagnosticNativeReact: '原生→React 事件路径',
    diagnosticAccessibility: '无障碍复制检测',
    diagnosticOverlay: '悬浮窗权限',
    diagnosticCapture: '剪贴板捕获协调器',
    diagnosticNativeEvents: '待处理原生事件',
    diagnosticOutboundQueue: '持久发送队列',
    diagnosticForeground: 'Foreground Service heartbeat',
    diagnosticSingleton: 'Foreground Service 单实例',
    diagnosticSharedPayload: 'Android 分享／已暂存内容',
    diagnosticP2P: 'P2P 兼容性',
    diagnosticClipboardProbe: '前台剪贴板实际读取',
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
    diagnosticsOverall: 'Overall',
    diagnosticsGenerated: 'Generated',
    diagnosticsRawStatus: 'Raw status',
    diagnosticsNativeProbe: 'Native active-path probe',
    diagnosticNativeReact: 'Native → React event bridge',
    diagnosticAccessibility: 'Accessibility copy detection',
    diagnosticOverlay: 'Overlay permission',
    diagnosticCapture: 'Clipboard capture coordinator',
    diagnosticNativeEvents: 'Pending native events',
    diagnosticOutboundQueue: 'Durable outbound queue',
    diagnosticForeground: 'Foreground Service heartbeat',
    diagnosticSingleton: 'Foreground Service singleton',
    diagnosticSharedPayload: 'Android Share / staged payload',
    diagnosticP2P: 'P2P compatibility',
    diagnosticClipboardProbe: 'Foreground clipboard probe',
""",
            "English diagnostic labels",
        ),
    )
    for old, new, label in locale_additions:
        replace_once(i18n, old, new, label)


if __name__ == "__main__":
    main()
