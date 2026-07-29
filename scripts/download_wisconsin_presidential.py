#!/usr/bin/env python3
"""Download official Wisconsin presidential results PDFs."""

from __future__ import annotations

import sys
import urllib.request
from pathlib import Path

from election_db import ROOT_DIR
from wisconsin_presidential_config import WISCONSIN_PRESIDENTIAL_SOURCES, raw_path


def download(url: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 election-night-map/0.1"})
    with urllib.request.urlopen(request, timeout=180) as response:
        path.write_bytes(response.read())


def main() -> int:
    for source in WISCONSIN_PRESIDENTIAL_SOURCES.values():
        path = ROOT_DIR / raw_path(source)
        print(f"Downloading Wisconsin {source.year} official results...")
        download(source.url, path)
    print("Downloaded official Wisconsin presidential source files.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
