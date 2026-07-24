#!/usr/bin/env python3
"""Guard visible-copy foreground runtime recovery in the canonical Activity."""
from __future__ import annotations

import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("destination", type=Path)
    root = parser.parse_args().destination.resolve()
    activity = root / "android/app/src/main/java/com/clipcascade/ClipboardFloatingActivity.kt"
    text = activity.read_text(encoding="utf-8")

    marker = 'ForegroundRuntimeRecovery.startIfRequested(this, "clipboard-overlay")'
    count = text.count(marker)
    if count != 1:
        raise RuntimeError(
            f"visible capture runtime recovery: expected one canonical call, found {count}"
        )

    overlay_index = text.find("windowManager.addView(view, params)")
    recovery_index = text.find(marker)
    capture_index = text.find("view.postDelayed(::captureClipboard, INITIAL_CAPTURE_DELAY_MS)")
    if not (0 <= overlay_index < recovery_index < capture_index):
        raise RuntimeError("visible capture runtime recovery is outside the guarded Activity window")


if __name__ == "__main__":
    main()
