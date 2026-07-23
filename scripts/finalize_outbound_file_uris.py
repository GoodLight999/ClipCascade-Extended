#!/usr/bin/env python3
"""Use JSON-safe file URI lists while retaining legacy queue compatibility."""
from __future__ import annotations

import argparse
import re
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
    service = root / "StartForegroundService.js"

    replace_once(
        service,
        "import { createP2SAckTracker } from './P2SAckTracker';",
        """import { createP2SAckTracker } from './P2SAckTracker';
import { parseOutboundFileUris } from './OutboundFileUris';""",
        "outbound file URI parser import",
    )

    text = service.read_text(encoding="utf-8")
    pattern = re.compile(
        r"(?P<indent>[ \t]*)const file_paths = clipContent\s*"
        r"\.split\(','\)\s*"
        r"\.filter\(item => item\.trim\(\) !== ''\);"
    )

    def replacement(match: re.Match[str]) -> str:
        return (
            f"{match.group('indent')}const file_paths = "
            "parseOutboundFileUris(clipContent);"
        )

    patched, count = pattern.subn(replacement, text)
    if count != 3:
        raise RuntimeError(
            f"Outbound file URI parsing: expected 3 comma-split markers, found {count}"
        )
    service.write_text(patched, encoding="utf-8")


if __name__ == "__main__":
    main()
