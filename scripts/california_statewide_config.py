"""Official California statewide source configuration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


SOURCE_NAME = "California Secretary of State"
SOURCE_URL = "https://www.sos.ca.gov/elections/prior-elections/statewide-election-results/general-election-nov-5-2024/statement-vote"
RAW_DIR = Path("data/raw/official/california")
OUTPUT_PATH = Path("public/results/california-statewide-summary.json")


@dataclass(frozen=True)
class CaliforniaContestSource:
    year: int
    office: str
    contest_label: str
    url: str
    file_name: str
    district: bool = False


CALIFORNIA_CONTEST_SOURCES = [
    CaliforniaContestSource(
        year=2024,
        office="President",
        contest_label="President",
        url="https://elections.cdn.sos.ca.gov/sov/2024-general/ssov/pres-summary-by-county.xlsx",
        file_name="pres-summary-by-county-2024.xlsx",
    ),
    CaliforniaContestSource(
        year=2024,
        office="U.S. Senate",
        contest_label="U.S. Senate (Full Term)",
        url="https://elections.cdn.sos.ca.gov/sov/2024-general/ssov/us-senate-summary-by-county-ft.xlsx",
        file_name="us-senate-summary-by-county-ft-2024.xlsx",
    ),
    CaliforniaContestSource(
        year=2024,
        office="U.S. Senate",
        contest_label="U.S. Senate (Partial/Unexpired Term)",
        url="https://elections.cdn.sos.ca.gov/sov/2024-general/ssov/us-senate-summary-by-county-pt.xlsx",
        file_name="us-senate-summary-by-county-pt-2024.xlsx",
    ),
]


CALIFORNIA_DISTRICT_CONTEST_SOURCES = [
    CaliforniaContestSource(
        year=2024,
        office="U.S. House",
        contest_label="U.S. House",
        url="https://elections.cdn.sos.ca.gov/sov/2024-general/sov/25-us-rep-congress.xlsx",
        file_name="us-house-by-district-2024.xlsx",
        district=True,
    ),
    CaliforniaContestSource(
        year=2024,
        office="State Senate",
        contest_label="State Senate",
        url="https://elections.cdn.sos.ca.gov/sov/2024-general/sov/37-state-senator.xlsx",
        file_name="state-senate-by-district-2024.xlsx",
        district=True,
    ),
    CaliforniaContestSource(
        year=2024,
        office="State Assembly",
        contest_label="State Assembly",
        url="https://elections.cdn.sos.ca.gov/sov/2024-general/sov/42-state-assembly.xlsx",
        file_name="state-assembly-by-district-2024.xlsx",
        district=True,
    ),
]


ALL_CALIFORNIA_CONTEST_SOURCES = CALIFORNIA_CONTEST_SOURCES + CALIFORNIA_DISTRICT_CONTEST_SOURCES


def raw_path(source: CaliforniaContestSource) -> Path:
    return RAW_DIR / source.file_name
