#!/usr/bin/env python3
"""Download supplemental county presidential returns used to fill MIT gaps."""

from __future__ import annotations

import sys
import urllib.request
from pathlib import Path

from election_db import ROOT_DIR


SOURCE_NAME = "tonmcg/US_County_Level_Election_Results_08-24"
SOURCE_URL = "https://github.com/tonmcg/US_County_Level_Election_Results_08-24"
RAW_DIR = Path("data/raw/supplement/tonmcg")
YEARS = (2020, 2024)


def raw_url(year: int) -> str:
    return f"https://raw.githubusercontent.com/tonmcg/US_County_Level_Election_Results_08-24/master/{year}_US_County_Level_Presidential_Results.csv"


def raw_path(year: int) -> Path:
    return ROOT_DIR / RAW_DIR / f"{year}_US_County_Level_Presidential_Results.csv"


def download(url: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": "election-night-map/0.1"})
    with urllib.request.urlopen(request, timeout=120) as response:
        path.write_bytes(response.read())


def main() -> int:
    for year in YEARS:
        path = raw_path(year)
        print(f"Downloading supplemental {year} county presidential CSV...")
        download(raw_url(year), path)
    print(f"Downloaded supplemental county presidential files to {RAW_DIR}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
