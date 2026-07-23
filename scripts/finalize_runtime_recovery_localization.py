#!/usr/bin/env python3
"""Add localized labels for visible-capture Foreground Service recovery."""
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
    panel = root / "ExtendedControlPanel.js"

    for old, new, label in (
        (
            "    diagnosticSingleton: 'Foreground Service単一ランタイム',\n",
            """    diagnosticSingleton: 'Foreground Service単一ランタイム',
    foregroundRecoveryLabel: 'Foreground Service復旧状態',
    diagnosticRecovery: '表示中コピー取得からのService復旧',
""",
            "Japanese recovery labels",
        ),
        (
            "    diagnosticSingleton: 'Foreground Service 单实例',\n",
            """    diagnosticSingleton: 'Foreground Service 单实例',
    foregroundRecoveryLabel: 'Foreground Service 恢复状态',
    diagnosticRecovery: '从可见复制捕获恢复 Service',
""",
            "Chinese recovery labels",
        ),
        (
            "    diagnosticSingleton: 'Foreground Service singleton',\n",
            """    diagnosticSingleton: 'Foreground Service singleton',
    foregroundRecoveryLabel: 'Foreground Service recovery state',
    diagnosticRecovery: 'Visible-copy runtime recovery',
""",
            "English recovery labels",
        ),
    ):
        replace_once(i18n, old, new, label)

    replace_once(
        panel,
        """      `${text.foregroundErrorLabel}: ${status.foregroundServiceError || '—'}`,
      `${text.p2pCompatibilityLabel}: ${status.p2pCandidatePeers || 0}/${""",
        """      `${text.foregroundErrorLabel}: ${status.foregroundServiceError || '—'}`,
      `${text.foregroundRecoveryLabel}: ${
        status.foregroundServiceRecoveryStatus || '—'
      }`,
      `${text.p2pCompatibilityLabel}: ${status.p2pCandidatePeers || 0}/${""",
        "localized recovery status in self-test",
    )


if __name__ == "__main__":
    main()
