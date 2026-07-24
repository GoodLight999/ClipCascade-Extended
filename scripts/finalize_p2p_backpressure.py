#!/usr/bin/env python3
"""Use one bounded DataChannel sender for every P2P fragment."""
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
        "import { createP2PFragmentAccumulator } from './P2PFragmentAccumulator';",
        """import { createP2PFragmentAccumulator } from './P2PFragmentAccumulator';
import { sendP2PFragment } from './P2PChannelSender';""",
        "P2P channel sender import",
    )
    replace_once(
        service,
        """                      // DataChannel.send is synchronous. A for...of loop keeps
                      // failures inside this send attempt instead of losing them in
                      // an unobserved async forEach callback.
                      for (const channel of openChannels) {
                        channel.send(messageJson);
                      }""",
        """                      // Bound bufferedAmount across every peer before sending
                      // this fragment. Timeout returns the durable queue item for retry.
                      await sendP2PFragment(openChannels, messageJson);""",
        "P2P fragment backpressure send",
    )


if __name__ == "__main__":
    main()
