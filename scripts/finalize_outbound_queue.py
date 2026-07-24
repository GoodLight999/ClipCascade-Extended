#!/usr/bin/env python3
"""Integrate the bounded durable outbound queue."""
from __future__ import annotations

import argparse
from pathlib import Path

from outbound_queue_integration import apply


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("destination", type=Path)
    apply(parser.parse_args().destination.resolve())


if __name__ == "__main__":
    main()
