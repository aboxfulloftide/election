#!/usr/bin/env python3
"""Download official Pennsylvania general-election bulk return files."""

from __future__ import annotations

import sys
from urllib.request import Request, urlopen

from pennsylvania_config import PENNSYLVANIA_GENERAL_SOURCES, readme_path, results_path


def download(url: str, path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    request = Request(url, headers={"User-Agent": "Mozilla/5.0 election-night-map/0.1"})
    with urlopen(request, timeout=180) as response:
        path.write_bytes(response.read())


def main() -> int:
    for source in PENNSYLVANIA_GENERAL_SOURCES:
        print(f"Downloading Pennsylvania {source.year} general readme...")
        download(source.readme_url, readme_path(source))
        print(f"Downloading Pennsylvania {source.year} general precinct returns...")
        download(source.results_url, results_path(source))
    print("Downloaded official Pennsylvania general-election source files.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
