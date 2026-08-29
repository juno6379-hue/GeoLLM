"""Normalize a UTF-16LE-wrapped PostgreSQL custom dump without changing its source."""

from __future__ import annotations

import argparse
from pathlib import Path


def normalize(source: Path, target: Path, chunk_size: int = 8 * 1024 * 1024) -> None:
    with source.open("rb") as src, target.open("wb") as dst:
        prefix = src.read(2)
        if prefix != b"\xff\xfe":
            raise ValueError("Source is not UTF-16LE wrapped; refusing to rewrite it")
        while chunk := src.read(chunk_size):
            # The file contains one original dump byte in each UTF-16LE code unit.
            dst.write(chunk[0::2])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("target", type=Path)
    args = parser.parse_args()
    args.target.parent.mkdir(parents=True, exist_ok=True)
    normalize(args.source, args.target)
    print(f"normalized={args.target} bytes={args.target.stat().st_size}")
