#!/usr/bin/env python3
"""Recover a requested dead runtime only from the visible clipboard capture Activity."""
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
    activity = root / "android/app/src/main/java/com/clipcascade/ClipboardFloatingActivity.kt"

    replace_once(
        activity,
        """            floatingView = view
            windowManager.addView(view, params)
            view.postDelayed(::captureClipboard, 80L)""",
        """            floatingView = view
            windowManager.addView(view, params)
            // The Activity/overlay is user-visible at this point, so Android permits a
            // requested dead Foreground Service to be recovered without an arbitrary
            // background launch. Healthy runtimes are ignored by the heartbeat guard.
            ForegroundRuntimeRecovery.startIfRequested(this, "clipboard-overlay")
            view.postDelayed(::captureClipboard, 80L)""",
        "visible capture runtime recovery",
    )


if __name__ == "__main__":
    main()
