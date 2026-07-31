#!/usr/bin/env python3
"""Download Kentucky certified statewide result PDFs with the official page referrer."""

from __future__ import annotations

import argparse
import urllib.request
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT_DIR / "data/raw/official/kentucky"
SOURCES = {
    2022: {
        "url": "https://elect.ky.gov/results/2020-2029/Documents/1.17.2023%20Certified%20General%20Election%20Results.pdf",
        "filename": "2022_certified_general_election_results.pdf",
        "page": "https://elect.ky.gov/results/2020-2029/Pages/2022.aspx",
    }
}


def download(year: int) -> Path:
    source = SOURCES[year]
    destination = RAW_DIR / source["filename"]
    if destination.exists() and destination.stat().st_size > 1000:
        return destination
    request = urllib.request.Request(
        source["url"],
        headers={
            "User-Agent": "Mozilla/5.0 election-night-map/0.1",
            "Referer": source["page"],
        },
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        data = response.read()
    if not data.startswith(b"%PDF"):
        raise RuntimeError(f"Unexpected response for Kentucky {year} certified results")
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(data)
    return destination


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, choices=sorted(SOURCES), action="append")
    args = parser.parse_args()
    for year in args.year or sorted(SOURCES):
        path = download(year)
        print(f"Kentucky {year} certified source staged: {path.relative_to(ROOT_DIR)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
