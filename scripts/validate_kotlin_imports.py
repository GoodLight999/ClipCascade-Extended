#!/usr/bin/env python3
"""Reject duplicate or ambiguous Kotlin imports before Gradle compilation."""
from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path


def exposed_name(import_line: str) -> str | None:
    target = import_line.removeprefix("import ").strip()
    if not target or target.endswith(".*"):
        return None
    if " as " in target:
        return target.rsplit(" as ", 1)[1].strip()
    return target.rsplit(".", 1)[-1]


def validate(path: Path) -> list[str]:
    imports = [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip().startswith("import ")
    ]
    errors: list[str] = []

    seen: set[str] = set()
    for item in imports:
        if item in seen:
            errors.append(f"duplicate import {item!r}")
        seen.add(item)

    by_name: dict[str, set[str]] = defaultdict(set)
    for item in imports:
        name = exposed_name(item)
        if name is not None:
            by_name[name].add(item)
    for name, items in sorted(by_name.items()):
        if len(items) > 1:
            errors.append(
                f"ambiguous imported name {name!r}: {', '.join(sorted(items))}"
            )
    return errors


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    root = parser.parse_args().root.resolve()
    kotlin_root = root / "android/app/src/main/java"
    if not kotlin_root.is_dir():
        raise RuntimeError(f"Kotlin source tree is missing: {kotlin_root}")

    failures: list[str] = []
    files = sorted(kotlin_root.rglob("*.kt"))
    for path in files:
        for error in validate(path):
            failures.append(f"{path.relative_to(root)}: {error}")

    if failures:
        raise RuntimeError("Kotlin import validation failed:\n" + "\n".join(failures))
    print(f"Kotlin imports validated: {len(files)} files, no duplicate/ambiguous names")


if __name__ == "__main__":
    main()
