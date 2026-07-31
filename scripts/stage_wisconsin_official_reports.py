#!/usr/bin/env python3
"""Validate browser-staged Wisconsin WEC county-by-county report PDFs."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

from election_db import ROOT_DIR


RAW_DIR = ROOT_DIR / "data/raw/official/wisconsin"
REQUIRED = {
    "2020": "Canvass Results for 2020 General Election.pdf",
    "2022": "Canvass Results for 2022 General Election.pdf",
    "2024": "County by County Report 2024 General Election.pdf",
}


def stage(year: str, source: Path | None) -> None:
    destination = RAW_DIR / f"wisconsin_{year}_general_official_results.pdf"
    if source is None:
        source = ROOT_DIR / REQUIRED[year]
    if not source.exists():
        raise RuntimeError(f"Missing browser-staged Wisconsin {year} report: {source}. Obtain the official WEC report named {REQUIRED[year]} from https://elections.wi.gov/ and place it in the project root.")
    if source.stat().st_size < 1000:
        raise RuntimeError(f"Wisconsin {year} source is unexpectedly small: {source}")
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)
    print(f"Staged {destination.relative_to(ROOT_DIR)} from {source.name}.")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", choices=sorted(REQUIRED), action="append")
    parser.add_argument("--file", type=Path, action="append")
    args = parser.parse_args()
    years = args.year or sorted(REQUIRED)
    files = args.file or []
    if files and len(files) != len(years):
        raise SystemExit("--file must be supplied once per --year")
    for index, year in enumerate(years):
        stage(year, files[index] if files else None)
    return 0


if __name__ == "__main__":
    sys.exit(main())
