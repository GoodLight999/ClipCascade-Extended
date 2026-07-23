#!/usr/bin/env python3
"""Ensure early native events are durable before transport functions exist."""
from __future__ import annotations

import argparse
from pathlib import Path


def replace_exact(text: str, old: str, new: str, expected: int, label: str) -> str:
    count = text.count(old)
    if count != expected:
        raise RuntimeError(f"{label}: expected {expected} marker(s), found {count}")
    return text.replace(old, new)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("destination", type=Path)
    root = parser.parse_args().destination.resolve()
    path = root / "StartForegroundService.js"
    text = path.read_text(encoding="utf-8")

    text = replace_exact(
        text,
        """        };

        // encrption""",
        """        };

        const enqueueOutboundClipboard = async (
          clipContent,
          type_ = 'text',
        ) => {
          await outboundQueue.enqueue(String(clipContent), type_);
          await updateOutboundQueueStatus('queued');
          await flushOutboundQueue();
        };

        // encrption""",
        1,
        "early durable enqueue function",
    )
    text = replace_exact(
        text,
        "await sendClipBoard(",
        "await enqueueOutboundClipboard(",
        4,
        "native event dispatches",
    )
    text = replace_exact(
        text,
        """        const sendClipBoard = async (clipContent, type_ = 'text') => {
          await outboundQueue.enqueue(String(clipContent), type_);
          await updateOutboundQueueStatus('queued');
          await flushOutboundQueue();
        };

""",
        "",
        1,
        "late transport-dependent enqueue declaration",
    )

    path.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
