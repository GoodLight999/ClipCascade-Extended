#!/usr/bin/env python3
"""Reject label-only localization, unsafe adaptive colors, and inherited UI regressions."""
from __future__ import annotations

import argparse
from pathlib import Path


def require(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise RuntimeError(f"missing {label}: {needle!r}")


def forbid(text: str, needle: str, label: str) -> None:
    if needle in text:
        raise RuntimeError(f"forbidden {label}: {needle!r}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    root = parser.parse_args().root.resolve()
    app = (root / "App.js").read_text(encoding="utf-8")
    i18n = (root / "ExtendedI18n.js").read_text(encoding="utf-8")
    panel = (root / "ExtendedControlPanel.js").read_text(encoding="utf-8")
    analyzer = (root / "AutoDebug.js").read_text(encoding="utf-8")

    for expression, label in (
        ("localizeRuntimeMessage(loadingPageMessage, EXTENDED_TEXT)", "loading-state localization"),
        ("localizeRuntimeMessage(loginStatusMessage, EXTENDED_TEXT)", "login-status localization"),
        ("localizeRuntimeMessage(wsPageMessage, EXTENDED_TEXT)", "connection-status localization"),
        ("localizeRuntimeMessage(wsPageP2PMessage, EXTENDED_TEXT)", "P2P-status localization"),
        ("EXTENDED_TEXT.errorTitle", "localized error dialog title"),
        ("EXTENDED_TEXT.unknownError", "localized unknown-error dialog"),
    ):
        require(app, expression, label)
    forbid(app, "Alert.alert('Error'", "hard-coded English Alert title")
    forbid(app, "Unknown error: ' +", "hard-coded English Alert body")

    require(app, "const extendedColorScheme = useColorScheme();", "runtime color-scheme hook")
    require(
        app,
        "backgroundColor={extendedColorScheme === 'dark' ? '#121212' : '#ffffff'}",
        "concrete StatusBar background colors",
    )
    require(
        app,
        "barStyle={extendedColorScheme === 'dark' ? 'light-content' : 'dark-content'}",
        "adaptive StatusBar icon style",
    )
    forbid(
        app,
        "backgroundColor={PlatformColor('?android:attr/colorBackground')}",
        "PlatformColor object passed to StatusBar",
    )

    for key in (
        "checkingService",
        "verifyingSession",
        "requestTimedOut",
        "genericError",
        "unknownError",
        "loginSuccess",
        "loginFailed",
        "logoutSuccess",
        "logoutFailed",
        "loginServerModeError",
        "loginStunError",
        "loginMaxSizeError",
        "loginHashError",
        "diagnosticsOverall",
        "diagnosticRecovery",
    ):
        require(i18n, f"{key}:", f"localized runtime key {key}")

    for inherited, label in (
        ("Checking foreground service", "foreground check mapping"),
        ("Verifying Session", "session verification mapping"),
        ("Login successful", "login success mapping"),
        ("Login failed", "login failure mapping"),
        ("Logout successful", "logout success mapping"),
        ("Logout failed", "logout failure mapping"),
        ("Error: Request timed out", "timeout mapping"),
        ("Unsupported protocol in URL", "URL protocol mapping"),
    ):
        require(i18n, inherited, label)

    require(panel, "formatDiagnosticsReport(report, text)", "localized diagnostic report")
    require(analyzer, "CHECK_LABEL_KEYS", "localized diagnostic check names")
    require(analyzer, "levels = { PASS: text.pass", "localized diagnostic levels")

    print("complete product/runtime localization: OK")


if __name__ == "__main__":
    main()
