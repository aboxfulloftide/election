"""Configuration for Texas official historical election summaries."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT_DIR / "public/results"
OUTPUT_PATH = RESULTS_DIR / "texas-statewide-summary.json"
COUNTY_PRESIDENTIAL_SUMMARY_PATH = RESULTS_DIR / "county-presidential-summary.json"
SOURCE_PAGE_URL = "https://www.sos.state.tx.us/elections/historical/elections-results-archive.shtml"
HISTORICAL_BASE_URL = "https://elections.sos.state.tx.us"


@dataclass(frozen=True)
class TexasHistoricalElection:
    year: int
    election_id: int
    election_date: str
    election_name: str

    @property
    def race_select_url(self) -> str:
        return f"{HISTORICAL_BASE_URL}/elchist{self.election_id}_raceselect.htm"

    def race_url(self, race_id: int) -> str:
        return f"{HISTORICAL_BASE_URL}/elchist{self.election_id}_race{race_id}.htm"


@dataclass(frozen=True)
class TexasCanvassPdfElection:
    year: int
    election_date: str
    election_name: str
    source_url: str
    raw_path: str


TEXAS_HISTORICAL_ELECTIONS = [
    TexasHistoricalElection(
        year=2018,
        election_id=331,
        election_date="2018-11-06",
        election_name="2018 General Election",
    )
]


TEXAS_CANVASS_PDF_ELECTIONS = [
    TexasCanvassPdfElection(
        year=2020,
        election_date="2020-11-03",
        election_name="2020 November 3rd General Election",
        source_url="https://results.texas-election.com/reports",
        raw_path="data/raw/texas/texas_2020_general_results_by_county.pdf",
    ),
    TexasCanvassPdfElection(
        year=2022,
        election_date="2022-11-08",
        election_name="2022 November 8th General Election",
        source_url="https://results.texas-election.com/reports",
        raw_path="data/raw/texas/texas_2022_general_results_by_county.pdf",
    ),
    TexasCanvassPdfElection(
        year=2024,
        election_date="2024-11-05",
        election_name="2024 November 5th General Election",
        source_url="https://results.texas-election.com/reports",
        raw_path="data/raw/texas/texas_2024_general_results_by_county.pdf",
    ),
]
