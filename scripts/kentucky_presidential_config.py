"""Official Kentucky county presidential source configuration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


SOURCE_NAME = "Kentucky State Board of Elections"
SOURCE_URL = "https://elect.ky.gov/results/2020-2029/Pages/2020.aspx"
RAW_DIR = Path("data/raw/official/kentucky")


@dataclass(frozen=True)
class KentuckyElectionSource:
    year: int
    url: str
    file_name: str


KENTUCKY_PRESIDENTIAL_SOURCES = {
    2020: KentuckyElectionSource(
        year=2020,
        url="https://elect.ky.gov/results/2020-2029/Documents/2020%20General%20Election%20Results.pdf",
        file_name="2020_general_election_results.pdf",
    ),
}


def raw_path(source: KentuckyElectionSource) -> Path:
    return RAW_DIR / source.file_name
