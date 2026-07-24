#!/usr/bin/env python3
"""Ensure failed P2S/P2P attempts are not marked as successfully sent."""
from __future__ import annotations

import argparse
from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one marker, found {count}")
    return text.replace(old, new, 1)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("destination", type=Path)
    root = parser.parse_args().destination.resolve()
    path = root / "StartForegroundService.js"
    text = path.read_text(encoding="utf-8")

    text = replace_once(
        text,
        """                  if (await newCB(hcb)) {
                    previous_clipboard_content_hash = hcb;

                    if (block_image_once) {
                      block_image_once = false;
                    } else {
                      toggle = true;

                      if (cipher_enabled === 'true') {""",
        """                  if (await newCB(hcb)) {
                    if (block_image_once) {
                      block_image_once = false;
                      previous_clipboard_content_hash = hcb;
                    } else {
                      if (cipher_enabled === 'true') {""",
        "defer P2S sent state until publish",
    )
    text = replace_once(
        text,
        """                      stompClient.publish({
                        destination: SEND_DESTINATION,
                        body: JSON.stringify({
                          payload: String(clipContent),
                          type: type_,
                        }),
                      });
                    }""",
        """                      stompClient.publish({
                        destination: SEND_DESTINATION,
                        body: JSON.stringify({
                          payload: String(clipContent),
                          type: type_,
                        }),
                      });
                      previous_clipboard_content_hash = hcb;
                      toggle = true;
                    }""",
        "commit P2S state after publish",
    )

    text = replace_once(
        text,
        """                if (await newCB(hcb)) {
                  previous_clipboard_content_hash = hcb;

                  if (block_image_once) {
                    block_image_once = false;
                  } else {""",
        """                if (await newCB(hcb)) {
                  if (block_image_once) {
                    block_image_once = false;
                    previous_clipboard_content_hash = hcb;
                  } else {""",
        "defer P2P sent state until all fragments",
    )
    text = replace_once(
        text,
        """                      if (sendingFragmentId !== metadata.id) {
                        loopBroken = true;
                        return;
                      }""",
        """                      if (sendingFragmentId !== metadata.id) {
                        loopBroken = true;
                        return false;
                      }""",
        "report interrupted P2P send as unsent",
    )
    text = replace_once(
        text,
        """                    if (!loopBroken) {
                      await resetSendingFragmentId();
                    }""",
        """                    if (!loopBroken) {
                      previous_clipboard_content_hash = hcb;
                      await resetSendingFragmentId();
                    }""",
        "commit P2P state after all fragments",
    )

    path.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
