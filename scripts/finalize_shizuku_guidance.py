#!/usr/bin/env python3
"""Add a click-driven Shizuku open/install step before one-time setup."""
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

    native = root / "android/app/src/main/java/com/clipcascade/NativeBridgeModule.kt"
    replace_once(
        native,
        '''    @ReactMethod
    fun getShizukuStatus(promise: Promise) {''',
        '''    @ReactMethod
    fun openOrGetShizuku(promise: Promise) {
        try {
            val packageName = "moe.shizuku.privileged.api"
            val launchIntent = reactApplicationContext.packageManager
                .getLaunchIntentForPackage(packageName)
            val intent = launchIntent ?: Intent(
                Intent.ACTION_VIEW,
                Uri.parse("https://github.com/thedjchi/Shizuku/releases")
            )
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            reactApplicationContext.startActivity(intent)
            promise.resolve(launchIntent != null)
        } catch (error: Exception) {
            promise.reject("SHIZUKU_OPEN_ERROR", "Unable to open or locate Shizuku", error)
        }
    }

    @ReactMethod
    fun getShizukuStatus(promise: Promise) {''',
        "Shizuku open/install native method",
    )

    app = root / "App.js"
    for old, new, label in (
        (
            "      shizuku: '3. Shizukuで一回だけ権限設定',",
            """      shizukuOpen: '3. Shizukuを開く／入手',
      shizuku: '4. Shizukuで一回だけ権限設定',
      shizukuGuide: 'Shizukuを導入して起動してください。未導入なら推奨フォークのリリース画面を開きます。起動後、この画面へ戻って一回だけ権限設定を押してください。',""",
            "Japanese Shizuku guidance",
        ),
        (
            "      shizuku: '3. 使用 Shizuku 一次性授权',",
            """      shizukuOpen: '3. 打开／获取 Shizuku',
      shizuku: '4. 使用 Shizuku 一次性授权',
      shizukuGuide: '请安装并启动 Shizuku。若尚未安装，将打开推荐分支的发布页面。启动后返回此处并点击一次性授权。',""",
            "Chinese Shizuku guidance",
        ),
        (
            "    shizuku: '3. One-time Shizuku permission setup',",
            """    shizukuOpen: '3. Open / get Shizuku',
    shizuku: '4. One-time Shizuku permission setup',
    shizukuGuide: 'Install and start Shizuku. If it is not installed, the recommended fork releases page opens. Return here and run the one-time setup.',""",
            "English Shizuku guidance",
        ),
    ):
        replace_once(app, old, new, label)

    shizuku_button = '''              <TouchableOpacity
                style={[styles.loginButton, { backgroundColor: '#4a148c' }]}
                onPress={async () => {
                  try {
                    await NativeBridgeModule.openOrGetShizuku();
                    Alert.alert('Shizuku', EXTENDED_SETUP_TEXT.shizukuGuide);
                  } catch (error) {
                    Alert.alert(
                      EXTENDED_SETUP_TEXT.setupFailed,
                      String(error),
                    );
                  }
                }}
              >
                <Text style={styles.loginButtonText}>
                  {EXTENDED_SETUP_TEXT.shizukuOpen}
                </Text>
              </TouchableOpacity>
'''
    marker = '''              <TouchableOpacity
                style={[styles.loginButton, { backgroundColor: '#4a148c' }]}
                onPress={async () => {
                  try {
                    let status = JSON.parse(
                      await NativeBridgeModule.getShizukuStatus(),
                    );'''
    replace_once(
        app,
        marker,
        shizuku_button + marker,
        "Shizuku open/install setup button",
    )


if __name__ == "__main__":
    main()
