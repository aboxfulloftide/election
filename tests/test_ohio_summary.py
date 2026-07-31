from __future__ import annotations

import sys
from pathlib import Path
from unittest import TestCase


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR / "scripts"))

from generate_ohio_summary import build_sheet_contests, group_contest_columns, office_for_contest, parse_candidate_label
from ohio_config import OhioSourceWorkbook


class OhioSummaryTests(TestCase):
    def test_parse_candidate_label_reads_party_and_write_in(self) -> None:
        self.assertEqual(parse_candidate_label("Sherrod Brown (D)"), ("Sherrod Brown", "DEMOCRAT"))
        self.assertEqual(parse_candidate_label("Stephen Faris (WI)*"), ("Stephen Faris", "WRITE-IN"))
        self.assertEqual(parse_candidate_label("Richard Duncan and Mitchell Preston Bupp"), ("Richard Duncan and Mitchell Preston Bupp", "NONPARTISAN"))

    def test_office_for_contest_maps_supported_races(self) -> None:
        self.assertEqual(office_for_contest("President and Vice President"), ("President", None, None))
        self.assertEqual(office_for_contest("Governor and Lieutenant Governor"), ("Governor", None, None))
        self.assertEqual(office_for_contest("U.S. Senator"), ("U.S. Senate", None, None))
        self.assertEqual(office_for_contest("Representative to Congress - District 03"), ("U.S. House", 3, "3 Congressional District"))
        self.assertEqual(office_for_contest("State Senator - District 02"), ("State Senate", 2, "2 State Senate District"))
        self.assertEqual(office_for_contest("State Representative - District 49"), ("State House", 49, "49 State House District"))

    def test_group_contest_columns_uses_heading_spans(self) -> None:
        rows = [
            [None, None, None, None, None, None, "President and Vice President", None, "Attorney General", None],
            ["County Name", None, None, None, None, None, "Candidate A (D)", "Candidate B (R)", "Candidate C (D)", "Candidate D (R)"],
        ]

        self.assertEqual(group_contest_columns(rows), [("President and Vice President", [6, 7])])

    def test_build_sheet_contests_materializes_county_rows(self) -> None:
        workbook = OhioSourceWorkbook(
            year=2024,
            election_date="2024-11-05",
            election_name="November 5, 2024 General Election",
            source_url="https://example.test/ohio.xlsx",
            raw_path="data/raw/ohio/example.xlsx",
            sheets=("President and Vice President",),
        )
        rows = [
            [None, None, None, None, None, None, "President and Vice President", None],
            ["County Name", "Region Name", "Media Market", "Registered Voters", "Ballots Counted", "Official Voter Turnout", "Kamala D. Harris and Tim Walz (D)", "Donald J. Trump and JD Vance (R)"],
            ["Total", None, None, 300, 250, 0.8, 100, 150],
            ["Percentage", None, None, None, None, None, 0.4, 0.6],
            ["Adams", "Southwest", "Cincinnati", 100, 90, 0.9, 30, 60],
            ["Allen", "West", "Lima", 200, 160, 0.8, 70, 90],
        ]
        counties = {
            "ADAMS": {"fips": "39001", "county_name": "Adams"},
            "ALLEN": {"fips": "39003", "county_name": "Allen"},
        }

        contests, next_id = build_sheet_contests(workbook, rows, counties, 7)

        self.assertEqual(next_id, 8)
        self.assertEqual(contests[0]["contest_id"], 7)
        self.assertEqual(contests[0]["office"], "President")
        self.assertEqual(contests[0]["total_votes"], 250)
        self.assertEqual(contests[0]["winner"], {"candidate": "Donald J. Trump and JD Vance", "party": "REPUBLICAN", "votes": 150})
        self.assertEqual(len(contests[0]["counties"]), 2)
        self.assertEqual(contests[0]["counties"][0]["total_votes"], 90)
