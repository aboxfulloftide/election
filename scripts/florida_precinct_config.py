"""Configuration for official Florida precinct-level general election files."""

from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass
from pathlib import Path

from election_db import ROOT_DIR


SOURCE_NAME = "Florida Division of Elections"
SOURCE_HOMEPAGE = "https://dos.fl.gov/elections/data-statistics/elections-data/precinct-level-election-results/"
DISCOVERY_URL = SOURCE_HOMEPAGE
DEFINITIONS_URL = (
    "https://fldoswebumbracoprod.blob.core.windows.net/media/709209/"
    "final-precinct-level-elections-data-definitions-and-field-codes_20250624.pdf"
)
DEFINITIONS_PATH = ROOT_DIR / "data/raw/florida/precinct-level-data-definitions-20250624.pdf"
DISTRICT_CONTEST_PATTERNS = (
    (re.compile(r"^(U\.S\. Representative|Representative in Congress)$", re.IGNORECASE), "U.S. House"),
    (re.compile(r"^Congress\s+\d+$", re.IGNORECASE), "U.S. House"),
    (re.compile(r"^State Senator$", re.IGNORECASE), "State Senate"),
    (re.compile(r"^Senate\s+\d+$", re.IGNORECASE), "State Senate"),
    (re.compile(r"^State Representative$", re.IGNORECASE), "State House"),
    (re.compile(r"^House\s+\d+$", re.IGNORECASE), "State House"),
)


@dataclass(frozen=True)
class FloridaGeneralElection:
    year: int
    election_date: dt.date
    url: str
    filename: str
    target_contests: dict[str, str]

    @property
    def output_dir(self) -> Path:
        return ROOT_DIR / f"data/raw/florida/{self.year}-general"

    @property
    def zip_path(self) -> Path:
        return self.output_dir / self.filename

    @property
    def election_name(self) -> str:
        return f"{self.year} Florida general election"


FLORIDA_GENERAL_ELECTIONS: dict[int, FloridaGeneralElection] = {
    2012: FloridaGeneralElection(
        year=2012,
        election_date=dt.date(2012, 11, 6),
        url="https://fldoswebumbracoprod.blob.core.windows.net/media/697204/precinctlevelelectionresults2012gen.zip",
        filename="precinctlevelelectionresults2012gen.zip",
        target_contests={
            "President of the United States": "President",
            "United States Senator": "U.S. Senate",
        },
    ),
    2014: FloridaGeneralElection(
        year=2014,
        election_date=dt.date(2014, 11, 4),
        url="https://fldoswebumbracoprod.blob.core.windows.net/media/697201/precinctlevelelectionresults2014gen.zip",
        filename="precinctlevelelectionresults2014gen.zip",
        target_contests={
            "Governor and Lieutenant Governor": "Governor",
            "Governor": "Governor",
            "GOVERNOR AND  LT.GOVERNOR": "Governor",
        },
    ),
    2016: FloridaGeneralElection(
        year=2016,
        election_date=dt.date(2016, 11, 8),
        url="https://fldoswebumbracoprod.blob.core.windows.net/media/697454/precinctlevelelectionresults2016gen.zip",
        filename="precinctlevelelectionresults2016gen.zip",
        target_contests={
            "President of the United States": "President",
            "PRESIDENT OF THE UNITED STATES": "President",
            "United States Senator": "U.S. Senate",
            "UNITED STATES SENATOR": "U.S. Senate",
        },
    ),
    2018: FloridaGeneralElection(
        year=2018,
        election_date=dt.date(2018, 11, 6),
        url="https://fldoswebumbracoprod.blob.core.windows.net/media/700501/precinctlevelelectionresults2018gen.zip",
        filename="precinctlevelelectionresults2018gen.zip",
        target_contests={
            "Governor": "Governor",
            "United States Senator": "U.S. Senate",
        },
    ),
    2020: FloridaGeneralElection(
        year=2020,
        election_date=dt.date(2020, 11, 3),
        url="https://fldoswebumbracoprod.blob.core.windows.net/media/703763/2020-general-election-rev.zip",
        filename="2020-general-election-rev.zip",
        target_contests={
            "President of the United States": "President",
        },
    ),
    2022: FloridaGeneralElection(
        year=2022,
        election_date=dt.date(2022, 11, 8),
        url="https://fldoswebumbracoprod.blob.core.windows.net/media/706300/2022-gen-outputofficial.zip",
        filename="2022-gen-outputofficial.zip",
        target_contests={
            "Governor and Lieutenant Governor": "Governor",
            "United States Senator": "U.S. Senate",
        },
    ),
    2024: FloridaGeneralElection(
        year=2024,
        election_date=dt.date(2024, 11, 5),
        url="https://fldoswebumbracoprod.blob.core.windows.net/media/708761/2024-gen-outputofficial1.zip",
        filename="2024-gen-outputofficial1.zip",
        target_contests={
            "President and Vice President": "President",
            "United States Senator": "U.S. Senate",
        },
    ),
}


def election_for_year(year: int) -> FloridaGeneralElection:
    try:
        return FLORIDA_GENERAL_ELECTIONS[year]
    except KeyError as exc:
        supported = ", ".join(str(value) for value in sorted(FLORIDA_GENERAL_ELECTIONS))
        raise ValueError(f"Unsupported Florida general election year {year}. Supported years: {supported}.") from exc


def selected_elections(year: int | None, all_years: bool) -> list[FloridaGeneralElection]:
    if all_years:
        return [FLORIDA_GENERAL_ELECTIONS[value] for value in sorted(FLORIDA_GENERAL_ELECTIONS)]
    if year is None:
        year = 2022
    return [election_for_year(year)]


def office_for_contest(election: FloridaGeneralElection, contest_name: str) -> str | None:
    exact_office = election.target_contests.get(contest_name)
    if exact_office is not None:
        return exact_office
    for pattern, office_name in DISTRICT_CONTEST_PATTERNS:
        if pattern.fullmatch(contest_name):
            return office_name
    return None


def normalize_district_label(contest_name: str, district_label: str) -> str:
    normalized = re.sub(r"\s+", " ", district_label.strip())
    if not normalized:
        contest_match = re.fullmatch(r"(?:Congress|House|Senate)\s+(\d+)", contest_name, flags=re.IGNORECASE)
        if contest_match:
            return f"District {int(contest_match.group(1))}"
        return ""

    district_match = re.fullmatch(r"District\s+(\d+)", normalized, flags=re.IGNORECASE)
    if district_match:
        return f"District {int(district_match.group(1))}"
    if normalized.isdigit():
        return f"District {int(normalized)}"
    return normalized
