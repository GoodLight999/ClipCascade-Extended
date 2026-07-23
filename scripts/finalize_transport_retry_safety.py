#!/usr/bin/env python3
"""Ensure failed P2S/P2P attempts are not marked as successfully sent."""
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
        """                  previous_clipboard_content_hash = hcb;

                  if (block_image_once) {""",
        """                  if (block_image_once) {""",
        2,
        "defer sent hash until transport success",
    )
    text = replace_exact(
        text,
        """                  if (block_image_once) {
                    block_image_once = false;
                  } else {""",
        """                  if (block_image_once) {
                    block_image_once = false;
                    previous_clipboard_content_hash = hcb;
                  } else {""",
        2,
        "retain inbound image loop suppression",
    )
    text = replace_exact(
        text,
        """                    stompClient.publish({
                      destination: SEND_DESTINATION,
                      body: clipContent,
                    });
                    toggle = true;""",
        """                    stompClient.publish({
                      destination: SEND_DESTINATION,
                      body: clipContent,
                    });
                    previous_clipboard_content_hash = hcb;
                    toggle = true;""",
        1,
        "commit P2S hash after publish",
    )
    text = replace_exact(
        text,
        """                      if (sendingFragmentId != metadata.id) {
                        loopBroken = true;
                        return;
                      }""",
        """                      if (sendingFragmentId != metadata.id) {
                        loopBroken = true;
                        return false;
                      }""",
        1,
        "report interrupted P2P send as unsent",
    )
    text = replace_exact(
        text,
        """                    if (!loopBroken) {
                      await resetSendingFragmentId();
                    }""",
        """                    if (!loopBroken) {
                      previous_clipboard_content_hash = hcb;
                      await resetSendingFragmentId();
                    }""",
        1,
        "commit P2P hash after all fragments",
    )

    path.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
