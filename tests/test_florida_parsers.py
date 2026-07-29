from __future__ import annotations

import sys
from pathlib import Path
from unittest import TestCase


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR / "scripts"))

from florida_precinct_config import FLORIDA_GENERAL_ELECTIONS, normalize_district_label, office_for_contest
from generate_florida_summary import district_number
from import_florida_general import aggregate_rows


class FloridaParserTests(TestCase):
    def test_office_for_configured_statewide_contest(self) -> None:
        election = FLORIDA_GENERAL_ELECTIONS[2024]
        self.assertEqual(office_for_contest(election, "President and Vice President"), "President")
        self.assertEqual(office_for_contest(election, "United States Senator"), "U.S. Senate")

    def test_office_for_district_contest_patterns(self) -> None:
        election = FLORIDA_GENERAL_ELECTIONS[2022]
        self.assertEqual(office_for_contest(election, "Congress 7"), "U.S. House")
        self.assertEqual(office_for_contest(election, "State Senator"), "State Senate")
        self.assertEqual(office_for_contest(election, "House 101"), "State House")
        self.assertIsNone(office_for_contest(election, "County Commissioner"))

    def test_normalize_district_label(self) -> None:
        self.assertEqual(normalize_district_label("Congress 7", ""), "District 7")
        self.assertEqual(normalize_district_label("State Representative", "101"), "District 101")
        self.assertEqual(normalize_district_label("State Senator", " District   12 "), "District 12")
        self.assertEqual(normalize_district_label("Governor", ""), "")

    def test_district_number(self) -> None:
        self.assertEqual(district_number("District 28"), 28)
        self.assertEqual(district_number(" district 7 "), 7)
        self.assertIsNone(district_number(None))
        self.assertIsNone(district_number("At Large"))

    def test_aggregate_rows_combines_write_in_aliases(self) -> None:
        election = FLORIDA_GENERAL_ELECTIONS[2024]
        base_row = {
            "office_name": "President",
            "district_label": "",
            "county_code": "DAD",
            "county_name": "Miami-Dade",
            "election_number": "123",
            "election_date": "11/05/2024",
            "election_name": "General Election",
            "precinct_id": "001",
            "precinct_name": "Precinct 001",
            "contest_name": "President and Vice President",
            "party_code": "",
            "candidate_number": "999",
            "candidate_fl_id": "999",
        }
        rows = [
            {**base_row, "candidate_name": "WriteinVotes", "votes": "2"},
            {**base_row, "candidate_name": "Write-In Votes", "votes": "3"},
        ]

        aggregated = aggregate_rows(election, rows)

        self.assertEqual(len(aggregated), 1)
        self.assertEqual(aggregated[0]["votes"], "5")
