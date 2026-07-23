#!/usr/bin/env python3
"""Localize inherited dynamic UI messages while preserving technical error details."""
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
    i18n = root / "ExtendedI18n.js"
    app = root / "App.js"

    for old, new, label in (
        (
            "    receiving: '受信中',\n",
            """    receiving: '受信中',
    checkingService: 'Foreground Serviceを確認中…',
    verifyingSession: 'セッションを確認中…',
    requestTimedOut: '要求がタイムアウトしました',
    errorTitle: 'エラー',
    genericError: 'エラー',
    unknownError: '不明なエラー',
    invalidUrl: 'URLが無効です',
    unsupportedProtocol: '未対応のURLプロトコル',
    loginSuccess: 'ログイン成功',
    loginFailed: 'ログイン失敗',
    loginServerModeError: 'ログイン後にサーバーモードを取得できません',
    loginStunError: 'ログイン後にSTUN URLを取得できません',
    loginMaxSizeError: 'ログイン後に最大サイズを取得できません',
    loginHashError: 'ログイン後の暗号鍵生成に失敗しました',
    logoutSuccess: 'ログアウト成功',
    logoutFailed: 'ログアウト失敗',
    fetchLoginError: 'ログイン画面を取得できません',
    csrfMissing: 'ログイン画面にCSRF tokenがありません',
    cookieMissing: 'ログイン応答にSet-Cookie headerがありません',
""",
            "Japanese runtime messages",
        ),
        (
            "    receiving: '正在接收',\n",
            """    receiving: '正在接收',
    checkingService: '正在检查 Foreground Service…',
    verifyingSession: '正在验证会话…',
    requestTimedOut: '请求超时',
    errorTitle: '错误',
    genericError: '错误',
    unknownError: '未知错误',
    invalidUrl: 'URL 无效',
    unsupportedProtocol: '不支持的 URL 协议',
    loginSuccess: '登录成功',
    loginFailed: '登录失败',
    loginServerModeError: '登录后无法获取服务器模式',
    loginStunError: '登录后无法获取 STUN URL',
    loginMaxSizeError: '登录后无法获取最大大小',
    loginHashError: '登录后生成加密密钥失败',
    logoutSuccess: '退出登录成功',
    logoutFailed: '退出登录失败',
    fetchLoginError: '无法获取登录页面',
    csrfMissing: '登录页面中没有 CSRF token',
    cookieMissing: '登录响应中没有 Set-Cookie header',
""",
            "Chinese runtime messages",
        ),
        (
            "    receiving: 'Receiving',\n",
            """    receiving: 'Receiving',
    checkingService: 'Checking Foreground Service…',
    verifyingSession: 'Verifying session…',
    requestTimedOut: 'Request timed out',
    errorTitle: 'Error',
    genericError: 'Error',
    unknownError: 'Unknown error',
    invalidUrl: 'Invalid URL',
    unsupportedProtocol: 'Unsupported URL protocol',
    loginSuccess: 'Login successful',
    loginFailed: 'Login failed',
    loginServerModeError: 'Unable to get server mode after login',
    loginStunError: 'Unable to get STUN URL after login',
    loginMaxSizeError: 'Unable to get maximum size after login',
    loginHashError: 'Unable to generate encryption key after login',
    logoutSuccess: 'Logout successful',
    logoutFailed: 'Logout failed',
    fetchLoginError: 'Unable to fetch login page',
    csrfMissing: 'No CSRF token found in login page',
    cookieMissing: 'No Set-Cookie header returned from login page',
""",
            "English runtime messages",
        ),
    ):
        replace_once(i18n, old, new, label)

    old_function = r"""export function localizeRuntimeMessage(value, strings = getExtendedStrings()) {
  if (value == null || value === '') return strings.noStatus;
  return String(value)
    .replace(/✅ Signaling connected; waiting for peer/g, `✅ ${strings.signalingWaiting}`)
    .replace(/✅ P2P peer connected/g, `✅ ${strings.peerConnected}`)
    .replace(/✅ Connected/g, `✅ ${strings.connected}`)
    .replace(/✅ Disconnected/g, `✅ ${strings.disconnected}`)
    .replace(/⏳ Connecting\.\.\./g, `⏳ ${strings.connecting}`)
    .replace(/⌛ Reconnecting\.\.\./g, `⌛ ${strings.reconnecting}`)
    .replace(/Starting foreground service\.\.\./gi, strings.startingService)
    .replace(/Stopping foreground service\.\.\./gi, strings.stoppingService)
    .replace(/Foreground service stopped running/gi, `${strings.fail}: ${strings.serviceError}`)
    .replace(/❌ Connection Failed:/g, `❌ ${strings.connectionFailed}:`)
    .replace(/❌ Outbound Error:/g, `❌ ${strings.outboundError}:`)
    .replace(/❌ Inbound Error:/g, `❌ ${strings.inboundError}:`)
    .replace(/❌ Foreground service:/gi, `❌ ${strings.serviceError}:`)
    .replace(/⚠️ Ignored (\d+) incompatible P2P peer\(s\)/g, `⚠️ ${strings.ignoredIncompatible}: $1`)
    .replace(/Peers:/g, `${strings.peers}:`)
    .replace(/Sending:/g, `${strings.sending}:`)
    .replace(/Receiving:/g, `${strings.receiving}:`)
    .replace(/Please wait\.\.\./gi, strings.working);
}"""
    new_function = r"""export function localizeRuntimeMessage(value, strings = getExtendedStrings()) {
  if (value == null || value === '') return strings.noStatus;
  return String(value)
    .replace(/✅ Signaling connected; waiting for peer/g, `✅ ${strings.signalingWaiting}`)
    .replace(/✅ P2P peer connected/g, `✅ ${strings.peerConnected}`)
    .replace(/✅ Connected/g, `✅ ${strings.connected}`)
    .replace(/✅ Disconnected/g, `✅ ${strings.disconnected}`)
    .replace(/⏳ Connecting\.\.\./g, `⏳ ${strings.connecting}`)
    .replace(/⌛ Reconnecting\.\.\./g, `⌛ ${strings.reconnecting}`)
    .replace(/Loading\.\.\./gi, strings.loading)
    .replace(/Checking foreground service\.\.\./gi, strings.checkingService)
    .replace(/Verifying Session\.\.\./gi, strings.verifyingSession)
    .replace(/Starting foreground service\.\.\./gi, strings.startingService)
    .replace(/Stopping foreground service\.\.\./gi, strings.stoppingService)
    .replace(/Foreground service stopped running/gi, `${strings.fail}: ${strings.serviceError}`)
    .replace(/Login Successful but unable to get server mode; Status:/gi, `${strings.loginServerModeError}; Status:`)
    .replace(/Login Successful but unable to get stun url; Status:/gi, `${strings.loginStunError}; Status:`)
    .replace(/Login Successful but unable to get max size; Status:/gi, `${strings.loginMaxSizeError}; Status:`)
    .replace(/Login successful but error generating hash:/gi, `${strings.loginHashError}:`)
    .replace(/Login successful:/gi, `${strings.loginSuccess}:`)
    .replace(/Login failed:/gi, `${strings.loginFailed}:`)
    .replace(/Logout successful:/gi, `${strings.logoutSuccess}:`)
    .replace(/Logout failed:/gi, `${strings.logoutFailed}:`)
    .replace(/Failed to fetch login page:/gi, `${strings.fetchLoginError}:`)
    .replace(/No CSRF token found in login page/gi, strings.csrfMissing)
    .replace(/No Set-Cookie header returned from login page/gi, strings.cookieMissing)
    .replace(/Invalid URL provided/gi, strings.invalidUrl)
    .replace(/Unsupported protocol in URL:/gi, `${strings.unsupportedProtocol}:`)
    .replace(/Error: Request timed out/gi, `${strings.genericError}: ${strings.requestTimedOut}`)
    .replace(/Unknown error:/gi, `${strings.unknownError}:`)
    .replace(/❌ Connection Failed:/g, `❌ ${strings.connectionFailed}:`)
    .replace(/❌ Outbound Error:/g, `❌ ${strings.outboundError}:`)
    .replace(/❌ Inbound Error:/g, `❌ ${strings.inboundError}:`)
    .replace(/❌ Foreground service:/gi, `❌ ${strings.serviceError}:`)
    .replace(/❌ Error:/gi, `❌ ${strings.genericError}:`)
    .replace(/⚠️ Ignored (\d+) incompatible P2P peer\(s\)/g, `⚠️ ${strings.ignoredIncompatible}: $1`)
    .replace(/Peers:/g, `${strings.peers}:`)
    .replace(/Sending:/g, `${strings.sending}:`)
    .replace(/Receiving:/g, `${strings.receiving}:`)
    .replace(/Please wait\.\.\./gi, strings.working);
}"""
    replace_once(i18n, old_function, new_function, "expanded runtime localization")

    replace_once(
        app,
        """        Alert.alert('Error', 'Unknown error: ' + JSON.stringify(e));""",
        """        Alert.alert(
          EXTENDED_TEXT.errorTitle,
          `${EXTENDED_TEXT.unknownError}: ${JSON.stringify(e)}`,
        );""",
        "localized file-download error dialog",
    )


if __name__ == "__main__":
    main()
