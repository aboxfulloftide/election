"""Official Georgia county presidential source configuration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


SOURCE_NAME = "Georgia Secretary of State"
SOURCE_URL = "https://sos.ga.gov/page/historical-elections-results"
RAW_DIR = Path("data/raw/official/georgia")


@dataclass(frozen=True)
class GeorgiaElectionSource:
    year: int
    url: str
    file_name: str
    notes: str


GEORGIA_PRESIDENTIAL_SOURCES = {
    2020: GeorgiaElectionSource(
        year=2020,
        url="https://sos.ga.gov/sites/default/files/2026-04/november_3_2020_-_general_election_recount.zip",
        file_name="november_3_2020_-_general_election_recount.zip",
        notes="Official 2020 general-election recount summary ZIP downloaded manually from the Georgia Secretary of State historical results page.",
    ),
}


def raw_path(source: GeorgiaElectionSource) -> Path:
    return RAW_DIR / source.file_name
