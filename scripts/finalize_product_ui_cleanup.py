#!/usr/bin/env python3
"""Remove inherited render-time side effects and keep adaptive colors runtime-safe."""
from __future__ import annotations

import argparse
from pathlib import Path


def replace_exact(path: Path, old: str, new: str, expected: int, label: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != expected:
        raise RuntimeError(f"{label}: expected {expected} marker(s), found {count}")
    path.write_text(text.replace(old, new), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("destination", type=Path)
    root = parser.parse_args().destination.resolve()
    app = root / "App.js"

    replace_exact(app, "  Image,\n", "", 1, "unused inherited Image import")
    replace_exact(
        app,
        "  getMultipleDataFromAsyncStorage,\n  clearAsyncStorage,\n",
        "",
        1,
        "unused inherited storage imports",
    )
    replace_exact(
        app,
        """  // Request permissions for notifications
  PermissionsAndroid.request(PermissionsAndroid.PERMISSIONS.POST_NOTIFICATIONS);

""",
        "",
        1,
        "render-time notification permission request",
    )
    replace_exact(
        app,
        """      try {
        // enable websocket button""",
        """      try {
        await PermissionsAndroid.request(
          PermissionsAndroid.PERMISSIONS.POST_NOTIFICATIONS,
        );
        // enable websocket button""",
        1,
        "one-shot notification permission request",
    )
    replace_exact(
        app,
        "{EXTENDED_TEXT.appSubtitle}</Text>",
        "{EXTENDED_TEXT.appSubtitle} · {APP_VERSION}</Text>",
        4,
        "visible Extended version labels",
    )
    replace_exact(
        app,
        "PlatformColor('?android:attr/editTextBackground')",
        "PlatformColor('?android:attr/colorBackgroundFloating')",
        1,
        "valid input background color",
    )
    replace_exact(
        app,
        "PlatformColor('?android:attr/listDivider')",
        "PlatformColor('?android:attr/textColorSecondary')",
        2,
        "valid adaptive border color",
    )
    replace_exact(
        app,
        "  StatusBar,\n  PlatformColor,\n",
        "  StatusBar,\n  PlatformColor,\n  useColorScheme,\n",
        1,
        "runtime color-scheme import",
    )
    replace_exact(
        app,
        "export default function App() {",
        "export default function App() {\n  const extendedColorScheme = useColorScheme();",
        1,
        "runtime color-scheme hook",
    )
    replace_exact(
        app,
        """      <StatusBar
        backgroundColor={PlatformColor('?android:attr/colorBackground')}
        barStyle="default"
      />""",
        """      <StatusBar
        backgroundColor={extendedColorScheme === 'dark' ? '#121212' : '#ffffff'}
        barStyle={extendedColorScheme === 'dark' ? 'light-content' : 'dark-content'}
      />""",
        1,
        "StatusBar concrete colors",
    )


if __name__ == "__main__":
    main()
