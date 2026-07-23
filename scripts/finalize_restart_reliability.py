#!/usr/bin/env python3
"""Harden boot/update restart wiring with guarded source edits."""
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

    replace_once(
        root / "android/app/src/main/AndroidManifest.xml",
        '''          <action android:name="android.intent.action.BOOT_COMPLETED" />''',
        '''          <action android:name="android.intent.action.BOOT_COMPLETED" />
          <action android:name="android.intent.action.MY_PACKAGE_REPLACED" />''',
        "restart receiver actions",
    )

    replace_once(
        root / "HeadlessTask.js",
        '''    if (data && data['event'] === 'BOOT_COMPLETED') {''',
        '''    if (
      data &&
      (data['event'] === 'android.intent.action.BOOT_COMPLETED' ||
        data['event'] === 'android.intent.action.MY_PACKAGE_REPLACED')
    ) {''',
        "headless restart events",
    )


if __name__ == "__main__":
    main()
