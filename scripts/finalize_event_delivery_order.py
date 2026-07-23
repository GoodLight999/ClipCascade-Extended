#!/usr/bin/env python3
"""Register JS listeners before native durable events are activated and drained."""
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
        """        const clipboardListener = new NativeEventEmitter(ClipboardListener);
        // start clipboard listening
        ClipboardListener.startListening();
        // clipboard listener callback
        const clipboardOnChange = clipboardListener.addListener(""",
        """        const clipboardListener = new NativeEventEmitter(ClipboardListener);
        // The native store drains synchronously when startListening() activates it.
        // Therefore the JS callback must exist before native activation.
        const clipboardOnChange = clipboardListener.addListener(""",
        "clipboard listener registration before native activation",
    )
    replace_once(
        service,
        """          },
        );

        const clearFiles = async (expensiveCall = false) => {""",
        """          },
        );
        await ClipboardListener.startListening();
        await setDataInAsyncStorage(
          'js_listener_status',
          'ready-after-registration',
        );

        const clearFiles = async (expensiveCall = false) => {""",
        "native activation after listener registration",
    )


if __name__ == "__main__":
    main()
