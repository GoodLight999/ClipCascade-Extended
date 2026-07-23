#!/usr/bin/env python3
"""Harden boot/update and visible-capture runtime restart wiring."""
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

    replace_once(
        root / "android/app/src/main/AndroidManifest.xml",
        '''          <action android:name="android.intent.action.BOOT_COMPLETED" />''',
        '''          <action android:name="android.intent.action.BOOT_COMPLETED" />
          <action android:name="android.intent.action.MY_PACKAGE_REPLACED" />''',
        "restart receiver actions",
    )

    replace_once(
        root / "HeadlessTask.js",
        '''    if (data && data['event'] === 'BOOT_COMPLETED') {
      const relaunch_on_boot = await getDataFromAsyncStorage(
        'relaunch_on_boot',
      );
      if (relaunch_on_boot !== null && relaunch_on_boot === 'true') {
        if ((await enableForegroundService()) === 'true') {
          await setDataInAsyncStorage('wsStatusMessage', '');
          const result = await StartForegroundService();
          if (result[0] === false) {
            throw result[1];
          }
        }
      }
    }''',
        '''    const event = data?.event;
    const restartFromBoot =
      event === 'android.intent.action.BOOT_COMPLETED' ||
      event === 'android.intent.action.MY_PACKAGE_REPLACED';
    const restartFromVisibleCapture =
      event === 'com.clipcascade.CAPTURE_RECOVERY';

    let restartAllowed = restartFromVisibleCapture;
    if (restartFromBoot) {
      const relaunchOnBoot = await getDataFromAsyncStorage('relaunch_on_boot');
      restartAllowed = relaunchOnBoot === 'true';
    }

    if (restartAllowed && (await enableForegroundService()) === 'true') {
      await setDataInAsyncStorage('wsStatusMessage', '');
      await setDataInAsyncStorage(
        'foreground_service_recovery_status',
        `headless-running:${event}`,
      );
      const result = await StartForegroundService();
      if (result[0] === false) {
        throw result[1];
      }
      await setDataInAsyncStorage(
        'foreground_service_recovery_status',
        `foreground-start-requested:${event}`,
      );
    }''',
        "boot/update/capture headless restart events",
    )

    replace_once(
        root / "HeadlessTask.js",
        '''  } catch (e) {
    console.error('Error in Headless JS Task:', e);
  }''',
        '''  } catch (e) {
    await setDataInAsyncStorage(
      'foreground_service_recovery_status',
      `headless-error:${String(e?.stack || e)}`.slice(0, 500),
    );
    console.error('Error in Headless JS Task:', e);
  }''',
        "headless restart failure evidence",
    )


if __name__ == "__main__":
    main()
