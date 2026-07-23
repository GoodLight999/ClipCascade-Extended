#!/usr/bin/env python3
"""Use JSON-safe file URI lists while retaining legacy queue compatibility."""
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

    replace_once(
        service,
        "import { createP2SAckTracker } from './P2SAckTracker';",
        """import { createP2SAckTracker } from './P2SAckTracker';
import { parseOutboundFileUris } from './OutboundFileUris';""",
        "outbound file URI parser import",
    )
    replace_exact(
        service,
        """                    const file_paths = clipContent
                      .split(',')
                      .filter(item => item.trim() !== '');""",
        """                    const file_paths = parseOutboundFileUris(clipContent);""",
        2,
        "P2S/P2P file URI parsing",
    )


if __name__ == "__main__":
    main()
