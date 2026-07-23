#!/usr/bin/env python3
"""Apply guarded post-integration fixes to the durable outbound queue."""
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
        """          await setDataInAsyncStorage(
            'outbound_queue_status',
            JSON.stringify({...snapshot, state}),
          );""",
        """          await setDataInAsyncStorage(
            'outbound_queue_status',
            {...snapshot, state},
          );""",
        "store queue diagnostics as an object",
    )
    replace_once(
        service,
        """        await updateOutboundQueueStatus('service-started');""",
        """        await updateOutboundQueueStatus('service-started');
        await flushOutboundQueue();""",
        "flush after transport function initialization",
    )


if __name__ == "__main__":
    main()
