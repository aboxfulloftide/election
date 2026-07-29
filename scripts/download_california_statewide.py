#!/usr/bin/env python3
"""Download official California statewide Statement of Vote XLSX files."""

from __future__ import annotations

import sys
import urllib.request
from pathlib import Path

from california_statewide_config import ALL_CALIFORNIA_CONTEST_SOURCES, raw_path
from election_db import ROOT_DIR


def download(url: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 election-night-map/0.1"})
    with urllib.request.urlopen(request, timeout=180) as response:
        path.write_bytes(response.read())


def main() -> int:
    for source in ALL_CALIFORNIA_CONTEST_SOURCES:
        path = ROOT_DIR / raw_path(source)
        print(f"Downloading California {source.year} {source.contest_label}...")
        download(source.url, path)
    print("Downloaded official California statewide source files.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
