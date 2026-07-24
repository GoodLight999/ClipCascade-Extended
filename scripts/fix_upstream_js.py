#!/usr/bin/env python3
"""Apply guarded correctness repairs to the pinned upstream JavaScript."""
from __future__ import annotations

import argparse
from pathlib import Path

from upstream_js_patches import apply


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("destination", type=Path)
    apply(parser.parse_args().destination.resolve())


if __name__ == "__main__":
    main()
