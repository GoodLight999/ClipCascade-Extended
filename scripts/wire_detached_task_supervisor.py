"""Wire generated foreground callbacks to the canonical tested supervisor."""
from __future__ import annotations

from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one marker, found {count}")
    return text.replace(old, new, 1)


def apply(root: Path) -> None:
    path = root / "StartForegroundService.js"
    text = path.read_text(encoding="utf-8")

    text = replace_once(
        text,
        "import { sendP2PFragment } from './P2PChannelSender';",
        """import { sendP2PFragment } from './P2PChannelSender';
import { createDetachedTaskSupervisor } from './DetachedTaskSupervisor';""",
        "canonical detached supervisor import",
    )

    text = replace_once(
        text,
        """function runDetached(scope, task) {
  Promise.resolve()
    .then(task)
    .catch(error => {
      const detail = `${scope}:${String(error?.stack || error)}`.slice(0, 4000);
      return Promise.all([
        setDataInAsyncStorage('foreground_service_detached_error', detail),
        setDataInAsyncStorage(
          'foreground_service_detached_error_at',
          String(Date.now()),
        ),
      ]).catch(() => undefined);
    });
}""",
        """const runDetached = createDetachedTaskSupervisor(async (scope, error) => {
  const detail = `${scope}:${String(error?.stack || error)}`.slice(0, 4000);
  await Promise.all([
    setDataInAsyncStorage('foreground_service_detached_error', detail),
    setDataInAsyncStorage(
      'foreground_service_detached_error_at',
      String(Date.now()),
    ),
  ]);
});""",
        "canonical detached supervisor instance",
    )

    path.write_text(text, encoding="utf-8")
