#!/usr/bin/env python3
"""Download official North Carolina presidential results ZIPs."""

from __future__ import annotations

import sys
import urllib.request

from election_db import ROOT_DIR
from north_carolina_presidential_config import NORTH_CAROLINA_PRESIDENTIAL_SOURCES, raw_path


def download(url: str, path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": "election-night-map/0.1"})
    with urllib.request.urlopen(request, timeout=180) as response:
        path.write_bytes(response.read())


def main() -> int:
    for source in NORTH_CAROLINA_PRESIDENTIAL_SOURCES.values():
        path = ROOT_DIR / raw_path(source)
        print(f"Downloading North Carolina {source.year} official results...")
        download(source.url, path)
    print("Downloaded official North Carolina presidential source files.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
