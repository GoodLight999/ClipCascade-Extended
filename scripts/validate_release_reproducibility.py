#!/usr/bin/env python3
"""Validate deterministic resources for the signed Extended Android variant."""
from __future__ import annotations

import argparse
import re
import zipfile
from pathlib import Path


FIXED_DEV_SERVER_IP = "127.0.0.1"
RESOURCE_MARKER = (
    'resValue "string", "react_native_dev_server_ip", '
    f'"{FIXED_DEV_SERVER_IP}"'
)
PRIVATE_IPV4 = re.compile(
    rb"(?<![0-9])(?:"
    rb"10(?:\.[0-9]{1,3}){3}|"
    rb"192\.168(?:\.[0-9]{1,3}){2}|"
    rb"172\.(?:1[6-9]|2[0-9]|3[01])(?:\.[0-9]{1,3}){2}"
    rb")(?![0-9])"
)


def matching_brace(text: str, marker: str) -> tuple[int, int]:
    start = text.find(marker)
    if start < 0:
        raise RuntimeError(f"build block not found: {marker!r}")
    opening = text.find("{", start)
    if opening < 0:
        raise RuntimeError(f"opening brace not found: {marker!r}")
    depth = 0
    for index in range(opening, len(text)):
        if text[index] == "{":
            depth += 1
        elif text[index] == "}":
            depth -= 1
            if depth == 0:
                return opening, index
    raise RuntimeError(f"unmatched build block: {marker!r}")


def validate_source(root: Path) -> None:
    path = root / "android/app/build.gradle"
    text = path.read_text(encoding="utf-8")
    build_opening, build_closing = matching_brace(text, "    buildTypes {")
    build_types = text[build_opening : build_closing + 1]
    extended_opening, extended_closing = matching_brace(build_types, "        extended {")
    extended = build_types[extended_opening : extended_closing + 1]
    if extended.count(RESOURCE_MARKER) != 1:
        raise RuntimeError(
            "Extended build type must contain exactly one deterministic "
            f"dev-server resource: {RESOURCE_MARKER!r}"
        )
    if text.count(RESOURCE_MARKER) != 1:
        raise RuntimeError("deterministic dev-server resource escaped Extended scope")
    print("Extended release resource source is deterministic: OK")


def validate_apk(apk: Path) -> None:
    with zipfile.ZipFile(apk) as archive:
        resources = archive.read("resources.arsc")
    if FIXED_DEV_SERVER_IP.encode("ascii") not in resources:
        raise RuntimeError("fixed release dev-server IP missing from resources.arsc")
    private_matches = sorted({match.group().decode("ascii") for match in PRIVATE_IPV4.finditer(resources)})
    if private_matches:
        raise RuntimeError(
            "build-host private IP leaked into resources.arsc: " + ", ".join(private_matches)
        )
    print("Packaged release resources contain no build-host private IP: OK")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("target", type=Path)
    parser.add_argument("--apk", action="store_true")
    args = parser.parse_args()
    target = args.target.resolve()
    if args.apk:
        validate_apk(target)
    else:
        validate_source(target)


if __name__ == "__main__":
    main()
