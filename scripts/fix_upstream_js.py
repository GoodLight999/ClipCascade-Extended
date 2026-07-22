#!/usr/bin/env python3
"""Repair verified correctness defects in the pinned upstream JavaScript.

These edits are kept separate from product-specific UI patches so each upstream
repair has a narrow, guarded marker and can be removed independently when the
primary project incorporates an equivalent fix.
"""

from __future__ import annotations

import argparse
from pathlib import Path


def replace_exact(
    text: str,
    old: str,
    new: str,
    expected: int,
    label: str,
) -> str:
    actual = text.count(old)
    if actual != expected:
        raise RuntimeError(f"{label}: expected {expected} marker(s), found {actual}")
    return text.replace(old, new)


def patch_app(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = replace_exact(
        text,
        "          validResult = await validateSession(data_s);",
        "          const validResult = await validateSession(data_s);",
        1,
        "session validation declaration",
    )
    text = replace_exact(
        text,
        "          hashResult = await hash(data_s, password);",
        "          const hashResult = await hash(data_s, password_s);",
        1,
        "encryption hash declaration and password source",
    )
    text = replace_exact(
        text,
        "        wsIsRunning_s = wsIsRunning === 'true' ? 'false' : 'true'; // toggle",
        "        const wsIsRunning_s =\n          wsIsRunning === 'true' ? 'false' : 'true'; // toggle",
        1,
        "foreground service state declaration",
    )
    text = replace_exact(
        text,
        "      if (response.status == 204) {",
        "      if (response.status === 204) {",
        1,
        "logout status comparison",
    )
    hook_end = """    };
  }, []);

  // Function to convert a server URL to a WebSocket URL"""
    hook_end_fixed = """    };
    // This initialization intentionally runs once. Runtime state is exchanged
    // through AsyncStorage and the native foreground service rather than by
    // restarting the complete login/bootstrap sequence after every render.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Function to convert a server URL to a WebSocket URL"""
    text = replace_exact(
        text,
        hook_end,
        hook_end_fixed,
        1,
        "intentional one-shot initialization",
    )
    path.write_text(text, encoding="utf-8")


def patch_foreground_service(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = replace_exact(
        text,
        "        const textEncoder = new TextEncoder();",
        "        const textEncoder = new encoding.TextEncoder();",
        1,
        "TextEncoder namespace",
    )
    text = replace_exact(
        text,
        "        const textDecoder = new TextDecoder();",
        "        const textDecoder = new encoding.TextDecoder();",
        1,
        "TextDecoder namespace",
    )
    text = replace_exact(
        text,
        "temp = {};",
        "const temp = {};",
        2,
        "file payload temporary declarations",
    )
    text = replace_exact(
        text,
        "              await clearFiles((expensiveCall = true));",
        "              await clearFiles(true);",
        1,
        "clearFiles argument assignment",
    )
    path.write_text(text, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    destination = args.destination.resolve()
    patch_app(destination / "App.js")
    patch_foreground_service(destination / "StartForegroundService.js")


if __name__ == "__main__":
    main()
