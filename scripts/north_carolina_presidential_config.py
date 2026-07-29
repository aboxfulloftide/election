"""Official North Carolina county presidential source configuration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


SOURCE_NAME = "North Carolina State Board of Elections"
SOURCE_URL = "https://www.ncsbe.gov/results-data/election-results/historical-election-results-data"
RAW_DIR = Path("data/raw/official/north-carolina")


@dataclass(frozen=True)
class NorthCarolinaElectionSource:
    year: int
    election_date: str
    url: str
    file_name: str


NORTH_CAROLINA_PRESIDENTIAL_SOURCES = {
    2020: NorthCarolinaElectionSource(
        year=2020,
        election_date="11/03/2020",
        url="https://s3.amazonaws.com/dl.ncsbe.gov/ENRS/2020_11_03/results_pct_20201103.zip",
        file_name="results_pct_20201103.zip",
    ),
    2024: NorthCarolinaElectionSource(
        year=2024,
        election_date="11/05/2024",
        url="https://s3.amazonaws.com/dl.ncsbe.gov/ENRS/2024_11_05/results_pct_20241105.zip",
        file_name="results_pct_20241105.zip",
    ),
}


def raw_path(source: NorthCarolinaElectionSource) -> Path:
    return RAW_DIR / source.file_name
