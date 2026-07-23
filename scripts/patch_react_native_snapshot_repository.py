#!/usr/bin/env python3
"""Constrain React Native's injected Sonatype snapshot repository.

React Native 0.80.x may classify its bundled Hermes coordinate as a snapshot and
add Sonatype's snapshot repository to every auto-linked project. Upstream's
filter excludes only org.webkit, so unrelated stable dependencies (Guava,
Kotlin, etc.) are also queried there and can make builds fail when the snapshot
service is slow. Keep the repository for the two React publishing groups only.
"""
from __future__ import annotations

import argparse
from pathlib import Path


OLD = '''          mavenRepoFromUrl("https://central.sonatype.com/repository/maven-snapshots/") { repo ->
            repo.content { it.excludeGroup("org.webkit") }
          }'''
NEW = '''          mavenRepoFromUrl("https://central.sonatype.com/repository/maven-snapshots/") { repo ->
            repo.content {
              it.includeGroup("com.facebook.react")
              it.includeGroup("com.facebook.hermes")
            }
          }'''


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
    count = text.count(OLD)
    if count != 1:
        raise RuntimeError(
            f"React Native snapshot repository marker drifted: expected 1, found {count}"
        )
    path.write_text(text.replace(OLD, NEW, 1), encoding="utf-8")

    patched = path.read_text(encoding="utf-8")
    for required in (
        'includeGroup("com.facebook.react")',
        'includeGroup("com.facebook.hermes")',
    ):
        if required not in patched:
            raise RuntimeError(f"Missing repository filter after patch: {required}")
    print(f"Scoped React Native snapshot repository in {path}")


if __name__ == "__main__":
    main()
