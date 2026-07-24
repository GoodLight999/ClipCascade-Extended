#!/usr/bin/env python3
"""Connect inherited App error paths to the canonical locale dictionary."""
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
    app = root / "App.js"

    replace_once(
        app,
        """        Alert.alert('Error', 'Unknown error: ' + JSON.stringify(e));""",
        """        Alert.alert(
          EXTENDED_TEXT.errorTitle,
          `${EXTENDED_TEXT.unknownError}: ${JSON.stringify(e)}`,
        );""",
        "localized file-download error dialog",
    )


if __name__ == "__main__":
    main()
