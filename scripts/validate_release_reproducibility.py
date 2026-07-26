#!/usr/bin/env python3
"""Validate deterministic resources and signing metadata for Extended."""
from __future__ import annotations

import argparse
import re
import struct
import zipfile
from pathlib import Path


FIXED_DEV_SERVER_IP = "127.0.0.1"
RESOURCE_MARKER = (
    'resValue "string", "react_native_dev_server_ip", '
    f'"{FIXED_DEV_SERVER_IP}"'
)
DEPENDENCY_INFO_BLOCK_ID = 0x504B4453
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

    android_opening, android_closing = matching_brace(text, "android {")
    android = text[android_opening : android_closing + 1]
    dependency_opening, dependency_closing = matching_brace(android, "    dependenciesInfo {")
    dependency_policy = android[dependency_opening : dependency_closing + 1]
    for marker in ("includeInApk = false", "includeInBundle = false"):
        if dependency_policy.count(marker) != 1 or text.count(marker) != 1:
            raise RuntimeError(f"deterministic dependency policy missing or escaped scope: {marker!r}")

    build_opening, build_closing = matching_brace(android, "    buildTypes {")
    build_types = android[build_opening : build_closing + 1]
    extended_opening, extended_closing = matching_brace(build_types, "        extended {")
    extended = build_types[extended_opening : extended_closing + 1]
    if extended.count(RESOURCE_MARKER) != 1:
        raise RuntimeError(
            "Extended build type must contain exactly one deterministic "
            f"dev-server resource: {RESOURCE_MARKER!r}"
        )
    if text.count(RESOURCE_MARKER) != 1:
        raise RuntimeError("deterministic dev-server resource escaped Extended scope")
    print("Extended release resource and dependency source are deterministic: OK")


def signing_block_ids(apk_bytes: bytes) -> list[int]:
    eocd = apk_bytes.rfind(b"PK\x05\x06")
    if eocd < 0 or eocd + 20 > len(apk_bytes):
        raise RuntimeError("APK ZIP end-of-central-directory record is missing")
    central_directory_offset = struct.unpack_from("<I", apk_bytes, eocd + 16)[0]
    if central_directory_offset < 24:
        raise RuntimeError("APK central-directory offset is invalid")
    if apk_bytes[central_directory_offset - 16 : central_directory_offset] != b"APK Sig Block 42":
        raise RuntimeError("APK Signing Block magic is missing")
    footer_size = struct.unpack_from("<Q", apk_bytes, central_directory_offset - 24)[0]
    block_start = central_directory_offset - (footer_size + 8)
    if block_start < 0:
        raise RuntimeError("APK Signing Block start is invalid")
    header_size = struct.unpack_from("<Q", apk_bytes, block_start)[0]
    if header_size != footer_size:
        raise RuntimeError("APK Signing Block size fields disagree")

    ids: list[int] = []
    position = block_start + 8
    pairs_end = central_directory_offset - 24
    while position < pairs_end:
        if position + 8 > pairs_end:
            raise RuntimeError("truncated APK Signing Block pair length")
        pair_size = struct.unpack_from("<Q", apk_bytes, position)[0]
        position += 8
        if pair_size < 4 or position + pair_size > pairs_end:
            raise RuntimeError("invalid APK Signing Block pair size")
        ids.append(struct.unpack_from("<I", apk_bytes, position)[0])
        position += pair_size
    if position != pairs_end:
        raise RuntimeError("APK Signing Block pairs do not end at the footer")
    return ids


def validate_apk(apk: Path) -> None:
    apk_bytes = apk.read_bytes()
    with zipfile.ZipFile(apk) as archive:
        resources = archive.read("resources.arsc")
    if FIXED_DEV_SERVER_IP.encode("ascii") not in resources:
        raise RuntimeError("fixed release dev-server IP missing from resources.arsc")
    private_matches = sorted({match.group().decode("ascii") for match in PRIVATE_IPV4.finditer(resources)})
    if private_matches:
        raise RuntimeError(
            "build-host private IP leaked into resources.arsc: " + ", ".join(private_matches)
        )
    ids = signing_block_ids(apk_bytes)
    if DEPENDENCY_INFO_BLOCK_ID in ids:
        raise RuntimeError("nondeterministic SDK dependency information remained in APK Signing Block")
    print("Packaged release contains no build-host IP or SDK dependency signing block: OK")


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
