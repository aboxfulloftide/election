"""Official Wisconsin county presidential source configuration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


SOURCE_NAME = "Wisconsin Elections Commission"
SOURCE_URL = "https://elections.wi.gov/"
RAW_DIR = Path("data/raw/official/wisconsin")


@dataclass(frozen=True)
class WisconsinElectionSource:
    year: int
    url: str
    file_name: str


WISCONSIN_PRESIDENTIAL_SOURCES = {
    2024: WisconsinElectionSource(
        year=2024,
        url="https://elections.wi.gov/sites/default/files/documents/County%20by%20County%20Report_POTUS.pdf",
        file_name="county_by_county_report_potus_2024.pdf",
    ),
}


def raw_path(source: WisconsinElectionSource) -> Path:
    return RAW_DIR / source.file_name
