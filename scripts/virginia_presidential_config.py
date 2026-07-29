"""Official Virginia county/locality presidential source configuration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


SOURCE_NAME = "Virginia Department of Elections"
SOURCE_URL = "https://historical.elections.virginia.gov/"
RAW_DIR = Path("data/raw/official/virginia")


@dataclass(frozen=True)
class VirginiaElectionSource:
    year: int
    contest_url: str
    download_url: str
    file_name: str


VIRGINIA_PRESIDENTIAL_SOURCES = {
    2020: VirginiaElectionSource(
        year=2020,
        contest_url="https://historical.elections.virginia.gov/contest/144567",
        download_url="https://va2.elstats3.civera.com/api/download_contest/144567_table.csv?split_party=false",
        file_name="va_2020_president.csv",
    ),
    2024: VirginiaElectionSource(
        year=2024,
        contest_url="https://historical.elections.virginia.gov/contest/161256",
        download_url="https://va2.elstats3.civera.com/api/download_contest/161256_table.csv?split_party=false",
        file_name="va_2024_president.csv",
    ),
}


def raw_path(source: VirginiaElectionSource) -> Path:
    return RAW_DIR / source.file_name
