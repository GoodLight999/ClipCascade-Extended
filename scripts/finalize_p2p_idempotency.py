#!/usr/bin/env python3
"""Keep one P2P message ID across durable queue retries."""
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
    service = root / "StartForegroundService.js"

    replace_once(
        service,
        """                  const sent = await sendClipBoardTransport(
                    item.content,
                    item.type,
                  );""",
        """                  const sent = await sendClipBoardTransport(
                    item.content,
                    item.type,
                    item.id,
                  );""",
        "pass durable delivery ID to transport",
    )
    replace_once(
        service,
        """          sendClipBoardP2P = async (clipContent, type_ = 'text') => {""",
        """          sendClipBoardP2P = async (
            clipContent,
            type_ = 'text',
            deliveryId = null,
          ) => {""",
        "P2P transport delivery ID",
    )
    replace_once(
        service,
        """                    const metadata = {
                      id: await generateUuid(),""",
        """                    const metadata = {
                      id: deliveryId || (await generateUuid()),""",
        "stable P2P fragment ID",
    )
    replace_once(
        service,
        """        sendClipBoardTransport = async (clipContent, type_ = 'text') => {""",
        """        sendClipBoardTransport = async (
          clipContent,
          type_ = 'text',
          deliveryId = null,
        ) => {""",
        "transport delivery ID signature",
    )
    replace_once(
        service,
        """            const result = await sendClipBoardP2P(clipContent, type_);""",
        """            const result = await sendClipBoardP2P(
              clipContent,
              type_,
              deliveryId,
            );""",
        "P2P delivery ID forwarding",
    )


if __name__ == "__main__":
    main()
