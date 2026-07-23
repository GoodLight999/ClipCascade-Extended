#!/usr/bin/env python3
"""Replace the inherited room-wide encryption wording in the P2S receive path."""
from __future__ import annotations

import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("destination", type=Path)
    root = parser.parse_args().destination.resolve()
    path = root / "StartForegroundService.js"
    text = path.read_text(encoding="utf-8")
    old = """                        throw new Error(
                          `Encryption must be enabled on all devices if enabled. JSON parsing failed: ${error.message}`,
                        );"""
    new = """                        throw new Error(
                          `Unable to decrypt P2S payload. Check the encryption setting and shared key: ${error.message}`,
                        );"""
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"P2S decrypt wording: expected one marker, found {count}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


if __name__ == "__main__":
    main()
