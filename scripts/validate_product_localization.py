#!/usr/bin/env python3
"""Reject label-only localization, unreadable diagnostics, and inherited UI regressions."""
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
    shizuku_policy = (root / "ShizukuSetupPolicy.js").read_text(encoding="utf-8")

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

    # The original self-test rendered dark text on a gray surface. Do not entrust
    # this critical report to OEM-dependent Android theme attributes again.
    require(panel, "createStyles(useColorScheme() === 'dark')", "deterministic panel theme")
    require(panel, "surface: '#1b1b1f'", "dark diagnostic surface")
    require(panel, "text: '#f5f5f7'", "dark diagnostic text")
    require(panel, "surface: '#ffffff'", "light diagnostic surface")
    require(panel, "text: '#15171a'", "light diagnostic text")
    forbid(panel, "PlatformColor(", "OEM-dependent diagnostic colors")

    # Setup instructions and ADB commands must be selectable and one-tap copyable.
    require(panel, "<Text selectable style={styles.dialogBody}>", "selectable dialog body")
    require(panel, "Clipboard.setString(dialog.copy)", "one-tap dialog copy")
    require(panel, "ADB_COMMANDS", "canonical two-command ADB fallback")

    # Shizuku must distinguish install/running/authorization states and must not
    # be required after Android has retained the one-time grants. Failure prose is
    # localized through setupFailed; codes stay machine-readable and language-neutral.
    require(panel, "planShizukuSetup(status)", "Shizuku setup planner wiring")
    require(panel, "isShizukuSetupVerified(status)", "Shizuku grant verification")
    require(panel, "formatSetupError(error, text)", "localized Shizuku failure wrapper")
    require(panel, "SHIZUKU_PERMISSION_NOT_RETAINED", "permission failure code")
    require(panel, "SHIZUKU_GRANTS_NOT_RETAINED", "grant verification failure code")
    forbid(panel, "Shizuku permission was not retained", "English-only Shizuku failure")
    forbid(panel, "Android did not retain the required grants", "English-only grant failure")
    require(shizuku_policy, "state: 'already-configured'", "post-setup independence")
    require(shizuku_policy, "state: 'not-running'", "stopped Shizuku classification")
    require(shizuku_policy, "state: 'permission-required'", "authorization classification")

    print("complete product/runtime localization and setup UX: OK")


if __name__ == "__main__":
    main()
