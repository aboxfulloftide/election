#!/usr/bin/env python3
"""Download official Florida precinct-level election files."""

from __future__ import annotations

import sys
import urllib.request
from pathlib import Path

from election_db import ROOT_DIR


FLORIDA_2022_GENERAL_URL = "https://fldoswebumbracoprod.blob.core.windows.net/media/706300/2022-gen-outputofficial.zip"
FLORIDA_2022_DEFINITIONS_URL = "https://fldoswebumbracoprod.blob.core.windows.net/media/709209/final-precinct-level-elections-data-definitions-and-field-codes_20250624.pdf"
OUTPUT_DIR = ROOT_DIR / "data/raw/florida/2022-general"
ZIP_PATH = OUTPUT_DIR / "2022-gen-outputofficial.zip"
DEFINITIONS_PATH = OUTPUT_DIR / "precinct-level-data-definitions-20250624.pdf"


def download(url: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": "election-night-map/0.1"})
    with urllib.request.urlopen(request, timeout=180) as response:
        with path.open("wb") as output:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                output.write(chunk)


def main() -> int:
    print("Downloading Florida 2022 general precinct-level ZIP...")
    download(FLORIDA_2022_GENERAL_URL, ZIP_PATH)
    print("Downloading Florida precinct-level data definitions...")
    download(FLORIDA_2022_DEFINITIONS_URL, DEFINITIONS_PATH)
    print(f"Downloaded Florida raw files to {OUTPUT_DIR.relative_to(ROOT_DIR)}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

