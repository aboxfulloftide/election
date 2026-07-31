"""Configuration for Ohio official statewide election summaries."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT_DIR / "public/results"
OUTPUT_PATH = RESULTS_DIR / "ohio-statewide-summary.json"
COUNTY_PRESIDENTIAL_SUMMARY_PATH = RESULTS_DIR / "county-presidential-summary.json"


@dataclass(frozen=True)
class OhioSourceWorkbook:
    year: int
    election_date: str
    election_name: str
    source_url: str
    raw_path: str
    sheets: tuple[str, ...]


OHIO_WORKBOOKS = (
    OhioSourceWorkbook(
        year=2020,
        election_date="2020-11-03",
        election_name="November 3, 2020 General Election",
        source_url="https://publicfiles.ohiosos.gov/election-results/past-elections/2020/General%20Election:%20November%203,%202020/group1/statewideresultsbycounty.xlsx",
        raw_path="data/raw/ohio/ohio_2020_general_statewide_results_by_county.xlsx",
        sheets=("President and Vice President", "U.S. Congress", "Ohio General Assembly"),
    ),
    OhioSourceWorkbook(
        year=2024,
        election_date="2024-11-05",
        election_name="November 5, 2024 General Election",
        source_url="https://publicfiles.ohiosos.gov/election-results/past-elections/2024/General%20Election:%20November%205,%202024/group1/statewide-race-summary.xlsx",
        raw_path="data/raw/ohio/ohio_2024_general_statewide_results_by_county.xlsx",
        sheets=("President and Vice President", "U.S. Congress", "General Assembly"),
    ),
    OhioSourceWorkbook(
        year=2022,
        election_date="2022-11-08",
        election_name="November 8, 2022 General Election",
        source_url="https://publicfiles.ohiosos.gov/election-results/past-elections/2022/General%20Election:%20November%208,%202022/group1/statewide-races-summary.xlsx",
        raw_path="data/raw/ohio/ohio_2022_general_statewide_races_summary.xlsx",
        sheets=("Statewide Offices", "U.S. Congress", "General Assembly"),
    ),
)
