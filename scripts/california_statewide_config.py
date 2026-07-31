"""Official California statewide source configuration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


SOURCE_NAME = "California Secretary of State"
RAW_DIR = Path("data/raw/official/california")
OUTPUT_PATH = Path("public/results/california-statewide-summary.json")


@dataclass(frozen=True)
class CaliforniaContestSource:
    year: int
    election_date: str
    source_page_url: str
    office: str
    contest_label: str
    url: str
    file_name: str
    district: bool = False


CALIFORNIA_CONTEST_SOURCES = [
    CaliforniaContestSource(
        year=2024,
        election_date="2024-11-05",
        source_page_url="https://www.sos.ca.gov/elections/prior-elections/statewide-election-results/general-election-nov-5-2024/statement-vote",
        office="President",
        contest_label="President",
        url="https://elections.cdn.sos.ca.gov/sov/2024-general/ssov/pres-summary-by-county.xlsx",
        file_name="pres-summary-by-county-2024.xlsx",
    ),
    CaliforniaContestSource(
        year=2024,
        election_date="2024-11-05",
        source_page_url="https://www.sos.ca.gov/elections/prior-elections/statewide-election-results/general-election-nov-5-2024/statement-vote",
        office="U.S. Senate",
        contest_label="U.S. Senate (Full Term)",
        url="https://elections.cdn.sos.ca.gov/sov/2024-general/ssov/us-senate-summary-by-county-ft.xlsx",
        file_name="us-senate-summary-by-county-ft-2024.xlsx",
    ),
    CaliforniaContestSource(
        year=2024,
        election_date="2024-11-05",
        source_page_url="https://www.sos.ca.gov/elections/prior-elections/statewide-election-results/general-election-nov-5-2024/statement-vote",
        office="U.S. Senate",
        contest_label="U.S. Senate (Partial/Unexpired Term)",
        url="https://elections.cdn.sos.ca.gov/sov/2024-general/ssov/us-senate-summary-by-county-pt.xlsx",
        file_name="us-senate-summary-by-county-pt-2024.xlsx",
    ),
    CaliforniaContestSource(
        year=2022,
        election_date="2022-11-08",
        source_page_url="https://www.sos.ca.gov/elections/prior-elections/statewide-election-results/general-election-nov-8-2022/statement-vote",
        office="Governor",
        contest_label="Governor",
        url="https://elections.cdn.sos.ca.gov/sov/2022-general/ssov/governor-summary.xlsx",
        file_name="governor-summary-by-county-2022.xlsx",
    ),
    CaliforniaContestSource(
        year=2022,
        election_date="2022-11-08",
        source_page_url="https://www.sos.ca.gov/elections/prior-elections/statewide-election-results/general-election-nov-8-2022/statement-vote",
        office="U.S. Senate",
        contest_label="U.S. Senate (Full Term)",
        url="https://elections.cdn.sos.ca.gov/sov/2022-general/ssov/us-senate-summary-by-county-ft.xlsx",
        file_name="us-senate-summary-by-county-ft-2022.xlsx",
    ),
    CaliforniaContestSource(
        year=2022,
        election_date="2022-11-08",
        source_page_url="https://www.sos.ca.gov/elections/prior-elections/statewide-election-results/general-election-nov-8-2022/statement-vote",
        office="U.S. Senate",
        contest_label="U.S. Senate (Partial/Unexpired Term)",
        url="https://elections.cdn.sos.ca.gov/sov/2022-general/ssov/us-senate-summary-by-county.xlsx",
        file_name="us-senate-summary-by-county-pt-2022.xlsx",
    ),
    CaliforniaContestSource(
        year=2020,
        election_date="2020-11-03",
        source_page_url="https://www.sos.ca.gov/elections/prior-elections/statewide-election-results/general-election-november-3-2020/statement-vote",
        office="President",
        contest_label="President",
        url="https://elections.cdn.sos.ca.gov/sov/2020-general/sov/18-presidential.xlsx",
        file_name="presidential-by-county-2020.xlsx",
    ),
    CaliforniaContestSource(
        year=2018,
        election_date="2018-11-06",
        source_page_url="https://www.sos.ca.gov/elections/prior-elections/statewide-election-results/general-election-november-6-2018/statement-vote",
        office="Governor",
        contest_label="Governor",
        url="https://elections.cdn.sos.ca.gov/sov/2018-general/sov/21-governor.xls",
        file_name="governor-by-county-2018.xls",
    ),
    CaliforniaContestSource(
        year=2018,
        election_date="2018-11-06",
        source_page_url="https://www.sos.ca.gov/elections/prior-elections/statewide-election-results/general-election-november-6-2018/statement-vote",
        office="U.S. Senate",
        contest_label="U.S. Senate",
        url="https://elections.cdn.sos.ca.gov/sov/2018-general/sov/45-us-senator.xls",
        file_name="us-senate-by-county-2018.xls",
    ),
]


CALIFORNIA_DISTRICT_CONTEST_SOURCES = [
    CaliforniaContestSource(
        year=2024,
        election_date="2024-11-05",
        source_page_url="https://www.sos.ca.gov/elections/prior-elections/statewide-election-results/general-election-nov-5-2024/statement-vote",
        office="U.S. House",
        contest_label="U.S. House",
        url="https://elections.cdn.sos.ca.gov/sov/2024-general/sov/25-us-rep-congress.xlsx",
        file_name="us-house-by-district-2024.xlsx",
        district=True,
    ),
    CaliforniaContestSource(
        year=2024,
        election_date="2024-11-05",
        source_page_url="https://www.sos.ca.gov/elections/prior-elections/statewide-election-results/general-election-nov-5-2024/statement-vote",
        office="State Senate",
        contest_label="State Senate",
        url="https://elections.cdn.sos.ca.gov/sov/2024-general/sov/37-state-senator.xlsx",
        file_name="state-senate-by-district-2024.xlsx",
        district=True,
    ),
    CaliforniaContestSource(
        year=2024,
        election_date="2024-11-05",
        source_page_url="https://www.sos.ca.gov/elections/prior-elections/statewide-election-results/general-election-nov-5-2024/statement-vote",
        office="State Assembly",
        contest_label="State Assembly",
        url="https://elections.cdn.sos.ca.gov/sov/2024-general/sov/42-state-assembly.xlsx",
        file_name="state-assembly-by-district-2024.xlsx",
        district=True,
    ),
    CaliforniaContestSource(
        year=2022,
        election_date="2022-11-08",
        source_page_url="https://www.sos.ca.gov/elections/prior-elections/statewide-election-results/general-election-nov-8-2022/statement-vote",
        office="U.S. House",
        contest_label="U.S. House",
        url="https://elections.cdn.sos.ca.gov/sov/2022-general/sov/48-congress.xlsx",
        file_name="us-house-by-district-2022.xlsx",
        district=True,
    ),
    CaliforniaContestSource(
        year=2022,
        election_date="2022-11-08",
        source_page_url="https://www.sos.ca.gov/elections/prior-elections/statewide-election-results/general-election-nov-8-2022/statement-vote",
        office="State Senate",
        contest_label="State Senate",
        url="https://elections.cdn.sos.ca.gov/sov/2022-general/sov/60-state-senator.xlsx",
        file_name="state-senate-by-district-2022.xlsx",
        district=True,
    ),
    CaliforniaContestSource(
        year=2022,
        election_date="2022-11-08",
        source_page_url="https://www.sos.ca.gov/elections/prior-elections/statewide-election-results/general-election-nov-8-2022/statement-vote",
        office="State Assembly",
        contest_label="State Assembly",
        url="https://elections.cdn.sos.ca.gov/sov/2022-general/sov/65-state-assemblymember.xlsx",
        file_name="state-assembly-by-district-2022.xlsx",
        district=True,
    ),
    CaliforniaContestSource(
        year=2020,
        election_date="2020-11-03",
        source_page_url="https://www.sos.ca.gov/elections/prior-elections/statewide-election-results/general-election-november-3-2020/statement-vote",
        office="U.S. House",
        contest_label="U.S. House",
        url="https://elections.cdn.sos.ca.gov/sov/2020-general/sov/24-us-reps.xlsx",
        file_name="us-house-by-district-2020.xlsx",
        district=True,
    ),
    CaliforniaContestSource(
        year=2020,
        election_date="2020-11-03",
        source_page_url="https://www.sos.ca.gov/elections/prior-elections/statewide-election-results/general-election-november-3-2020/statement-vote",
        office="State Senate",
        contest_label="State Senate",
        url="https://elections.cdn.sos.ca.gov/sov/2020-general/sov/36-state-senate.xlsx",
        file_name="state-senate-by-district-2020.xlsx",
        district=True,
    ),
    CaliforniaContestSource(
        year=2020,
        election_date="2020-11-03",
        source_page_url="https://www.sos.ca.gov/elections/prior-elections/statewide-election-results/general-election-november-3-2020/statement-vote",
        office="State Assembly",
        contest_label="State Assembly",
        url="https://elections.cdn.sos.ca.gov/sov/2020-general/sov/41-state-assembly.xlsx",
        file_name="state-assembly-by-district-2020.xlsx",
        district=True,
    ),
    CaliforniaContestSource(
        year=2018,
        election_date="2018-11-06",
        source_page_url="https://www.sos.ca.gov/elections/prior-elections/statewide-election-results/general-election-november-6-2018/statement-vote",
        office="U.S. House",
        contest_label="U.S. House",
        url="https://elections.cdn.sos.ca.gov/sov/2018-general/sov/48-congress.xls",
        file_name="us-house-by-district-2018.xls",
        district=True,
    ),
    CaliforniaContestSource(
        year=2018,
        election_date="2018-11-06",
        source_page_url="https://www.sos.ca.gov/elections/prior-elections/statewide-election-results/general-election-november-6-2018/statement-vote",
        office="State Senate",
        contest_label="State Senate",
        url="https://elections.cdn.sos.ca.gov/sov/2018-general/sov/62-state-senator.xls",
        file_name="state-senate-by-district-2018.xls",
        district=True,
    ),
    CaliforniaContestSource(
        year=2018,
        election_date="2018-11-06",
        source_page_url="https://www.sos.ca.gov/elections/prior-elections/statewide-election-results/general-election-november-6-2018/statement-vote",
        office="State Assembly",
        contest_label="State Assembly",
        url="https://elections.cdn.sos.ca.gov/sov/2018-general/sov/68-state-assemblymember.xls",
        file_name="state-assembly-by-district-2018.xls",
        district=True,
    ),
]


ALL_CALIFORNIA_CONTEST_SOURCES = CALIFORNIA_CONTEST_SOURCES + CALIFORNIA_DISTRICT_CONTEST_SOURCES


def raw_path(source: CaliforniaContestSource) -> Path:
    return RAW_DIR / source.file_name
