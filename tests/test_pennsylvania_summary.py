from __future__ import annotations

import sys
from pathlib import Path
from unittest import TestCase


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR / "scripts"))

from generate_pennsylvania_summary import materialize_contest, parse_counties
from pennsylvania_config import PennsylvaniaGeneralSource


class PennsylvaniaSummaryTests(TestCase):
    def test_parse_counties_reads_all_county_codes(self) -> None:
        readme = "County Code Table\n-----------------\n01 Adams\n02 Allegheny\n" + "\n".join(f"{code:02d} County {code}" for code in range(3, 68)) + "\n\n"

        counties = parse_counties(readme)

        self.assertEqual(len(counties), 67)
        self.assertEqual(counties[1], "ADAMS")
        self.assertEqual(counties[67], "COUNTY 67")

    def test_materialize_contest_builds_winner_and_counties(self) -> None:
        source = PennsylvaniaGeneralSource(2024, "2024-11-05", "readme", "results", "readme.txt", "results.txt")
        raw = {
            "office": "President",
            "district_number": None,
            "district_label": None,
            "candidates": {("A", "DEMOCRAT"): 15, ("B", "REPUBLICAN"): 10},
            "counties": {
                1: {
                    "fips": "42001",
                    "county_name": "ADAMS",
                    "candidates": {("A", "DEMOCRAT"): 15, ("B", "REPUBLICAN"): 10},
                }
            },
            "source_file_url": "https://example.test/results.txt",
            "quality_grade": "A",
        }

        contest = materialize_contest(raw, 4, source)

        self.assertEqual(contest["contest_id"], 4)
        self.assertEqual(contest["total_votes"], 25)
        self.assertEqual(contest["winner"]["candidate"], "A")
        self.assertEqual(contest["margin_votes"], 5)
        self.assertEqual(contest["counties"][0]["fips"], "42001")
