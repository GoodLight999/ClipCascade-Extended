#!/usr/bin/env python3
"""Constrain React Native's injected Sonatype snapshot repository.

React Native 0.80.x may classify its bundled Hermes coordinate as a snapshot and
add Sonatype's snapshot repository to every auto-linked project. The upstream
filter is broad enough that unrelated stable dependencies (Guava, Kotlin, etc.)
can also be queried there. Keep the repository available only for React Native
and Hermes artifacts.
"""
from __future__ import annotations

import argparse
from pathlib import Path


SNAPSHOT_URL = "https://central.sonatype.com/repository/maven-snapshots/"
REQUIRED_GROUPS = (
    'includeGroup("com.facebook.react")',
    'includeGroup("com.facebook.hermes")',
)


def find_matching_brace(text: str, opening: int) -> int:
    depth = 0
    in_string = False
    escaped = False
    quote = ""
    for index in range(opening, len(text)):
        char = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                in_string = False
            continue
        if char in ('"', "'"):
            in_string = True
            quote = char
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return index
    raise RuntimeError("React Native snapshot repository block has unmatched braces")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mobile_root", type=Path)
    args = parser.parse_args()
    root = args.mobile_root.resolve()
    path = (
        root
        / "node_modules/@react-native/gradle-plugin/react-native-gradle-plugin/src/main/kotlin"
        / "com/facebook/react/utils/DependencyUtils.kt"
    )
    if not path.is_file():
        raise RuntimeError(f"React Native Gradle source not found: {path}")

    text = path.read_text(encoding="utf-8")
    if text.count(SNAPSHOT_URL) != 1:
        raise RuntimeError(
            "React Native snapshot repository URL drifted: "
            f"expected 1, found {text.count(SNAPSHOT_URL)}"
        )

    url_index = text.index(SNAPSHOT_URL)
    line_start = text.rfind("\n", 0, url_index) + 1
    call_start = text.rfind("mavenRepoFromUrl", line_start, url_index)
    if call_start < 0:
        raise RuntimeError("Snapshot URL is not inside mavenRepoFromUrl on its line")
    opening = text.find("{", url_index)
    if opening < 0:
        raise RuntimeError("Snapshot repository block opening brace not found")
    closing = find_matching_brace(text, opening)
    block = text[call_start : closing + 1]
    if "repo.content" not in block:
        raise RuntimeError("Snapshot repository no longer contains a content filter")

    if all(required in block for required in REQUIRED_GROUPS):
        print(f"React Native snapshot repository already scoped in {path}")
        return

    indent = text[line_start:call_start]
    replacement = f'''mavenRepoFromUrl("{SNAPSHOT_URL}") {{ repo ->
{indent}  repo.content {{
{indent}    it.includeGroup("com.facebook.react")
{indent}    it.includeGroup("com.facebook.hermes")
{indent}  }}
{indent}}}'''
    patched = text[:call_start] + replacement + text[closing + 1 :]

    for required in REQUIRED_GROUPS:
        if patched.count(required) != 1:
            raise RuntimeError(f"Missing or duplicated repository filter: {required}")
    path.write_text(patched, encoding="utf-8")
    print(f"Scoped React Native snapshot repository in {path}")


if __name__ == "__main__":
    main()
