"""Official Georgia statewide and district contest source configuration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


SOURCE_NAME = "Georgia Secretary of State"
SOURCE_URL = "https://sos.ga.gov/page/historical-elections-results"
RAW_DIR = Path("data/raw/official/georgia")


@dataclass(frozen=True)
class GeorgiaContestSource:
    year: int
    url: str
    file_name: str


GEORGIA_CONTEST_SOURCES = {
    2020: GeorgiaContestSource(
        year=2020,
        url="https://sos.ga.gov/sites/default/files/2026-04/november_3_2020_-_general_election.zip",
        file_name="november_3_2020_-_general_election.zip",
    ),
    2022: GeorgiaContestSource(
        year=2022,
        url="https://sos.ga.gov/sites/default/files/2026-05/November%208%2C%202022%20-%20General-Special%20Election.zip",
        file_name="november_8_2022_-_general_special_election.zip",
    ),
}


def raw_path(source: GeorgiaContestSource) -> Path:
    return RAW_DIR / source.file_name
