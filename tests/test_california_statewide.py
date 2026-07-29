from __future__ import annotations

import sys
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR / "scripts"))

from california_statewide_config import CaliforniaContestSource
from generate_california_statewide_summary import build_contest, contest_county_rows, county_fips, district_contests


class CaliforniaStatewideTests(TestCase):
    def test_contest_county_rows_parses_county_rows_and_skips_percent_rows(self) -> None:
        source = CaliforniaContestSource(2024, "President", "President", "https://example.test/pres.xlsx", "pres.xlsx")
        rows = [
            [None, "Kamala D.\nHarris", "Donald J.\nTrump", "Chase\nOliver"],
            [None, "DEM", "REP", "LIB"],
            ["Alameda", 10, 5, 1],
            ["  Percent", "62.5%", "31.3%", "6.3%"],
            [],
            ["Alpine", 3, 7, 0],
            ["State Totals", 13, 12, 1],
        ]

        with patch("generate_california_statewide_summary.read_first_sheet", return_value=rows):
            counties = contest_county_rows(source)

        self.assertEqual(len(counties), 2)
        self.assertEqual(counties[0]["fips"], "06001")
        self.assertEqual(counties[0]["county_name"], "ALAMEDA")
        self.assertEqual(counties[0]["total_votes"], 16)
        self.assertEqual(counties[0]["winner"]["party"], "DEMOCRAT")
        self.assertEqual(counties[1]["winner"]["party"], "REPUBLICAN")

    def test_build_contest_aggregates_candidate_totals(self) -> None:
        source = CaliforniaContestSource(2024, "U.S. Senate", "U.S. Senate", "https://example.test/senate.xlsx", "senate.xlsx")
        counties = [
            {
                "county_name": "ALAMEDA",
                "total_votes": 15,
                "winner": {"candidate": "A", "party": "DEMOCRAT", "votes": 10},
                "margin_votes": 5,
                "candidates": [
                    {"candidate": "A", "party": "DEMOCRAT", "votes": 10},
                    {"candidate": "B", "party": "REPUBLICAN", "votes": 5},
                ],
            },
            {
                "county_name": "ALPINE",
                "total_votes": 8,
                "winner": {"candidate": "B", "party": "REPUBLICAN", "votes": 6},
                "margin_votes": 4,
                "candidates": [
                    {"candidate": "B", "party": "REPUBLICAN", "votes": 6},
                    {"candidate": "A", "party": "DEMOCRAT", "votes": 2},
                ],
            },
        ]

        with patch("generate_california_statewide_summary.contest_county_rows", return_value=counties):
            contest = build_contest(source, 7)

        self.assertEqual(contest["contest_id"], 7)
        self.assertEqual(contest["total_votes"], 23)
        self.assertEqual(contest["winner"]["candidate"], "A")
        self.assertEqual(contest["margin_votes"], 1)

    def test_district_contests_parse_official_block_format(self) -> None:
        source = CaliforniaContestSource(
            2024,
            "U.S. House",
            "U.S. House",
            "https://example.test/house.xlsx",
            "house.xlsx",
            district=True,
        )
        rows = [
            ["1st Congressional District", None, None],
            [None, "Jane\nDoe*", "John Smith"],
            [None, "DEM", "REP"],
            ["Butte", 10, 20],
            ["Plumas", 7, 3],
            ["District Totals", 17, 23],
            ["Percent", "42.5%", "57.5%"],
            [],
        ]

        with patch("generate_california_statewide_summary.read_first_sheet", return_value=rows):
            contests = district_contests(source, 12)

        self.assertEqual(len(contests), 1)
        contest = contests[0]
        self.assertEqual(contest["contest_id"], 12)
        self.assertEqual(contest["district_label"], "1st Congressional District")
        self.assertEqual(contest["district_number"], 1)
        self.assertEqual(contest["total_votes"], 40)
        self.assertEqual(contest["winner"]["candidate"], "John Smith")
        self.assertEqual(contest["winner"]["party"], "REPUBLICAN")
        self.assertEqual(contest["margin_votes"], 6)
        self.assertEqual([county["county_name"] for county in contest["counties"]], ["BUTTE", "PLUMAS"])
        self.assertEqual([county["fips"] for county in contest["counties"]], ["06007", "06063"])
        self.assertEqual(contest["candidates"][1]["candidate"], "Jane Doe")

    def test_county_fips_rejects_unknown_county(self) -> None:
        with self.assertRaises(RuntimeError):
            county_fips("NOT A COUNTY")
